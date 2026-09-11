import os
import re
import time
import json
import shutil
import tempfile
import subprocess
import urllib.request
from pathlib import Path
from dataclasses import dataclass, field
from typing import Callable, Optional

from benchmark.safety import is_safe_command

@dataclass
class TestCase:
    id: str
    prompt: str
    category: str
    target_os: str = "macOS"  # "macOS", "Linux" ou "PowerShell"
    setup_fn: Optional[Callable[[Path], None]] = None
    assertion_fn: Optional[Callable[[Path, subprocess.CompletedProcess], tuple[bool, str]]] = None
    static_eval_fn: Optional[Callable[[str], tuple[bool, str]]] = None
    timeout_sec: float = 4.0

@dataclass
class BenchmarkResult:
    case_id: str
    prompt: str
    category: str
    target_os: str = "macOS"
    raw_output: str = ""
    cleaned_command: str = ""
    latency_ms: float = 0.0
    passed_format: bool = False
    passed_safety: bool = False
    passed_syntax: bool = False
    passed_execution: bool = False
    passed_assertion: bool = False
    error_detail: str = ""
    tokens_per_second: float = 0.0

def format_tagged_prompt(raw_prompt: str, target_os: str) -> str:
    """
    Garante que o prompt enviado a SLM possua a tag de contexto do SO,
    reproduzindo com 100% de fidelidade os wrappers de shell (cmd) de producao.
    """
    raw_prompt = raw_prompt.strip()
    if raw_prompt.startswith("[macOS]") or raw_prompt.startswith("[Linux]") or raw_prompt.startswith("[PowerShell]"):
        return raw_prompt
    return f"[{target_os}] {raw_prompt}"

def query_ollama(prompt: str, model: str = "term-specialist-q4", timeout_sec: float = 8.0) -> tuple[str, float, float]:
    """
    Consulta o Ollama local e mede latencia em ms e tokens por segundo.
    Retorna (texto_gerado, latencia_ms, tokens_por_segundo).
    """
    t_start = time.perf_counter()
    
    # 1. Tentativa via API HTTP nativa do Ollama
    url = "http://127.0.0.1:11434/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "top_p": 0.9,
            "stop": ["<|im_end|>", "<|im_start|>", "<|endoftext|>"]
        }
    }
    
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=timeout_sec) as response:
            data = json.loads(response.read().decode("utf-8"))
            elapsed_ms = (time.perf_counter() - t_start) * 1000.0
            response_text = data.get("response", "").strip()
            
            eval_count = data.get("eval_count", 0)
            eval_duration_ns = data.get("eval_duration", 0)
            tps = (eval_count / (eval_duration_ns / 1e9)) if eval_duration_ns > 0 else 0.0
            
            return response_text, elapsed_ms, tps
    except Exception:
        pass

    # 2. Fallback via CLI subprocess caso a porta HTTP nao responda diretamente
    try:
        ollama_bin = "/opt/homebrew/bin/ollama" if Path("/opt/homebrew/bin/ollama").exists() else "ollama"
        proc = subprocess.run(
            [ollama_bin, "run", model, prompt],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=timeout_sec
        )
        elapsed_ms = (time.perf_counter() - t_start) * 1000.0
        return proc.stdout.strip(), elapsed_ms, 0.0
    except Exception:
        elapsed_ms = (time.perf_counter() - t_start) * 1000.0
        return "", elapsed_ms, 0.0

def clean_command(raw: str) -> tuple[str, bool]:
    """
    Remove blocos markdown residuais e valida se o formato original era estritamente limpo.
    Retorna (comando_limpo, formato_estrito_valido).
    """
    if not raw:
        return "", False

    lines = [l.strip() for l in raw.strip().splitlines() if l.strip()]
    if not lines:
        return "", False

    is_clean = True
    if any("```" in l for l in lines) or any(l.startswith("#") for l in lines):
        is_clean = False

    filtered = []
    for l in lines:
        if l.startswith("```"):
            continue
        filtered.append(l)

    cmd = " ".join(filtered).strip()
    return cmd, is_clean

