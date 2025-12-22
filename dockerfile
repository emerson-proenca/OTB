FROM python:3.13-slim

WORKDIR /app

# Evita que o Python gere arquivos .pyc e permite logs em tempo real
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instala dependências do sistema necessárias para algumas bibliotecas
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copia os arquivos de dependências primeiro (otimiza o cache do Docker)
COPY pyproject.toml .
COPY uv.lock .
 

RUN pip install --no-cache-dir .
COPY . .

# Expõe a porta que o Render utiliza
EXPOSE 8000

# Usamos 4 workers para lidar com múltiplas requisições se necessário
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]