# SLM Especialista em Terminal & Automacao CLI

> Modelo de Linguagem Compacto (SLM) especializado na traducao de intencoes em linguagem natural (PT-BR) para comandos de terminal Unix/macOS Zsh deterministas e de alta performance.

---

## 1. Visao Geral

O **SLM Especialista em Terminal** e um modelo ajustado (fine-tuned) a partir do `Qwen/Qwen2.5-Coder-1.5B-Instruct`, projetado especificamente para o ecossistema **macOS (Apple Silicon)** e terminal **Zsh**.

### A Tese Central
*"A IA e o compilador da intencao; o Sistema Operacional e o motor de execucao."*

Em vez de enviar gigabytes de arquivos para modelos gigantes em nuvem, o usuario expressa sua intencao no terminal, a SLM local sugere a linha de comando ideal em menos de 50ms, e utilitarios de sistema nativos em C/Rust/Bash processam os dados na velocidade do hardware.

### Principio da Soberania Humana e Seguranca Inegociavel
* **Zero Execucao Autonoma:** O modelo e estritamente um sugeridor. Ele **nunca** executa comandos diretamente nem invoca chamadas de sistema (`os.system`, `subprocess`, etc.).
* **Injecao no Buffer (`print -z`):** O comando sugerido e carregado diretamente na linha de edicao do Zsh, cabendo exclusivamente ao usuario revisar a sintaxe antes de teclar `[ENTER]`.
* **Zero Markdown Residual:** A inferencia produz apenas o comando puro, sem introducoes, sem explicacoes e sem cercas de codigo markdown (` ``` `).

---

## 2. Arquitetura do Pipeline

```
[Gemini API (Google Pro)]
        │
        ▼ (Destilacao de Conhecimento & Validacao Pydantic)
[Dataset Formatado (train.jsonl / valid.jsonl)]
        │
        ▼ (Fine-Tuning LoRA via GPU Apple Silicon)
[MLX-LM: Adaptadores LoRA (adapters/)]
        │
        ▼ (Fusao de Pesos)
[Modelo Fundido Safetensors (models/fused-qwen-terminal)]
        │
        ▼ (Empacotamento via Modelfile)
[Ollama Daemon Local (term-specialist)]
        │
        ▼ (Injecao no Buffer via Zsh Widget)
[Terminal Zsh: cmd "sua intencao"]
```

---

## 3. Estrutura do Repositorio

```
slm-terminal-specialist/
├── .env.example                 # Exemplo de configuracao de variaveis de ambiente
├── .gitignore                   # Regras de exclusao do Git (pesos binarios e segredos)
├── CONSTITUTION.md              # Documento normativo de governanca e fronteiras
├── GEMINI.md                    # Diretrizes de estilo e regras do projeto
├── LICENSE                      # Licenca Apache 2.0
├── Makefile                     # Atalhos de automacao para o ciclo de vida
├── README.md                    # Documentacao tecnica principal
├── requirements.txt             # Dependencias Python
├── dataset/
│   ├── generator.py             # Gerador de dados sinteticos via Gemini API
│   ├── validate_dataset.py      # Auditoria de integridade e qualidade do dataset
│   └── data/
│       ├── train.jsonl          # Split de treino (450 pares)
│       └── valid.jsonl          # Split de validacao (50 pares)
├── deploy/
│   ├── Modelfile                # Configuracao de importacao no Ollama
│   └── zsh_integration.zsh      # Funcao cmd() para o ~/.zshrc
├── models/                      # Diretorio de modelos fundidos (ignorado no Git)
├── adapters/                    # Checkpoints LoRA MLX (ignorado no Git)
└── training/
    └── config.yaml              # Hiperparametros de treino LoRA via MLX-LM
```

---

## 4. Pre-requisitos

* **Hardware:** Mac com chip Apple Silicon (M1/M2/M3/M4) com memoria unificada (minimo 8 GB, recomendado 16 GB+).
* **Sistema Operacional:** macOS 14+ (Sonoma ou superior) com terminal Zsh nativo.
* **Linguagem:** Python 3.10 ou superior.
* **Ollama:** Instalado e em execucao (`brew install ollama`).

---

## 5. Instalacao e Configuracao

### Passo 1: Clonar o Repositorio
```bash
git clone https://github.com/contatovictorhugos-hash/slm-terminal-specialist.git
cd slm-terminal-specialist
```

### Passo 2: Criar e Ativar Ambiente Virtual
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Passo 3: Configurar Chaves de API
Copie o arquivo de exemplo e insira sua chave do Google AI Studio:
```bash
cp .env.example .env
```
Edite `.env`:
```env
GEMINI_API_KEY=sua_chave_aqui
```

---

## 6. Fluxo de Trabalho (Guia Passo a Passo)

Voce pode utilizar os alvos do `Makefile` ou executar os comandos diretamente.

### 6.1. Auditoria e Validacao do Dataset
Para inspecionar a qualidade dos dados, distribuicao de comandos e garantir ausencia de emojis e erros sintaticos:
```bash
make validate
# ou: python dataset/validate_dataset.py
```

### 6.2. Geracao de Dados Sinteticos (Destilacao)
O gerador utiliza a API do Gemini com validacao estruturada Pydantic e sistema de fallback com rotacao automatica entre modelos caso atinja cotas temporarias:
```bash
make generate
# ou: python dataset/generator.py --total 500 --batch-size 25
```

### 6.3. Fine-Tuning LoRA via MLX-LM
O treinamento e acelerado diretamente na GPU do Apple Silicon atraves do MLX:
```bash
make train
# ou: python -m mlx_lm.lora --config training/config.yaml
```

Parametros principais em `training/config.yaml`:
* **Modelo Base:** `Qwen/Qwen2.5-Coder-1.5B-Instruct`
* **Iteracoes:** 600
* **Batch Size:** 4
* **Learning Rate:** 1.0e-4
* **Mask Prompt:** `true` (perda calculada apenas na resposta do assistente)

### 6.4. Fusao dos Adaptadores LoRA
Apos o treinamento, funda os adaptadores ao modelo base para gerar o modelo final unificado:
```bash
make fuse
# ou: python -m mlx_lm.fuse --model Qwen/Qwen2.5-Coder-1.5B-Instruct --adapter-path adapters --save-path models/fused-qwen-terminal
```

### 6.5. Registro no Ollama
Com o Ollama em execucao, crie o modelo local a partir do Modelfile:
```bash
make deploy
# ou: ollama create term-specialist -f deploy/Modelfile
```

---

## 7. Integracao com o Zsh

Para ter o assistente disponivel diretamente em qualquer sessao do seu terminal:

1. Abra seu arquivo `~/.zshrc`:
   ```bash
   nano ~/.zshrc
   ```
2. Adicione a seguinte funcao (ou faca `source` de `deploy/zsh_integration.zsh`):
   ```bash
   cmd() {
       local prompt="$*"
       if [[ -z "$prompt" ]]; then
           echo "Uso: cmd <o que voce deseja fazer em portugues>"
           return 1
       fi

       local suggestion=$(ollama run term-specialist "$prompt" 2>/dev/null | head -n 1 | sed 's/^```bash//;s/^```zsh//;s/^```//;s/```$//')

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
3. Recarregue o terminal:
   ```bash
   source ~/.zshrc
   ```

---

## 8. Exemplos Praticos de Uso

| Entrada do Usuario (`cmd "..."`) | Comando Sugerido | Categoria |
| :--- | :--- | :--- |
| `cmd "junte todos os csvs mantendo so o primeiro cabecalho"` | `awk 'FNR==1 && NR!=1 {next} 1' *.csv > consolidado.csv` | Filtros & Tabular |
| `cmd "achar o processo que esta travando a porta 3000 e matar"` | `lsof -ti:3000 \| xargs kill -9` | DevOps / Processos |
| `cmd "converter todos os webp da pasta para jpg"` | `for f in *.webp; do magick "$f" "${f%.webp}.jpg"; done` | Manipulacao de Midia |
| `cmd "comprimir a pasta /var/log em tar.gz excluindo arquivos .tmp"` | `tar --exclude='*.tmp' -czvf logs.tar.gz /var/log` | Arquivos & Backup |
| `cmd "extrair os status code e contar ocorrencias do access.log"` | `awk '{print $9}' access.log \| sort \| uniq -c \| sort -nr` | Processamento de Logs |

---

## 9. Governanca e Constituicao

O projeto segue rigorosamente os limites e principios estipulados no arquivo [CONSTITUTION.md](CONSTITUTION.md):
* **Fronteira Operacional:** O modelo nao analisa o conteudo semantico de arquivos (nao interpreta contratos nem resume textos). Ele e um especialista em sintaxe CLI.
* **Padrao Textual Limpo:** Conforme [GEMINI.md](GEMINI.md), todos os codigos e documentacoes sao estritamente desprovidos de emojis, mantendo padrao formal de engenharia.

---

## 10. Licenca

Distribuido sob a licenca **Apache 2.0**. Consulte o arquivo [LICENSE](LICENSE) para obter mais informacoes.
