# Données du projet Gogol

Ce dossier contient les données collectées et indexées par le moteur de recherche Gogol.

## Structure

```
data/
├── raw/          # Données brutes crawlées depuis Wikipedia
└── indexed/      # Base de données indexée
```

## Statistiques du crawling

### Données brutes (raw/)
- **Nombre de pages crawlées**: 1 000 pages
- **Nombre de fichiers JSON**: 1 000
- **Taille totale**: 120 MB
- **Date du crawling**: 25 décembre 2025
- **Période de collecte**: 17h03 - 19h21
- **Lignes de données totales**: ~1 119 311

### Données indexées (indexed/)
- **Base de données**: gogol_index.db
- **Taille**: 109 MB
- **Type**: SQLite database

## Format des données brutes

Chaque fichier JSON dans `raw/` contient:
```json
{
  "url": "URL de la page Wikipedia",
  "title": "Titre de la page",
  "text": "Contenu textuel complet de la page"
}
```

## Source des données

Les données proviennent de Wikipedia (fr.wikipedia.org) et ont été collectées via le crawler implémenté dans le projet.
