
# Sincronização de relógio Windows
w32tm /resync

# Verificar status
w32tm /query /status

# Forçar sincronização
net stop w32time
net start w32time
w32tm /resync
