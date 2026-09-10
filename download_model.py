import os
import sys

# Ativar variavel de alta performance
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"

from huggingface_hub import snapshot_download

MODEL_ID = "Qwen/Qwen2.5-Coder-1.5B-Instruct"

def main():
    token = os.getenv("HF_TOKEN")
    print("=" * 60)
    print(f"[INFO] Iniciando download do modelo: {MODEL_ID}")
    if token:
        print(f"[INFO] Token detectado: {token[:8]}...{token[-4:]}")
    else:
        print("[AVISO] Nenhum HF_TOKEN detectado no ambiente.")
    print("=" * 60)

    try:
        path = snapshot_download(
            repo_id=MODEL_ID,
            token=token,
            max_workers=8
        )
        print("\n" + "=" * 60)
        print(f"[OK] Download concluido com sucesso!")
        print(f"[INFO] Arquivos salvos em: {path}")
        print("=" * 60)
    except Exception as e:
        print(f"\n[ERRO] Falha no download: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
