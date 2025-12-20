# Gogol - Moteur de Recherche

Un moteur de recherche développé de manière progressive, inspiré de Google.

## Description

Gogol est un projet éducatif visant à comprendre et implémenter les concepts fondamentaux d'un moteur de recherche :
- Crawling de pages web
- Indexation de contenu
- Algorithmes de recherche et ranking
- Interface utilisateur web

## Structure du Projet

```
gogol/
├── src/
│   ├── crawler/          # Module de crawling web
│   ├── indexer/          # Indexation et stockage des documents
│   ├── search_engine/    # Logique de recherche et ranking
│   └── web_interface/    # API et interface web
├── tests/                # Tests unitaires et d'intégration
├── data/
│   ├── raw/             # Données brutes crawlées
│   └── indexed/         # Index de recherche
├── logs/                # Fichiers de logs
└── requirements.txt     # Dépendances Python
```

## Roadmap

### Version 1.0 - Moteur de Recherche Basique
- [x] Crawler simple pour fichiers HTML (101 pages Wikipedia FR crawlées)
- [x] Indexation par mots-clés (inverted index avec TF-IDF)
- [ ] Recherche basique par correspondance de termes
- [ ] Interface web minimaliste

### Version 2.0 - Améliorations
- [ ] Crawling de pages web réelles
- [ ] Ranking TF-IDF
- [ ] Support de recherche multi-mots
- [ ] Amélioration de l'interface

### Version 3.0 - Fonctionnalités Avancées
- [ ] Implémentation de PageRank
- [ ] Recherche full-text avec Elasticsearch
- [ ] Crawling distribué
- [ ] Suggestions de recherche

## Installation

1. Cloner le repository
```bash
git clone <url>
cd gogol
```

2. Créer un environnement virtuel
```bash
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate
```

3. Installer les dépendances
```bash
pip install -r requirements.txt
```

## Utilisation

### 1. Crawling de pages web

Crawler des pages web à partir d'une URL de départ :

```bash
python main.py crawl --url https://fr.wikipedia.org/wiki/France
```

Le crawler :
- Télécharge les pages HTML
- Extrait le contenu textuel et les liens
- Sauvegarde les données en JSON dans `data/raw/`
- Respecte un délai entre les requêtes (politesse)

**Données actuelles** : 101 pages Wikipedia FR (~66 MB)

### 2. Indexation des documents

Créer l'index inversé à partir des documents crawlés :

```bash
# Indexer tous les documents
python main.py index

# Reconstruire l'index complet
python main.py index --force

# Afficher les statistiques de l'index
python main.py index --stats
```

