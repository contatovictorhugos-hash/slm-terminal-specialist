from pathlib import Path
import subprocess
import re

def get_devops_cases():
    cases = []

    # 1. Matar processo na porta 3000
    def static_dev01(cmd: str):
        if ("lsof" in cmd or "fuser" in cmd) and "kill" in cmd and "3000" in cmd:
            return True, ""
        return False, f"Comando nao utiliza lsof/fuser e kill apontando para 3000: {cmd}"
    cases.append({
        "id": "devops_01",
        "prompt": "achar o processo que esta travando a porta 3000 e matar",
        "category": "DevOps & Redes",
        "static_eval": static_dev01
    })

    # 2. Consumo de RAM no macOS
    def static_dev02(cmd: str):
        if any(tool in cmd for tool in ["vm_stat", "top", "memory_pressure"]):
            return True, ""
        return False, f"Comando nao invocou utilitarios de memoria do macOS: {cmd}"
    cases.append({
        "id": "devops_02",
        "prompt": "exibir o consumo de memoria ram no macos",
        "category": "DevOps & Redes",
        "static_eval": static_dev02
    })

    # 3. Headers HTTP via curl
    def static_dev03(cmd: str):
        if "curl" in cmd and ("-I" in cmd or "--head" in cmd or "-i" in cmd):
            return True, ""
        return False, f"Curl nao utilizou flag de inspecao de cabecalhos: {cmd}"
    cases.append({
        "id": "devops_03",
        "prompt": "fazer uma requisicao http get para https://api.github.com exibindo apenas os cabecalhos de resposta",
        "category": "DevOps & Redes",
        "static_eval": static_dev03
    })

    # 4. Docker ps IDs
    def static_dev04(cmd: str):
        if "docker" in cmd and "ps" in cmd and ("-q" in cmd or "--quiet" in cmd):
            return True, ""
        return False, f"Comando docker nao utilizou flag -q para extrair apenas IDs: {cmd}"
    cases.append({
        "id": "devops_04",
        "prompt": "listar todos os containers docker em execucao ou parados exibindo apenas seus ids",
        "category": "DevOps & Redes",
        "static_eval": static_dev04
    })

    # 5. Git log resumido (testado funcionalmente em sandbox)
    def setup_dev05(p: Path):
        subprocess.run(["git", "init"], cwd=p, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Tester"], cwd=p, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=p, capture_output=True)
        for i in range(5):
            (p / f"file_{i}.txt").write_text(f"v{i}", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=p, capture_output=True)
            subprocess.run(["git", "commit", "-m", f"commit {i}"], cwd=p, capture_output=True)
    def assert_dev05(p: Path, res: subprocess.CompletedProcess):
        lines = [l for l in res.stdout.strip().splitlines() if l.strip()]
        if 1 <= len(lines) <= 5:
            return True, ""
        return False, f"Esperava ate 5 commits resumidos, obteve {len(lines)} linhas"
    cases.append({
        "id": "devops_05",
        "prompt": "ver os ultimos 5 commits do git em formato resumido de uma linha",
        "category": "DevOps & Redes",
        "setup": setup_dev05,
        "assertion": assert_dev05
    })

    # 6. Espaco em disco humano
    def static_dev06(cmd: str):
        if "df" in cmd and ("-h" in cmd or "-H" in cmd):
            return True, ""
        return False, f"Comando nao invocou df com flag human-readable (-h): {cmd}"
    cases.append({
        "id": "devops_06",
        "prompt": "inspecionar o espaco livre e ocupado em disco em formato legivel humano",
        "category": "DevOps & Redes",
        "static_eval": static_dev06
    })

    # 7. Portas abertas escutando
    def static_dev07(cmd: str):
        if ("lsof" in cmd and "LISTEN" in cmd) or ("netstat" in cmd) or ("ss" in cmd):
            return True, ""
        return False, f"Comando nao utilizou lsof ou netstat com filtro de escuta: {cmd}"
    cases.append({
        "id": "devops_07",
        "prompt": "listar todas as portas tcp atualmente abertas e em escuta na maquina",
        "category": "DevOps & Redes",
        "static_eval": static_dev07
    })

    # 8. Follow de arquivo de log
    def static_dev08(cmd: str):
        if "tail" in cmd and "-f" in cmd and "syslog.log" in cmd:
            return True, ""
        return False, f"Comando nao utilizou tail -f apontando para syslog.log: {cmd}"
    cases.append({
        "id": "devops_08",
        "prompt": "acompanhar em tempo real as novas linhas adicionadas ao arquivo syslog.log",
        "category": "DevOps & Redes",
        "static_eval": static_dev08
    })

    # 9. Processo consumindo mais CPU
    def static_dev09(cmd: str):
        if ("ps" in cmd or "top" in cmd) and ("cpu" in cmd.lower() or "%cpu" in cmd.lower()):
            return True, ""
        return False, f"Comando nao filtra processos ordenando por CPU: {cmd}"
    cases.append({
        "id": "devops_09",
        "prompt": "encontrar os 5 processos que estao consumindo mais cpu no sistema",
        "category": "DevOps & Redes",
        "static_eval": static_dev09
    })

    # 10. Download com curl preservando nome
    def static_dev10(cmd: str):
        if ("curl" in cmd and ("-O" in cmd or "-o" in cmd)) or "wget" in cmd:
            return True, ""
        return False, f"Comando de download nao preserva nome remoto de saida: {cmd}"
    cases.append({
        "id": "devops_10",
        "prompt": "fazer download de um arquivo remoto https://example.com/arquivo.zip salvando com o mesmo nome",
        "category": "DevOps & Redes",
        "static_eval": static_dev10
    })

    return cases
