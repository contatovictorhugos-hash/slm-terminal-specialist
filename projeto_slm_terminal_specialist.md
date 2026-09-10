# Projeto: SLM Especialista em Terminal & Automação CLI (NL ➔ Shell)

> **Documento de Arquitetura Técnica, Pipeline e Fronteiras do Sistema**  
> *Autor:* Victor Moreira  
> *Ambiente Alvo:* macOS (Apple Silicon) + Terminal ZSH  

---

## 1. Objetivo do Projeto

O objetivo deste projeto é construir uma **SLM (Small Language Model) de 1.5B a 3B parâmetros** finamente ajustada para traduzir comandos em linguagem natural (português) em **comandos de terminal precisos, determinísticos e de alta performance** (Bash, Zsh, AWK, Sed, Python one-liners e utilitários Unix).

### A Tese Central: "A IA é o Piloto, o Sistema Operacional é o Motor"
Em vez de fazer um modelo de IA gigante carregar gigabytes de arquivos para a memória:
1. O usuário expressa o que deseja em português no terminal.
2. A **SLM local responde em menos de 100ms** com o comando exato.
3. O **sistema operacional nativo (em C/Rust/Bash) processa os dados** em velocidade de hardware sem estourar limites de contexto e sem custo de tokens.

---

## 2. O Papel Estratégico da sua Assinatura Google Pro (API do Gemini)

A sua assinatura Google Pro com acesso à **API do Gemini** é o ingrediente que viabiliza o projeto com **custo zero de treinamento**.

Em projetos de SLM, aplica-se o conceito de **Destilação de Conhecimento (*Knowledge Distillation*)**:
* Um modelo gigante e inteligente (**Gemini 1.5 Pro / Flash**) atua como o **"Professor"**: ele gera milhares de pares perfeitos de treino *(Linguagem Natural ➔ Comando Terminal)*.
* A SLM local (**Qwen 2.5 Coder 1.5B/3B** ou **Llama 3.2 3B**) atua como o **"Aluno"**: aprende a imitar a precisão sintática do professor, tornando-se ultra-especialista naquele domínio restrito.

---

## 3. Arquitetura do Pipeline (As 5 Ferramentas)

```mermaid
flowchart TD
    subgraph Fase 1: Dados & Destilação
        G[Gemini API (Google Pro)] -->|Gera 3.000 pares NL -> Bash| D[Distilabel]
        D -->|Filtra e Valida Sintaxe| DS[(Dataset HuggingFace Format)]
    end

    subgraph Fase 2: Fine-Tuning Local
        DS --> M[MLX-LM (Apple Silicon GPU)]
        M -->|LoRA Adapters| F[Pesos Ajustados]
        L[LLaMA-Factory] -.->|Opcional: Gráficos de Perda / WebUI| M
    end

    subgraph Fase 3: Quantização & Deploy
        F --> C[llama.cpp]
        C -->|Converte para GGUF Q4_K_M| Q[(Modelo 4-bit ~1.8GB)]
        Q --> O[Ollama Local Daemon]
    end

    subgraph Fase 4: Uso no Terminal
        U[Usuário no Zsh: cmd 'junte os csvs'] --> O
        O -->|50ms| R[Comando sugerido pronto para execução]
    end
```

### Detalhamento das Ferramentas:

1. **Distilabel (+ Gemini API via LiteLLM / Google GenAI):**
   * Automatiza a criação do dataset em lote. Envia prompts sistemáticos para o Gemini gerar casos de uso reais (manipulação de CSV, junção de PDFs, filtros de texto, monitoramento de portas e processos).
   * Valida se os comandos gerados não contêm alucinações antes de salvar.

2. **MLX-LM (Treinamento no Mac):**
   * O motor de fine-tuning oficial da Apple. Usa a memória unificada do seu chip M-series para treinar os pesos via LoRA em 15 a 30 minutos, sem precisar alugar máquinas em nuvem.

