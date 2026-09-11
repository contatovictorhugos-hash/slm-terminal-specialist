import os
import re
import json
import time
import random
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from tqdm import tqdm

# 1. Carregar variaveis de ambiente
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("A variavel GEMINI_API_KEY nao foi encontrada no arquivo .env!")

client = genai.Client(api_key=API_KEY)

# 2. Pool de Modelos do Google Gemini e Controle de Taxa
MODELS_POOL = [
    "gemini-3.5-flash-lite",     # 1a opcao: Ultra-rapido, estavel e sem gargalo de 503
    "gemini-flash-lite-latest",  # 2a opcao: Alias oficial de alta disponibilidade
    "gemini-3.7-flash",          # 3a opcao: Fallback avancado
    "gemini-3.8-flash",          # 4a opcao: Fallback avancado
    "gemini-3.6-flash"           # 5a opcao: Maxima fidelidade de comandos
]

MAX_REQS_PER_MODEL = 18
MAX_RETRIES_PER_MODEL = 3

model_status = {
    model: {"calls": 0, "available": True}
    for model in MODELS_POOL
}

# 3. Schemas Pydantic para Saida Estruturada
class CommandPair(BaseModel):
    user_prompt: str = Field(description="Pedido comecando com [macOS], [Linux] ou [PowerShell] seguido da intencao em portugues")
    command: str = Field(description="Comando puro correspondente sem formatacao markdown e sem explicacoes")
    category: str = Field(description="Categoria tematica do comando")

class CommandBatch(BaseModel):
    items: list[CommandPair]

