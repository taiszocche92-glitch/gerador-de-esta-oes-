# Define as instruções para "empacotar" nossa aplicação em um contêiner,
# que é o formato que o Cloud Run utiliza para implantar serviços.

# Use uma imagem base oficial do Python.
FROM python:3.11-slim

# Define o diretório de trabalho dentro do contêiner.
WORKDIR /app

# Copia o arquivo de dependências para o contêiner.
COPY requirements.txt .

# Instala as dependências.
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código da aplicação para o contêiner.
COPY . .

# Expõe a porta que a aplicação irá rodar.
EXPOSE 8080

# Comando para iniciar a aplicação quando o contêiner for executado.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
