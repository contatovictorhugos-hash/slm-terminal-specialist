from pathlib import Path
import subprocess

def get_tabular_cases():
    cases = []

    # 1. Juncao de CSVs com cabecalho unico
    def setup_tab01(p: Path):
        (p / "a.csv").write_text("id,nome\n1,Ana\n", encoding="utf-8")
        (p / "b.csv").write_text("id,nome\n2,Bia\n", encoding="utf-8")
    def assert_tab01(p: Path, res: subprocess.CompletedProcess):
        out_f = p / "consolidado.csv"
        if not out_f.exists():
            # Pode ter gravado na saida padrao se o prompt nao especificou arquivo
            return False, "Arquivo consolidado.csv nao foi gerado"
        lines = [l.strip() for l in out_f.read_text(encoding="utf-8").splitlines() if l.strip()]
        if len(lines) != 3:
            return False, f"Esperado 3 linhas, obtido {len(lines)}"
        if lines[0] != "id,nome":
            return False, f"Cabecalho incorreto: {lines[0]}"
        return True, ""
    cases.append({
        "id": "tab_01",
        "prompt": "juntar todos os csvs da pasta ignorando o cabecalho a partir do segundo salvando em consolidado.csv",
        "category": "Filtros & Tabular",
        "setup": setup_tab01,
        "assertion": assert_tab01
    })

    # 2. Extracao de coluna especifica em CSV
    def setup_tab02(p: Path):
        (p / "dados.csv").write_text("id,email,status\n1,a@x.com,ativo\n2,b@x.com,inativo\n", encoding="utf-8")
    def assert_tab02(p: Path, res: subprocess.CompletedProcess):
        out = res.stdout.strip()
        if "a@x.com" in out and "b@x.com" in out:
            return True, ""
        return False, f"Email nao encontrado na saida: {out}"
    cases.append({
        "id": "tab_02",
        "prompt": "imprimir a segunda coluna do arquivo dados.csv separado por virgula",
        "category": "Filtros & Tabular",
        "setup": setup_tab02,
        "assertion": assert_tab02
    })

    # 3. Extracao de coluna em TSV (tabulacao)
    def setup_tab03(p: Path):
        (p / "vendas.tsv").write_text("1\tprodutoA\t100\n2\tprodutoB\t250\n", encoding="utf-8")
    def assert_tab03(p: Path, res: subprocess.CompletedProcess):
        out = res.stdout.strip()
        if "100" in out and "250" in out:
            return True, ""
        return False, f"Valores de vendas nao encontrados na saida: {out}"
    cases.append({
        "id": "tab_03",
        "prompt": "imprimir apenas a terceira coluna do arquivo vendas.tsv delimitado por tabulacao",
        "category": "Filtros & Tabular",
        "setup": setup_tab03,
        "assertion": assert_tab03
    })

    # 4. Contar linhas excluindo vazias
    def setup_tab04(p: Path):
        (p / "access.log").write_text("log1\n\nlog2\nlog3\n\nlog4\nlog5\n", encoding="utf-8")
    def assert_tab04(p: Path, res: subprocess.CompletedProcess):
        out = res.stdout.strip()
        # Procura pelo numero 5 na saida
        if "5" in out:
            return True, ""
        return False, f"Esperava contagem 5, obteve: {out}"
    cases.append({
        "id": "tab_04",
        "prompt": "contar o numero de linhas nao vazias do arquivo access.log",
        "category": "Filtros & Tabular",
        "setup": setup_tab04,
        "assertion": assert_tab04
    })

    # 5. Ordenar e remover duplicatas
    def setup_tab05(p: Path):
        (p / "nomes.txt").write_text("Carlos\nAna\nCarlos\nBeto\nAna\n", encoding="utf-8")
    def assert_tab05(p: Path, res: subprocess.CompletedProcess):
        out_f = p / "unicos.txt"
        if out_f.exists():
            lines = [l.strip() for l in out_f.read_text(encoding="utf-8").splitlines() if l.strip()]
        else:
            lines = [l.strip() for l in res.stdout.splitlines() if l.strip()]
        if lines == ["Ana", "Beto", "Carlos"]:
            return True, ""
        return False, f"Resultado de ordenacao inesperado: {lines}"
    cases.append({
        "id": "tab_05",
        "prompt": "ordenar o arquivo nomes.txt em ordem alfabetica e remover linhas duplicadas salvando em unicos.txt",
        "category": "Filtros & Tabular",
        "setup": setup_tab05,
        "assertion": assert_tab05
    })

    # 6. Soma com awk
    def setup_tab06(p: Path):
        (p / "valores.txt").write_text("10\n20\n30\n40\n", encoding="utf-8")
    def assert_tab06(p: Path, res: subprocess.CompletedProcess):
        out = res.stdout.strip()
        if "100" in out:
            return True, ""
        return False, f"Esperava soma 100, obteve: {out}"
    cases.append({
        "id": "tab_06",
        "prompt": "somar todos os numeros da primeira coluna do arquivo valores.txt usando awk",
        "category": "Filtros & Tabular",
        "setup": setup_tab06,
        "assertion": assert_tab06
    })

    # 7. Filtro condicional por coluna
    def setup_tab07(p: Path):
        (p / "clientes.csv").write_text("id,nome,status\n1,Carlos,ativo\n2,Marcos,inativo\n3,Lucas,ativo\n", encoding="utf-8")
    def assert_tab07(p: Path, res: subprocess.CompletedProcess):
        out = res.stdout.strip()
        if "Carlos" in out and "Lucas" in out and "Marcos" not in out:
            return True, ""
        return False, f"Filtro falhou: {out}"
    cases.append({
        "id": "tab_07",
        "prompt": "filtrar o arquivo clientes.csv exibindo apenas linhas onde a terceira coluna e igual a ativo",
        "category": "Filtros & Tabular",
        "setup": setup_tab07,
        "assertion": assert_tab07
    })

    # 8. Extracao com jq
    def setup_tab08(p: Path):
        (p / "usuarios.json").write_text('[{"name": "Alice"}, {"name": "Bob"}]', encoding="utf-8")
    def assert_tab08(p: Path, res: subprocess.CompletedProcess):
        out = res.stdout.strip()
        if "Alice" in out and "Bob" in out:
            return True, ""
        return False, f"Extracao jq falhou: {out}"
    cases.append({
        "id": "tab_08",
        "prompt": "extrair o campo name de todos os objetos do arquivo usuarios.json usando jq",
        "category": "Filtros & Tabular",
        "setup": setup_tab08,
        "assertion": assert_tab08
    })

    # 9. Frequencia de ocorrencias com sort e uniq -c
    def setup_tab09(p: Path):
        (p / "palavras.txt").write_text("erro\nsucesso\nerro\nerro\nsucesso\n", encoding="utf-8")
    def assert_tab09(p: Path, res: subprocess.CompletedProcess):
        out = res.stdout.strip()
        if "erro" in out and "3" in out and "2" in out:
            return True, ""
        return False, f"Contagem de frequencia falhou: {out}"
    cases.append({
        "id": "tab_09",
        "prompt": "contar a frequencia de ocorrencia de cada linha no arquivo palavras.txt ordenando pelo mais frequente",
        "category": "Filtros & Tabular",
        "setup": setup_tab09,
        "assertion": assert_tab09
    })

    # 10. Substituicao in-place no arquivo
    def setup_tab10(p: Path):
        (p / "config.env").write_text("AMBIENTE=DEV\nMODO=DEV\n", encoding="utf-8")
    def assert_tab10(p: Path, res: subprocess.CompletedProcess):
        content = (p / "config.env").read_text(encoding="utf-8")
        if "AMBIENTE=PROD" in content and "MODO=PROD" in content and "DEV" not in content:
            return True, ""
        return False, f"Substituicao falhou. Conteudo atual: {content}"
    cases.append({
        "id": "tab_10",
        "prompt": "substituir todas as ocorrencias de DEV por PROD no arquivo config.env",
        "category": "Filtros & Tabular",
        "setup": setup_tab10,
        "assertion": assert_tab10
    })

    return cases