# 4. Catalogo de Categorias por Sistema Operacional
CATEGORIES_BY_OS = {
    "PowerShell": [
        {
            "name": "PowerShell - Arquivos, Pastas e Busca",
            "os_tag": "[PowerShell]",
            "description": "Comandos nativos do PowerShell: Get-ChildItem -Recurse, Remove-Item -Force, New-Item, Copy-Item, Test-Path, Get-ItemProperty, Move-Item.",
            "weight": 0.20,
        },
        {
            "name": "PowerShell - Texto, Logs e Strings",
            "os_tag": "[PowerShell]",
            "description": "Busca e transformacao: Select-String -Pattern, Get-Content -Tail, Measure-Object -Line, (Get-Content f) -replace 'a','b' | Set-Content f, Select-Object -Unique.",
            "weight": 0.20,
        },
        {
            "name": "PowerShell - Processos, Servicos e Sistema",
            "os_tag": "[PowerShell]",
            "description": "Gestao de processos e servicos: Get-Process | Sort-Object CPU, Stop-Process -Name/-Id, Get-Service, Restart-Service, Get-CimInstance.",
            "weight": 0.20,
        },
        {
            "name": "PowerShell - Dados Estruturados, CSV e JSON",
            "os_tag": "[PowerShell]",
            "description": "Pipelines estruturados: Import-Csv | Where-Object | Export-Csv -NoTypeInformation, ConvertFrom-Json, ConvertTo-Json, Group-Object.",
            "weight": 0.20,
        },
        {
            "name": "PowerShell - Rede, Download, Compressao e Utilitarios",
            "os_tag": "[PowerShell]",
            "description": "Utilitarios: Invoke-WebRequest -OutFile, Invoke-RestMethod, Test-NetConnection -Port, Compress-Archive, Expand-Archive, Set-Clipboard.",
            "weight": 0.20,
        },
    ],
    "macOS": [
        {
            "name": "macOS - Utilitarios BSD e Sistema de Arquivos",
            "os_tag": "[macOS]",
            "description": "Comandos BSD macOS: sed -i '' 's///g', stat -f %m, sips -Z 800, pbcopy, pbpaste, open -a, diskutil.",
            "weight": 0.25,
        },
        {
            "name": "macOS - Processos, Portas e launchd",
            "os_tag": "[macOS]",
            "description": "Processos macOS: top -l 1 -o cpu, ps -m -o %cpu,comm, killall Finder, lsof -ti:PORT | xargs kill -9, launchctl.",
            "weight": 0.25,
        },
        {
            "name": "macOS - Pipelines, CSV e Zsh",
            "os_tag": "[macOS]",
            "description": "Filtros Zsh: awk 'FNR==1 && NR!=1 {next} 1' *.csv, sort | uniq, grep -c ., cut -f3, jq.",
            "weight": 0.25,
        },
        {
            "name": "macOS - DevOps, Docker, Git e Brew",
            "os_tag": "[macOS]",
            "description": "DevOps no Mac: docker ps -q | xargs -r docker stop, docker system prune -af, brew cleanup, git status -s.",
            "weight": 0.25,
        },
    ],
    "Linux": [
        {
            "name": "Linux - Utilitarios GNU e Arquivos",
            "os_tag": "[Linux]",
            "description": "Comandos GNU Linux: sed -i 's///g' (sem aspas extras), stat -c %Y, xclip -selection clipboard, xdg-open, lsblk, df -h.",
            "weight": 0.25,
        },
        {
            "name": "Linux - Systemd, Processos e Servicos",
            "os_tag": "[Linux]",
            "description": "Administracao Linux: systemctl restart/status, journalctl -u, ps aux --sort=-%cpu, free -h, ss -tulpn, pidof | xargs kill -9.",
            "weight": 0.25,
        },
        {
            "name": "Linux - Pipelines, CSV e Bash",
            "os_tag": "[Linux]",
            "description": "Filtros Bash: awk 'FNR==1 && NR!=1 {next} 1' *.csv, sort | uniq, grep -c ., cut -d$'\\t' -f3, jq.",
            "weight": 0.25,
        },
        {
            "name": "Linux - DevOps, Docker, Rede e Pacotes",
            "os_tag": "[Linux]",
            "description": "DevOps Linux: docker ps -q | xargs -r docker stop, docker system prune -af, apt-get, ip addr, ip route, ufw.",
            "weight": 0.25,
        },
    ],
    "all": [
        {
            "name": "PowerShell Nativo (Windows / pwsh)",
            "os_tag": "[PowerShell]",
            "description": "Comandos nativos do PowerShell: Get-Process, Stop-Process, Select-String, Get-Content, Set-Content, Get-ChildItem, Invoke-WebRequest, Export-Csv.",
            "weight": 0.40,
        },
        {
            "name": "Matriz OS Contrastiva (Linux GNU vs macOS BSD)",
            "os_tag": "MISTO",
            "description": "Sintaxe contrastiva GNU vs BSD: sed -i vs sed -i '', xclip vs pbcopy, stat -c %Y vs stat -f %m, xdg-open vs open.",
            "weight": 0.30,
        },
        {
            "name": "Filtros e Pipelines Cirurgicos (Benchmark Patching)",
            "os_tag": "MISTO",
            "description": "Filtros precisos Unix (macOS/Linux): awk 'FNR==1 && NR!=1 {next} 1', sort | uniq, grep -c ., cut -f3, lsof -ti:PORT | xargs kill -9.",
            "weight": 0.30,
        },
    ],
}

SYSTEM_PROMPT = """Voce e um compilador especialista em terminal e automacao CLI para macOS (Zsh/BSD), Linux (Bash/GNU) e Windows (PowerShell).
Sua missao e gerar pares sinteticos para treino de uma SLM de terminal.

REGRAS:
1. 'user_prompt': DEVE OBRIGATORIAMENTE comecar com o prefixo do ambiente: [macOS], [Linux] ou [PowerShell].
2. 'command': DEVE ser estritamente o comando executavel puro. Sem blocos markdown (nada de ```) e sem explicacoes.
"""

def get_active_model() -> str | None:
    for model in MODELS_POOL:
        state = model_status[model]
        if state["available"] and state["calls"] < MAX_REQS_PER_MODEL:
            return model
    return None

