import os
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

# 2. Pool de Modelos e Controle de Cotas
MODELS_POOL = [
    "gemini-3.5-flash-lite",     # 1a opcao: Ultra-rapido, estavel e sem gargalo de 503
    "gemini-flash-lite-latest",  # 2a opcao: Alias oficial de alta disponibilidade
    "gemini-3.7-flash",          # 3a opcao: Fallback avancado
    "gemini-3.8-flash",          # 4a opcao: Fallback avancado
    "gemini-3.6-flash"           # 5a opcao: Maxima fidelidade de comandos
]

MAX_REQS_PER_MODEL = 15  # Teto de seguranca por modelo
MAX_RETRIES_PER_MODEL = 3  # Tentativas antes de alternar de modelo

# Estado de cada modelo no pool
model_status = {
    model: {"calls": 0, "available": True}
    for model in MODELS_POOL
}

# 3. Schemas de Validacao Estruturada com Pydantic
class CommandPair(BaseModel):
    user_prompt: str = Field(description="Pedido do usuario em portugues do Brasil natural e coloquial")
    command: str = Field(description="Comando puro do terminal Unix/macOS Zsh, sem markdown e sem explicacoes")
    category: str = Field(description="Categoria do comando")

class CommandBatch(BaseModel):
    items: list[CommandPair]

# 4. Distribuicao das Categorias (conforme a Constituicao do Projeto)
CATEGORIES = [
    {
        "name": "Manipulacao de Arquivos e Midia",
        "description": "Juntar PDFs (pdfunite/gs), converter imagens (sips/magick), manipular audio e video com ffmpeg, compactar (tar, zip, rsync), renomear em massa.",
        "weight": 0.35,
    },
    {
        "name": "Filtros e Processamento Tabular",
        "description": "Comandos com awk, sed, grep, cut, sort, uniq, jq, uniao de CSVs preservando apenas o primeiro cabecalho, contagem e extracao de colunas.",
        "weight": 0.30,
    },
    {
        "name": "DevOps, Rede e Administracao de Sistema",
        "description": "Achar e matar processos em portas especificas (lsof, kill), monitorar memoria e CPU no macOS (top, ps, vm_stat), certificados SSL com curl, Git e Docker.",
        "weight": 0.25,
    },
    {
        "name": "One-liners Complexos e Pipelines Zsh",
        "description": "Pipelines encadeados com multiplos pipes (|), xargs paralelos, python3 -c one-liners rapidos, substituicao de comandos.",
        "weight": 0.10,
    }
]

SYSTEM_PROMPT = """Voce e um especialista em terminal Unix e Zsh no macOS (Apple Silicon).
Sua missao e gerar pares sinteticos de alta fidelidade para treinar uma SLM especialista em terminal.

REGRAS RIGIDAS:
1. 'user_prompt': Deve ser uma intencao realista em portugues do Brasil (coloquial, direto, com ou sem acentos).
2. 'command': Deve ser APENAS a linha de comando pura executavel.
   - NUNCA inclua explicacoes, comentarios ou markdown (nada de ```bash).
   - Use comandos compativeis com macOS (utilitarios BSD quando aplicavel, ou ferramentas comuns como ffmpeg, jq, git, docker).
3. Varie o nivel de complexidade e vocabulario a cada lote.
"""

def get_active_model() -> str | None:
    """Retorna o proximo modelo do pool disponivel e com cota."""
    for model in MODELS_POOL:
        state = model_status[model]
        if state["available"] and state["calls"] < MAX_REQS_PER_MODEL:
            return model
    return None

def generate_batch_with_fallback(category: dict, num_items: int) -> tuple[list[dict], str | None]:
    """
    Tenta gerar o lote com o modelo ativo.
    Se o modelo falhar 3 vezes (ex: 503 ou erro temporario), marca-o como indisponivel
    e pula imediatamente para o proximo modelo do pool.
    """
    prompt = f"""Gere exatamente {num_items} pares de treino distintos para a categoria:
Categoria: {category['name']}
Detalhes: {category['description']}

Gere casos de uso diversificados, variando termos em portugues e comandos reais de terminal."""

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
                    )
                )
                batch = CommandBatch.model_validate_json(response.text)
                items = [item.model_dump() for item in batch.items]
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
            # 3 falhas consecutivas: marca o modelo como indisponivel nesta rodada e tenta o proximo
            print(f"\n[ROTAÇÃO] Modelo {current_model} atingiu {MAX_RETRIES_PER_MODEL} falhas. Alternando para o proximo modelo do pool...")
            model_status[current_model]["available"] = False

