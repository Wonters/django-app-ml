# Page de Liste des Datasets

## Description

Cette page affiche la liste de tous les datasets disponibles dans l'application dans un datatable interactif avec des fonctionnalités de recherche, tri et pagination.

## Fonctionnalités

### Datatable
- **Recherche globale** : Recherche dans toutes les colonnes
- **Tri** : Tri par colonne (ID, Nom, Source, Status)
- **Pagination** : 10 éléments par page par défaut
- **Responsive** : Adaptation automatique aux différentes tailles d'écran

### Colonnes affichées

1. **ID** : Identifiant unique du dataset
2. **Nom** : Nom du dataset
3. **Source** : Lien vers la source des données
4. **Status** : Indicateur visuel du statut de déploiement
   - 🟢 **Déployé** : Le dataset a des modèles associés
   - 🟡 **Non déployé** : Aucun modèle associé au dataset
5. **Actions** : Trois boutons d'action
   - 👁️ **Voir** : Affiche les détails du dataset dans un modal
   - ✏️ **Modifier** : Redirection vers la page d'édition (à implémenter)
   - 📥 **Télécharger** : Télécharge les données du dataset en CSV

### Actions disponibles

#### Bouton "Voir" (👁️)
- Ouvre un modal avec les détails complets du dataset
- Affiche :
  - Informations générales (ID, Nom, Source, Status)
  - Statistiques (nombre de modèles associés)
  - Liste des modèles associés au dataset

#### Bouton "Modifier" (✏️)
- Actuellement affiche un message d'information
- À implémenter : redirection vers une page d'édition

#### Bouton "Télécharger" (📥)
- Télécharge automatiquement un fichier CSV contenant les métadonnées du dataset
- Nom du fichier : `dataset_{id}.csv`

## Structure technique

### Fichiers créés/modifiés

#### Templates
- `django_app_ml/templates/ml_app/dataset_list.html` : Template principal
- `django_app_ml/templates/scoring_app/base.html` : Ajout du lien de navigation

#### Vues
- `django_app_ml/views.py` :
  - `DatasetListView` : Vue principale pour afficher la liste
  - `DatasetDetailView` : API pour récupérer les détails d'un dataset
  - `DatasetDownloadView` : API pour télécharger un dataset

#### URLs
- `django_app_ml/urls/urls_scoring_app.py` : Ajout des nouvelles routes

#### Assets statiques
- `static/ml_app/js/dataset_list.js` : Logique JavaScript pour le datatable
- `static/ml_app/css/dataset_list.css` : Styles personnalisés

### APIs disponibles

#### GET `/django_app_ml/scoring_model/api/datasets/{id}/detail/`
Retourne les détails d'un dataset au format JSON :
```json
{
  "id": 1,
  "name": "Dataset Example",
  "source": "https://example.com/data",
  "is_deployed": true,
  "deployment_status": "Déployé",
  "models_count": 2,
  "models": [
    {"id": 1, "name": "Model 1"},
    {"id": 2, "name": "Model 2"}
  ]
}
```

#### GET `/django_app_ml/scoring_model/api/datasets/{id}/download/`
Télécharge un fichier CSV contenant les métadonnées du dataset.

## Utilisation

### Accès à la page
1. Naviguer vers l'application Django ML
2. Cliquer sur le bouton "Datasets" dans la barre de navigation
3. Ou accéder directement à `/django_app_ml/scoring_model/datasets/`

### Utilisation du datatable
- **Recherche** : Utiliser la barre de recherche en haut à droite
- **Tri** : Cliquer sur les en-têtes de colonnes
- **Navigation** : Utiliser les boutons de pagination en bas
- **Actions** : Cliquer sur les boutons dans la colonne Actions

## Personnalisation

### Ajout de nouvelles colonnes
1. Modifier le template `dataset_list.html`
2. Ajouter la colonne dans le tableau HTML
3. Mettre à jour la configuration DataTable dans `dataset_list.js`

### Modification des actions
1. Éditer les fonctions dans `dataset_list.js`
2. Ajouter de nouvelles vues API si nécessaire
3. Mettre à jour les URLs

### Styles personnalisés
1. Modifier le fichier `dataset_list.css`
2. Les styles utilisent Bootstrap 4 et Font Awesome 5

## Dépendances

### Frontend
- **jQuery** : Pour les interactions DOM
- **DataTables** : Pour le datatable
- **Bootstrap 4** : Pour le design
- **Font Awesome 5** : Pour les icônes

### Backend
- **Django REST Framework** : Pour les APIs
- **Django** : Framework principal

## Améliorations futures

1. **Page d'édition** : Implémenter la fonctionnalité de modification
2. **Filtres avancés** : Ajouter des filtres par status, date, etc.
3. **Bulk actions** : Actions en lot sur plusieurs datasets
4. **Export avancé** : Support pour d'autres formats (Excel, JSON)
5. **Historique** : Suivi des modifications sur les datasets
6. **Permissions** : Gestion des droits d'accès par utilisateur 