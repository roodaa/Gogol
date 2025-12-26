# Gogol - Interface Web Frontend

Interface web moderne Angular pour le moteur de recherche Gogol.

## Description

Application Angular 21 avec une interface moderne incluant :
- Sidebar avec statistiques en temps réel
- Barre de recherche intuitive
- Affichage des résultats avec pourcentage de cohérence
- Design responsive avec gradient violet moderne

## Prérequis

- Node.js 18+ et npm
- L'API backend Gogol doit être lancée sur http://127.0.0.1:8000

## Installation

```bash
# Installer les dépendances
npm install
```

## Démarrage

```bash
# Lancer le serveur de développement
npm start
# ou
ng serve
```

L'application sera disponible sur http://localhost:4200

## Avant de lancer l'interface

**IMPORTANT** : Assurez-vous que l'API backend est démarrée :

```bash
# Dans le dossier racine du projet Gogol
python run_api.py
```

L'API doit être accessible sur http://127.0.0.1:8000

## Fonctionnalités

### Sidebar
- 🔍 Logo et titre Gogol
- ✅ Statut de l'API (en ligne/hors ligne)
- 📊 Statistiques de l'index :
  - Nombre de documents indexés
  - Nombre de termes uniques
  - Nombre de postings
  - Taille de la base de données

### Zone de recherche
- 🎯 Barre de recherche avec validation
- 🔘 Bouton de recherche avec état de chargement
- ⚡ Loader animé pendant la recherche

### Résultats
- 📈 **Pourcentage de cohérence** affiché pour chaque résultat
- 🏷️ Termes traités (après stemming) affichés en chips
- 📄 Cartes de résultats avec :
  - Titre du document
  - URL cliquable
  - Score de cohérence en grand
  - Métadonnées (ID document, score détaillé)
- 🎨 Effets hover et animations

## Architecture

```
frontend/
├── src/
│   ├── app/
│   │   ├── services/
│   │   │   └── search.ts          # Service API (HttpClient)
│   │   ├── app.ts                 # Composant principal
│   │   ├── app.html               # Template avec sidebar
│   │   ├── app.css                # Styles modernes
│   │   └── app.config.ts          # Configuration Angular
│   ├── styles.css                 # Styles globaux
│   └── main.ts                    # Bootstrap application
├── angular.json                   # Configuration Angular CLI
├── package.json                   # Dépendances npm
└── tsconfig.json                  # Configuration TypeScript
```

## Technologies utilisées

- **Angular 21** - Framework moderne
- **TypeScript** - Langage typé
- **RxJS** - Programmation réactive pour les appels API
- **Standalone Components** - Pas de NgModule
- **Signals** - Gestion d'état réactive
- **HttpClient** - Communication avec l'API FastAPI

## Build de production

```bash
npm run build
```

Les fichiers de production seront générés dans `dist/frontend/`

## Développement

### Structure du composant principal (App)

```typescript
export class App implements OnInit {
  // Signals pour la réactivité
  title = signal('Gogol Search');
  query = signal('');
  searchResults = signal<SearchResponse | null>(null);
  isLoading = signal(false);
  errorMessage = signal<string | null>(null);
  healthStatus = signal<HealthResponse | null>(null);
  stats = signal<IndexStats | null>(null);

  // Méthodes
  ngOnInit() - Charge le statut et les stats au démarrage
  onSearch() - Effectue une recherche
  formatScore(score) - Formate le score en pourcentage
}
```

### Service de recherche

```typescript
@Injectable({ providedIn: 'root' })
export class SearchService {
  search(query, limit) - Recherche des documents
  getHealth() - Vérifie le statut de l'API
  getStats() - Récupère les statistiques de l'index
}
```

## Endpoints API utilisés

- `GET /api/search?q=query&limit=10` - Recherche
- `GET /api/health` - Statut de l'API
- `GET /api/stats` - Statistiques de l'index

## Style et design

- **Couleurs principales** : Gradient violet (#667eea → #764ba2)
- **Police** : System font stack (SF Pro, Segoe UI, Roboto)
- **Layout** : Flexbox avec sidebar fixe
- **Responsive** : Mobile-first avec breakpoint à 768px
- **Animations** : Transitions CSS pour les interactions

## Contribution

Ce projet fait partie du moteur de recherche Gogol développé par Romaric Dacosse (UTC GI04).

## Licence

Projet éducatif - UTC 2024-2025
