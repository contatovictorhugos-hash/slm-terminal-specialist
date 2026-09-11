.PHONY: help install validate generate train fuse deploy clean

PYTHON ?= .venv/bin/python
PIP ?= .venv/bin/pip

help:
	@echo "Comandos disponiveis para SLM Especialista em Terminal:"
	@echo "  make install    - Instala as dependencias do projeto no .venv"
	@echo "  make validate   - Executa a auditoria de integridade do dataset"
	@echo "  make generate   - Executa o gerador de dataset sintetico com Gemini API"
	@echo "  make train      - Inicia o treinamento LoRA no Apple Silicon via MLX-LM"
	@echo "  make fuse       - Funde os adaptadores LoRA ao modelo base"
	@echo "  make deploy     - Cria o modelo localmente no Ollama via Modelfile"
	@echo "  make benchmark  - Executa a suite de benchmark com assercoes de estado em sandbox"
	@echo "  make clean      - Remove caches e arquivos temporarios"

install:
	$(PIP) install -r requirements.txt

validate:
	$(PYTHON) dataset/validate_dataset.py

generate:
	$(PYTHON) dataset/generator.py

train:
	$(PYTHON) -m mlx_lm.lora --config training/config.yaml

fuse:
	$(PYTHON) -m mlx_lm.fuse --model Qwen/Qwen2.5-Coder-1.5B-Instruct --adapter-path adapters --save-path models/fused-qwen-terminal

deploy:
	ollama create term-specialist -f deploy/Modelfile -q q4_K_M
	ollama create term-specialist-q4 -f deploy/Modelfile -q q4_K_M

benchmark:
	$(PYTHON) benchmark/run.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.py[cod]" -delete
	find . -type f -name ".DS_Store" -delete
	rm -rf .cache
