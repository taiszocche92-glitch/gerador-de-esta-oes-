# Teste do endpoint /api/agent/start-creation via PowerShell

$body = @{
    tema = "Crise Asmática"
    especialidade = "Clínica Médica"
}

$bodyJson = @{
    tema = "Crise Asmática"
    especialidade = "Clínica Médica"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8080/api/agent/start-creation" -Method POST -ContentType "application/json" -Body $bodyJson

Write-Host "Status Code:" $response.StatusCode
Write-Host "Response Body:" $response | ConvertTo-Json -Depth 10