3. **LLaMA-Factory (Gestão e Avaliação):**
   * Fornece a interface visual para acompanhar as curvas de perda (*loss*) e testar o modelo antes de empacotar.

4. **llama.cpp (Quantização):**
   * Converte o modelo treinado para o formato padrão da indústria **GGUF** em 4-bit (`Q4_K_M`). Isso reduz o tamanho do modelo de ~7 GB para apenas ~1.8 GB sem perda perceptível de inteligência.

5. **Ollama (Serviço Local):**
   * Roda o modelo como serviço em segundo plano no macOS com consumo quase nulo de bateria quando ocioso.

---

## 4. Avaliação Crítica da Stack: É a melhor para esse objetivo?

> [!NOTE]
> **Veredito:** Para um desenvolvedor no ecossistema **macOS (Apple Silicon)**, esta é a **stack mais moderna, barata e eficiente existente hoje no mercado open-source.**

* **Por que MLX-LM em vez de PyTorch tradicional?**  
  No Mac, PyTorch com Metal Performance Shaders (MPS) ainda tem gargalos de alocação de memória. O MLX foi desenhado pelos engenheiros da Apple especificamente para a arquitetura de memória compartilhada do seu computador.
* **Por que Distilabel + Gemini?**  
  Com a API do Gemini Pro inclusa na sua assinatura, você elimina a necessidade de pagar provedores como OpenAI para sintetizar dados. O Gemini é excelente na geração de sintaxes de código e comandos POSIX.
* **Onde há uma redundância controlada:**  
  O *LLaMA-Factory* é excelente para quem usa Linux/Nvidia. No Mac, você pode fazer todo o fine-tuning diretamente pelo *MLX-LM* via terminal. O LLaMA-Factory torna-se uma ferramenta de apoio visual caso você queira inspecionar hiperparâmetros graficamente.

---

## 5. A Fronteira: Até onde vamos? (O Limite do Sistema)

Definir claramente o escopo evita frustrações e previne acidentes no sistema operacional.

```
┌────────────────────────────────────────────────────────┐
│               DENTRO DA FRONTEIRA                      │
│  ✔ Tradução de intenção em linguagem natural           │
│  ✔ Geração e impressão do comando puro (apenas sugere) │
│  ✔ Manipulação de arquivos em massa (PDF, CSV, JSON)   │
│  ✔ Troubleshooting (portas, processos, rede, disco)    │
│  ✔ Python one-liners e filtros AWK/Sed complexos       │
│  ✔ Latência ultrabaixa (< 100ms) e 100% offline        │
├────────────────────────────────────────────────────────┤
│                FORA DA FRONTEIRA (LIMITES)             │
│  ✖ Zero execução: a SLM NÃO roda comandos (só imprime) │
│  ✖ Leitura semântica do conteúdo interno de arquivos   │
│  ✖ Agente autônomo com múltiplos passos de raciocínio  │
│  ✖ Tarefas criativas ou conversa fiada (chat generalista)│
└────────────────────────────────────────────────────────┘
```

### O que ela faz com maestria (Dentro da fronteira):
* **Automação de dados em lote:** Juntar 50 PDFs em ordem natural; juntar 100 CSVs preservando apenas o primeiro cabeçalho; extrair colunas de relatórios.
* **Comandos difíceis de memorizar:** Sintaxes intrincadas de `ffmpeg`, `tar`, `awk`, `find`, `rsync` e `sed`.
* **Ações de DevOps locais:** Matar processos presos em portas específicas, inspecionar consumo de RAM/CPU por processo, verificar certificados SSL via `curl`.

### Onde ela para (Fora da fronteira):
1. **Zero Execução no Sistema (Regra de Ouro):**  
   A SLM **não executa nenhum comando no seu computador**. Ela funciona como um compilador de intenção: gera e imprime a linha de comando como texto puro no terminal. A responsabilidade de bater o olho, revisar e teclar `[ENTER]` para executar é **100% sua**. Isso elimina qualquer risco de acidentes ou execução não intencional.
