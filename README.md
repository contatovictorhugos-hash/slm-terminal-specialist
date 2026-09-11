# SLM Especialista em Terminal & Automacao CLI

> Modelo de Linguagem Compacto (SLM) especializado na traducao deterministica e de alta performance de intencoes em linguagem natural (PT-BR) para comandos de terminal Tri-OS: macOS (Zsh/BSD), Linux (Bash/GNU) e Windows (PowerShell/pwsh).

---

## 1. Visao Geral (Versao 2.0 Tri-OS)

O **SLM Especialista em Terminal** e um modelo ajustado (fine-tuned) a partir do `Qwen/Qwen2.5-Coder-1.5B-Instruct`. Na versao 2.0, o modelo opera como um compilador CLI universal multiplataforma com suporte nativo a:

* **macOS (Zsh / BSD):** Sintaxe BSD nativa (`sed -i ''`, `stat -f %m`, `pbcopy`, `sips`, `launchctl`, etc.).
* **Linux (Bash / GNU):** Sintaxe GNU padrao (`sed -i`, `stat -c %Y`, `xclip`, `systemctl`, `ip`, `ss`, etc.).
* **Windows (PowerShell / pwsh):** Cmdlets e pipelines orientados a objetos (`Get-Process`, `Stop-Process`, `Select-String`, `Get-Content`, `Invoke-WebRequest`, `Export-Csv`, etc.).

### A Tese Central
*"A IA e o compilador da intencao; o Sistema Operacional e o motor de execucao."*

Em vez de transferir grandes volumes de dados para modelos de nuvem, o usuario expressa a intencao diretamente no terminal. A SLM local gera a linha de comando ideal em menos de 50ms, permitindo que binarios compilados de baixo nivel processem os dados com maxima velocidade e privacidade total.

