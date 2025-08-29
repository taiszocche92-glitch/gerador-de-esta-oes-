<#
.SYNOPSIS
    Script para monitoramento automático de arquivos em um projeto.

.DESCRIPTION
    Este script atualiza a lista de arquivos do projeto, detecta mudanças
    e realiza revisões diárias com estatísticas. Ideal para manter o controle
    de alterações em projetos de desenvolvimento.

.PARAMETER DailyReview
    Executa a revisão diária com estatísticas do projeto

.PARAMETER UpdateList
    Atualiza a lista de arquivos do projeto

.PARAMETER ShowChanges
    Mostra detalhes das mudanças detectadas

.EXAMPLE
    .\monitor-files.ps1 -UpdateList
    Atualiza a lista de arquivos do projeto

.EXAMPLE
    .\monitor-files.ps1 -DailyReview
    Executa a revisão diária do projeto

.NOTES
    Autor: Equipe de Desenvolvimento
    Versão: 2.0
    Data: 2025-08-26
#>

param(
    [switch]$DailyReview,
    [switch]$UpdateList,
    [switch]$ShowChanges
)

# Configurações
$Cores = @{
    Erro = "Red"
    Sucesso = "Green" 
    Alerta = "Yellow"
    Info = "Blue"
}

$Caminhos = @{
    Projeto = Get-Location
    Memoria = ".\memoria"
    ListaArquivos = ".\memoria\file-list.md"
    LogMudancas = ".\memoria\file-changes-log.md"
}

# Funções utilitárias de monitoramento e backup

function Save-FileList {
    <#
    .SYNOPSIS
        Cria um backup da lista atual de arquivos do projeto.
    .DESCRIPTION
        Salva uma cópia da lista de arquivos antes de atualizá-la, permitindo
        comparação e histórico de alterações.
    #>
    if (Test-Path $Caminhos.ListaArquivos) {
        $CaminhoBackup = "$($Caminhos.Memoria)\file-list-backup-$(Get-Date -Format 'yyyyMMdd-HHmmss').md"
        Copy-Item $Caminhos.ListaArquivos $CaminhoBackup
        Write-Host "Backup criado: $CaminhoBackup" -ForegroundColor $Cores.Alerta
    }
}

function Update-ProjectFileList {
    <#
    .SYNOPSIS
        Atualiza a lista de arquivos do projeto, excluindo diretórios irrelevantes.
    .DESCRIPTION
        Gera uma nova lista de arquivos, faz backup da anterior e registra estatísticas.
    .OUTPUTS
        Retorna array com caminhos dos arquivos encontrados.
    #>
    Write-Host "Atualizando lista de arquivos..." -ForegroundColor $Cores.Alerta
    Save-FileList
    
    try {
        # Diretórios excluídos do monitoramento (configuráveis)
        $DiretoriosExcluidos = @(
            '\\node_modules\\', '\\dist\\', '\\.git\\',
            '\\__pycache__\\', '\\.venv\\', '\\.pytest_cache\\'
        )
        
        # Gerar lista filtrada de arquivos válidos
        $ListaArquivos = Get-ChildItem -Recurse -File |
            Where-Object {
                $caminho = $_.FullName
                $excluido = $false
                foreach ($dir in $DiretoriosExcluidos) {
                    if ($caminho -match $dir) {
                        $excluido = $true
                    }
                }
                -not $excluido
            } |
            Select-Object -ExpandProperty FullName

        # Criar cabeçalho do documento
        $Cabecalho = @"
# LISTA DE ARQUIVOS DO PROJETO

**Data:** $(Get-Date -Format 'dd/MM/yyyy HH:mm:ss')  
**Total:** $($ListaArquivos.Count)  
**Projeto:** $(Split-Path -Leaf $Caminhos.Projeto)  

**Diretórios Excluídos:**
$(($DiretoriosExcluidos | ForEach-Object { "# $_" }) -join "`n")

---

"@

        # Salvar lista
        $Cabecalho | Out-File -FilePath $Caminhos.ListaArquivos -Encoding UTF8
        $ListaArquivos | ForEach-Object { "* $_" } | Out-File -FilePath $Caminhos.ListaArquivos -Append -Encoding UTF8
        
    Write-Host "Lista atualizada com $($ListaArquivos.Count) arquivos" -ForegroundColor $Cores.Sucesso
        return $ListaArquivos
    }
    catch {
        Write-Host "Erro ao atualizar lista: $($_.Exception.Message)" -ForegroundColor $Cores.Erro
        return $null
    }
}

