FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Define o diretório de trabalho dentro do container
WORKDIR /app

COPY requirements.txt .

# Instala as dependências
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copia todo o resto do código do projeto para o container
COPY . .

# Cria as pastas de estáticos e mídia e dá permissões
RUN mkdir -p staticfiles media

# Coleta os arquivos estáticos do Django
RUN python manage.py collectstatic --noinput --settings=ponto_frequencia.settings

EXPOSE 8000

CMD ["gunicorn", "ponto_frequencia.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]