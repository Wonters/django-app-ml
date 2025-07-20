# Audit de Dataset avec Daft

Ce module fournit des outils complets pour auditer des datasets en utilisant Daft, une bibliothèque de traitement de données distribuées en Python.

## Fonctionnalités

### 🔍 Analyse de base
- **Informations générales** : Nombre de lignes, colonnes, types de données
- **Valeurs manquantes** : Détection et quantification des données manquantes
- **Qualité des données** : Métriques de complétude et de doublons

### 📊 Statistiques descriptives
- **Colonnes numériques** : Moyenne, écart-type, min, max, médiane
- **Colonnes catégorielles** : Nombre de valeurs uniques, valeurs les plus fréquentes
- **Détection d'outliers** : Méthodes IQR et Z-score

### 📈 Rapports détaillés
- **Export JSON** : Rapports complets sauvegardés au format JSON
- **Logging** : Traçabilité complète des opérations
- **Intégration Dramatiq** : Traitement asynchrone des audits

## Installation

Les dépendances sont déjà incluses dans `requirements.txt` :
```bash
pip install -r requirements.txt
```

## Utilisation

### 1. Audit rapide

```python
from django_app_ml.dataset_audit import quick_audit

# Audit rapide d'un dataset
results = quick_audit("path/to/your/dataset.parquet")
print(f"Nombre de lignes: {results['basic_info']['row_count']}")
```

### 2. Audit complet avec classe

```python
from django_app_ml.dataset_audit import DatasetAuditor

# Créer un auditeur
auditor = DatasetAuditor()

# Audit complet avec sauvegarde du rapport
results = auditor.full_audit(
    dataset_path="path/to/your/dataset.parquet",
    save_report=True,
    report_path="audit_report.json"
)
```

### 3. Audit asynchrone avec Dramatiq

```python
from django_app_ml.tasks import audit_dataset_task

# Lancer un audit en arrière-plan
audit_dataset_task.send(
    dataset_path="path/to/your/dataset.parquet",
    save_report=True,
    report_path="audit_report.json"
)
```

### 4. Script d'exemple

```bash
# Exécuter le script d'exemple
python example_audit.py
```

## Formats supportés

- **Parquet** : `.parquet`
- **CSV** : `.csv`

## Structure des résultats

### Informations de base
```json
{
  "basic_info": {
    "row_count": 1000,
    "column_count": 6,
    "column_names": ["id", "age", "salary", "department"],
    "column_types": {"id": "Int64", "age": "Int64", "salary": "Int64"}
  }
}
```

### Valeurs manquantes
```json
{
  "missing_values": {
    "age": 50,
    "salary": 30
  }
}
```

### Statistiques descriptives
```json
{
  "descriptive_stats": {
    "age": {
      "mean": 35.2,
      "std": 10.1,
      "min": 18,
      "max": 65,
      "median": 34
    }
  }
}
```

### Qualité des données
```json
{
  "data_quality": {
    "age": {
      "duplicate_ratio": 0.05,
      "missing_ratio": 0.05,
      "completeness": 0.95
    }
  }
}
```

### Outliers
```json
{
  "outliers": {
    "salary": {
      "method": "iqr",
      "lower_bound": 25000,
      "upper_bound": 75000,
      "outlier_count": 15
    }
  }
}
```

## Méthodes de détection d'outliers

### 1. Méthode IQR (Interquartile Range)
- Calcule Q1 (25ème percentile) et Q3 (75ème percentile)
- Définit les bornes : `[Q1 - 1.5*IQR, Q3 + 1.5*IQR]`
- Les valeurs en dehors de ces bornes sont considérées comme des outliers

### 2. Méthode Z-score
- Calcule la moyenne et l'écart-type
- Définit les outliers comme les valeurs avec `|z-score| > 3`
- Plus sensible aux distributions normales

## Intégration avec Django

### Vue pour l'audit de dataset

```python
from django.http import JsonResponse
from django_app_ml.dataset_audit import DatasetAuditor

def audit_dataset_view(request):
    dataset_path = request.POST.get('dataset_path')
    
    try:
        auditor = DatasetAuditor()
        results = auditor.full_audit(dataset_path, save_report=True)
        return JsonResponse({'success': True, 'results': results})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
```

### Template HTML

```html
<form method="post" enctype="multipart/form-data">
    {% csrf_token %}
    <input type="file" name="dataset" accept=".parquet,.csv">
    <button type="submit">Auditer le dataset</button>
</form>
```

## Configuration

### Variables d'environnement

```bash
# Chemin par défaut pour les rapports d'audit
AUDIT_REPORTS_DIR=./audit_reports

# Niveau de logging
AUDIT_LOG_LEVEL=INFO
```

### Configuration Dramatiq

```python
# settings.py
DRAMATIQ_BROKER = {
    "BROKER": "dramatiq.brokers.redis.RedisBroker",
    "OPTIONS": {
        "url": "redis://localhost:6379",
    },
    "MIDDLEWARE": [
        "dramatiq.middleware.Prometheus",
        "dramatiq.middleware.Deduplication",
    ]
}
```

## Bonnes pratiques

### 1. Gestion de la mémoire
- Utilisez Daft pour les gros datasets (distribué)
- Évitez de charger tout le dataset en mémoire pour les analyses simples

### 2. Performance
- Utilisez l'audit asynchrone pour les gros datasets
- Cachez les résultats d'audit fréquemment utilisés

### 3. Sécurité
- Validez les chemins de fichiers
- Limitez l'accès aux fichiers sensibles
- Utilisez des timeouts appropriés

### 4. Monitoring
- Surveillez les temps d'exécution
- Loggez les erreurs et exceptions
- Utilisez des métriques pour les audits

## Exemples d'utilisation avancée

### Audit personnalisé

```python
auditor = DatasetAuditor()

# Charger le dataset
df = auditor.load_dataset("dataset.parquet")

# Analyses spécifiques
missing_info = auditor.get_missing_values(df)
numeric_stats = auditor.get_descriptive_stats(df, ["age", "salary"])
categorical_stats = auditor.get_categorical_stats(df, ["department"])
outliers = auditor.detect_outliers(df, ["salary"], method="zscore")
```

### Audit de plusieurs datasets

```python
import glob
from pathlib import Path

datasets = glob.glob("data/*.parquet")
auditor = DatasetAuditor()

for dataset_path in datasets:
    print(f"Audit de {dataset_path}")
    results = auditor.full_audit(dataset_path)
    print(f"Complétude moyenne: {sum(results['data_quality'].values()) / len(results['data_quality']):.2%}")
```

## Dépannage

### Erreurs courantes

1. **Format non supporté**
   ```
   ValueError: Format de fichier non supporté: dataset.txt
   ```
   Solution : Utilisez des fichiers .parquet ou .csv

2. **Mémoire insuffisante**
   ```
   MemoryError: Unable to allocate array
   ```
   Solution : Utilisez Daft pour le traitement distribué

3. **Timeout**
   ```
   TimeoutError: Operation timed out
   ```
   Solution : Augmentez les timeouts ou utilisez l'audit asynchrone

### Logs utiles

```python
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("django_app_ml.dataset_audit")
```

## Support

Pour toute question ou problème :
1. Consultez les logs Django
2. Vérifiez la documentation Daft
3. Testez avec le script d'exemple
4. Contactez l'équipe de développement 