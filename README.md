# 🍽️ Délice Express - Application de Livraison de Repas

Une application web Flask complète pour la gestion de livraison de repas préparés à domicile.

## ✨ Fonctionnalités

### Pour les utilisateurs
- **Inscription et connexion** sécurisées avec hachage des mots de passe
- **Catalogue de repas** avec filtrage par catégorie
- **Panier d'achat** avec gestion des quantités
- **Commande et paiement** avec choix de l'heure de livraison
- **Suivi des commandes** en temps réel avec timeline visuelle
- **Profil utilisateur** modifiable avec préférences

### Caractéristiques techniques
- Framework Flask avec SQLAlchemy ORM
- Authentification via Flask-Login
- Support SQLite (dev) et PostgreSQL (prod)
- **Conteneurisé avec Docker** 🐳
- Interface responsive et moderne

---

## 🚀 Installation

### Option 1: Docker (Recommandé) 🐳

#### Développement avec SQLite
```bash
# Cloner le projet
git clone <repo-url>
cd delice-express

# Lancer avec Docker Compose
docker-compose up -d

# L'application est disponible sur http://localhost:5000
```

#### Production avec PostgreSQL
```bash
# Copier et configurer les variables d'environnement
cp .env.example .env
# Éditer .env avec vos valeurs (SECRET_KEY obligatoire!)

# Lancer la stack de production
docker-compose -f docker-compose.prod.yml up -d

# L'application est disponible sur http://localhost (port 80)
```

### Option 2: Installation locale

```bash
# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou: venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -r requirements.txt

# Lancer l'application
python app.py

# Accéder à http://localhost:5000
```

---

## 🐳 Architecture Docker

### Fichiers Docker
| Fichier | Description |
|---------|-------------|
| `Dockerfile` | Image de développement (SQLite) |
| `Dockerfile.prod` | Image de production optimisée (multi-stage) |
| `docker-compose.yml` | Stack de développement |
| `docker-compose.prod.yml` | Stack de production (PostgreSQL + Nginx) |
| `nginx.conf` | Configuration du reverse proxy |

### Commandes utiles
```bash
# Voir les logs
docker-compose logs -f web

# Reconstruire l'image
docker-compose build --no-cache

# Arrêter les conteneurs
docker-compose down

# Supprimer les volumes (⚠️ efface les données)
docker-compose down -v

# Entrer dans le conteneur
docker exec -it delice-express-app bash
```

---

## ⚙️ Configuration

### Variables d'environnement

| Variable | Description | Défaut |
|----------|-------------|--------|
| `FLASK_ENV` | Environnement (development/production) | `development` |
| `SECRET_KEY` | Clé secrète pour les sessions | Auto-générée |
| `DATABASE_URL` | URL de connexion BDD | SQLite local |
| `APP_PORT` | Port de l'application | `5000` |

### Générer une clé secrète
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 📁 Structure du projet

```
delice-express/
├── app.py                  # Application Flask principale
├── requirements.txt        # Dépendances Python
├── Dockerfile              # Image Docker (dev)
├── Dockerfile.prod         # Image Docker (prod)
├── docker-compose.yml      # Stack Docker (dev)
├── docker-compose.prod.yml # Stack Docker (prod)
├── nginx.conf              # Config Nginx
├── .env.example            # Variables d'environnement
├── .dockerignore           # Fichiers exclus de Docker
├── README.md               # Documentation
└── templates/              # Templates HTML
    ├── base.html
    ├── index.html
    ├── login.html
    ├── register.html
    ├── cart.html
    ├── checkout.html
    ├── orders.html
    ├── order_detail.html
    └── profile.html
```

---

## 🔒 Sécurité en production

1. **Toujours définir `SECRET_KEY`** avec une valeur aléatoire longue
2. **Utiliser HTTPS** (configurer SSL dans Nginx)
3. **Changer les mots de passe** PostgreSQL par défaut
4. **Limiter l'accès réseau** avec un firewall
5. **Mettre à jour régulièrement** les images Docker

---

## 🎨 Design

L'application utilise un design moderne avec :
- **Palette** : tons crème, terracotta et olive
- **Typographies** : Playfair Display + DM Sans
- **Animations** subtiles
- **Interface responsive**

---

## 📝 Repas de démonstration

12 repas variés pré-chargés : Bowls, Cuisine asiatique, Italienne, Burgers, Salades, etc.
Options végétariennes et vegan disponibles.

---

## 🛠️ API Endpoints

| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/` | Page d'accueil / Menu |
| GET/POST | `/register` | Inscription |
| GET/POST | `/login` | Connexion |
| GET | `/logout` | Déconnexion |
| GET | `/cart` | Voir le panier |
| POST | `/add_to_cart/<id>` | Ajouter au panier |
| POST | `/update_cart/<id>` | Modifier le panier |
| GET/POST | `/checkout` | Paiement |
| GET | `/orders` | Liste des commandes |
| GET | `/order/<id>` | Détail commande |
| GET/POST | `/profile` | Profil utilisateur |
| GET | `/api/cart/count` | Nombre d'articles (JSON) |

---

## 📄 Licence

Projet libre d'utilisation et de modification.

---

Développé avec ❤️ et Flask 🐍
