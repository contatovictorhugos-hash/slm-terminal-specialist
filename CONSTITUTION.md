# Constituição do Projeto: SLM Especialista em Terminal & Automação CLI

> **Documento Normativo de Governança, Arquitetura e Fronteiras Operacionais**  
> *Versão:* 1.0  
> *Ambiente Primário:* macOS (Apple Silicon / M-Series) + Zsh  
> *Modelo Base:* Qwen 2.5 Coder (1.5B / 3B)  

---

## Preâmbulo

Este documento estabelece as diretrizes inegociáveis, a arquitetura de engenharia e os limites de segurança para a concepção, treinamento, empacotamento e distribuição da **SLM Especialista em Terminal**. Qualquer decisão de implementação, alteração de pipeline ou expansão de dataset deve estar em estrita conformidade com os artigos aqui definidos.

---

## Artigo I — Missão e Filosofia Central

1. **A Tese:** *"A IA é o compilador da intenção; o Sistema Operacional é o motor de execução."*
2. **Propósito:** Capacitar desenvolvedores e administradores a orquestrarem fluxos de trabalho no terminal Unix/macOS através de linguagem natural (PT-BR), reduzindo o atrito cognitivo de sintaxes complexas (`awk`, `sed`, `ffmpeg`, `find`, `xargs`, `tar`, `rsync`, etc.).
3. **Eficiência de Recursos:** O modelo não deve carregar dados massivos para a memória de contexto; ele emite a instrução de terminal determinística para que utilitários nativos em C, Rust e Bash processem dados em velocidade de hardware.

---

## Artigo II — Princípio da Soberania Humana e Segurança Inegociável

1. **Cláusula de Zero Execução Autônoma:**  
   O modelo é estritamente um **gerador/sugeridor de comandos**. Sob nenhuma circunstância a SLM terá permissão de invocar subprocessos, disparar chamadas de sistema (`os.system`, `subprocess.run`, `eval`) ou executar diretamente os comandos gerados.
2. **Formato de Resposta Estritamente Limpo:**  
   A resposta do modelo deve ser única e exclusivamente a linha de comando pura.
   * **Proibido:** Textos introdutórios (*"Aqui está o comando:"*), explicações adicionais, conversação de preenchimento ou blocos de formatação markdown (` ```bash `) na inferência final de produção.
3. **Revisão Humana Obrigatória:**  
   A integração no shell Zsh deve carregar o comando diretamente no buffer de digitação do usuário (`print -z "$cmd"`), mantendo a prerrogativa soberana do usuário de inspecionar a sintaxe antes de teclar `[ENTER]`.

---

## Artigo III — Fronteiras do Sistema (Escopo e Limites)

### Seção 1: Dentro do Escopo (Capacidades Essenciais)
* **Manipulação de Arquivos e Diretórios:** Junção, separação, conversão e renomeação em massa (PDF, CSV, JSON, imagens via ImageMagick, mídia via FFmpeg).
* **Filtros e Processamento Tabular:** Extração de colunas, contagem condicional, agregação e limpeza de texto (`awk`, `sed`, `grep`, `cut`, `sort`, `uniq`, `jq`).
* **DevOps e Operações de Sistema:** Identificação e liberação de portas de rede (`lsof`, `netstat`), inspeção de processos (`ps`, `pkill`, `kill`), consumo de hardware (`top`, `df`, `du`), certificados SSL (`curl`), Git e Docker.
* **Pipelines Concatenados e One-liners:** Encadeamento lógico via pipes (`|`), redirecionamentos (`>`, `>>`) e substituição de comandos quando requisitado.

### Seção 2: Fora do Escopo (Linhas Vermelhas)
* **Sem Raciocínio Semântico sobre Conteúdo:** O modelo não analisa contratos, não resume textos de arquivos e não responde a dúvidas semânticas gerais.
* **Sem Agência Multi-passo (Loops Autônomos):** O modelo opera em modo de tiro único (*single-shot instruction following*). Não haverá ciclos de auto-correção iterativos no terminal sem supervisão.
* **Sem Respostas Conversacionais:** Dúvidas abertas fora de automação CLI devem ser rejeitadas ou redirecionadas.

---

## Artigo IV — Arquitetura de Pipeline e Ferramental

O ciclo de vida do modelo é composto por quatro fases desacopladas e integradas:

```
[Gemini API (Google Pro)] ➔ [Dataset Formatado] ➔ [MLX-LM (Fine-Tuning M-Series)] ➔ [GGUF Q4_K_M] ➔ [Ollama + Zsh]
```

1. **Destilação de Conhecimento (Professor ➔ Aluno):**  
   Utilização da API do Gemini (Google AI Studio) para gerar e validar pares de treino sintéticos de alta densidade sem custo de inferência na nuvem.
2. **Motor de Treinamento:**  
   **MLX-LM** como motor de treinamento primário, tirando proveito da arquitetura de memória unificada da GPU Apple Silicon via LoRA (Low-Rank Adaptation).
3. **Quantização e Empacotamento:**  
   Exportação e quantização para formato **GGUF 4-bit (`Q4_K_M`)**, assegurando pegada de memória mínima sem degradação de precisão sintática.
4. **Camada de Inferência Local:**  
   Distribuição via daemon local do **Ollama**, operando 100% offline com consumo energético desprezível em estado ocioso.

---

## Artigo V — Critérios de Desempenho e Modelo Base

1. **Modelo Base Oficial:** `Qwen/Qwen2.5-Coder-1.5B-Instruct` (alternativa para pipelines complexos: `Qwen/Qwen2.5-Coder-3B-Instruct`).
2. **Latência Máxima Aceitável:** Tempo de resposta do primeiro token inferior a **100ms** (meta operacional: **30 a 50ms** no Apple Silicon).
3. **Pegada de Memória:**  
   * Variante 1.5B (Q4_K_M): ≤ 1.2 GB de VRAM/RAM.  
   * Variante 3.0B (Q4_K_M): ≤ 2.2 GB de VRAM/RAM.
4. **Isolamento de Rede:**  
   Após o download e quantização, a inferência diária deve funcionar em modo estritamente **offline (air-gapped)**.

---

## Artigo VI — Governança e Qualidade do Dataset

1. **Distribuição Proporcional de Classes:**
   * **35% — Manipulação de Arquivos e Mídia** (PDFs, CSVs, imagens, compressão, backup).
   * **30% — Filtros e Processamento de Texto** (`awk`, `sed`, `jq`, regex, parsing).
   * **25% — Engenharia de Sistemas e Redes** (portas, processos, Docker, Git, diagnósticos).
   * **10% — One-liners Complexos e Automações Especiais** (Python `-c`, xargs complexos).
2. **Fidelidade ao Ecossistema macOS/BSD:**  
   O dataset deve contemplar explicitamente as particularidades do ecossistema macOS (utilitários BSD vs GNU, flags de `sed`, `find`, `stat`, `date`, `grep` e caminhos do sistema Apple).
3. **Validação Sintática Automática:**  
   Nenhum comando com erros de sintaxe ou alucinação de flags inexistentes poderá ser incluído no split final de treino (`train.jsonl`).

---

## Artigo VII — Disposições Finais e Evolução

Qualquer expansão deste projeto para incluir novos shells (ex: Fish, Bash puro em Linux) ou modelos de maior porte deverá respeitar integralmente os Artigos II e III desta Constituição.