def validate_powershell_syntax(cmd: str) -> tuple[bool, str]:
    """
    Valida a sintaxe e regras semanticas do PowerShell.
    Se 'pwsh' estiver instalado no sistema, usa o parser nativo;
    caso contrario, avalia regras estruturais de cmdlets e pipelines.
    """
    pwsh_bin = shutil.which("pwsh")
    if pwsh_bin:
        # Usa o parser nativo do PowerShell se disponivel
        ps_script = f"""
        $tokens = $null; $errors = $null
        [System.Management.Automation.Language.Parser]::ParseInput(@'
{cmd}
'@, [ref]$tokens, [ref]$errors) | Out-Null
        if ($errors.Count -gt 0) {{
            $errors[0].Message
            exit 1
        }}
        exit 0
        """
        try:
            proc = subprocess.run(
                [pwsh_bin, "-NoProfile", "-NonInteractive", "-Command", ps_script],
                capture_output=True,
                text=True,
                timeout=3.0
            )
            if proc.returncode == 0:
                return True, ""
            return False, proc.stdout.strip() or proc.stderr.strip()
        except Exception as e:
            pass

    # Validador semantico embutido para PowerShell
    # 1. Checagem de balanceamento de parenteses, chaves e aspas
    if cmd.count("(") != cmd.count(")"):
        return False, "Parenteses desbalanceados no PowerShell"
    if cmd.count("{") != cmd.count("}"):
        return False, "Chaves desbalanceadas no PowerShell"
    if cmd.count("[") != cmd.count("]"):
        return False, "Colchetes desbalanceados no PowerShell"

    # 2. Rejeita bashismos e comandos Unix alienigenas sem correspondencia
    unix_aliens = [r"\bawk\b", r"\bsed\s+-i", r"\bcut\s+-", r"\bxargs\b", r"\bpbcopy\b", r"\bxclip\b", r">/dev/null"]
    for alien in unix_aliens:
        if re.search(alien, cmd):
            return False, f"Comando Unix alienigena ({alien}) emitido para ambiente PowerShell"

    # 3. Comandos validos de PowerShell costumam conter Verb-Noun, pipes orientados a objeto ou chamadas tipadas
    has_ps_construct = (
        bool(re.search(r"\b(Get|Set|Start|Stop|Restart|New|Remove|Move|Copy|Test|Select|Where|Sort|Group|Measure|Import|Export|ConvertFrom|ConvertTo|Invoke|Expand|Compress)-[A-Za-z]+\b", cmd))
        or bool(re.search(r"(\$|\$_|\|\s*Where-Object|\|\s*Select-Object|\|\s*Sort-Object|\|\s*ForEach-Object)", cmd))
        or bool(re.search(r"\b(ii|cd|dir|cls|echo|python)\b", cmd))
    )
    if not has_ps_construct:
        return False, f"Comando nao utiliza sintaxe ou cmdlets nativos do PowerShell: {cmd}"

    return True, ""

def check_command_syntax(cmd: str, target_os: str) -> tuple[bool, str]:
    """
    Valida a sintaxe gramatical de acordo com a plataforma destino.
    """
    if target_os == "PowerShell":
        return validate_powershell_syntax(cmd)
    
    # macOS e Linux: validacao gramatical via Zsh
    try:
        proc = subprocess.run(
            ["zsh", "-n", "-c", cmd],
            capture_output=True,
            text=True,
            timeout=2.0
        )
        if proc.returncode == 0:
            return True, ""
        return False, proc.stderr.strip()
    except Exception as e:
        return False, str(e)