def generate_batch(category: dict, num_items: int) -> tuple[list[dict], str | None]:
    os_req = category.get("os_tag", "MISTO")
    if os_req == "MISTO":
        prefix_rule = "Todo 'user_prompt' deve comecar com '[macOS] ' ou '[Linux] '."
    else:
        prefix_rule = f"Todo 'user_prompt' DEVE comecar com o prefixo '{os_req} '."

    prompt = f"""Gere exatamente {num_items} pares de treino distintos para:
Categoria: {category['name']}
Detalhes: {category['description']}

Lembre-se:
1. {prefix_rule}
2. O campo 'command' DEVE ser o comando executavel puro, sem markdown."""

    while True:
        current_model = get_active_model()
        if not current_model:
            print("\n[AVISO] Todos os modelos do pool foram esgotados ou estao indisponiveis.")
            return [], None

        success = False
        items = []

        for attempt in range(1, MAX_RETRIES_PER_MODEL + 1):
            try:
                response = client.models.generate_content(
                    model=current_model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        response_mime_type="application/json",
                        response_schema=CommandBatch,
                        temperature=0.75,
                    ),
                )
                batch = CommandBatch.model_validate_json(response.text)
                for it in batch.items:
                    d = it.model_dump()
                    up = d["user_prompt"].strip()
                    # Garante prefixo estrito
                    if os_req in ["[PowerShell]", "[macOS]", "[Linux]"]:
                        if not up.startswith(os_req):
                            clean_up = re.sub(r"^\[(macOS|Linux|PowerShell)\]\s*", "", up)
                            d["user_prompt"] = f"{os_req} {clean_up}"
                    items.append(d)

                model_status[current_model]["calls"] += 1
                success = True
                break

            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    print(f"\n[AVISO] Cota esgotada no modelo {current_model}.")
                    model_status[current_model]["available"] = False
                    break

                print(f"\n[Tentativa {attempt}/{MAX_RETRIES_PER_MODEL}] Falha no modelo {current_model}: {e}")
                if attempt < MAX_RETRIES_PER_MODEL:
                    time.sleep(6)

        if success:
            return items, current_model
        else:
            print(f"\n[ROTACAO] Modelo {current_model} atingiu falhas consecutivas. Alternando...")
            model_status[current_model]["available"] = False

