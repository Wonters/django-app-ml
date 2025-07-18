# Django ML App

## Description
Django ML App est une application Django pour intégrer des capacités de machine learning dans vos applications Django. Elle fournit une façon transparente de gérer les modèles ML, suivre les expériences et gérer les tâches asynchrones dans un environnement de production.

## Version
Version actuelle: 1.0.0

## Fonctionnalités
- Intégration serveur Django pour le déploiement de modèles ML
- Intégration notebook Marimo pour le développement ML interactif
- Intégration MLflow pour le suivi d'expériences et la gestion de modèles
- Dramatiq et Redis pour la gestion des tâches ML asynchrones
- Gestion de pipeline ML prêt pour la production
- Interface frontend moderne avec Vite
- API REST complète avec Django REST Framework

## Table des matières
1. [Prérequis](#prérequis)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Développement Frontend](#développement-frontend)
5. [Production](#production)
6. [Utilisation](#utilisation)
7. [API Reference](#api-reference)
8. [Contribuer](#contribuer)
9. [Licence](#licence)

## Prérequis

### Système
- Python 3.8+
- Node.js 16+ (pour le frontend)
- Redis 6.0+
- PostgreSQL (recommandé) ou SQLite

### Services externes
- Redis pour Dramatiq et le cache
- Base de données PostgreSQL (optionnel mais recommandé)

## Installation

### 1. Installation du package Python

```bash
# Installation via pip
pip install django-app-ml

# Ou installation depuis le source
git clone https://github.com/Wonters/django-ml-app.git
cd django-app-ml
pip install -e .
```

### 2. Installation des dépendances système

#### Ubuntu/Debian
```bash
# Redis
sudo apt update
sudo apt install redis-server

# PostgreSQL (optionnel)
sudo apt install postgresql postgresql-contrib

# Node.js et npm
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

#### macOS
```bash
# Avec Homebrew
brew install redis postgresql node

# Démarrer Redis
brew services start redis
```

#### Windows
```bash
# Installer Redis via WSL ou Docker
# Installer Node.js depuis https://nodejs.org/
```

### 3. Installation des dépendances frontend

```bash
cd django-app-ml/static/ml_app
npm install
```

## Configuration

### 1. Configuration Django Settings

Ajoutez les applications suivantes dans votre `settings.py`:

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Applications tierces
    'rest_framework',
    'corsheaders',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'bootstrap4',
    'django_dramatiq',
    
    # Application ML
    'django_app_ml',
]

# Configuration Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'django_app_ml.renderer.MLDataRenderer',
    ],
}

# Configuration CORS
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",  # Vite dev server
]

CORS_ALLOW_CREDENTIALS = True

# Configuration Redis et Dramatiq
REDIS_URL = "redis://localhost:6379/0"

DRAMATIQ_BROKER = {
    "BROKER": "dramatiq.brokers.redis.RedisBroker",
    "OPTIONS": {
        "url": REDIS_URL,
    },
    "MIDDLEWARE": [
        "dramatiq.middleware.Prometheus",
        "dramatiq.middleware.AgeLimit",
        "dramatiq.middleware.TimeLimit",
        "dramatiq.middleware.Callbacks",
        "dramatiq.middleware.Retries",
        "django_dramatiq.middleware.DbConnectionsMiddleware",
        "django_dramatiq.middleware.AdminMiddleware",
    ]
}

# Configuration cache
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

# Configuration base de données (PostgreSQL recommandé)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'your_db_name',
        'USER': 'your_db_user',
        'PASSWORD': 'your_db_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Configuration statiques et médias
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Configuration ML App
ML_APP_CONFIG = {
    'MODEL_STORAGE_PATH': os.path.join(BASE_DIR, 'ml_models'),
    'EXPERIMENT_TRACKING': True,
    'MLFLOW_TRACKING_URI': 'http://localhost:5000',
    'DEFAULT_MODEL_FORMAT': 'pickle',
    'ASYNC_TASK_TIMEOUT': 3600,  # 1 heure
    'MAX_FILE_SIZE': 100 * 1024 * 1024,  # 100MB
}
```

### 2. Configuration des URLs

Dans votre `urls.py` principal:

```python
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('django_app_ml.urls')),
    path('ml/', include('django_app_ml.urls')),
    path('accounts/', include('allauth.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
```

### 3. Configuration Dramatiq

Créez un fichier `dramatiq.py` à la racine de votre projet:

```python
import dramatiq
from django_dramatiq import setup_dramatiq

# Configuration Dramatiq
setup_dramatiq()

# Import des tâches
from django_app_ml.tasks import *
```

### 4. Migrations

```bash
python manage.py makemigrations django_app_ml
python manage.py migrate
```

## Développement Frontend

### 1. Configuration Vite

Le frontend utilise Vite pour le développement. Configuration dans `static/ml_app/vite.config.js`:

```javascript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  root: 'static/ml_app',
  build: {
    outDir: '../../staticfiles/ml_app',
    emptyOutDir: true,
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'static/ml_app/src/main.js'),
        dashboard: resolve(__dirname, 'static/ml_app/src/dashboard.js'),
      },
      output: {
        entryFileNames: 'js/[name]-[hash].js',
        chunkFileNames: 'js/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash].[ext]'
      }
    }
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
```

### 2. Structure Frontend

```
static/ml_app/
├── src/
│   ├── components/
│   │   ├── MLDashboard.vue
│   │   ├── ModelUpload.vue
│   │   └── ExperimentTracker.vue
│   ├── services/
│   │   ├── api.js
│   │   └── mlService.js
│   ├── main.js
│   └── dashboard.js
├── package.json
└── vite.config.js
```

### 3. Scripts de développement

```bash
# Développement frontend
cd static/ml_app
npm run dev
# ou dans un container 
npm run dev -- --host 0.0.0.0

# Build de développement
npm run build:dev

# Build de production
npm run build:prod
```

## Production

### 1. Build des assets

```bash
# Build frontend
cd static/ml_app
npm run build:prod

# Collecte des statiques Django
python manage.py collectstatic --noinput
```

### 2. Configuration serveur

#### Gunicorn + Nginx

```bash
# Installation Gunicorn
pip install gunicorn

# Démarrage avec Gunicorn
gunicorn --workers 3 --bind 0.0.0.0:8000 your_project.wsgi:application
```

#### Configuration Nginx

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /static/ {
        alias /path/to/your/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /path/to/your/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 3. Services système

#### Service Dramatiq

```bash
# /etc/systemd/system/dramatiq.service
[Unit]
Description=Dramatiq Worker
After=network.target redis.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/your/project
ExecStart=/path/to/venv/bin/python manage.py runserver dramatiq
Restart=always

[Install]
WantedBy=multi-user.target
```

## Utilisation

### 1. Démarrage des services

```bash
# Démarrer Dramatiq worker
python manage.py runserver dramatiq

# Démarrer Django
python manage.py runserver

# Démarrer Vite (développement)
cd static/ml_app && npm run dev
```

### 2. Interface d'administration

Accédez à `http://localhost:8000/admin/` pour gérer:
- Modèles ML
- Expériences
- Tâches asynchrones
- Utilisateurs

### 3. API REST

L'API est disponible sur `/api/` avec les endpoints:
- `/api/models/` - Gestion des modèles
- `/api/experiments/` - Suivi d'expériences
- `/api/tasks/` - Tâches asynchrones
- `/api/predictions/` - Prédictions

## API Reference

### Modèles

```python
from django_app_ml.models import MLModel, Experiment, Prediction

# Créer un modèle
model = MLModel.objects.create(
    name="Mon Modèle",
    version="1.0.0",
    model_file="path/to/model.pkl",
    algorithm="random_forest"
)

# Créer une expérience
experiment = Experiment.objects.create(
    name="Test Expérience",
    model=model,
    parameters={"n_estimators": 100},
    metrics={"accuracy": 0.95}
)
```

### Tâches asynchrones

```python
from django_app_ml.tasks import train_model_task, predict_task

# Lancer une tâche d'entraînement
task_id = train_model_task.send(
    model_id=model.id,
    training_data="path/to/data.csv",
    parameters={"n_estimators": 100}
)

# Lancer une prédiction
prediction_id = predict_task.send(
    model_id=model.id,
    input_data={"feature1": 1.0, "feature2": 2.0}
)
```

## Contribuer

Nous accueillons les contributions ! Veuillez lire nos directives de contribution avant de soumettre des pull requests.

### Processus de contribution

1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/AmazingFeature`)
3. Commit vos changements (`git commit -m 'Add some AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

### Tests

```bash
# Lancer les tests
pytest

# Avec couverture
pytest --cov=django_app_ml
```

## Licence

Ce projet est sous licence MIT - voir le fichier LICENSE pour plus de détails.