def load_existing_data(data_dir: Path) -> list[dict]:
    """Carrega dados ja gerados anteriormente para nao perder amostras."""
    existing = []
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
                            existing.append({"user_prompt": user_p, "command": cmd, "category": "existente"})
    return existing

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Gerador de Dataset com Rotacao Automatica de Modelos")
    parser.add_argument("--total", type=int, default=300, help="Quantidade total desejada de comandos")
    parser.add_argument("--batch-size", type=int, default=25, help="Quantidade por chamada a API")
    parser.add_argument("--delay", type=int, default=15, help="Intervalo em segundos entre chamadas com sucesso")
    args = parser.parse_args()

    output_dir = Path("dataset/data")
    output_dir.mkdir(parents=True, exist_ok=True)

    all_pairs = load_existing_data(output_dir)
    initial_count = len(all_pairs)

    print("=" * 60)
    print("[INFO] Gerador de Dataset com Rotacao por Falha e Protecao de Cota")
    print(f"  - Meta total: {args.total} exemplos")
    print(f"  - Exemplos existentes preservados: {initial_count}")
    print(f"  - Novos a gerar: {max(0, args.total - initial_count)}")
    print(f"  - Modelos no Pool: {', '.join(MODELS_POOL)}")
    print(f"  - Limite seguro por modelo: {MAX_REQS_PER_MODEL} requisicoes")
    print(f"  - Intervalo configurado: {args.delay}s")
    print("=" * 60)

    pbar = tqdm(total=args.total, initial=initial_count, desc="Total acumulado")

    while len(all_pairs) < args.total:
        active = get_active_model()
        if not active:
            print("\n[STOP] Todos os modelos do pool foram esgotados ou estao indisponiveis.")
            break

        cat = random.choices(CATEGORIES, weights=[c["weight"] for c in CATEGORIES])[0]
        remaining = args.total - len(all_pairs)
        batch_size = min(args.batch_size, remaining)

        items, used_model = generate_batch_with_fallback(cat, num_items=batch_size)

        if items:
            all_pairs.extend(items)
            pbar.update(len(items))
            pbar.set_postfix({
                "modelo": used_model.replace("gemini-", ""),
                "reqs": f"{model_status[used_model]['calls']}/{MAX_REQS_PER_MODEL}",
                "total": len(all_pairs)
            })
            time.sleep(args.delay)
        else:
            # Se nao conseguiu com nenhum modelo disponivel
            if not get_active_model():
                break

    pbar.close()

    # Embaralhar para distribuir uniformly os exemplos
    random.shuffle(all_pairs)

    # Divisao 90% treino e 10% validacao
    split_idx = int(len(all_pairs) * 0.9)
    train_data = all_pairs[:split_idx]
    valid_data = all_pairs[split_idx:]

    SYSTEM_ROLE_CONTENT = "Voce e um especialista em terminal Unix/macOS Zsh. Responda unica e exclusivamente com o comando pronto para execucao, sem explicacoes e sem formatacao markdown."

    def save_jsonl(data: list[dict], filepath: Path):
        with open(filepath, "w", encoding="utf-8") as f:
            for item in data:
                entry = {
                    "messages": [
                        {"role": "system", "content": SYSTEM_ROLE_CONTENT},
                        {"role": "user", "content": item["user_prompt"].strip()},
                        {"role": "assistant", "content": item["command"].strip()}
                    ]
                }
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    train_path = output_dir / "train.jsonl"
    valid_path = output_dir / "valid.jsonl"

    save_jsonl(train_data, train_path)
    save_jsonl(valid_data, valid_path)

    print("\n" + "=" * 60)
    print("[RELATORIO DA RODADA]")
    for model, state in model_status.items():
        status_txt = "ativo" if state["available"] else "indisponivel/esgotado"
        print(f"  - {model}: {state['calls']}/{MAX_REQS_PER_MODEL} requisicoes (status: {status_txt})")
    print(f"  - Total consolidado no dataset: {len(all_pairs)} comandos")
    print(f"[OK] Treino:    {train_path} ({len(train_data)} pares)")
    print(f"[OK] Validacao: {valid_path} ({len(valid_data)} pares)")
    print("=" * 60)

if __name__ == "__main__":
    main()
