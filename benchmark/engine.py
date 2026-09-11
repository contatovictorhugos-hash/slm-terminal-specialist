import os
import time
import json
import tempfile
import subprocess
import urllib.request
from pathlib import Path
from dataclasses import dataclass, field
from typing import Callable, Optional

from benchmark.safety import is_safe_command

@dataclass
class BenchmarkResult:
    case_id: str
    prompt: str
    category: str
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
            
            # Calculo de tokens/segundo atraves dos dados do Ollama se disponivel
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
    except Exception as e:
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
    # Inspeciona violacao de markdown
    if any("```" in l for l in lines) or any(l.startswith("#") for l in lines):
        is_clean = False

    # Filtra marcadores de markdown
    filtered = []
    for l in lines:
        if l.startswith("```"):
            continue
        filtered.append(l)

    cmd = " ".join(filtered).strip()
    return cmd, is_clean

def check_zsh_syntax(cmd: str) -> tuple[bool, str]:
    """
    Valida a sintaxe da gramatica Zsh sem executar o comando.
    """
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
    case_id: str,
    prompt: str,
    category: str,
    setup_fn: Optional[Callable[[Path], None]] = None,
    assertion_fn: Optional[Callable[[Path, subprocess.CompletedProcess], tuple[bool, str]]] = None,
    static_eval_fn: Optional[Callable[[str], tuple[bool, str]]] = None,
    model: str = "term-specialist-q4",
    timeout_sec: float = 4.0
) -> BenchmarkResult:
    """
    Executa um caso de teste completo:
    1. Consulta ao modelo.
    2. Checagem de formato.
    3. Checagem de seguranca.
    4. Checagem sintatica Zsh.
    5. Execucao em Sandbox com Assercao de Estado (ou avaliacao estatica/semantica).
    """
    res = BenchmarkResult(case_id=case_id, prompt=prompt, category=category)

    # 1. Consulta ao modelo
    raw_output, latency_ms, tps = query_ollama(prompt, model=model)
    res.raw_output = raw_output
    res.latency_ms = latency_ms
    res.tokens_per_second = tps

    if not raw_output:
        res.error_detail = "Modelo retornou resposta vazia ou tempo limite esgotado"
        return res

    # 2. Checagem de formato
    cleaned_cmd, passed_format = clean_command(raw_output)
    res.cleaned_command = cleaned_cmd
    res.passed_format = passed_format

    # 3. Checagem de seguranca preventiva
    safe, safety_reason = is_safe_command(cleaned_cmd)
    res.passed_safety = safe
    if not safe:
        res.error_detail = safety_reason
        return res

    # 4. Checagem sintatica Zsh
    syntax_ok, syntax_err = check_zsh_syntax(cleaned_cmd)
    res.passed_syntax = syntax_ok
    if not syntax_ok:
        res.error_detail = f"Erro de sintaxe Zsh: {syntax_err}"

    # 5. Execucao Funcional em Sandbox (se possuir setup e assercao)
    if setup_fn and assertion_fn:
        with tempfile.TemporaryDirectory(prefix="slm_bench_") as tmpdir:
            tmppath = Path(tmpdir)
            try:
                # Cria os arquivos de mock
                setup_fn(tmppath)

                # Executa o comando na sandbox
                exec_proc = subprocess.run(
                    cleaned_cmd,
                    shell=True,
                    cwd=tmppath,
                    capture_output=True,
                    text=True,
                    timeout=timeout_sec,
                    executable="/bin/zsh"
                )
                res.passed_execution = (exec_proc.returncode == 0)

                # Executa as assercoes de estado em disco
                assert_ok, assert_reason = assertion_fn(tmppath, exec_proc)
                res.passed_assertion = assert_ok
                if not assert_ok:
                    res.error_detail = assert_reason

            except subprocess.TimeoutExpired:
                res.passed_execution = False
                res.error_detail = f"Tempo limite de execucao excedido ({timeout_sec}s)"
            except Exception as e:
                res.passed_execution = False
                res.error_detail = f"Falha na execucao: {str(e)}"
    elif static_eval_fn:
        # Avaliacao semantica / dialeto (para casos de Linux GNU vs macOS ou PowerShell)
        static_ok, static_reason = static_eval_fn(cleaned_cmd)
        res.passed_assertion = static_ok
        res.passed_execution = static_ok
        if not static_ok:
            res.error_detail = static_reason
    else:
        # Se nao houver sandbox nem validador customizado, a assercao equivale a sintaxe
        res.passed_execution = res.passed_syntax
        res.passed_assertion = res.passed_syntax

    return res
