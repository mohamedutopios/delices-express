FROM python:3.11-slim

# Métadonnées
LABEL maintainer="Délice Express"
LABEL description="Application de livraison de repas préparés"
LABEL version="1.0"

# Variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=app.py \
    FLASK_ENV=production \
    APP_ENV=production \
    DATA_DIR=/app

# Créer un utilisateur non-root pour la sécurité
RUN groupadd -r delice && useradd -r -g delice delice

# Répertoire de travail
WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copier et installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code de l'application
COPY app.py .
COPY templates/ templates/

# Créer le répertoire pour la base de données et donner les permissions
RUN mkdir -p /app/data && chown -R delice:delice /app

# Utiliser l'utilisateur non-root
USER delice

# Exposer le port
EXPOSE 5000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/')" || exit 1

# Commande de démarrage avec Gunicorn pour la production
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--threads", "2", "--timeout", "120", "app:app"]
