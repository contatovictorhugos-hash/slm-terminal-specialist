from pathlib import Path
import subprocess
import re

def get_os_matrix_cases():
    cases = []

    # ==========================================
    # 1. Ecossistema macOS (Dialeto BSD / Darwin)
    # ==========================================

    # mac_01: sed in-place no macOS (exige aspas vazias '')
    def eval_mac01(cmd: str):
        # No macOS BSD, sed -i exige aspas vazias ou extensao de backup: sed -i '' ou sed -i ""
        if "sed" in cmd and (re.search(r"-i\s*['\"]{2}", cmd) or re.search(r"-i['\"]{2}", cmd)):
            return True, ""
        return False, f"sed no macOS deve utilizar -i '' (sintaxe BSD). Obtido: {cmd}"
    cases.append({
        "id": "os_mac_01",
        "prompt": "substituir a palavra erro por aviso diretamente no arquivo notas.txt no macos",
        "category": "Matriz OS (macOS BSD)",
        "target_os": "macOS",
        "static_eval": eval_mac01
    })

    # mac_02: clipboard no macOS (pbcopy)
    def eval_mac02(cmd: str):
        if "pbcopy" in cmd and "chave.pub" in cmd:
            return True, ""
        return False, f"Area de transferencia nativa no macOS deve utilizar pbcopy: {cmd}"
    cases.append({
        "id": "os_mac_02",
        "prompt": "copiar o conteudo do arquivo chave.pub para a area de transferencia no macos",
        "category": "Matriz OS (macOS BSD)",
        "target_os": "macOS",
        "static_eval": eval_mac02
    })

    # mac_03: manipulador nativo de imagens no macOS (sips)
    def eval_mac03(cmd: str):
        if "sips" in cmd or "magick" in cmd:
            return True, ""
        return False, f"Esperado utilitario nativo sips (ou ImageMagick) para macOS: {cmd}"
    cases.append({
        "id": "os_mac_03",
        "prompt": "redimensionar a imagem foto.jpg para largura de 800 pixels mantendo a proporcao no macos",
        "category": "Matriz OS (macOS BSD)",
        "target_os": "macOS",
        "static_eval": eval_mac03
    })

    # mac_04: abrir no finder (open .)
    def eval_mac04(cmd: str):
        if "open" in cmd and "." in cmd:
            return True, ""
        return False, f"Esperado comando 'open .' nativo do macOS: {cmd}"
    cases.append({
        "id": "os_mac_04",
        "prompt": "abrir a pasta atual no finder pelo terminal",
        "category": "Matriz OS (macOS BSD)",
        "target_os": "macOS",
        "static_eval": eval_mac04
    })

    # ==========================================
    # 2. Ecossistema Linux (Dialeto GNU)
    # ==========================================

    # linux_01: sed in-place no Linux GNU (sem aspas vazias)
    def eval_linux01(cmd: str):
        # No Linux GNU, sed -i nao usa aspas vazias
        if "sed" in cmd and ("-i" in cmd or "--in-place" in cmd):
            if "''" not in cmd and '""' not in cmd:
                return True, ""
            return False, f"No Linux GNU sed nao deve usar aspas vazias apos -i: {cmd}"
        return False, f"Esperava comando sed com flag -i: {cmd}"
    cases.append({
        "id": "os_linux_01",
        "prompt": "substituir a palavra erro por aviso diretamente no arquivo notas.txt no linux",
        "category": "Matriz OS (Linux GNU)",
        "target_os": "Linux",
        "static_eval": eval_linux01
    })

    # linux_02: clipboard no Linux (xclip / xsel / wl-copy)
    def eval_linux02(cmd: str):
        if any(tool in cmd for tool in ["xclip", "xsel", "wl-copy"]):
            return True, ""
        return False, f"Esperado xclip, xsel ou wl-copy para clipboard no Linux: {cmd}"
    cases.append({
        "id": "os_linux_02",
        "prompt": "copiar o conteudo do arquivo chave.pub para a area de transferencia no linux",
        "category": "Matriz OS (Linux GNU)",
        "target_os": "Linux",
        "static_eval": eval_linux02
    })

    # linux_03: abrir arquivo padrao no Linux (xdg-open)
    def eval_linux03(cmd: str):
        if "xdg-open" in cmd:
            return True, ""
        return False, f"Esperado utilitario xdg-open para Linux: {cmd}"
    cases.append({
        "id": "os_linux_03",
        "prompt": "abrir o arquivo relatorio.pdf no aplicativo padrao pelo terminal no linux",
        "category": "Matriz OS (Linux GNU)",
        "target_os": "Linux",
        "static_eval": eval_linux03
    })

    # ==========================================
    # 3. Traducao de PowerShell para Unix POSIX
    # ==========================================

    # pwsh_01: Get-Process -> ps
    def eval_pwsh01(cmd: str):
        if ("ps" in cmd or "top" in cmd) and "Get-Process" not in cmd:
            return True, ""
        return False, f"Esperado traducao para ps ou top (evitando sintaxe PowerShell): {cmd}"
    cases.append({
        "id": "os_pwsh_01",
        "prompt": "[macOS] como faco o equivalente unix ao comando powershell Get-Process para listar processos",
        "category": "Matriz OS (PowerShell ➔ POSIX)",
        "target_os": "macOS",
        "static_eval": eval_pwsh01
    })

    # pwsh_02: Select-String -> grep
    def eval_pwsh02(cmd: str):
        if "grep" in cmd and "Select-String" not in cmd and "erro" in cmd:
            return True, ""
        return False, f"Esperado traducao de Select-String para grep: {cmd}"
    cases.append({
        "id": "os_pwsh_02",
        "prompt": "[macOS] como faco o equivalente unix ao comando powershell Select-String 'erro' em log.txt",
        "category": "Matriz OS (PowerShell ➔ POSIX)",
        "target_os": "macOS",
        "static_eval": eval_pwsh02
    })

    # pwsh_03: Get-Content -Tail -> tail -n
    def eval_pwsh03(cmd: str):
        if "tail" in cmd and "20" in cmd and "Get-Content" not in cmd:
            return True, ""
        return False, f"Esperado traducao de Get-Content -Tail para tail: {cmd}"
    cases.append({
        "id": "os_pwsh_03",
        "prompt": "[macOS] como faco o equivalente unix do comando powershell Get-Content arquivo.txt -Tail 20",
        "category": "Matriz OS (PowerShell ➔ POSIX)",
        "target_os": "macOS",
        "static_eval": eval_pwsh03
    })

    # ==========================================
    # 4. Ecossistema Windows PowerShell Nativo
    # ==========================================

    # pwsh_nat_01: Listar processos por memoria
    def eval_pwsh_nat01(cmd: str):
        if "Get-Process" in cmd and ("Sort-Object" in cmd or "sort" in cmd) and ("WorkingSet" in cmd or "WS" in cmd):
            return True, ""
        return False, f"Esperado cmdlet Get-Process ordenando por WorkingSet: {cmd}"
    cases.append({
        "id": "pwsh_nat_01",
        "prompt": "listar os 10 processos que estao consumindo mais memoria ram",
        "category": "Matriz OS (PowerShell Nativo)",
        "target_os": "PowerShell",
        "static_eval": eval_pwsh_nat01
    })

    # pwsh_nat_02: Select-String em logs
    def eval_pwsh_nat02(cmd: str):
        if "Select-String" in cmd and "erro" in cmd.lower():
            return True, ""
        return False, f"Esperado cmdlet Select-String buscando padrao 'erro': {cmd}"
    cases.append({
        "id": "pwsh_nat_02",
        "prompt": "buscar a palavra erro nos arquivos de log",
        "category": "Matriz OS (PowerShell Nativo)",
        "target_os": "PowerShell",
        "static_eval": eval_pwsh_nat02
    })

    # pwsh_nat_03: Get-Content -Tail
    def eval_pwsh_nat03(cmd: str):
        if "Get-Content" in cmd and "app.log" in cmd and ("-Tail" in cmd or "-Last" in cmd or "20" in cmd):
            return True, ""
        return False, f"Esperado cmdlet Get-Content com flag -Tail apontando para app.log: {cmd}"
    cases.append({
        "id": "pwsh_nat_03",
        "prompt": "ler as ultimas 20 linhas do arquivo app.log",
        "category": "Matriz OS (PowerShell Nativo)",
        "target_os": "PowerShell",
        "static_eval": eval_pwsh_nat03
    })

    # pwsh_nat_04: Stop-Process por nome
    def eval_pwsh_nat04(cmd: str):
        if "Stop-Process" in cmd and "node" in cmd:
            return True, ""
        return False, f"Esperado cmdlet Stop-Process com parametro -Name node: {cmd}"
    cases.append({
        "id": "pwsh_nat_04",
        "prompt": "parar todos os processos com o nome node",
        "category": "Matriz OS (PowerShell Nativo)",
        "target_os": "PowerShell",
        "static_eval": eval_pwsh_nat04
    })

    # pwsh_nat_05: Get-PSDrive para espaco em disco
    def eval_pwsh_nat05(cmd: str):
        if any(tool in cmd for tool in ["Get-PSDrive", "Get-Volume", "Get-CimInstance"]):
            return True, ""
        return False, f"Esperado cmdlet Get-PSDrive ou Get-Volume para inspecao de disco: {cmd}"
    cases.append({
        "id": "pwsh_nat_05",
        "prompt": "ver quanto espaco tenho no disco",
        "category": "Matriz OS (PowerShell Nativo)",
        "target_os": "PowerShell",
        "static_eval": eval_pwsh_nat05
    })

    return cases
