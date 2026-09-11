# Integracao do SLM Especialista em Terminal com Zsh
# Adicione este conteudo ao seu ~/.zshrc

cmd() {
    local prompt="$*"
    if [[ -z "$prompt" ]]; then
        echo "Uso: cmd <o que voce deseja fazer em portugues>"
        return 1
    fi

    local model="term-specialist-q4"
    if ! ollama list 2>/dev/null | grep -q "term-specialist-q4"; then
        model="term-specialist"
    fi

    local suggestion=$(ollama run "$model" "$prompt" 2>/dev/null | head -n 1 | sed 's/^```bash//;s/^```zsh//;s/^```//;s/```$//')

    if [[ -n "$suggestion" ]]; then
        echo ""
        echo "\033[1;32m[Sugestao]\033[0m $suggestion"
        echo ""
        # Injeta o comando diretamente no buffer de digitacao do Zsh para revisao humana
        print -z "$suggestion"
    else
        echo "[AVISO] Nao foi possivel gerar um comando para essa intencao."
    fi
}
