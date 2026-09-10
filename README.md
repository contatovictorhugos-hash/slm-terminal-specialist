# SLM Especialista em Terminal & Automacao CLI

> Modelo de Linguagem Compacto (SLM) especializado na traducao de intencoes em linguagem natural (PT-BR) para comandos de terminal Unix/macOS Zsh deterministas e de alta performance.

---

## 1. Visao Geral

O **SLM Especialista em Terminal** e um modelo ajustado (fine-tuned) a partir do `Qwen/Qwen2.5-Coder-1.5B-Instruct`, projetado especificamente para o ecossistema **macOS (Apple Silicon)** e terminal **Zsh** (com total compatibilidade para Linux / Bash).

### A Tese Central
*"A IA e o compilador da intencao; o Sistema Operacional e o motor de execucao."*

Em vez de enviar gigabytes de arquivos para modelos gigantes em nuvem, o usuario expressa sua intencao no terminal, a SLM local sugere a linha de comando ideal em menos de 50ms, e utilitarios de sistema nativos em C/Rust/Bash processam os dados na velocidade do hardware.

### Principio da Soberania Humana e Seguranca Inegociavel
* **Zero Execucao Autonoma:** O modelo e estritamente um sugeridor. Ele **nunca** executa comandos diretamente nem invoca chamadas de sistema (`os.system`, `subprocess`, etc.).
* **Injecao no Buffer (`print -z`):** O comando sugerido e carregado diretamente na linha de edicao do shell, cabendo exclusivamente ao usuario revisar a sintaxe antes de teclar `[ENTER]`.
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
        ▼ (Empacotamento via Modelfile / Hugging Face)
[Ollama Daemon Local (term-specialist)]
        │
        ▼ (Injecao no Buffer via Zsh Widget)
[Terminal Zsh / Bash: cmd "sua intencao"]
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
├── upload_to_hf.py              # Utilitario para publicacao de pesos no Hugging Face
├── dataset/
│   ├── generator.py             # Gerador de dados sinteticos via Gemini API
│   ├── validate_dataset.py      # Auditoria de integridade e qualidade do dataset
│   └── data/
│       ├── train.jsonl          # Split de treino (450 pares)
│       └── valid.jsonl          # Split de validacao (50 pares)
├── deploy/
│   ├── Modelfile                # Configuracao de importacao no Ollama
│   └── zsh_integration.zsh      # Funcao cmd() para o shell
├── models/                      # Diretorio de modelos fundidos (ignorado no Git)
├── adapters/                    # Checkpoints LoRA MLX (ignorado no Git)
└── training/
    └── config.yaml              # Hiperparametros de treino LoRA via MLX-LM
```

---

## 4. Guia de Uso Rapido (Para quem quer apenas USAR o modelo)

Se o seu objetivo e apenas **utilizar o assistente no seu dia a dia** (sem treinar, sem gerar dados e sem precisar ativar ambientes virtuais Python):

### Pre-requisito Unico
Basta ter o **Ollama** instalado e em execucao no seu computador (macOS, Linux ou Windows):
```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh
```

### Opcao A: Uso Direto pelo Terminal
Voce pode invocar o modelo diretamente via Ollama apontando para o repositorio do Hugging Face. Na primeira vez, o Ollama baixa os pesos automaticamente e armazena localmente; nas vezes seguintes, roda 100% offline:

```bash
ollama run hf.co/VictorMr/slm-terminal-specialist "junte todos os csvs mantendo apenas o primeiro cabecalho"
```

*(Se voce ja realizou o deploy local com o nome `term-specialist`, basta rodar: `ollama run term-specialist "sua intencao"`)*

---

### Opcao B: Integracao Global com o Shell (`cmd "sua intencao"`)
A forma mais produtiva e configurar uma funcao no seu arquivo de inicializacao do terminal. O comando sugerido aparecera **ja digitado no seu cursor**, pronto para voce conferir e teclar `[ENTER]`.

#### 1. Para macOS (Terminal Zsh):
Adicione ao final do seu arquivo `~/.zshrc`:
```bash
cmd() {
    local prompt="$*"
    if [[ -z "$prompt" ]]; then
        echo "Uso: cmd <o que voce deseja fazer em portugues>"
        return 1
    fi

    local model="term-specialist"
    # Fallback para o Hub se nao estiver registrado localmente
    if ! ollama list | grep -q "term-specialist"; then
        model="hf.co/VictorMr/slm-terminal-specialist"
    fi

    local suggestion=$(ollama run "$model" "$prompt" 2>/dev/null | head -n 1 | sed 's/^```bash//;s/^```zsh//;s/^```//;s/```$//')

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

#### 2. Para Linux (Terminal Bash):
Adicione ao seu `~/.bashrc`:
```bash
cmd() {
    local prompt="$*"
    if [[ -z "$prompt" ]]; then
        echo "Uso: cmd <o que voce deseja fazer em portugues>"
        return 1
    fi

    local model="term-specialist"
    if ! ollama list | grep -q "term-specialist"; then
        model="hf.co/VictorMr/slm-terminal-specialist"
    fi

    local suggestion=$(ollama run "$model" "$prompt" 2>/dev/null | head -n 1 | sed 's/^```bash//;s/^```//;s/```$//')

    if [[ -n "$suggestion" ]]; then
        echo -e "\n\033[1;32m[Sugestao]\033[0m $suggestion\n"
        history -s "$suggestion"
    else
        echo "[AVISO] Nao foi possivel gerar um comando para essa intencao."
    fi
}
```

Recarregue o shell:
```bash
source ~/.zshrc   # ou source ~/.bashrc
```

Agora, em **qualquer diretorio** da sua maquina, basta digitar:
```zsh
cmd "achar o processo que esta travando a porta 3000 e matar"
```

---

### Exemplos Praticos de Uso

| Entrada do Usuario (`cmd "..."`) | Comando Sugerido | Categoria |
| :--- | :--- | :--- |
| `cmd "junte todos os csvs mantendo so o primeiro cabecalho"` | `awk 'FNR==1 && NR!=1 {next} 1' *.csv > consolidado.csv` | Filtros & Tabular |
| `cmd "achar o processo que esta travando a porta 3000 e matar"` | `lsof -ti:3000 \| xargs kill -9` | DevOps / Processos |
| `cmd "converter todos os webp da pasta para jpg"` | `for f in *.webp; do magick "$f" "${f%.webp}.jpg"; done` | Manipulacao de Midia |
| `cmd "comprimir a pasta /var/log em tar.gz excluindo arquivos .tmp"` | `tar --exclude='*.tmp' -czvf logs.tar.gz /var/log` | Arquivos & Backup |
| `cmd "extrair os status code e contar ocorrencias do access.log"` | `awk '{print $9}' access.log \| sort \| uniq -c \| sort -nr` | Processamento de Logs |

---

## 5. Guia para Desenvolvedores: Treinamento e Reproducao Completa

Se voce deseja **reproduzir o treinamento**, gerar novos pares de dados ou criar sua propria versao da SLM, siga as etapas abaixo.

### 5.1. Pre-requisitos de Desenvolvimento
* **Hardware:** Mac com Apple Silicon (M1/M2/M3/M4) com memoria unificada (minimo 8 GB, recomendado 16 GB+).
* **Sistema Operacional:** macOS 14+ com terminal Zsh.
* **Python:** Versao 3.10 ou superior.
* **Chave de API:** Conta no Google AI Studio (para a etapa de geracao sintetica com Gemini).

### 5.2. Instalacao do Ambiente
```bash
# 1. Clonar o repositorio
git clone https://github.com/contatovictorhugos-hash/slm-terminal-specialist.git
cd slm-terminal-specialist

