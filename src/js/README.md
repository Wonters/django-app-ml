# Module task.js - Gestion des tâches asynchrones

Ce module fournit des fonctions pour gérer les tâches asynchrones avec polling automatique et feedback utilisateur.

## Fonctions disponibles

### `getCookie(name)`
Récupère la valeur d'un cookie par son nom.

```javascript
import { getCookie } from './task.js';
const csrfToken = getCookie("csrftoken");
```

### `pollUploadStatus(taskId, downloadLink, originalText)`
Fonction spécialisée pour le polling des tâches d'upload de dataset.

```javascript
import { pollUploadStatus } from './task.js';

// Après avoir lancé une tâche d'upload
if (data.status === 'pending' && data.task_id) {
    pollUploadStatus(data.task_id, downloadLink, originalText);
}
```

### `pollTaskStatus(taskId, endpoint, element, originalText, taskName)`
Fonction générique pour le polling de n'importe quelle tâche.

**Paramètres :**
- `taskId` : ID de la tâche
- `endpoint` : URL de l'endpoint pour vérifier le statut
- `element` : Élément DOM à mettre à jour (optionnel)
- `originalText` : Texte original de l'élément (optionnel)
- `taskName` : Nom de la tâche pour les messages (défaut: "Tâche")

```javascript
import { pollTaskStatus } from './task.js';

pollTaskStatus(
    taskId,
    `/ml_app/api/datasets/${datasetId}/audit/`,
    auditButton,
    originalText,
    "Audit de dataset"
);
```

### `launchTaskAndPoll(taskEndpoint, taskData, element, originalText, taskName)`
Fonction complète pour lancer une tâche et gérer automatiquement le polling.

**Paramètres :**
- `taskEndpoint` : URL de l'endpoint pour lancer la tâche
- `taskData` : Données à envoyer avec la requête POST
- `element` : Élément DOM à mettre à jour
- `originalText` : Texte original de l'élément
- `taskName` : Nom de la tâche pour les messages

```javascript
import { launchTaskAndPoll } from './task.js';

launchTaskAndPoll(
    `/ml_app/api/datasets/${datasetId}/audit/`,
    {}, // Données vides pour l'audit
    auditButton,
    originalText,
    "Audit de dataset"
);
```

## Exemples d'utilisation

### Gestion de l'upload de dataset (main.js)
```javascript
import { getCookie, pollUploadStatus } from './task.js';

// Dans handleDatasetDownload()
if (data.status === 'pending' && data.task_id) {
    pollUploadStatus(data.task_id, downloadLink, originalText);
}
```

### Gestion de l'audit de dataset (dataset_analysis/tasks.js)
```javascript
import { getCookie, pollTaskStatus } from '../task.js';

// Dans pollAnalysisStatus()
const adaptedPollTaskStatus = (taskId, endpoint, element, originalText, taskName) => {
    // Utilise pollTaskStatus avec des callbacks adaptés
    pollTaskStatus(taskId, endpoint, element, originalText, taskName);
};
```

## Intégration avec le dossier dataset_analysis

Le module `task.js` est utilisé dans le dossier `dataset_analysis` pour :

1. **Import des fonctions utilitaires** : `getCookie` est importé dans `tasks.js`
2. **Polling des tâches** : `pollTaskStatus` est utilisé dans `pollAnalysisStatus`
3. **Gestion des tâches d'audit et d'analyse IA** : Les fonctions existantes utilisent le module

### Structure des fichiers :
```
django-app-ml/static/js/
├── task.js                    # Module principal
├── main.js                    # Utilise pollUploadStatus
└── dataset_analysis/
    ├── main.js               # Point d'entrée
    ├── tasks.js              # Utilise getCookie et pollTaskStatus
    ├── audit.js              # Gestion de l'audit
    └── ia_analysis.js        # Gestion de l'analyse IA
```

## États des tâches

Le module gère automatiquement les états suivants :

- **pending** : Tâche en attente de traitement
- **running** : Tâche en cours d'exécution
- **completed** : Tâche terminée avec succès
- **failed** : Tâche échouée

## Configuration

- **Timeout** : 5 minutes maximum (60 tentatives × 5 secondes)
- **Intervalle de polling** : 5 secondes
- **Messages d'erreur** : Automatiques avec le nom de la tâche
- **Rechargement** : Automatique après succès

## Intégration avec Vite

Le module est compatible avec Vite et sera automatiquement inclus via les imports ES6. Assurez-vous que le fichier `task.js` est dans le bon répertoire par rapport aux fichiers qui l'importent. 