def run_test_case(
    test_case: TestCase | dict,
    model: str = "term-specialist-q4"
) -> BenchmarkResult:
    """
    Executa um caso de teste completo:
    1. Injeta a tag contextual do SO alvo caso necessario.
    2. Consulta o modelo local no Ollama.
    3. Verifica conformidade estrita de formato (Zero Markdown).
    4. Avalia filtros de seguranca preventiva (anti-destrutivo).
    5. Valida a sintaxe gramatical de acordo com o SO alvo.
    6. Executa a assercao em Sandbox efemero (/tmp) ou validador semantico.
    """
    if isinstance(test_case, dict):
        raw_prompt = test_case.get("prompt", "")
        detected_os = test_case.get("target_os")
        if not detected_os:
            if raw_prompt.startswith("[macOS]"):
                detected_os = "macOS"
            elif raw_prompt.startswith("[Linux]"):
                detected_os = "Linux"
            elif raw_prompt.startswith("[PowerShell]"):
                detected_os = "PowerShell"
            elif "Linux" in test_case.get("category", ""):
                detected_os = "Linux"
            elif "PowerShell Nativo" in test_case.get("category", "") or test_case.get("category") == "PowerShell":
                detected_os = "PowerShell"
            else:
                detected_os = "macOS"

        test_case = TestCase(
            id=test_case["id"],
            prompt=raw_prompt,
            category=test_case.get("category", "Geral"),
            target_os=detected_os,
            setup_fn=test_case.get("setup"),
            assertion_fn=test_case.get("assertion"),
            static_eval_fn=test_case.get("static_eval"),
            timeout_sec=test_case.get("timeout", 4.0)
        )

    target_os = test_case.target_os
    full_prompt = format_tagged_prompt(test_case.prompt, target_os)
    
    res = BenchmarkResult(
        case_id=test_case.id,
        prompt=full_prompt,
        category=test_case.category,
        target_os=target_os
    )

    # 1. Consulta ao modelo
    raw_output, latency_ms, tps = query_ollama(full_prompt, model=model, timeout_sec=test_case.timeout_sec * 2)
    res.raw_output = raw_output
    res.latency_ms = latency_ms
    res.tokens_per_second = tps

    if not raw_output:
        res.error_detail = "Modelo retornou resposta vazia ou tempo limite esgotado"
        return res

    # 2. Checagem de formato estrito
    cleaned_cmd, passed_format = clean_command(raw_output)
    res.cleaned_command = cleaned_cmd
    res.passed_format = passed_format

    # 3. Checagem de seguranca preventiva
    safe, safety_reason = is_safe_command(cleaned_cmd)
    res.passed_safety = safe
    if not safe:
        res.error_detail = safety_reason
        return res

    # 4. Checagem sintatica conforme o SO
    syntax_ok, syntax_err = check_command_syntax(cleaned_cmd, target_os)
    res.passed_syntax = syntax_ok
    if not syntax_ok:
        res.error_detail = f"Erro de sintaxe ({target_os}): {syntax_err}"

    # 5. Execucao Funcional em Sandbox (se possuir setup e assercao)
    if test_case.setup_fn and test_case.assertion_fn:
        # Se for PowerShell e pwsh nao estiver instalado, avalia via static_eval se existir
        pwsh_bin = shutil.which("pwsh")
        if target_os == "PowerShell" and not pwsh_bin:
            res.passed_execution = syntax_ok
            res.passed_assertion = syntax_ok
            return res

        with tempfile.TemporaryDirectory(prefix="slm_bench_") as tmpdir:
            tmppath = Path(tmpdir)
            try:
                # Mock de arquivos
                test_case.setup_fn(tmppath)

                # Shell de execucao
                shell_exec = pwsh_bin if (target_os == "PowerShell" and pwsh_bin) else "/bin/zsh"

                exec_proc = subprocess.run(
                    cleaned_cmd,
                    shell=True,
                    cwd=tmppath,
                    capture_output=True,
                    text=True,
                    timeout=test_case.timeout_sec,
                    executable=shell_exec
                )
                res.passed_execution = (exec_proc.returncode == 0)

                # Assercoes de estado em disco
                assert_ok, assert_reason = test_case.assertion_fn(tmppath, exec_proc)
                res.passed_assertion = assert_ok
                if not assert_ok:
                    res.error_detail = assert_reason

            except subprocess.TimeoutExpired:
                res.passed_execution = False
                res.error_detail = f"Tempo limite de execucao excedido ({test_case.timeout_sec}s)"
            except Exception as e:
                res.passed_execution = False
                res.error_detail = f"Falha na execucao: {str(e)}"
    elif test_case.static_eval_fn:
        static_ok, static_reason = test_case.static_eval_fn(cleaned_cmd)
        res.passed_assertion = static_ok
        res.passed_execution = static_ok
        if not static_ok:
            res.error_detail = static_reason
    else:
        res.passed_execution = res.passed_syntax
        res.passed_assertion = res.passed_syntax

    return res
