# Relatorio Oficial de Benchmark — SLM Especialista em Terminal (Tri-OS)

- **Data da Avaliacao:** 2026-09-11 18:48:13
- **Modelo Avaliado:** `term-specialist-q4`
- **Total de Casos de Teste:** 45
- **Acuracia Global:** **97.8%** (44/45 aprovados)
- **Latencia Media:** 174.8 ms

---

## 1. Metricas por Camada de Inspecao

| Camada de Inspecao | Taxa de Conformidade | Casos Aprovados |
| :--- | :--- | :--- |
| **Seguranca Preventiva** | 100.0% | 45/45 |
| **Formato Estrito (Zero Markdown)** | 100.0% | 45/45 |
| **Sintaxe Gramatical no Shell Alvo** | 100.0% | 45/45 |
| **Assercao Funcional em Sandbox** | 97.8% | 44/45 |

---

## 2. Desempenho por Sistema Operacional

| Sistema Operacional | Taxa de Sucesso | Aprovados | Latencia Media |
| :--- | :--- | :--- | :--- |
| **Linux** | **100.0%** | 3/3 | 163.9 ms |
| **PowerShell** | **100.0%** | 5/5 | 194.1 ms |
| **macOS** | **97.3%** | 36/37 | 173.1 ms |

---

## 3. Desempenho por Categoria Tematica

| Categoria Tematica | Taxa de Sucesso | Aprovados | Latencia Media |
| :--- | :--- | :--- | :--- |
| Arquivos & Midia | **90.0%** | 9/10 | 169.9 ms |
| DevOps & Redes | **100.0%** | 10/10 | 176.1 ms |
| Filtros & Tabular | **100.0%** | 10/10 | 201.0 ms |
| Matriz OS (Linux GNU) | **100.0%** | 3/3 | 163.9 ms |
| Matriz OS (PowerShell Nativo) | **100.0%** | 5/5 | 194.1 ms |
| Matriz OS (PowerShell ➔ POSIX) | **100.0%** | 3/3 | 120.6 ms |
| Matriz OS (macOS BSD) | **100.0%** | 4/4 | 143.2 ms |

---

## 4. Detalhamento de Falhas Identificadas

### Caso `file_07`: [macOS] copiar recursivamente todos os arquivos da pasta origem para a pasta destino
- **Sistema Operacional:** macOS
- **Categoria:** Arquivos & Midia
- **Comando Gerado:** `find origem -type f -exec cp -r "{}" destino/`
- **Diagnostico:** Arquivos nao foram copiados para o destino: []

