# Script PowerShell: execução rápida de reindex (smoke test)
Write-Host "Iniciando smoke reindex: 10 documentos" -ForegroundColor Cyan
$script = Join-Path -Path $PSScriptRoot -ChildPath "reindex_vectors.py"
if (-not (Test-Path $script)) {
    Write-Host "Arquivo reindex_vectors.py não encontrado em $PSScriptRoot" -ForegroundColor Red
    exit 1
}

python $script --model models/text-embedding-004 --limit 10 --sleep-between 0.1
$exit = $LASTEXITCODE
if ($exit -eq 0) {
    Write-Host "Reindex smoke concluído com código 0" -ForegroundColor Green
} else {
    Write-Host "Reindex smoke terminou com código $exit" -ForegroundColor Yellow
}