# 2. Criar e ativar o ambiente virtual
python3 -m venv .venv
source .venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt
# ou: make install

# 4. Configurar variaveis de ambiente
cp .env.example .env
```
Edite o arquivo `.env`:
```env
GEMINI_API_KEY=sua_chave_do_google_ai_studio
HF_TOKEN=seu_token_do_huggingface_opcional
```

---

### 5.3. Passo a Passo do Pipeline de Treinamento

#### Passo 1: Auditoria e Validacao do Dataset
Verifica se ha erros estruturais de JSON, duplicatas, presenca indevida de markdown ou violacoes de estilo:
```bash
make validate
# ou: python dataset/validate_dataset.py
```

#### Passo 2: Geracao Sintetica via Gemini (Destilacao de Conhecimento)
O gerador `dataset/generator.py` envia prompts balanceados para o Gemini com validacao estrita via Pydantic e sistema de rotacao de contingencia entre 5 variantes de modelos:
```bash
make generate
# ou: python dataset/generator.py --total 500 --batch-size 25
```

#### Passo 3: Fine-Tuning LoRA com MLX-LM
O treinamento e executado diretamente na memoria unificada da GPU do Apple Silicon:
```bash
make train
# ou: python -m mlx_lm.lora --config training/config.yaml
```

Parametros configurados em `training/config.yaml`:
* **Modelo Base:** `Qwen/Qwen2.5-Coder-1.5B-Instruct`
* **Iteracoes de Treino:** 600
* **Batch Size:** 4
* **Learning Rate:** 1.0e-4
* **Camadas LoRA:** 16
* **Mask Prompt:** `true` (otimiza a perda unicamente na resposta do comando)
* **Destino dos Adaptadores:** `adapters/`

#### Passo 4: Fusao dos Adaptadores LoRA
Funde os pesos dos adaptadores ao modelo base gerando os arquivos unificados em `safetensors`:
```bash
make fuse
# ou: python -m mlx_lm.fuse --model Qwen/Qwen2.5-Coder-1.5B-Instruct --adapter-path adapters --save-path models/fused-qwen-terminal
```

#### Passo 5: Registro Local no Ollama via Modelfile
Cria o modelo local `term-specialist` no daemon do Ollama com template ChatML e stop tokens definidos:
```bash
make deploy
# ou: ollama create term-specialist -f deploy/Modelfile
```

#### Passo 6: Publicacao dos Pesos no Hugging Face (Opcional)
Para enviar o modelo fundido para o seu perfil no Hugging Face:
```bash
python upload_to_hf.py --repo-id SEU_USUARIO/slm-terminal-specialist
```

---

## 6. Governanca e Constituicao

O projeto segue rigorosamente os limites e principios estipulados no arquivo [CONSTITUTION.md](CONSTITUTION.md):
* **Fronteira Operacional:** O modelo nao analisa o conteudo semantico de arquivos (nao interpreta contratos nem resume textos). Ele e um especialista em sintaxe CLI.
* **Padrao Textual Limpo:** Conforme [GEMINI.md](GEMINI.md), todos os codigos e documentacoes sao estritamente desprovidos de emojis, mantendo padrao formal de engenharia.

---

## 7. Licenca

Distribuido sob a licenca **Apache 2.0**. Consulte o arquivo [LICENSE](LICENSE) para obter mais informacoes.
