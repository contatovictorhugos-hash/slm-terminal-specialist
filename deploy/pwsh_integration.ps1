# Integracao do SLM Especialista em Terminal para Windows / PowerShell (pwsh)
# Adicione este conteudo ao seu perfil do PowerShell ($PROFILE)

function cmd {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$PromptArgs
    )

    $prompt = $PromptArgs -join " "
    if ([string]::IsNullOrWhiteSpace($prompt)) {
        Write-Host "Uso: cmd <o que voce deseja fazer em portugues>"
        return
    }

    $model = "term-specialist-q4"
    $taggedPrompt = "[PowerShell] $prompt"

    try {
        $rawOutput = (ollama run $model $taggedPrompt 2>$null) | Select-Object -First 1
    } catch {
        $rawOutput = $null
    }

    if ($rawOutput) {
        $cleanCmd = $rawOutput -replace '^```(powershell|pwsh|bash|zsh)?', '' -replace '```$', ''
        $cleanCmd = $cleanCmd.Trim()

        Write-Host ""
        Write-Host "[Sugestao (PowerShell)] $cleanCmd" -ForegroundColor Green
        Write-Host ""

        # Copia automaticamente para a area de transferencia para colar imediato (Ctrl+V)
        Set-Clipboard -Value $cleanCmd
        Write-Host "[INFO] Comando copiado para a area de transferencia. Use Ctrl+V para colar e executar." -ForegroundColor DarkGray
    } else {
        Write-Warning "[AVISO] Nao foi possivel gerar um comando para essa intencao."
    }
}