def load_existing_dataset(data_dir: Path) -> list[dict]:
    """Carrega dados existentes preservando tags já atribuídas."""
    pairs = []
    for filename in ["train.jsonl", "valid.jsonl"]:
        filepath = data_dir / filename
        if filepath.exists():
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        obj = json.loads(line)
                        msgs = obj.get("messages", [])
                        user_p = next((m["content"] for m in msgs if m["role"] == "user"), None)
                        cmd = next((m["content"] for m in msgs if m["role"] == "assistant"), None)
                        if user_p and cmd:
                            pairs.append({"user_prompt": user_p, "command": cmd, "category": "existente"})

    # Se houver registros legados sem tag de SO, distribui 50/50 entre macOS e Linux
    result = []
    for idx, item in enumerate(pairs):
        up = item["user_prompt"].strip()
        cmd = item["command"].strip()
        if up.startswith("[macOS]") or up.startswith("[Linux]") or up.startswith("[PowerShell]"):
            result.append({"user_prompt": up, "command": cmd, "category": item["category"]})
        else:
            tag = "[macOS]" if (idx % 2 == 0) else "[Linux]"
            result.append({"user_prompt": f"{tag} {up}", "command": cmd, "category": item["category"]})

    return result

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Gerador de Dataset Sintetico Tri-OS (macOS, Linux, PowerShell)")
    parser.add_argument("--add", "-n", type=int, default=150, help="Quantidade de registros a adicionar (padrao: 150)")
    parser.add_argument("--os", "--focus-os", type=str, default="PowerShell", choices=["PowerShell", "macOS", "Linux", "all"], dest="target_os", help="Sistema operacional alvo (padrao: PowerShell)")
    parser.add_argument("--delay", "-d", type=int, default=10, help="Intervalo em segundos entre chamadas bem-sucedidas (padrao: 10s)")
    parser.add_argument("--batch-size", "-b", type=int, default=25, help="Quantidade de exemplos por requisicao a API (padrao: 25)")
    args = parser.parse_args()

    output_dir = Path("dataset/data")
    output_dir.mkdir(parents=True, exist_ok=True)

    all_pairs = load_existing_dataset(output_dir)
    initial_count = len(all_pairs)
    target_total = initial_count + args.add
    categories = CATEGORIES_BY_OS[args.target_os]

    print("=" * 65)
    print(f"[INFO] Sintese de Dados para SLM de Terminal")
    print(f"  - SO Alvo:             {args.target_os}")
    print(f"  - Registros a Gerar:   {args.add}")
    print(f"  - Base Atual:          {initial_count} registros")
    print(f"  - Meta Consolidada:    {target_total} registros")
    print(f"  - Delay:               {args.delay}s")
    print(f"  - Tamanho do Lote:     {args.batch_size}")
    print(f"  - Modelos no Pool:     {', '.join(MODELS_POOL)}")
    print("=" * 65)

    pbar = tqdm(total=target_total, initial=initial_count, desc="Total acumulado")

    while len(all_pairs) < target_total:
        active = get_active_model()
        if not active:
            print("\n[STOP] Todos os modelos do pool foram esgotados ou estao indisponiveis.")
            break

        cat = random.choices(categories, weights=[c["weight"] for c in categories])[0]
        remaining = target_total - len(all_pairs)
        batch_size = min(args.batch_size, remaining)

        items, used_model = generate_batch(cat, num_items=batch_size)

        if items:
            all_pairs.extend(items)
            pbar.update(len(items))
            pbar.set_postfix({
                "modelo": used_model.replace("gemini-", ""),
                "total": len(all_pairs),
            })
            time.sleep(args.delay)
        else:
            if not get_active_model():
                break

    pbar.close()

    # Embaralha e divide: 90% treino e 10% validacao
    random.shuffle(all_pairs)
    split_idx = int(len(all_pairs) * 0.9)
    train_data = all_pairs[:split_idx]
    valid_data = all_pairs[split_idx:]

    SYSTEM_ROLE_CONTENT = "Voce e um especialista em terminal CLI (macOS Zsh, Linux Bash e Windows PowerShell). Responda unica e exclusivamente com o comando pronto para execucao, sem explicacoes e sem formatacao markdown."

    def save_jsonl(data: list[dict], filepath: Path):
        with open(filepath, "w", encoding="utf-8") as f:
            for item in data:
                entry = {
                    "messages": [
                        {"role": "system", "content": SYSTEM_ROLE_CONTENT},
                        {"role": "user", "content": item["user_prompt"].strip()},
                        {"role": "assistant", "content": item["command"].strip()},
                    ]
                }
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    train_path = output_dir / "train.jsonl"
    valid_path = output_dir / "valid.jsonl"

    save_jsonl(train_data, train_path)
    save_jsonl(valid_data, valid_path)

    mac_cnt = sum(1 for p in all_pairs if p["user_prompt"].startswith("[macOS]"))
    linux_cnt = sum(1 for p in all_pairs if p["user_prompt"].startswith("[Linux]"))
    pwsh_cnt = sum(1 for p in all_pairs if p["user_prompt"].startswith("[PowerShell]"))

    print("\n" + "=" * 65)
    print("[RELATORIO CONSOLIDADO DA BASE V2.0]")
    print(f"  - Total de Exemplos:      {len(all_pairs)}")
    print(f"  - Cobertura [macOS]:         {mac_cnt} ({mac_cnt/len(all_pairs)*100:.1f}%)")
    print(f"  - Cobertura [Linux]:         {linux_cnt} ({linux_cnt/len(all_pairs)*100:.1f}%)")
    print(f"  - Cobertura [PowerShell]:    {pwsh_cnt} ({pwsh_cnt/len(all_pairs)*100:.1f}%)")
    print(f"[OK] Treino:    {train_path} ({len(train_data)} pares)")
    print(f"[OK] Validacao: {valid_path} ({len(valid_data)} pares)")
    print("=" * 65)

if __name__ == "__main__":
    main()