2. **Não analisa o "conteúdo" profundo dos arquivos:**  
   Se você perguntar *"o que esse contrato em PDF diz na cláusula 4?"*, essa SLM **não** serve. Ela manipula a estrutura do arquivo (junta, separa, converte), mas não substitui um modelo de raciocínio multimodal (para isso, use o Gemini Pro ou o Antigravity).
3. **Não é um agente com estado contínuo (Multi-turn):**  
   Ela é um modelo de tiro único (*single-shot instruction follower*): `Pergunta ➔ Comando Bash`.

---

## 6. A Escolha da SLM Base: Por que Qwen 2.5 Coder?

A escolha do modelo base é fundamental para o sucesso do projeto. O modelo vencedor indiscutível para esta tarefa é o **`Qwen 2.5 Coder`** (especificamente as variantes **1.5B** e **3B**).

### Escolha Principal: `Qwen/Qwen2.5-Coder-1.5B-Instruct`
* **Parâmetros:** 1.54 Bilhões
* **Tamanho quantizado (GGUF 4-bit):** Apenas **~1.1 GB**
* **Consumo de Memória RAM:** ~1.5 GB
* **Velocidade no Mac (Apple Silicon):** ~90 a 130 tokens/segundo (resposta em ~30-50ms)

#### Os 4 Diferenciais Técnicos:
1. **Pré-treinado especificamente em Código e Terminal:** Diferente de modelos generalistas que gastam parâmetros com conhecimentos enciclopédicos gerais, a família *Coder* foi treinada em petabytes de código, scripts Bash, sintaxe POSIX e ferramentas de sistema.
2. **Precisão Cirúrgica de Flags:** Modelos generalistas pequenos tendem a inventar flags inexistentes no Unix. O Qwen Coder já possui uma base sólida da sintaxe real do Linux/macOS.
3. **Tokenizer Eficiente para Português:** Possui vocabulário amplo de 152k tokens, evitando a fragmentação excessiva de palavras em português e garantindo latência mínima.
4. **Suporte Nativo no MLX-LM:** Treina e roda no chip Apple Silicon do seu Mac sem necessidade de patches ou adaptações.

> [!TIP]
> **Quando optar pelo `Qwen2.5-Coder-3B-Instruct`?**  
> Se o seu objetivo incluir gerar pipelines muito extensos com múltiplos comandos encadeados (`awk` complexo, `sed` e `xargs` com regex avançado na mesma linha), a versão de **3B** (~2.1 GB) oferece maior capacidade de raciocínio mantendo resposta abaixo de 100ms.

---

## 7. Como fica a experiência final no seu Terminal

Após o deploy no Ollama, criamos uma função simples no seu `~/.zshrc`:

```bash
# Adicionado ao ~/.zshrc
cmd() {
    local prompt="$*"
    local command=$(ollama run term-specialist "Gere apenas o comando para: $prompt")
    echo "\n\033[1;32mSugestão:\033[0m $command\n"
    print -z "$command" # Carrega o comando direto na sua linha de digitação
}
```

### Exemplo de uso no seu dia a dia:
```zsh
$ cmd "junte todos os csvs da pasta ignorando o cabecalho a partir do segundo"

Sugestão: awk 'FNR==1 && NR!=1 {next} 1' *.csv > consolidado.csv
# O comando já aparece no seu cursor pronto para você revisar e dar [ENTER]!
```

---

## 8. Próximos Passos Recomendados

1. **Obter chave de API do Gemini:** Gerar uma chave no Google AI Studio (vinculada à sua conta Google Pro).
2. **Definir o Schema do Dataset:** Criar um script Python simples com `distilabel` para gerar os primeiros 500 exemplos de teste.
3. **Download do Modelo Base:** Baixar os pesos do `Qwen/Qwen2.5-Coder-1.5B-Instruct`.
4. **Treino e Teste:** Rodar o primeiro fine-tuning com `mlx-lm` no Mac e validar o modelo no Zsh.
