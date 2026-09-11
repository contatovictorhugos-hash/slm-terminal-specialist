from pathlib import Path
import subprocess
import tarfile

def get_files_cases():
    cases = []

    # 1. Renomeacao em lote de extensoes
    def setup_f01(p: Path):
        (p / "doc1.txt").write_text("conteudo 1", encoding="utf-8")
        (p / "doc2.txt").write_text("conteudo 2", encoding="utf-8")
        (p / "doc3.txt").write_text("conteudo 3", encoding="utf-8")
    def assert_f01(p: Path, res: subprocess.CompletedProcess):
        mds = list(p.glob("*.md"))
        txts = list(p.glob("*.txt"))
        if len(mds) == 3 and len(txts) == 0:
            return True, ""
        return False, f"Esperava 3 .md e 0 .txt. Encontrado: {len(mds)} md, {len(txts)} txt"
    cases.append({
        "id": "file_01",
        "prompt": "mudar a extensao de todos os arquivos txt para md no diretorio atual",
        "category": "Arquivos & Midia",
        "setup": setup_f01,
        "assertion": assert_f01
    })

    # 2. Compactacao tar.gz
    def setup_f02(p: Path):
        logs_dir = p / "logs"
        logs_dir.mkdir()
        (logs_dir / "app.log").write_text("log data", encoding="utf-8")
    def assert_f02(p: Path, res: subprocess.CompletedProcess):
        tars = list(p.glob("*.tar.gz"))
        if not tars:
            return False, "Nenhum arquivo .tar.gz encontrado"
        # Valida integridade do tar
        try:
            with tarfile.open(tars[0], "r:gz") as tar:
                names = tar.getnames()
                if any("app.log" in n for n in names):
                    return True, ""
            return False, f"app.log nao encontrado no arquivo tar: {names}"
        except Exception as e:
            return False, f"Arquivo tar invalido ou corrompido: {e}"
    cases.append({
        "id": "file_02",
        "prompt": "criar um arquivo tar.gz compactado da pasta logs chamado backup.tar.gz",
        "category": "Arquivos & Midia",
        "setup": setup_f02,
        "assertion": assert_f02
    })

    # 3. Compactacao zip excluindo .DS_Store
    def setup_f03(p: Path):
        docs_dir = p / "docs"
        docs_dir.mkdir()
        (docs_dir / "relatorio.txt").write_text("relatorio", encoding="utf-8")
        (docs_dir / ".DS_Store").write_text("lixo", encoding="utf-8")
    def assert_f03(p: Path, res: subprocess.CompletedProcess):
        zips = list(p.glob("*.zip"))
        if not zips:
            return False, "Nenhum arquivo zip gerado"
        check = subprocess.run(["zipinfo", "-1", str(zips[0])], capture_output=True, text=True)
        if ".DS_Store" in check.stdout:
            return False, ".DS_Store foi incluido no zip indevidamente"
        if "relatorio.txt" in check.stdout:
            return True, ""
        return False, "relatorio.txt nao encontrado no zip"
    cases.append({
        "id": "file_03",
        "prompt": "compactar a pasta docs em zip excluindo arquivos .DS_Store",
        "category": "Arquivos & Midia",
        "setup": setup_f03,
        "assertion": assert_f03
    })

    # 4. Encontrar arquivos por extensao
    def setup_f04(p: Path):
        (p / "app.log").write_text("log", encoding="utf-8")
        (p / "error.log").write_text("error", encoding="utf-8")
        (p / "dados.csv").write_text("csv", encoding="utf-8")
    def assert_f04(p: Path, res: subprocess.CompletedProcess):
        out = res.stdout
        if "app.log" in out and "error.log" in out and "dados.csv" not in out:
            return True, ""
        return False, f"Busca de logs falhou: {out}"
    cases.append({
        "id": "file_04",
        "prompt": "encontrar todos os arquivos com extensao .log na pasta atual",
        "category": "Arquivos & Midia",
        "setup": setup_f04,
        "assertion": assert_f04
    })

    # 5. Excluir arquivos temporarios .tmp
    def setup_f05(p: Path):
        (p / "temp1.tmp").write_text("temp", encoding="utf-8")
        (p / "temp2.tmp").write_text("temp", encoding="utf-8")
        (p / "permanente.txt").write_text("guardar", encoding="utf-8")
    def assert_f05(p: Path, res: subprocess.CompletedProcess):
        tmps = list(p.glob("*.tmp"))
        if len(tmps) == 0 and (p / "permanente.txt").exists():
            return True, ""
        return False, f"Arquivos tmp ainda existem: {tmps}"
    cases.append({
        "id": "file_05",
        "prompt": "apagar todos os arquivos com extensao .tmp no diretorio atual",
        "category": "Arquivos & Midia",
        "setup": setup_f05,
        "assertion": assert_f05
    })

    # 6. Descompactar tar.gz
    def setup_f06(p: Path):
        (p / "item.txt").write_text("conteudo descompactado", encoding="utf-8")
        with tarfile.open(p / "arquivo.tar.gz", "w:gz") as tar:
            tar.add(p / "item.txt", arcname="item.txt")
        (p / "item.txt").unlink()
    def assert_f06(p: Path, res: subprocess.CompletedProcess):
        if (p / "item.txt").exists():
            return True, ""
        return False, "item.txt nao foi extraido do arquivo tar.gz"
    cases.append({
        "id": "file_06",
        "prompt": "descompactar o arquivo arquivo.tar.gz no diretorio atual",
        "category": "Arquivos & Midia",
        "setup": setup_f06,
        "assertion": assert_f06
    })

    # 7. Copia recursiva
    def setup_f07(p: Path):
        src = p / "origem"
        src.mkdir()
        (src / "arquivo_a.txt").write_text("A", encoding="utf-8")
        (src / "arquivo_b.txt").write_text("B", encoding="utf-8")
        (p / "destino").mkdir()
    def assert_f07(p: Path, res: subprocess.CompletedProcess):
        dest = p / "destino"
        found = list(dest.rglob("*.txt"))
        if len(found) >= 2:
            return True, ""
        return False, f"Arquivos nao foram copiados para o destino: {found}"
    cases.append({
        "id": "file_07",
        "prompt": "copiar recursivamente todos os arquivos da pasta origem para a pasta destino",
        "category": "Arquivos & Midia",
        "setup": setup_f07,
        "assertion": assert_f07
    })

    # 8. Encontrar arquivos vazios (0 bytes)
    def setup_f08(p: Path):
        (p / "vazio1.txt").write_text("", encoding="utf-8")
        (p / "vazio2.txt").write_text("", encoding="utf-8")
        (p / "cheio.txt").write_text("tem dados aqui", encoding="utf-8")
    def assert_f08(p: Path, res: subprocess.CompletedProcess):
        out = res.stdout
        if "vazio1.txt" in out and "vazio2.txt" in out and "cheio.txt" not in out:
            return True, ""
        return False, f"Filtro de arquivos vazios falhou: {out}"
    cases.append({
        "id": "file_08",
        "prompt": "encontrar todos os arquivos com tamanho zero bytes na pasta atual",
        "category": "Arquivos & Midia",
        "setup": setup_f08,
        "assertion": assert_f08
    })

    # 9. Calcular hash SHA-256
    def setup_f09(p: Path):
        (p / "documento.pdf").write_text("conteudo para hash", encoding="utf-8")
    def assert_f09(p: Path, res: subprocess.CompletedProcess):
        out = res.stdout.strip()
        # SHA256 possui 64 caracteres hexadecimais
        import re
        if re.search(r"\b[a-fA-F0-9]{64}\b", out):
            return True, ""
        return False, f"Hash SHA-256 nao identificado na saida: {out}"
    cases.append({
        "id": "file_09",
        "prompt": "calcular o hash sha256 do arquivo documento.pdf",
        "category": "Arquivos & Midia",
        "setup": setup_f09,
        "assertion": assert_f09
    })

    # 10. Criacao de arvore aninhada de pastas
    def setup_f10(p: Path):
        pass
    def assert_f10(p: Path, res: subprocess.CompletedProcess):
        target = p / "app" / "core" / "services"
        if target.is_dir():
            return True, ""
        return False, f"Diretorio aninhado {target} nao foi criado"
    cases.append({
        "id": "file_10",
        "prompt": "criar a arvore de diretorios app/core/services de uma vez so",
        "category": "Arquivos & Midia",
        "setup": setup_f10,
        "assertion": assert_f10
    })

    return cases
