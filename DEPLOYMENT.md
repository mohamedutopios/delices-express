# 🚀 Guide de Déploiement - Délice Express

Ce guide vous explique comment déployer l'application en ligne pour la rendre accessible.

---

## Option 1: Railway (Recommandé pour démo) ⭐

**Gratuit** : 500 heures/mois + $5 de crédit offert

### Étapes

1. **Créer un compte** sur [railway.app](https://railway.app)

2. **Installer Railway CLI** (optionnel mais pratique)
   ```bash
   npm install -g @railway/cli
   railway login
   ```

3. **Déployer depuis GitHub**
   - Poussez votre code sur GitHub
   - Sur Railway : "New Project" → "Deploy from GitHub repo"
   - Sélectionnez votre repo

4. **Ou déployer en ligne de commande**
   ```bash
   cd delice-express
   railway init
   railway up
   ```

5. **Configurer les variables d'environnement**
   - Dans Railway Dashboard → Variables :
   ```
   SECRET_KEY=votre-cle-secrete-generee
   FLASK_ENV=production
   STRIPE_PUBLIC_KEY=pk_test_xxx (optionnel)
   STRIPE_SECRET_KEY=sk_test_xxx (optionnel)
   ```

6. **Générer un domaine**
   - Settings → Domains → "Generate Domain"
   - Vous obtenez : `delice-express-xxx.up.railway.app`

### ✅ C'est tout ! Votre app est en ligne.

---

## Option 2: Render.com

**Gratuit** : Plan free avec limitations (spin down après 15min d'inactivité)

### Étapes

1. **Créer un compte** sur [render.com](https://render.com)

2. **Nouveau Web Service**
   - "New" → "Web Service"
   - Connecter votre repo GitHub

3. **Configuration**
   - Name: `delice-express`
   - Environment: `Docker`
   - Plan: `Free`

4. **Variables d'environnement**
   ```
   SECRET_KEY=votre-cle-secrete
   FLASK_ENV=production
   ```

5. **Déployer** → Cliquez "Create Web Service"

### URL finale : `delice-express.onrender.com`

---

## Option 3: Fly.io

**Gratuit** : 3 VMs partagées gratuites

### Étapes

1. **Installer Fly CLI**
   ```bash
   # macOS
   brew install flyctl
   
   # Linux
   curl -L https://fly.io/install.sh | sh
   
   # Windows
   powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
   ```

2. **Se connecter**
   ```bash
   fly auth signup  # ou fly auth login
   ```

3. **Déployer**
   ```bash
   cd delice-express
   fly launch  # Répondre aux questions
   fly deploy
   ```

4. **Configurer les secrets**
   ```bash
   fly secrets set SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
   fly secrets set STRIPE_PUBLIC_KEY=pk_test_xxx
   fly secrets set STRIPE_SECRET_KEY=sk_test_xxx
   ```

5. **Ouvrir l'application**
   ```bash
   fly open
   ```

### URL finale : `delice-express.fly.dev`

---

## Option 4: VPS (DigitalOcean, Hetzner, OVH)

Pour plus de contrôle et une vraie production.

### DigitalOcean ($4-6/mois)

1. **Créer un Droplet**
   - Image: Ubuntu 22.04
   - Plan: Basic $4/mois (1GB RAM)
   - Région: Frankfurt ou Amsterdam

2. **Se connecter en SSH**
   ```bash
   ssh root@votre-ip
   ```

3. **Installer Docker**
   ```bash
   curl -fsSL https://get.docker.com | sh
   apt install docker-compose-plugin
   ```

4. **Déployer l'application**
   ```bash
   git clone https://github.com/votre-user/delice-express.git
   cd delice-express
   cp .env.example .env
   nano .env  # Configurer les variables
   docker compose up -d
   ```

5. **Configurer Nginx + SSL (optionnel)**
   ```bash
   apt install nginx certbot python3-certbot-nginx
   # Configurer le reverse proxy et obtenir un certificat SSL
   ```

---

## 🔧 Variables d'environnement requises

| Variable | Description | Obligatoire |
|----------|-------------|-------------|
| `SECRET_KEY` | Clé secrète Flask | ✅ Oui |
| `FLASK_ENV` | `production` | ✅ Oui |
| `STRIPE_PUBLIC_KEY` | Clé publique Stripe | Non (mode démo) |
| `STRIPE_SECRET_KEY` | Clé secrète Stripe | Non (mode démo) |

### Générer une clé secrète
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 🗄️ Persistance des données

### SQLite (par défaut)
- ⚠️ Sur Railway/Render gratuit, les données peuvent être perdues au redémarrage
- Solution : Utiliser PostgreSQL

### PostgreSQL (recommandé pour production)

**Sur Railway :**
1. "New" → "Database" → "PostgreSQL"
2. Copier `DATABASE_URL` dans les variables

**Sur Render :**
1. "New" → "PostgreSQL"
2. Copier l'Internal Database URL

**Variable à ajouter :**
```
DATABASE_URL=postgresql://user:password@host:5432/dbname
```

---

## 🌐 Domaine personnalisé

### Sur Railway/Render/Fly
1. Acheter un domaine (Namecheap, OVH, Gandi...)
2. Dans les settings du service : "Custom Domain"
3. Ajouter les enregistrements DNS fournis

### Certificat SSL
- Railway/Render/Fly : **Automatique** ✅
- VPS : Utiliser Let's Encrypt avec Certbot

---

## 📊 Comparatif des options

| Critère | Railway | Render | Fly.io | VPS |
|---------|---------|--------|--------|-----|
| **Facilité** | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐ |
| **Gratuit** | 500h/mois | Limité | 3 VMs | Non |
| **SSL** | Auto | Auto | Auto | Manuel |
| **Persistance** | Volume $$ | Disk $$ | Volume | ✅ |
| **PostgreSQL** | Inclus | Inclus | Add-on | Manuel |
| **Scalabilité** | Bonne | Bonne | Excellente | Manuelle |

---

## ❓ FAQ

**Q: Quelle option pour une simple démo ?**
> Railway ou Render - déploiement en 5 minutes

**Q: Mes données sont-elles persistantes ?**
> Sur les plans gratuits, pas toujours. Utilisez PostgreSQL pour plus de sécurité.

**Q: Comment avoir un nom de domaine personnalisé ?**
> Achetez un domaine et configurez-le dans les settings de votre plateforme.

**Q: L'application ne démarre pas ?**
> Vérifiez les logs et assurez-vous que SECRET_KEY est définie.

---

## 🆘 Support

- **Railway** : [docs.railway.app](https://docs.railway.app)
- **Render** : [render.com/docs](https://render.com/docs)
- **Fly.io** : [fly.io/docs](https://fly.io/docs)
