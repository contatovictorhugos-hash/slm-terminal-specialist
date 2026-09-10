import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv
from huggingface_hub import HfApi, create_repo

load_dotenv()

def main():
    parser = argparse.ArgumentParser(description="Publicar modelo fundido ou adaptadores no Hugging Face Hub")
    parser.add_argument("--repo-id", type=str, required=True, help="Identificador do repositorio no Hugging Face (ex: usuario/qwen-terminal-specialist)")
    parser.add_argument("--path", type=str, default="models/fused-qwen-terminal", help="Diretorio local contendo os arquivos a serem enviados")
    parser.add_argument("--private", action="store_true", help="Criar o repositorio como privado")
    args = parser.parse_args()

    token = os.getenv("HF_TOKEN")
    if not token:
        print("[ERRO] Variavel HF_TOKEN nao encontrada no ambiente ou no arquivo .env!")
        print("[INFO] Obtenha seu token em: https://huggingface.co/settings/tokens")
        sys.exit(1)

    local_path = Path(args.path)
    if not local_path.exists():
        print(f"[ERRO] O caminho local '{local_path}' nao existe!")
        sys.exit(1)

    api = HfApi(token=token)

    print("=" * 65)
    print(f"[INFO] Iniciando upload para o Hugging Face Hub")
    print(f"  - Repositorio de destino: {args.repo_id}")
    print(f"  - Diretorio de origem:    {local_path}")
    print(f"  - Visibilidade:           {'Privado' if args.private else 'Publico'}")
    print("=" * 65)

    try:
        print(f"[INFO] Verificando/criando repositorio no Hugging Face...")
        create_repo(repo_id=args.repo_id, token=token, private=args.private, exist_ok=True)

        print(f"[INFO] Enviando arquivos (isso pode levar alguns minutos)...")
        api.upload_folder(
            folder_path=str(local_path),
            repo_id=args.repo_id,
            repo_type="model",
            commit_message="Initial commit: Fused Qwen 2.5 Coder 1.5B for Unix/macOS Zsh"
        )

        print("=" * 65)
        print(f"[OK] Upload concluido com sucesso!")
        print(f"[INFO] Acesse em: https://huggingface.co/{args.repo_id}")
        print("=" * 65)
    except Exception as e:
        print(f"\n[ERRO] Falha durante o upload: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
