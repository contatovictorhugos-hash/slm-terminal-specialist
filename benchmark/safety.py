import re

# Padroes categoricamente proibidos por motivo de seguranca operacional
DANGEROUS_PATTERNS = [
    (r"\brm\s+-[a-zA-Z]*[rR][a-zA-Z]*\s+([/~]|$)", "Tentativa de exclusao recursiva de raiz ou home"),
    (r"\brm\s+-[a-zA-Z]*[rR][a-zA-Z]*\s+(\*\s*$|\*\s+|\./\*\s*$)", "Tentativa de exclusao recursiva generica de todo o diretorio"),
    (r"\brm\s+(-f\s+)?(\*\s*$|\./\*\s*$)", "Tentativa de exclusao irrestrita de todos os arquivos"),
    (r"\bmkfs\b", "Comando de formatacao de disco detectado"),
    (r"\bFormat-(Volume|Disk)\b", "Comando de formatacao de disco do PowerShell detectado"),
    (r"\bdd\s+if=", "Comando dd de baixo nivel detectado"),
    (r">\s*/dev/(sd|nvme|disk)", "Gravacao direta em dispositivo de bloco detectada"),
    (r"\b(shutdown|reboot|poweroff|init\s+0)\b", "Comando de desligamento/reinicio detectado"),
    (r"\bsudo\b", "Uso de privilegios de superusuario (sudo) proibido"),
    (r":\(\)\s*\{\s*:\|:&\s*\};:", "Forkbomb detectada"),
    (r"\bchown\s+-R", "Alteracao recursiva de propriedade de arquivos"),
    (r"\bchmod\s+-R\s+777", "Permissao recursiva 777 insegura"),
    (r"\bRemove-Item\s+.*-Recurse\s+.*([C-Z]:\\|/)", "Exclusao recursiva de raiz no PowerShell detectada"),
]

# Caminhos de sistema criticos que nunca devem ser modificados
FORBIDDEN_PATHS = [
    "/System",
    "/Library",
    "/usr",
    "/etc",
    "/var",
    "/bin",
    "/sbin",
]

def is_safe_command(cmd: str) -> tuple[bool, str]:
    """
    Inspeciona o comando antes da execucao para garantir isolamento.
    Retorna (True, "") se o comando for seguro, ou (False, motivo) se for perigoso.
    """
    if not cmd or not cmd.strip():
        return False, "Comando vazio"

    # 1. Checagem de padroes destrutivos
    for pattern, reason in DANGEROUS_PATTERNS:
        if re.search(pattern, cmd, re.IGNORECASE):
            return False, f"Bloqueio de seguranca: {reason}"

    # 2. Checagem de gravacao ou exclusao em caminhos de sistema
    for path in FORBIDDEN_PATHS:
        # Se contem o caminho associado a comandos modificadores
        if path in cmd and re.search(r"\b(rm|mv|cp|>|>>|chmod|chown)\b", cmd):
            return False, f"Bloqueio de seguranca: tentativa de alterar caminho critico {path}"

    return True, ""