function Compare-ProjectFileLists {
    <#
    .SYNOPSIS
        Compara listas de arquivos e registra mudanças detectadas.
    .PARAMETER ListaNova
        Array com lista atual de arquivos.
    .PARAMETER CaminhoListaAntiga
        Caminho do backup anterior para comparação.
    .DESCRIPTION
        Detecta arquivos adicionados/removidos e registra log detalhado.
    #>
    param(
        [array]$ListaNova,
        [string]$CaminhoListaAntiga
    )
    
    if (-not (Test-Path $CaminhoListaAntiga)) {
        Write-Host "Lista anterior não encontrada" -ForegroundColor $Cores.Alerta
        return
    }
    
    try {
        # Ler lista anterior
        $ConteudoAntigo = Get-Content $CaminhoListaAntiga -Encoding UTF8
        $ListaAntiga = $ConteudoAntigo |
            Where-Object { $_ -match '^\* ' } |
            ForEach-Object { $_.Substring(2) }
        
        # Detectar mudanças
        $Adicionados = Compare-Object $ListaAntiga $ListaNova |
            Where-Object SideIndicator -eq '=>' |
            Select-Object -ExpandProperty InputObject
        
        $Removidos = Compare-Object $ListaAntiga $ListaNova |
            Where-Object SideIndicator -eq '<=' |
            Select-Object -ExpandProperty InputObject
        
        # Registrar mudanças se houver
        if ($Adicionados -or $Removidos) {
            $RegistroMudancas = "## $(Get-Date -Format 'dd/MM/yyyy HH:mm:ss')`n"
            if ($Adicionados) {
                $RegistroMudancas += "### ARQUIVOS ADICIONADOS ($($Adicionados.Count))`n"
                foreach ($item in $Adicionados) { $RegistroMudancas += "- $item`n" }
            }
            if ($Removidos) {
                $RegistroMudancas += "### ARQUIVOS REMOVIDOS ($($Removidos.Count))`n"
                foreach ($item in $Removidos) { $RegistroMudancas += "- $item`n" }
            }
            
            if (-not (Test-Path $Caminhos.LogMudancas)) {
                "# LOG DE MUDANÇAS`n" | Out-File $Caminhos.LogMudancas -Encoding UTF8
            }
            
            $RegistroMudancas | Out-File $Caminhos.LogMudancas -Append -Encoding UTF8
            
            # Exibir resumo
            Write-Host "Mudanças detectadas:" -ForegroundColor $Cores.Alerta
            Write-Host "  Adicionados: $($Adicionados.Count)" -ForegroundColor $Cores.Sucesso
            Write-Host "  Removidos: $($Removidos.Count)" -ForegroundColor $Cores.Erro
            
            if ($ShowChanges) {
                Write-Host "`nDetalhes:" -ForegroundColor $Cores.Info
                $Adicionados | ForEach-Object { Write-Host "  + $_" -ForegroundColor $Cores.Sucesso }
                $Removidos | ForEach-Object { Write-Host "  - $_" -ForegroundColor $Cores.Erro }
            }
        }
        else {
            Write-Host "Nenhuma mudança detectada" -ForegroundColor $Cores.Sucesso
        }
    }
    catch {
        Write-Host "Erro na comparação: $($_.Exception.Message)" -ForegroundColor $Cores.Erro
    }
}