**Résultats de l'indexation** :
- 📄 **101 documents** indexés
- 🔤 **6,368 termes uniques** (vocabulaire français)
- 📊 **426,168 postings** (entrées dans l'index inversé)
- 💾 **48.12 MB** de base de données SQLite
- ⚡ Temps d'indexation : ~8 minutes

#### Comment fonctionne l'indexeur ?

L'indexeur transforme les documents bruts en un index inversé recherchable :

**1. Traitement du texte français**
- Tokenisation avec NLTK (`word_tokenize`)
- Normalisation : lowercase, suppression ponctuation
- Filtrage par longueur (3-50 caractères)
- Suppression de 157 stop words français ("le", "la", "de", etc.)
- Stemming avec FrenchStemmer ("châteaux" → "château")

**2. Construction de l'index inversé**

L'index inversé permet de rechercher rapidement : "Quels documents contiennent ce terme ?"

Structure en 4 tables SQLite :

```
Documents (101 entrées)
├── url, title, doc_hash
├── text_length, term_count
└── indexed_at

Terms (6,368 entrées)
├── term (mot normalisé)
├── document_frequency (nombre de docs contenant ce terme)
└── total_occurrences

Postings (426,168 entrées) - Index inversé
├── term_id → doc_id (relation)
├── term_frequency (fréquence dans le document)
├── tf_idf_score (score de pertinence pré-calculé)
└── positions (JSON des positions pour phrase search)

IndexMetadata
└── Statistiques globales (total_docs, etc.)
```

**3. Scoring TF-IDF**

Chaque terme reçoit un score de pertinence par document :

```
TF (Term Frequency) = occurrences du terme / total de termes dans le doc
IDF (Inverse Document Frequency) = log(total docs / docs contenant le terme)
TF-IDF = TF × IDF
```

Les scores TF-IDF sont **pré-calculés** et stockés dans la base pour des recherches ultra-rapides.

**Exemple de traitement** :

```
Texte original : "Les châteaux de la Loire sont magnifiques"

↓ Tokenisation
["Les", "châteaux", "de", "la", "Loire", "sont", "magnifiques"]

↓ Normalisation + Stop words
["châteaux", "Loire", "magnifiques"]

↓ Stemming
["château", "loir", "magnifiq"]

↓ Stockage dans l'index inversé
"château" → Document #42 (TF=0.05, IDF=2.3, TF-IDF=0.115)
"loir" → Document #42 (TF=0.02, IDF=4.1, TF-IDF=0.082)
"magnifiq" → Document #42 (TF=0.01, IDF=1.8, TF-IDF=0.018)
```

### 3. Recherche (à venir)

```bash
python main.py search --query "châteaux de la Loire"
```

### 4. Interface web (à venir)

```bash
python main.py web
```

Démarrera l'interface web sur http://127.0.0.1:8000

## Technologies

- **Python 3.14** - Langage principal
- **FastAPI** - Framework web (à venir)
- **BeautifulSoup** - Parsing HTML pour le crawler
- **SQLAlchemy** - ORM pour la base de données SQLite
- **NLTK** - Traitement du langage naturel français
  - FrenchStemmer (Snowball)
  - Stop words français (157 mots)
  - Tokenisation `word_tokenize`
- **SQLite** - Base de données de l'index inversé

## Architecture de l'Indexeur

```
Fichiers JSON (data/raw/)
         ↓
    [Indexer]
         ↓
┌────────────────────────┐
│  1. Chargement JSON    │
│  2. Tokenisation NLTK  │
│  3. Normalisation      │
│     - Lowercase        │
│     - Stop words       │
│     - Stemming         │
│  4. Calcul statistiques│
│  5. Stockage SQLite    │
│  6. Calcul TF-IDF      │
└────────────────────────┘
         ↓
Base de données SQLite
(gogol_index.db)
         ↓
Prêt pour recherche!
```

### Fichiers du module indexer

- **`src/indexer/models.py`** - Modèles SQLAlchemy (Document, Term, Posting, IndexMetadata)
- **`src/indexer/indexer.py`** - Classe Indexer avec la logique de traitement
- **`docs/database_schema.puml`** - Diagramme PlantUML de la base de données

### Exemples de requêtes sur l'index

Vous pouvez interroger directement la base de données SQLite pour explorer l'index :

```bash
# Se connecter à la base de données
sqlite3 data/indexed/gogol_index.db
```

**Exemples de requêtes SQL** :

```sql
-- Termes les plus fréquents
SELECT term, total_occurrences, document_frequency
FROM terms
ORDER BY total_occurrences DESC
LIMIT 10;

-- Documents indexés
SELECT title, url, term_count, text_length
FROM documents
ORDER BY term_count DESC
LIMIT 5;

-- Rechercher un terme spécifique
SELECT d.title, d.url, p.tf_idf_score
FROM postings p
JOIN terms t ON p.term_id = t.id
JOIN documents d ON p.doc_id = d.id
WHERE t.term = 'château'
ORDER BY p.tf_idf_score DESC
LIMIT 10;

-- Statistiques globales
SELECT
  (SELECT COUNT(*) FROM documents) as total_docs,
  (SELECT COUNT(*) FROM terms) as total_terms,
  (SELECT COUNT(*) FROM postings) as total_postings;
```

## Auteur

Romaric Dacosse - Étudiant Ingénieur UTC (GI04)
- Spécialisation : IA, Analyse Data, Machine Learning

## Licence

Projet éducatif - UTC 2024-2025
