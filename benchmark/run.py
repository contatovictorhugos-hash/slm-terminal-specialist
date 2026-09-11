import sys
import time
from pathlib import Path
from datetime import datetime

# Adiciona a raiz do projeto ao sys.path para importacao dos modulos
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from benchmark.engine import run_test_case, BenchmarkResult
from benchmark.cases.test_tabular import get_tabular_cases
from benchmark.cases.test_files import get_files_cases
from benchmark.cases.test_devops import get_devops_cases
from benchmark.cases.test_os_matrix import get_os_matrix_cases

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Executor Oficial de Benchmark - SLM Especialista em Terminal")
    parser.add_argument("--model", type=str, default="term-specialist-q4", help="Nome do modelo no Ollama a ser avaliado")
    parser.add_argument("--timeout", type=float, default=4.0, help="Timeout por caso de teste em segundos")
    args = parser.parse_args()

    # Coleta de todos os 40 casos calibrados
    all_cases = []
    all_cases.extend(get_tabular_cases())     # 10 casos
    all_cases.extend(get_files_cases())       # 10 casos
    all_cases.extend(get_devops_cases())      # 10 casos
    all_cases.extend(get_os_matrix_cases())   # 10 casos

    total_cases = len(all_cases)
    results: list[BenchmarkResult] = []

    print("=" * 70)
    print(f"[INICIANDO BENCHMARK DE ESTADO EM SANDBOX E MATRIZ MULTIPLATAFORMA]")
    print(f"  - Modelo Alvo:        {args.model}")
    print(f"  - Total de Cenarios:  {total_cases} casos")
    print(f"  - Arquitetura:        Execucao Efemera em /tmp + Validacao zsh -n")
    print(f"  - Timeout por Teste:  {args.timeout}s")
    print("=" * 70)

    for idx, c in enumerate(all_cases, 1):
        cid = c["id"]
        prompt = c["prompt"]
        cat = c["category"]
        setup = c.get("setup")
        assertion = c.get("assertion")
        static_eval = c.get("static_eval")

        res = run_test_case(
            case_id=cid,
            prompt=prompt,
            category=cat,
            setup_fn=setup,
            assertion_fn=assertion,
            static_eval_fn=static_eval,
            model=args.model,
            timeout_sec=args.timeout
        )
        results.append(res)

        # Status do caso individual
        is_fully_passed = (
            res.passed_format and
            res.passed_safety and
            res.passed_syntax and
            res.passed_assertion
        )
        status_tag = "[OK]   " if is_fully_passed else "[FALHA]"
        print(f"  {status_tag} #{idx:02d}/{total_cases:02d} [{cid}] {cat[:20]:<20} ({res.latency_ms:.1f}ms)")
        if not is_fully_passed:
            print(f"           Cmd: {res.cleaned_command}")
            print(f"           Erro: {res.error_detail}")

    # Consolidacao das metricas
    passed_format_cnt = sum(1 for r in results if r.passed_format)
    passed_safety_cnt = sum(1 for r in results if r.passed_safety)
    passed_syntax_cnt = sum(1 for r in results if r.passed_syntax)
    passed_assert_cnt = sum(1 for r in results if r.passed_assertion)
    fully_passed_cnt = sum(
        1 for r in results
        if r.passed_format and r.passed_safety and r.passed_syntax and r.passed_assertion
    )

    latencies = [r.latency_ms for r in results if r.latency_ms > 0]
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
    min_latency = min(latencies) if latencies else 0.0
    max_latency = max(latencies) if latencies else 0.0

    tps_list = [r.tokens_per_second for r in results if r.tokens_per_second > 0]
    avg_tps = sum(tps_list) / len(tps_list) if tps_list else 0.0

    # Metricas por categoria
    categories = sorted(list(set(r.category for r in results)))
    cat_stats = {}
    for cat in categories:
        cat_res = [r for r in results if r.category == cat]
        cat_passed = sum(
            1 for r in cat_res
            if r.passed_format and r.passed_safety and r.passed_syntax and r.passed_assertion
        )
        cat_stats[cat] = {
            "total": len(cat_res),
            "passed": cat_passed,
            "rate": (cat_passed / len(cat_res)) * 100.0 if cat_res else 0.0,
            "avg_lat": sum(r.latency_ms for r in cat_res) / len(cat_res) if cat_res else 0.0
        }

    overall_score = (fully_passed_cnt / total_cases) * 100.0

    # Exibicao no terminal
    print("\n" + "=" * 70)
    print(f"[RESULTADOS CONSOLIDADOS DO BENCHMARK]")
    print("=" * 70)
    print(f"Modelo Avaliado:                     {args.model}")
    print(f"Acuracia Global Ponderada:          {overall_score:.1f}% ({fully_passed_cnt}/{total_cases})")
    print(f"Latencia Media por Invocacao:       {avg_latency:.1f}ms (Min: {min_latency:.1f}ms | Max: {max_latency:.1f}ms)")
    if avg_tps > 0:
        print(f"Velocidade Media de Geracao:        {avg_tps:.1f} tokens/segundo")
    print("-" * 70)
    print(f"Métricas por Camada:")
    print(f"  - Seguranca Preventiva:            {(passed_safety_cnt / total_cases) * 100.0:.1f}% ({passed_safety_cnt}/{total_cases})")
    print(f"  - Formato Estrito (Zero Markdown): {(passed_format_cnt / total_cases) * 100.0:.1f}% ({passed_format_cnt}/{total_cases})")
    print(f"  - Sintaxe Valida no Shell:         {(passed_syntax_cnt / total_cases) * 100.0:.1f}% ({passed_syntax_cnt}/{total_cases})")
    print(f"  - Assercao de Estado Funcional:    {(passed_assert_cnt / total_cases) * 100.0:.1f}% ({passed_assert_cnt}/{total_cases})")
    print("-" * 70)
    print("Desempenho por Categoria:")
    for cat, stat in cat_stats.items():
        print(f"  * {cat:<32} {stat['rate']:>5.1f}% ({stat['passed']}/{stat['total']}) | Latencia: {stat['avg_lat']:.1f}ms")
    print("=" * 70)

    # Gravacao do Relatorio em Markdown
    reports_dir = Path("benchmark/reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_file = reports_dir / "latest_report.md"

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(report_file, "w", encoding="utf-8") as f:
        f.write("# Relatorio Oficial de Benchmark — SLM Especialista em Terminal\n\n")
        f.write(f"- **Data da Avaliacao:** {now_str}\n")
        f.write(f"- **Modelo Avaliado:** `{args.model}`\n")
        f.write(f"- **Total de Casos de Teste:** {total_cases}\n")
        f.write(f"- **Acuracia Global:** **{overall_score:.1f}%** ({fully_passed_cnt}/{total_cases} aprovados)\n")
        f.write(f"- **Latencia Media:** {avg_latency:.1f} ms\n\n")
        f.write("---\n\n")
        f.write("## 1. Metricas por Camada de Inspecao\n\n")
        f.write("| Camada de Inspecao | Taxa de Conformidade | Casos Aprovados |\n")
        f.write("| :--- | :--- | :--- |\n")
        f.write(f"| **Seguranca Preventiva** | {(passed_safety_cnt / total_cases) * 100.0:.1f}% | {passed_safety_cnt}/{total_cases} |\n")
        f.write(f"| **Formato Estrito (Zero Markdown)** | {(passed_format_cnt / total_cases) * 100.0:.1f}% | {passed_format_cnt}/{total_cases} |\n")
        f.write(f"| **Sintaxe Gramatical Zsh (zsh -n)** | {(passed_syntax_cnt / total_cases) * 100.0:.1f}% | {passed_syntax_cnt}/{total_cases} |\n")
        f.write(f"| **Assercao Funcional em Sandbox** | {(passed_assert_cnt / total_cases) * 100.0:.1f}% | {passed_assert_cnt}/{total_cases} |\n\n")
        f.write("---\n\n")
        f.write("## 2. Desempenho por Categoria\n\n")
        f.write("| Categoria Tematica | Taxa de Sucesso | Aprovados | Latencia Media |\n")
        f.write("| :--- | :--- | :--- | :--- |\n")
        for cat, stat in cat_stats.items():
            f.write(f"| {cat} | **{stat['rate']:.1f}%** | {stat['passed']}/{stat['total']} | {stat['avg_lat']:.1f} ms |\n")
        f.write("\n---\n\n")
        f.write("## 3. Detalhamento de Falhas Identificadas\n\n")
        failures = [
            r for r in results
            if not (r.passed_format and r.passed_safety and r.passed_syntax and r.passed_assertion)
        ]
        if not failures:
            f.write("*[OK] Nenhuma falha identificada em todos os cenarios de teste.*\n")
        else:
            for fail in failures:
                f.write(f"### Caso `{fail.case_id}`: {fail.prompt}\n")
                f.write(f"- **Categoria:** {fail.category}\n")
                f.write(f"- **Comando Gerado:** `{fail.cleaned_command}`\n")
                f.write(f"- **Diagnostico:** {fail.error_detail}\n\n")

    print(f"\n[INFO] Relatorio detalhado salvo com sucesso em: {report_file}")

if __name__ == "__main__":
    main()
