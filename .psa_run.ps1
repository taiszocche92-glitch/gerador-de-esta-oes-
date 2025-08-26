Import-Module PSScriptAnalyzer -ErrorAction SilentlyContinue
if (-not (Get-Module -ListAvailable PSScriptAnalyzer)) {
    Write-Host 'PSScriptAnalyzer não instalado'
    exit 2
}

$target = 'd:\Site arquivos\Projeto vs code\meuapp\backend-python-agent\memoria\monitoring\monitor-files.ps1'
$issues = Invoke-ScriptAnalyzer -Path $target -Recurse -Severity Warning,Error,Information
if ($issues) {
    $issues | Select-Object Severity,RuleName,RuleId,Message,ScriptName,Line | Format-Table -AutoSize | Out-String -Width 200 | Write-Host
} else {
    Write-Host 'Nenhum problema encontrado pelo PSScriptAnalyzer'
}
