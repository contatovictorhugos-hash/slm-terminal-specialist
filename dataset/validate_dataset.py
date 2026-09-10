import json
import re
from pathlib import Path

def validate_dataset_file(filepath: Path) -> dict:
    if not filepath.exists():
        return {"error": f"Arquivo {filepath} nao encontrado."}

    total = 0
    errors = []
    markdown_blocks = 0
    emoji_count = 0
    prompts = set()
    duplicates = 0
    commands = []

    # Regex para capturar emojis Unicode
    emoji_pattern = re.compile(r"[\U00010000-\U0010ffff]", flags=re.UNICODE)

    with open(filepath, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            total += 1
            try:
                data = json.loads(line)
                msgs = data.get("messages", [])
                if len(msgs) != 3:
                    errors.append(f"Linha {idx}: esperado 3 mensagens, encontrado {len(msgs)}")
                    continue

                roles = [m.get("role") for m in msgs]
                if roles != ["system", "user", "assistant"]:
                    errors.append(f"Linha {idx}: sequencia de roles invalida: {roles}")
                    continue

                user_msg = msgs[1].get("content", "")
                asst_msg = msgs[2].get("content", "")

                if not user_msg:
                    errors.append(f"Linha {idx}: mensagem de usuario vazia")
                if not asst_msg:
                    errors.append(f"Linha {idx}: comando de assistente vazio")

                if user_msg in prompts:
                    duplicates += 1
                prompts.add(user_msg)

                # Checagem de markdown residual
                if "```" in asst_msg:
                    markdown_blocks += 1

                # Checagem de emojis
                if emoji_pattern.search(user_msg) or emoji_pattern.search(asst_msg):
                    emoji_count += 1

                first_token = asst_msg.strip().split()[0] if asst_msg.strip() else "EMPTY"
                commands.append(first_token)

            except Exception as e:
                errors.append(f"Linha {idx}: erro de parsing JSON ({e})")

    command_freq = {}
    for c in commands:
        command_freq[c] = command_freq.get(c, 0) + 1

    top_commands = sorted(command_freq.items(), key=lambda x: x[1], reverse=True)[:12]

    return {
        "total": total,
        "errors": errors,
        "duplicates": duplicates,
        "markdown_blocks": markdown_blocks,
        "emoji_count": emoji_count,
        "unique_commands": len(command_freq),
        "top_commands": top_commands,
    }

def main():
    train_file = Path("dataset/data/train.jsonl")
    valid_file = Path("dataset/data/valid.jsonl")

    print("=" * 65)
    print("[AUDITORIA DE QUALIDADE E INTEGRIDADE DO DATASET]")
    print("=" * 65)

    train_res = validate_dataset_file(train_file)
    print(f"Base de Treino ({train_file.name}):")
    print(f"  - Total de registros:           {train_res['total']}")
    print(f"  - Erros estruturais ou de JSON: {len(train_res['errors'])}")
    print(f"  - Duplicatas exatas de prompt:  {train_res['duplicates']}")
    print(f"  - Blocos de markdown indevidos: {train_res['markdown_blocks']}")
    print(f"  - Emojis detectados:            {train_res['emoji_count']}")
    print(f"  - Comandos Unix distintos:      {train_res['unique_commands']}")
    print("  - Principais utilitarios identificados:")
    for cmd, count in train_res["top_commands"]:
        print(f"      * {cmd:<15} ({count} ocorrencias)")

    print("-" * 65)

    valid_res = validate_dataset_file(valid_file)
    print(f"Base de Validacao ({valid_file.name}):")
    print(f"  - Total de registros:           {valid_res['total']}")
    print(f"  - Erros estruturais ou de JSON: {len(valid_res['errors'])}")
    print(f"  - Duplicatas exatas de prompt:  {valid_res['duplicates']}")
    print(f"  - Blocos de markdown indevidos: {valid_res['markdown_blocks']}")
    print(f"  - Emojis detectados:            {valid_res['emoji_count']}")
    print(f"  - Comandos Unix distintos:      {valid_res['unique_commands']}")
    print("=" * 65)

    # Verificacao de amostras aleatorias para inspecao humana
    print("\n[AMOSTRAS REAIS DA BASE DE TREINO]")
    print("-" * 65)
    with open(train_file, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
        sample_indices = [0, len(lines)//4, len(lines)//2, (3*len(lines))//4, len(lines)-1]
        for i in sample_indices:
            entry = json.loads(lines[i])
            user_text = entry["messages"][1]["content"]
            cmd_text = entry["messages"][2]["content"]
            print(f"Exemplo #{i+1}:")
            print(f"  Prompt:  {user_text}")
            print(f"  Comando: {cmd_text}")
            print()

if __name__ == "__main__":
    main()
