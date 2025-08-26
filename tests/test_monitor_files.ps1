# Teste automatizado para monitor-files.ps1
# Executa as funções principais em um ambiente temporário.

$ErrorActionPreference = 'Stop'

$scriptPath = Join-Path $PSScriptRoot '..\memoria\monitoring\monitor-files.ps1'
. $scriptPath

# Criar workspace temporário
$tempDir = Join-Path $env:TEMP "monitor-test-$(Get-Random)"
New-Item -ItemType Directory -Path $tempDir | Out-Null

try {
    # Criar arquivos de teste
    New-Item -ItemType File -Path (Join-Path $tempDir 'README.md') -Value "test" | Out-Null
    New-Item -ItemType File -Path (Join-Path $tempDir 'sample.txt') -Value "sample" | Out-Null

    # Apontar caminhos para o teste
    $Caminhos.Projeto = $tempDir
    $Caminhos.Memoria = Join-Path $tempDir 'memoria'
    if (-not (Test-Path $Caminhos.Memoria)) { New-Item -ItemType Directory -Path $Caminhos.Memoria | Out-Null }
    $Caminhos.ListaArquivos = Join-Path $Caminhos.Memoria 'file-list.md'
    $Caminhos.LogMudancas = Join-Path $Caminhos.Memoria 'file-changes-log.md'

    # Executar atualização e revisão
    $lista = Update-ProjectFileList
    if (-not $lista) { throw "Update-ProjectFileList retornou nulo" }

    Start-DailyReview

    Write-Host "TEST PASSED: Funções executaram sem erro" -ForegroundColor Green
}
catch {
    Write-Host "TEST FAILED: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
finally {
    # Limpar
    Remove-Item -Recurse -Force $tempDir
}
