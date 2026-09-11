# Relatorio Oficial de Benchmark — SLM Especialista em Terminal

- **Data da Avaliacao:** 2026-09-10 22:48:22
- **Modelo Avaliado:** `term-specialist-q4`
- **Total de Casos de Teste:** 40
- **Acuracia Global:** **75.0%** (30/40 aprovados)
- **Latencia Media:** 224.4 ms

---

## 1. Metricas por Camada de Inspecao

| Camada de Inspecao | Taxa de Conformidade | Casos Aprovados |
| :--- | :--- | :--- |
| **Seguranca Preventiva** | 100.0% | 40/40 |
| **Formato Estrito (Zero Markdown)** | 100.0% | 40/40 |
| **Sintaxe Gramatical Zsh (zsh -n)** | 100.0% | 40/40 |
| **Assercao Funcional em Sandbox** | 75.0% | 30/40 |

---

## 2. Desempenho por Categoria

| Categoria Tematica | Taxa de Sucesso | Aprovados | Latencia Media |
| :--- | :--- | :--- | :--- |
| Arquivos & Midia | **100.0%** | 10/10 | 165.5 ms |
| DevOps & Redes | **70.0%** | 7/10 | 202.0 ms |
| Filtros & Tabular | **50.0%** | 5/10 | 378.2 ms |
| Matriz OS (Linux GNU) | **33.3%** | 1/3 | 167.2 ms |
| Matriz OS (PowerShell ➔ POSIX) | **100.0%** | 3/3 | 118.5 ms |
| Matriz OS (macOS BSD) | **100.0%** | 4/4 | 165.3 ms |

---

## 3. Detalhamento de Falhas Identificadas

### Caso `tab_01`: juntar todos os csvs da pasta ignorando o cabecalho a partir do segundo salvando em consolidado.csv
- **Categoria:** Filtros & Tabular
- **Comando Gerado:** `awk 'FNR>1' *.csv > consolidado.csv`
- **Diagnostico:** Esperado 3 linhas, obtido 2

### Caso `tab_03`: imprimir apenas a terceira coluna do arquivo vendas.tsv delimitado por tabulacao
- **Categoria:** Filtros & Tabular
- **Comando Gerado:** `cut -d'\t' -f3 vendas.tsv`
- **Diagnostico:** Valores de vendas nao encontrados na saida: 

### Caso `tab_04`: contar o numero de linhas nao vazias do arquivo access.log
- **Categoria:** Filtros & Tabular
- **Comando Gerado:** `wc -l access.log | tail -n 1`
- **Diagnostico:** Esperava contagem 5, obteve: 7 access.log

### Caso `tab_05`: ordenar o arquivo nomes.txt em ordem alfabetica e remover linhas duplicadas salvando em unicos.txt
- **Categoria:** Filtros & Tabular
- **Comando Gerado:** `sort nomes.txt | uniq -u > unicos.txt`
- **Diagnostico:** Resultado de ordenacao inesperado: ['Beto']

### Caso `tab_07`: filtrar o arquivo clientes.csv exibindo apenas linhas onde a terceira coluna e igual a ativo
- **Categoria:** Filtros & Tabular
- **Comando Gerado:** `grep -E '.*,"ativo",.*' clientes.csv`
- **Diagnostico:** Filtro falhou: 

### Caso `devops_01`: achar o processo que esta travando a porta 3000 e matar
- **Categoria:** DevOps & Redes
- **Comando Gerado:** `lsof -t -i:3000`
- **Diagnostico:** Comando nao utiliza lsof/fuser e kill apontando para 3000: lsof -t -i:3000

### Caso `devops_03`: fazer uma requisicao http get para https://api.github.com exibindo apenas os cabecalhos de resposta
- **Categoria:** DevOps & Redes
- **Comando Gerado:** `curl -s https://api.github.com | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin).keys())))"`
- **Diagnostico:** Curl nao utilizou flag de inspecao de cabecalhos: curl -s https://api.github.com | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin).keys())))"

### Caso `devops_04`: listar todos os containers docker em execucao ou parados exibindo apenas seus ids
- **Categoria:** DevOps & Redes
- **Comando Gerado:** `docker ps -a`
- **Diagnostico:** Comando docker nao utilizou flag -q para extrair apenas IDs: docker ps -a

### Caso `os_linux_01`: substituir a palavra erro por aviso diretamente no arquivo notas.txt no linux
- **Categoria:** Matriz OS (Linux GNU)
- **Comando Gerado:** `sed -i '' 's/erro/aviso/g' notas.txt`
- **Diagnostico:** No Linux GNU sed nao deve usar aspas vazias apos -i: sed -i '' 's/erro/aviso/g' notas.txt

### Caso `os_linux_02`: copiar o conteudo do arquivo chave.pub para a area de transferencia no linux
- **Categoria:** Matriz OS (Linux GNU)
- **Comando Gerado:** `cat ~/.ssh/chave.pub | pbcopy`
- **Diagnostico:** Esperado xclip, xsel ou wl-copy para clipboard no Linux: cat ~/.ssh/chave.pub | pbcopy

