# Système de Recommandation IA avec LangChain et ChatGPT

Ce module fournit un système complet pour générer des recommandations d'utilisation IA basées sur l'audit d'un dataset, en utilisant LangChain et ChatGPT.

## 🚀 Fonctionnalités

- **Analyse automatique** des rapports d'audit de datasets
- **Recommandations IA** personnalisées avec types de modèles et applications
- **Parsing robuste** des réponses ChatGPT avec fallback
- **Résumé statistique** des recommandations
- **Intégration facile** dans les applications Django

## 📋 Prérequis

### Dépendances

Les dépendances suivantes ont été ajoutées au `requirements.txt` :

```txt
langchain==0.2.16
langchain-openai==0.1.25
openai==1.58.1
python-dotenv==1.0.1
```

### Configuration

1. **Clé API OpenAI** : Définissez votre clé API OpenAI dans l'environnement :
   ```bash
   export OPENAI_API_KEY='votre_cle_api_openai'
   ```

2. **Variables d'environnement** : Créez un fichier `.env` à la racine du projet :
   ```env
   OPENAI_API_KEY=votre_cle_api_openai
   ```

## 🔧 Installation

1. **Installer les dépendances** :
   ```bash
   pip install -r requirements.txt
   ```

2. **Vérifier l'installation** :
   ```bash
   python -c "from django_app_ml.recommandation import DatasetRecommendationService; print('✅ Installation réussie')"
   ```

## 📖 Utilisation

### Utilisation Simple

```python
from django_app_ml.recommandation import get_ai_recommendations

# Votre rapport d'audit
audit_report = {
    "dataset_info": {
        "nom": "Mon_Dataset",
        "nombre_lignes": 1000,
        "nombre_colonnes": 5
    },
    "colonnes": [
        {
            "nom": "feature1",
            "type": "numeric",
            "description": "Feature numérique"
        },
        {
            "nom": "target",
            "type": "categorical",
            "valeurs_uniques": ["A", "B", "C"],
            "description": "Variable cible"
        }
    ]
}

# Obtenir les recommandations
recommendations = get_ai_recommendations(audit_report)

# Afficher les résultats
for i, rec in enumerate(recommendations, 1):
    print(f"Recommandation {i}:")
    print(f"  Descriptif: {rec['descriptif']}")
    print(f"  Modèles: {', '.join(rec['type_models'])}")
    print(f"  Applications: {len(rec['applications_probables'])}")
```

### Utilisation avec Résumé

```python
from django_app_ml.recommandation import get_recommendations_with_summary

# Obtenir recommandations avec résumé
resultat = get_recommendations_with_summary(audit_report)

print(f"Nombre de recommandations: {resultat['nombre_recommandations']}")
print("Types de modèles populaires:")
for model, count in resultat['types_modeles_populaires']:
    print(f"  - {model}: {count} fois")
```

### Utilisation Avancée

```python
from django_app_ml.recommandation import DatasetRecommendationService

# Créer une instance du service
service = DatasetRecommendationService(api_key="votre_cle_api")

# Générer les recommandations
recommendations = service.generate_recommendations(audit_report)

# Obtenir le résumé
summary = service.get_recommendations_summary(recommendations)

# Utiliser les résultats
print(json.dumps(summary, indent=2, ensure_ascii=False))
```

## 📊 Structure des Données

### Format du Rapport d'Audit

Le rapport d'audit doit être un dictionnaire JSON contenant :

```json
{
    "dataset_info": {
        "nom": "Nom du dataset",
        "nombre_lignes": 1000,
        "nombre_colonnes": 5,
        "taille_fichier_mb": 25.5
    },
    "colonnes": [
        {
            "nom": "nom_colonne",
            "type": "numeric|categorical|string|datetime",
            "description": "Description de la colonne",
            "valeurs_uniques": ["val1", "val2"],  // Pour les colonnes catégorielles
            "min": 0,  // Pour les colonnes numériques
            "max": 100
        }
    ],
    "qualite_donnees": {
        "valeurs_manquantes": 0.02,
        "doublons": 0.01,
        "incoherences": 0.005
    },
    "statistiques": {
        "repartition_categories": {
            "categorie1": 0.6,
            "categorie2": 0.4
        }
    }
}
```

### Format des Recommandations

Les recommandations sont retournées sous la forme :

```json
{
    "recommendations": [
        {
            "descriptif": "Description détaillée de l'utilisation possible",
            "type_models": ["RandomForest", "XGBoost", "LightGBM"],
            "applications_probables": [
                {
                    "type_application": "classification",
                    "descriptif_court": "Classification des données"
                },
                {
                    "type_application": "prediction",
                    "descriptif_court": "Prédiction de valeurs"
                }
            ]
        }
    ]
}
```

## 🧪 Tests

### Exécuter les Tests

```bash
# Tests unitaires
python test_recommandation.py

# Tests avec couverture
python -m pytest test_recommandation.py -v --cov=django_app_ml.recommandation
```

### Exemple d'Utilisation

```bash
# Exécuter l'exemple
python example_usage.py
```

## 🔍 Types de Modèles Supportés

Le système reconnaît et recommande les types de modèles suivants :