### Principio da Soberania Humana e Seguranca
* **Zero Execucao Autonoma:** O modelo atua unicamente como sugeridor. Ele nunca executa comandos diretamente nem aciona chamadas de sistema autonomamente.
* **Injecao no Buffer de Edicao (`print -z` / Clipboard):** No Zsh, o comando e injetado diretamente no prompt para revisao humana antes do `[ENTER]`. No PowerShell, e copiado para a area de transferencia.
* **Zero Markdown Residual:** A saida do modelo e exclusivamente o comando executavel puro, sem delimitadores markdown (` ``` `) e sem explicacoes prolixas.
* **Injecao Dinamica de SO:** O shell identifica automaticamente a plataforma em execucao (`uname -s` ou `$PSVersionTable`) e injeta o prefixo contextual (`[macOS]`, `[Linux]` ou `[PowerShell]`), garantindo precisao sintatica sem exigir esforco do usuario.

---

## 2. Arquitetura do Pipeline

```
[Gemini API (Google GenAI)]
        │
        ▼ (Sintese Parametrizada: --add, --os, --delay)
[Dataset Tri-OS Formatado (dataset/data/train.jsonl e valid.jsonl)]
        │
        ▼ (Fine-Tuning LoRA acelerado via GPU Metal no Apple Silicon)
[MLX-LM: Adaptadores LoRA (adapters/)]
        │
        ▼ (Fusao de Pesos float16)
[Modelo Fundido Safetensors (models/fused-qwen-terminal)]
        │
        ▼ (Quantizacao Nativa Q4_K_M via Modelfile)
[Ollama Local: term-specialist e term-specialist-q4 (986 MB)]
        │
        ├─────────────────────────────────────────┐
        ▼                                         ▼
[Suite de Benchmark em Sandbox]         [Integracao de Shell]
- 45 cenarios automatizados (Tri-OS)    - Zsh (macOS / Linux)
- Assercoes em /tmp + multi-shell       - PowerShell (Windows / pwsh)
- Relatorio: latest_report.md           - Buffer interativo cmd "..."
```

---

## 3. Estrutura do Repositorio

```
slm-terminal-specialist/
├── .env.example                 # Variaveis de ambiente de exemplo
├── .gitignore                   # Exclusoes do Git (pesos binarios, caches e segredos)
├── CONSTITUTION.md              # Documento normativo de governanca e fronteiras operacionais
├── GEMINI.md                    # Diretrizes de estilo, engenharia e proibicao de emojis
├── LICENSE                      # Licenca Apache 2.0
├── Makefile                     # Automacao completa do ciclo de vida do modelo
├── README.md                    # Documentacao tecnica principal
├── requirements.txt             # Dependencias Python
├── upload_to_hf.py              # Utilitario para publicacao de pesos no Hugging Face Hub
├── dataset/
│   ├── generator.py             # Gerador sintetico parametrizado com fallback de cota
│   ├── validate_dataset.py      # Auditoria de integridade, emojis e distribuicao por SO
│   └── data/
│       ├── train.jsonl          # Base de treino formatada em ChatML (1.081 registros)
│       └── valid.jsonl          # Base de validacao (121 registros)
├── deploy/
│   ├── Modelfile                # Definicao do modelo para compilacao no Ollama
│   ├── zsh_integration.zsh      # Integracao com auto-deteccao de SO para Zsh
│   └── pwsh_integration.ps1     # Integracao nativa para Windows PowerShell
├── benchmark/
│   ├── engine.py                # Motor de inferencia local, sandbox /tmp e parser multi-shell
│   ├── safety.py                # Filtros de seguranca contra comandos destrutivos
│   ├── run.py                   # Executor oficial da suite de 45 cenarios Tri-OS
│   ├── cases/                   # Casos de teste divididos por categoria tematica
│   │   ├── test_tabular.py      # Casos de CSV, TSV, awk, cut e sort
│   │   ├── test_files.py        # Casos de busca, regex e manipulacao de arquivos
│   │   ├── test_devops.py       # Casos de processos, portas e Docker
│   │   └── test_os_matrix.py    # Casos contrastivos macOS BSD, Linux GNU e PowerShell Nativo
│   └── reports/
│       └── latest_report.md     # Relatorio consolidado de metricas do benchmark
├── models/                      # Diretorio de pesos fundidos (ignorado no Git)
├── adapters/                    # Checkpoints LoRA MLX (ignorado no Git)
└── training/
    └── config.yaml              # Configuracao de hiperparametros de treino LoRA
```

---

## 4. Guia de Uso Rapido (Para Consumo do Modelo)

Se o seu objetivo e apenas **utilizar o assistente no seu terminal**:

### Pre-requisito
Ter o **Ollama** instalado e em execucao:
* **macOS:** `brew install ollama`
* **Linux:** `curl -fsSL https://ollama.com/install.sh | sh`
* **Windows:** Baixar o instalador oficial em [ollama.com/download](https://ollama.com/download)

---

### Integracao com o Shell (`cmd "sua intencao"`)

#### 1. macOS e Linux (Zsh):
Adicione a seguinte funcao ao seu `~/.zshrc`:

```bash
cmd() {
    local prompt="$*"
    if [[ -z "$prompt" ]]; then
        echo "Uso: cmd <o que voce deseja fazer em portugues>"
        return 1
    fi

    local os_tag="[Linux]"
    if [[ "$(uname -s)" == "Darwin" ]]; then
        os_tag="[macOS]"
    fi

    local model="term-specialist-q4"
    if ! ollama list | grep -q "term-specialist-q4"; then
        model="term-specialist"
    fi

    local full_prompt="${os_tag} ${prompt}"
    local suggestion=$(ollama run "$model" "$full_prompt" 2>/dev/null | head -n 1 | sed 's/^```[a-z]*//;s/^```//;s/```$//')

    if [[ -n "$suggestion" ]]; then
        echo ""
        echo "\033[1;32m[Sugestao]\033[0m $suggestion"
        echo ""
        print -z "$suggestion"
    else
        echo "[AVISO] Nao foi possivel gerar um comando para essa intencao."
    fi
}
```

Recarregue a sessao:
```bash
source ~/.zshrc
```

#### 2. Windows (PowerShell / pwsh):
Adicione ao seu perfil do PowerShell (`$PROFILE`):

```powershell
function cmd {
    param([Parameter(Mandatory=$true, ValueFromRemainingArguments=$true)][string[]]$PromptArgs)
    $prompt = $PromptArgs -join " "
    $fullPrompt = "[PowerShell] $prompt"

    $model = "term-specialist-q4"
    $raw = ollama run $model $fullPrompt 2>$null
    $clean = ($raw -split "`n")[0] -replace '^```[a-zA-Z]*','' -replace '```$',''
    $clean = $clean.Trim()

    if ($clean) {
        Write-Host "`n[Sugestao] $clean`n" -ForegroundColor Green
        Set-Clipboard -Value $clean
        Write-Host "[OK] Comando copiado para a area de transferencia! Cole com Ctrl+V." -ForegroundColor Gray
    } else {
        Write-Host "[AVISO] Nao foi possivel gerar o comando." -ForegroundColor Yellow
    }
}
```

---

### Exemplos Praticos Multiplataforma

| Intencao do Usuario | Sistema Operacional | Comando Gerado pela SLM |
| :--- | :--- | :--- |
| `cmd "substituir foo por bar no arquivo sem backup"` | **macOS** | `sed -i '' 's/foo/bar/g' arquivo.txt` |
| `cmd "substituir foo por bar no arquivo sem backup"` | **Linux** | `sed -i 's/foo/bar/g' arquivo.txt` |
| `cmd "juntar csvs mantendo apenas primeiro cabecalho"` | **macOS / Linux** | `awk 'FNR==1 && NR!=1 {next} 1' *.csv > final.csv` |
| `cmd "extrair terceira coluna de arquivo separado por tab"` | **macOS / Linux** | `cut -f3 dados.tsv` |
| `cmd "matar processo travando a porta 3000"` | **macOS / Linux** | `lsof -ti:3000 \| xargs kill -9` |
| `cmd "listar processos consumindo mais memoria"` | **PowerShell** | `Get-Process \| Sort-Object WorkingSet -Descending \| Select-Object -First 10` |
| `cmd "buscar erro ignorando maiusculas nos logs"` | **PowerShell** | `Select-String -Path *.log -Pattern "erro" -SimpleMatch` |
| `cmd "baixar arquivo executavel de url"` | **PowerShell** | `Invoke-WebRequest -Uri "https://site.com/app.exe" -OutFile "app.exe"` |

---

## 5. Guia do Desenvolvedor: Pipeline Completo de Treinamento

Siga este passo a passo caso deseje expandir a base de dados, retreinar o modelo ou executar os testes de benchmark.

### 5.1. Instalacao e Ativacao do Ambiente
```bash
# 1. Clonar o repositorio
git clone https://github.com/contatovictorhugos-hash/slm-terminal-specialist.git
cd slm-terminal-specialist

# 2. Criar e ativar o ambiente virtual Python
python3 -m venv .venv
source .venv/bin/activate

# 3. Instalar dependencias
make install

# 4. Configurar variaveis de ambiente
cp .env.example .env
```

Preencha no arquivo `.env`:
```env
GEMINI_API_KEY=sua_chave_do_google_ai_studio
HF_TOKEN=seu_token_huggingface_opcional
```

---

### 5.2. Ciclo de Vida via Makefile

O `Makefile` concentra todos os comandos do pipeline:

| Comando | Descricao |
| :--- | :--- |
| `make validate` | Executa a auditoria de integridade do dataset e distribuicao por SO |
| `make generate` | Sintetiza novos registros (padrao: `OS=PowerShell ADD=150 DELAY=10`) |
| `make train` | Executa o fine-tuning LoRA acelerado por GPU Metal via MLX-LM |
| `make fuse` | Mescla os adaptadores LoRA ao modelo base gerando os pesos unificados |
| `make deploy` | Quantiza em 4-bits (`q4_K_M`) e instancia os modelos no Ollama |
| `make benchmark` | Executa os 45 cenarios em sandbox efemero e relatorio multi-shell |
| `make clean` | Limpa caches Python e arquivos temporarios |

---

### 5.3. Detalhamento dos Passos

#### Passo 1: Geracao Sintetica Parametrizada
O gerador `dataset/generator.py` permite apontar a quantidade de registros, o sistema operacional e o intervalo de requisicao:

```bash
# Execucao padrao (adiciona 150 registros de PowerShell com delay de 10s):
make generate

# Execucao customizada via Makefile:
make generate OS=Linux ADD=50 DELAY=8
make generate OS=macOS ADD=100 DELAY=12

# Execucao direta via CLI Python:
python dataset/generator.py --add 150 --os PowerShell --delay 10
```

#### Passo 2: Validacao e Auditoria
Verifica formato JSON, sequencia ChatML, ausencia de markdown indevido, ausencia de emojis e percentual por plataforma:
```bash
make validate
```

#### Passo 3: Fine-Tuning LoRA (MLX-LM no Apple Silicon)
Ajusta os pesos unicamente nos tokens do assistente (`mask_prompt: true`):
```bash
make train
```
Configuracao padrao (`training/config.yaml`):
* **Modelo Base:** `Qwen/Qwen2.5-Coder-1.5B-Instruct`
* **Iteracoes:** `1000`
* **Batch Size:** `4`
* **Learning Rate:** `1.0e-4`
* **Camadas LoRA:** `16`

#### Passo 4: Fusao dos Adaptadores
Consolida os adaptadores treinados ao modelo original em formato `safetensors`:
```bash
make fuse
```

#### Passo 5: Quantizacao Q4_K_M e Deploy no Ollama
Compila o modelo local aplicando quantizacao simétrica de 4 bits:
```bash
make deploy
```
* **Otimizacao de Memoria:** Reducao de 2.9 GB para **986 MB** (mais de 66% de reducao de pegada de memoria), viabilizando execucao com latencia inferior a 50ms em maquinas com 8 GB de RAM.

#### Passo 6: Execucao da Suite Oficial de Benchmark Tri-OS
Avalia o modelo em tempo real contra 45 casos de teste equilibrados entre macOS (BSD), Linux (GNU) e Windows (PowerShell nativo):
```bash
make benchmark
```
O benchmark valida 4 camadas de inspecao:
1. **Seguranca Preventiva:** Bloqueio e prevencao de comandos destrutivos perigosos sem sandbox (`rm -rf *`, `mkfs`, exclusao de raiz no PowerShell).
2. **Formato Estrito (Zero Markdown):** 100% de comandos puros sem cercas markdown ou texto conversacional.
3. **Validade Sintatica Multi-Shell:** Checagem rigorosa via `zsh -n` para Unix e analisador sintatico/semantico estruturado para PowerShell.
4. **Assercao Funcional de Estado em Sandbox:** Execucao real em diretorios efemeros `/tmp` e verificacao deterministica dos efeitos colaterais.

**Resultado Consolidado:**
* **Acuracia Global:** **97.8%** (44/45 casos aprovados)
* **Linux GNU:** 100.0% (3/3)
* **PowerShell Nativo:** 100.0% (5/5)
* **PowerShell ➔ POSIX:** 100.0% (3/3)
* **macOS BSD:** 97.3% (36/37)
* **Latencia Media:** 174.8 ms (~93.7 tokens/s)
* **Relatorio Completo:** Gravado automaticamente em `benchmark/reports/latest_report.md`.

---

## 6. Governanca e Constituicao

O projeto segue as diretrizes estabelecidas no arquivo [CONSTITUTION.md](CONSTITUTION.md) e [GEMINI.md](GEMINI.md):
* **Fronteira Operacional:** O modelo e estritamente um compilador de sintaxe CLI. Ele nao interpreta conteudo semantico de documentos nem atua como assistente conversacional generico.
* **Padrao Textual Limpo:** E terminantemente proibido o uso de emojis em arquivos de codigo, strings de log, comentarios e documentos Markdown do projeto.

---

## 7. Licenca

Distribuido sob a licenca **Apache 2.0**. Consulte o arquivo [LICENSE](LICENSE) para obter mais informacoes.
