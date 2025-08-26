# start-backend.ps1 - ativa .venv, carrega .env (se existir) e inicia uvicorn.
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $here

# Activate venv
$activate = Join-Path $here ".venv\Scripts\Activate.ps1"
if (Test-Path $activate) {
    & $activate
}
else {
    Write-Host "Aviso: .venv não encontrado em $here. Ative manualmente se necessário." -ForegroundColor Yellow
}

# Load .env if exists
$envFile = Join-Path $here ".env"
if (Test-Path $envFile) {
    Write-Host "Carregando variáveis de ambiente de .env..."
    Get-Content $envFile | ForEach-Object {
        if ($_ -and -not $_.StartsWith("#")) {
            $parts = $_ -split "=", 2
            if ($parts.Length -eq 2) {
                $k = $parts[0].Trim()
                $v = $parts[1].Trim().Trim("'`"")
                try {
                    # Definir variável de ambiente usando Set-Item para nomes dinâmicos
                    Set-Item -Path ("Env:" + $k) -Value $v -ErrorAction Stop
                }
                catch {
                    Write-Host ("⚠️ Não foi possível definir variável de ambiente {0}: {1}" -f $k, $_) -ForegroundColor Yellow
                }
            }
        }
    }
}

# Ensure GOOGLE_APPLICATION_CREDENTIALS if exists in typical local path
$credPath = "C:\Users\helli\secrets\revalida-companion-firebase-adminsdk.json"
if (Test-Path $credPath) {
    $env:GOOGLE_APPLICATION_CREDENTIALS = $credPath
}

# Start uvicorn (executar dentro de backend-python-agent)
Write-Host "Iniciando backend: python -m uvicorn main:app --reload --port 8080" -ForegroundColor Green
python -m uvicorn main:app --reload --port 8080