- **CNN** : Convolutional Neural Networks
- **LLM** : Large Language Models
- **LightGBM** : Gradient Boosting
- **RandomForest** : Random Forest
- **XGBoost** : Extreme Gradient Boosting
- **SVM** : Support Vector Machines
- **KNN** : K-Nearest Neighbors
- **Neural Networks** : Réseaux de neurones
- **Transformer** : Modèles Transformer
- **BERT** : Bidirectional Encoder Representations from Transformers

## 🎯 Types d'Applications Supportés

- **Classification** : Classification binaire ou multi-classes
- **Prédiction** : Prédiction de valeurs continues
- **Segmentation d'image** : Segmentation d'images
- **Génération d'image** : Génération d'images
- **Détection d'objets** : Détection d'objets dans les images
- **Analyse de sentiment** : Analyse de sentiment
- **Recommandation** : Systèmes de recommandation
- **Clustering** : Groupement de données
- **Anomaly Detection** : Détection d'anomalies
- **Time Series** : Analyse de séries temporelles

## ⚙️ Configuration Avancée

### Personnalisation du Prompt

Vous pouvez personnaliser les prompts en modifiant les attributs de la classe `DatasetRecommendationService` :

```python
service = DatasetRecommendationService(api_key="votre_cle")

# Personnaliser le prompt système
service.system_prompt = "Votre prompt système personnalisé"

# Personnaliser le template utilisateur
service.user_prompt_template = "Votre template personnalisé {audit_report}"
```

### Paramètres du Modèle

```python
from langchain_openai import ChatOpenAI

# Créer un modèle personnalisé
llm = ChatOpenAI(
    model="gpt-4",  # ou "gpt-3.5-turbo"
    temperature=0.3,  # Contrôle la créativité (0.0 = déterministe, 1.0 = très créatif)
    max_tokens=2000,  # Nombre maximum de tokens
    api_key="votre_cle"
)

service = DatasetRecommendationService(api_key="votre_cle")
service.llm = llm
```

## 🚨 Gestion d'Erreurs

Le système inclut une gestion robuste des erreurs :

- **Validation de la clé API** : Vérification de la présence de la clé API
- **Parsing de fallback** : Méthode alternative si le parsing Pydantic échoue
- **Logging détaillé** : Logs pour le débogage
- **Gestion des exceptions** : Capture et gestion des erreurs

### Exemples d'Erreurs Courantes

```python
# Erreur : Clé API manquante
try:
    service = DatasetRecommendationService()
except ValueError as e:
    print(f"Erreur: {e}")  # "Clé API OpenAI requise"

# Erreur : Format d'audit invalide
try:
    recommendations = service.generate_recommendations({})
except Exception as e:
    print(f"Erreur lors de la génération: {e}")
```

## 🔄 Intégration Django

### Dans une Vue Django

```python
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django_app_ml.recommandation import get_recommendations_with_summary
import json

@csrf_exempt
def generate_recommendations(request):
    if request.method == 'POST':
        try:
            audit_report = json.loads(request.body)
            resultat = get_recommendations_with_summary(audit_report)
            return JsonResponse(resultat)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
```

### Dans un Modèle Django

```python
from django.db import models
from django_app_ml.recommandation import get_ai_recommendations
import json

class Dataset(models.Model):
    name = models.CharField(max_length=200)
    audit_report = models.JSONField()
    recommendations = models.JSONField(null=True, blank=True)
    
    def generate_recommendations(self):
        """Génère et sauvegarde les recommandations IA"""
        try:
            recommendations = get_ai_recommendations(self.audit_report)
            self.recommendations = recommendations
            self.save()
            return recommendations
        except Exception as e:
            raise Exception(f"Erreur lors de la génération: {e}")
```

## 📈 Performance

### Optimisations Recommandées

1. **Cache des recommandations** : Stockez les recommandations pour éviter les appels répétés
2. **Batch processing** : Traitez plusieurs datasets en lot
3. **Async processing** : Utilisez des tâches asynchrones pour les gros datasets

### Exemple avec Cache

```python
import redis
from django_app_ml.recommandation import get_ai_recommendations
import hashlib
import json

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def get_cached_recommendations(audit_report, cache_ttl=3600):
    """Récupère les recommandations avec cache Redis"""
    # Créer une clé de cache basée sur le contenu de l'audit
    audit_hash = hashlib.md5(json.dumps(audit_report, sort_keys=True).encode()).hexdigest()
    cache_key = f"recommendations:{audit_hash}"
    
    # Vérifier le cache
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Générer les recommandations
    recommendations = get_ai_recommendations(audit_report)
    
    # Mettre en cache
    redis_client.setex(cache_key, cache_ttl, json.dumps(recommendations))
    
    return recommendations
```

## 🤝 Contribution

Pour contribuer au projet :

1. Fork le repository
2. Créez une branche pour votre fonctionnalité
3. Ajoutez des tests pour votre code
4. Soumettez une pull request

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.

## 🆘 Support

Pour toute question ou problème :

1. Consultez la documentation
2. Vérifiez les tests unitaires
3. Ouvrez une issue sur GitHub
4. Contactez l'équipe de développement 