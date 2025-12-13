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
- [ ] Crawler simple pour fichiers HTML locaux
- [ ] Indexation par mots-clés (inverted index)
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

(À compléter au fur et à mesure du développement)

## Technologies

- **Python 3.10+**
- **FastAPI** - Framework web
- **BeautifulSoup** - Parsing HTML
- **SQLAlchemy** - ORM pour la base de données
- **NLTK** - Traitement du langage naturel

## Auteur

Romaric Dacosse - Étudiant Ingénieur UTC (GI04)
- Spécialisation : IA, Analyse Data, Machine Learning

## Licence

Projet éducatif - UTC 2024-2025