function Start-DailyReview {
    <#
    .SYNOPSIS
        Executa revisão diária do projeto, gerando estatísticas e verificando arquivos essenciais.
    .DESCRIPTION
        Conta arquivos, calcula tamanho total e verifica presença dos arquivos críticos de memória.
    #>
    Write-Host "Iniciando revisão diária..." -ForegroundColor $Cores.Info
    
    # Estatísticas básicas do projeto
    $Arquivos = Get-ChildItem -Recurse -File
    $TotalArquivos = $Arquivos.Count
    $TamanhoTotal = [math]::Round(($Arquivos | Measure-Object -Property Length -Sum).Sum / 1MB, 2)
    
    Write-Host "Estatísticas do Projeto:" -ForegroundColor $Cores.Info
    Write-Host "  Arquivos: $TotalArquivos" -ForegroundColor $Cores.Sucesso
    Write-Host "  Tamanho: $TamanhoTotal MB" -ForegroundColor $Cores.Sucesso
    
    # Verificar arquivos de memória essenciais
    $ArquivosEssenciais = @(
        "$($Caminhos.Memoria)\referencias_base.md",
        "$($Caminhos.Memoria)\config_memoria.json",
        "$($Caminhos.Memoria)\aprendizados_usuario.jsonl"
    )
    
    Write-Host "Verificando arquivos essenciais:" -ForegroundColor $Cores.Info
    $ArquivosEssenciais | ForEach-Object {
        if (Test-Path $_) {
            Write-Host "  OK: $_" -ForegroundColor $Cores.Sucesso
        } else {
            Write-Host "  FALTANDO: $_" -ForegroundColor $Cores.Erro
        }
    }
}

# ===================== Execução Principal do Script ===========================
try {
    Write-Host "`nINÍCIO DO MONITORAMENTO" -ForegroundColor $Cores.Info
    Write-Host "Projeto: $($Caminhos.Projeto)" -ForegroundColor $Cores.Info
    Write-Host "Memória: $($Caminhos.Memoria)" -ForegroundColor $Cores.Info
    Write-Host "Parâmetros: UpdateList=$UpdateList, DailyReview=$DailyReview, ShowChanges=$ShowChanges`n" -ForegroundColor $Cores.Info

    # Criar diretório de memória se necessário
    if (-not (Test-Path $Caminhos.Memoria)) {
        New-Item -ItemType Directory -Path $Caminhos.Memoria -Force | Out-Null
        Write-Host "Diretório de memória criado" -ForegroundColor $Cores.Sucesso
    }

    # Processar operações
    if ($UpdateList) {
        $NovaLista = Update-ProjectFileList
        if ($NovaLista) {
            $Backups = Get-ChildItem "$($Caminhos.Memoria)\file-list-backup-*.md" |
                Sort-Object LastWriteTime -Descending
            if ($Backups) {
                Compare-ProjectFileLists -ListaNova $NovaLista -CaminhoListaAntiga $Backups[0].FullName
            }
        }
    }

    if ($DailyReview) {
        Start-DailyReview
    }

    Write-Host "`nMONITORAMENTO CONCLUÍDO`n" -ForegroundColor $Cores.Sucesso
}
catch {
    Write-Host "ERRO FATAL NO MONITORAMENTO: $($_.Exception.Message)" -ForegroundColor $Cores.Erro
    Write-Host $_.Exception.StackTrace -ForegroundColor $Cores.Erro
    exit 1
}
finally {
    # Pode colocar limpeza aqui se necessário
    Write-Host "Encerrando rotina de monitoramento." -ForegroundColor $Cores.Info
}

<#
===============================================================================
INSTRUÇÕES DE USO RÁPIDO
===============================================================================
1. Execute o script via PowerShell:
    .\monitor-files.ps1 -UpdateList
    .\monitor-files.ps1 -DailyReview
    .\monitor-files.ps1 -UpdateList -ShowChanges

2. Configure o diretório 'memoria' e garanta que arquivos essenciais existam.

3. Consulte os logs em memoria/file-changes-log.md para histórico de alterações.

4. Para dúvidas ou problemas, verifique mensagens de erro/alerta no terminal.

===============================================================================
#>
