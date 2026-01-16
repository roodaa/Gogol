# Script YouTube - Projet Gogol : Moteur de Recherche

**Duree estimee : 15-25 minutes**
**Auteur : Romaric Dacosse - Etudiant Ingenieur UTC (GI04) - Filiere IAD**
**Projet : Gogol - Moteur de Recherche Educatif**

---

## TIMESTAMPS (pour la description YouTube)

```
0:00 - Introduction
1:00 - Apercu de l'interface
2:00 - Chiffres cles du projet
3:00 - Source d'inspiration
4:00 - Stack technique
6:00 - Architecture globale
7:30 - PARTIE 1 : Web Crawling
12:00 - PARTIE 2 : Indexation et NLP
17:00 - PARTIE 3 : Moteur de recherche
20:00 - PARTIE 4 : API et Interface
23:00 - Demonstration en direct
26:00 - Conclusion et contact
```

---

## SLIDE 1 : PAGE TITRE

**[Afficher : GOGOL - Un moteur de recherche educatif - Du crawling au resultat]**

Bonjour a tous et bienvenue sur cette video !

Je suis Romaric Dacosse, etudiant ingenieur a l'UTC en branche Genie Informatique, semestre GI04, specialise dans la filiere IAD - Intelligence Artificielle et Analyse de Donnees.

Aujourd'hui, je vais vous presenter un projet personnel qui me tient particulierement a coeur : **Gogol**, un moteur de recherche que j'ai developpe entierement de A a Z.

L'objectif de ce projet etait de comprendre comment fonctionne un moteur de recherche comme Google. Comment fait-il pour retrouver des informations pertinentes parmi des milliards de pages web en seulement quelques millisecondes ?

Dans cette video, je vais vous montrer tout le parcours : du crawling des pages web jusqu'a l'affichage des resultats. Allez, c'est parti !

---

## SLIDE 2 : APERCU DE L'INTERFACE

**[Afficher : Screenshot de Gogol Search avec la recherche "Victor Hugo"]**

Avant de plonger dans les details techniques, laissez-moi vous montrer le resultat final.

Voici l'interface de Gogol Search. On a une sidebar a gauche avec :
- Le **statut de l'API** qui indique "En ligne"
- L'**index** qui est pret
- Les **statistiques** en temps reel : 1000 documents indexes, pres de 99 000 termes uniques, plus d'un million de postings, et une base de donnees de 108 Mo

Au centre, on a notre barre de recherche. Ici j'ai tape "Victor Hugo" et on obtient 10 resultats.

Ce qui est interessant, c'est qu'on voit les **termes traites** : "victor" et "hugo". Ce sont les termes apres le traitement NLP dont on va parler.

Et pour chaque resultat, on a un **pourcentage de coherence**. Par exemple, la page sur la "Litterature francaise du XIXe siecle" a un score de 21.8%. Ce score est calcule grace a l'algorithme TF-IDF et la similarite cosinus.

---

## SLIDE 3 : CHIFFRES CLES DU PROJET

**[Afficher : Les 6 chiffres cles]**

Voici les chiffres cles de ce projet :

- **1000 pages Wikipedia** crawlees depuis le site francais
- **119 Mo** de donnees textuelles brutes
- **98 935 termes uniques** dans notre vocabulaire
- Plus de **1 million de postings** dans l'index inverse - c'est-a-dire 1 million de relations entre les termes et les documents
- Une **base de donnees SQLite de 110 Mo**
- Et un **temps de reponse moyen inferieur a 10 millisecondes**

Ces chiffres montrent qu'on a un moteur de recherche fonctionnel et performant, meme si c'est bien sur a une echelle beaucoup plus petite que Google !

---

## SLIDE 4 : SOURCE D'INSPIRATION

**[Afficher : Video YouTube de V2F "Une semaine pour recoder Google"]**

Alors, pourquoi ce projet ?

C'est en retombant sur cette video de V2F, "Une semaine pour recoder Google", que j'ai eu envie de me lancer dans ce defi.

Cette video m'a fait realiser que meme si Google est un systeme extremement complexe a l'echelle mondiale, les concepts fondamentaux d'un moteur de recherche sont accessibles et comprehensibles.

J'ai donc decide de creer ma propre version, en me concentrant sur les aspects que je voulais approfondir : le traitement du langage naturel, les algorithmes de ranking, et l'architecture logicielle.

---

## SLIDE 5 : STACK TECHNIQUE - BACKEND

**[Afficher : Logos SQLAlchemy, FastAPI, SQLite, NLTK, BeautifulSoup, Python]**

Parlons maintenant des technologies utilisees.

Pour le **backend**, j'ai choisi :

- **Python** comme langage principal - ideal pour le prototypage rapide et le traitement de donnees
- **FastAPI** pour l'API REST - un framework moderne, rapide, avec validation automatique des donnees
- **SQLAlchemy** comme ORM pour interagir avec la base de donnees de maniere elegante
- **SQLite** pour stocker l'index - simple, sans serveur, parfait pour ce type de projet
- **NLTK** pour le traitement du langage naturel francais - tokenisation, stemming, stop words
- **BeautifulSoup** pour parser le HTML des pages web crawlees

---

## SLIDE 6 : STACK TECHNIQUE - FRONTEND

**[Afficher : Logos Angular et TypeScript]**

Pour le **frontend**, j'ai opte pour :

- **Angular 21** - la derniere version du framework avec les standalone components et les Signals pour la reactivite
- **TypeScript** - pour un code type et maintenable

L'interface est volontairement simple et epuree, inspiree de Google, avec une sidebar pour les statistiques et une zone centrale pour la recherche et les resultats.

---

## SLIDE 7 : ARCHITECTURE GLOBALE

**[Afficher : Schema d'architecture avec les 4 modules]**

Voici l'architecture globale du projet. On a 4 modules principaux :

1. **Le Crawler** - represente par l'araignee - qui telecharge les pages web en utilisant une approche BFS, Breadth-First Search, c'est-a-dire un parcours en largeur

2. **L'Indexer** - qui construit l'index inverse avec du traitement NLP

3. **Le Search Engine** - qui traite les requetes utilisateur et calcule la pertinence des documents

4. **L'API et l'Interface** - FastAPI pour le backend et Angular pour le frontend

A gauche, vous voyez la structure du projet avec les differents dossiers : `src/` contient les modules, `data/raw/` les donnees brutes crawlees, `data/indexed/` l'index de recherche.

Chaque module a une responsabilite unique. C'est le principe de separation des responsabilites, tres important en genie logiciel.

---

## SLIDE 8 : TITRE PARTIE 1 - WEB CRAWLING

**[Afficher : "1. WEB CRAWLING" avec image de toile d'araignee]**

Commencons par la premiere partie : le Web Crawling.

Le crawler, c'est notre "araignee web". Son role est de parcourir internet et de telecharger des pages pour les indexer ensuite.

---

## SLIDE 9 : CODE DU CRAWLER

**[Afficher : Code Python avec visited_urls et urls_to_visit]**

Voici le coeur du crawler. On utilise deux structures de donnees :

```python
# URLs deja visitees (pour eviter de crawler 2 fois la meme page)
self.visited_urls: Set[str] = set()

# URLs en attente de visite (file FIFO)
self.urls_to_visit: List[str] = []
```

Le **Set** `visited_urls` permet de tracker les URLs deja visitees. Grace a la structure de set, la verification est en O(1), donc tres rapide meme avec des milliers d'URLs.

La **List** `urls_to_visit` est notre file d'attente. On utilise une approche FIFO - First In, First Out - ce qui correspond a un parcours BFS.

L'algorithme est simple :
1. On prend la premiere URL de la file
2. On la telecharge
3. On extrait le contenu et les liens
4. On ajoute les nouveaux liens a la file
5. On recommence jusqu'a atteindre la limite de pages

---

## SLIDE 10 : EXTRACTION DES DONNEES

**[Afficher : Page Wikipedia France avec annotations url, titre, texte]**

Quand on crawle une page, on extrait trois informations principales :

- L'**URL** - ici `https://fr.wikipedia.org/wiki/France`
- Le **titre** de la page - "France"
- Le **texte** du contenu principal

Pour Wikipedia, j'ai implemente une extraction intelligente qui ne garde que le contenu principal de l'article, sans les menus de navigation, la sidebar, les references, etc. Cela permet d'avoir un contenu propre et pertinent pour l'indexation.

---

## SLIDE 11 : RESULTAT DU CRAWLING

**[Afficher : VSCode avec fichiers JSON et contenu d'un fichier]**

Voici le resultat du crawling. Chaque page est sauvegardee dans un fichier JSON separe.

Le nom du fichier est un hash MD5 de l'URL, ce qui garantit l'unicite.

Dans le fichier, on retrouve :
- L'URL de la page
- Le titre
- Le texte extrait
- La liste des liens trouves sur la page

Par exemple, ici on a la page "Fatu Huku" - une petite ile inhabitee de l'archipel des Marquises. On voit le texte de l'article et tous les liens vers d'autres pages Wikipedia.

A la fin du crawling, on a 1000 fichiers JSON dans le dossier `data/raw/`, representant 119 Mo de donnees textuelles.

---

## SLIDE 12 : TITRE PARTIE 2 - INDEXATION ET NLP

**[Afficher : "PARTIE 2 : INDEXATION ET TRAITEMENT NLP"]**

Passons maintenant a la partie la plus interessante techniquement : l'indexation et le traitement du langage naturel.

C'est vraiment le coeur du moteur de recherche.

---

## SLIDE 13 : PIPELINE DE TRAITEMENT NLP

**[Afficher : Pipeline Tokenisation -> Normalisation -> Stop Words -> Stemming]**

Le traitement NLP suit un pipeline en 4 etapes. Prenons l'exemple de la phrase : "Les chateaux de la Loire sont magnifiques"

**Etape 1 - Tokenisation** : On decoupe le texte en mots.
```
["Les", "chateaux", "de", "la", "Loire", "sont", "magnifiques"]
```

**Etape 2 - Normalisation** : On passe tout en minuscules.
```
["les", "chateaux", "de", "la", "loire", "sont", "magnifiques"]
```

**Etape 3 - Stop Words** : On retire les mots vides qui n'apportent pas de sens - "les", "de", "la", "sont".
```
["chateaux", "loire", "magnifiques"]
```

**Etape 4 - Stemming** : On reduit chaque mot a sa racine. "chateaux" devient "chateau", "magnifiques" devient "magnifiq".
```
["chateau", "loir", "magnifiq"]
```

Ce pipeline est applique a chaque document lors de l'indexation, et aussi a chaque requete lors de la recherche. C'est crucial que les deux traitements soient identiques pour que les termes correspondent !

---

## SLIDE 14 : STRUCTURE DE LA BASE DE DONNEES

**[Afficher : Schema de base de donnees avec 4 tables]**

Voici le schema de notre base de donnees SQLite. On a 4 tables :

**Documents** - 1000 entrees
- `id`, `url`, `title`, `doc_hash`
- `text_length`, `term_count`
- `indexed_at`

**Terms** - 98 935 entrees
- `term` - le mot normalise
- `document_frequency` - dans combien de documents il apparait
- `total_occurrences`

**Postings** - Plus d'un million d'entrees - C'est l'index inverse !
- `term_id` et `doc_id` - la relation entre terme et document
- `term_frequency` - combien de fois le terme apparait dans ce document
- `tf_idf_score` - le score de pertinence pre-calcule
- `positions` - les positions du terme dans le document

**IndexMetadata** - Les statistiques globales de l'index

La table **Postings** est vraiment le coeur du systeme. Elle permet de repondre instantanement a la question : "Quels documents contiennent ce terme ?"

---

## SLIDE 15 : INDEX INVERSE ET TF-IDF

**[Afficher : Formules TF-IDF]**

Parlons maintenant de l'algorithme TF-IDF. C'est un algorithme fondamental en recherche d'information.

**TF - Term Frequency** = occurrences du terme / total de termes dans le document

C'est la frequence du terme dans un document specifique. Plus un mot apparait souvent dans un document, plus il est probablement important pour ce document.

**IDF - Inverse Document Frequency** = log(total docs / docs contenant le terme)

C'est l'inverse de la frequence documentaire. Un mot qui apparait dans beaucoup de documents, comme "le" ou "est", aura un IDF faible. Un mot rare aura un IDF eleve.

**TF-IDF** = TF x IDF

Le produit des deux donne un score eleve aux mots qui sont a la fois frequents dans un document specifique ET rares dans le corpus global. C'est exactement ce qu'on veut pour mesurer la pertinence !

Les scores TF-IDF sont **pre-calcules** lors de l'indexation et stockes dans la base de donnees. Cela rend les recherches ultra-rapides car on n'a pas a les recalculer a chaque requete.

---

## SLIDE 16 : TITRE PARTIE 3 - MOTEUR DE RECHERCHE

**[Afficher : "PARTIE 3 : Moteur de recherche"]**

Maintenant qu'on a notre index, voyons comment fonctionne le moteur de recherche lui-meme.

---

## SLIDE 17 : TRAITEMENT DES REQUETES - EXEMPLES

**[Afficher : Terminal avec exemples de requetes et termes normalises]**

Voici des exemples de traitement de requetes :

```
Requete : Comment apprendre le Python rapidement ?
Termes  : ['comment', 'apprendr', 'python', 'rapid']
```

On voit que "le" a ete supprime (stop word), et "rapidement" a ete reduit a "rapid".

```
Requete : Tutoriel sur l'API REST avec FastAPI
Termes  : ['tutoriel', 'rest', 'fastap']
```

"sur", "l'" et "avec" sont des stop words.

```
Requete : Machine Learning et Intelligence Artificielle
Termes  : ['machin', 'learning', 'intelligent', 'artificiel']
```

```
Requete : Chercher des informations sur la recherche d'information
Termes  : ['cherch', 'inform', 'recherch']
```

Ce dernier exemple est interessant : "chercher" et "recherche" sont reduits a des formes similaires grace au stemming !

---

## SLIDE 18 : TRAITEMENT DES REQUETES - CODE

**[Afficher : Code Python pour le calcul des normes + requete SQL]**

Voici le code du Ranker qui calcule les scores de pertinence.

En haut, on a le calcul des **normes des documents**. La norme d'un document, c'est la longueur de son vecteur TF-IDF :

```python
document_norms = defaultdict(float)

for posting in postings:
    if posting.tf_idf_score is not None:
        # Ajouter le carre du score TF-IDF
        document_norms[posting.doc_id] += posting.tf_idf_score ** 2

# Application de la racine carree
for doc_id in document_norms:
    document_norms[doc_id] = math.sqrt(document_norms[doc_id])
```

Ces normes sont pre-calculees au demarrage pour optimiser les recherches.

En bas, on a une requete SQL equivalente qui montre comment on recupere les resultats :

```sql
SELECT d.title, d.url, SUM(p.tf_idf_score) as score
FROM postings p
JOIN documents d ON p.doc_id = d.id
WHERE p.term_id IN (select id from terms where term IN ('chateau', 'loir'))
GROUP BY d.id
ORDER BY score DESC
```

On selectionne les documents qui contiennent au moins un des termes de la requete, on somme les scores TF-IDF, et on trie par score decroissant.

En realite, j'utilise la **similarite cosinus** qui est plus sophistiquee, mais l'idee est la meme.

---

## SLIDE 19 : TITRE PARTIE 4 - API ET INTERFACE

**[Afficher : "PARTIE 4 : API et Interface"]**

Derniere partie : l'API et l'interface utilisateur.

---

## SLIDE 20 : API FASTAPI

**[Afficher : Code de l'endpoint /api/search]**

Voici le code de l'endpoint de recherche avec FastAPI :

```python
@app.get("/api/search", response_model=SearchResponse)
async def search(
    q: str = Query(..., description="Requete de recherche", min_length=1),
    limit: int = Query(10, ge=1, le=100, description="Nombre maximum de resultats")
):
```

FastAPI genere automatiquement la documentation Swagger et valide les parametres.

Le processus est simple :
1. On verifie que le moteur est initialise
2. On traite la requete avec le QueryProcessor
3. On recupere les resultats avec le Ranker
4. On formate et retourne la reponse

L'API expose trois endpoints :
- `GET /api/search?q=...` pour la recherche
- `GET /api/stats` pour les statistiques
- `GET /api/health` pour verifier le statut

La documentation Swagger est accessible sur `/api/docs` - tres pratique pour tester l'API !

---

## SLIDE 21 : MERCI ET CONTACT

**[Afficher : Slide de conclusion avec coordonnees]**

Et voila, nous avons fait le tour de Gogol !

Pour resumer ce que j'ai appris avec ce projet :
- Les **algorithmes de recherche d'information** - TF-IDF, similarite cosinus, index inverse
- Le **traitement du langage naturel** - tokenisation, stemming, stop words
- L'**architecture logicielle** - separation des responsabilites, API REST
- Les **technologies modernes** - FastAPI, Angular, SQLAlchemy

C'est un projet qui m'a permis de mettre en pratique beaucoup de concepts vus en cours, notamment en IAD, mais aussi d'aller plus loin par curiosite personnelle.

---

## SECTION BONUS : DEMONSTRATION EN DIRECT

**[Passer a l'ecran de demonstration]**

Maintenant, passons a la demonstration en direct !

### Lancement de l'API

```bash
python run_api.py
```

On voit que l'API demarre, charge les 1000 documents, et pre-calcule les normes pour optimiser les recherches futures.

### Lancement du frontend

```bash
cd frontend
npm start
```

L'interface Angular est maintenant accessible sur `localhost:4200`.

### Tests de recherche

Faisons quelques recherches :

1. **"Victor Hugo"** - On retrouve des pages sur la litterature francaise du XIXe siecle

2. **"Revolution francaise"** - Des pages sur l'histoire de France

3. **"Intelligence artificielle"** - Des pages sur l'IA et le machine learning

Observez comment les termes sont traites et comment les resultats sont classes par pertinence.

---

## CONCLUSION FINALE

Merci d'avoir regarde cette video jusqu'au bout !

Si vous avez des questions ou des suggestions, n'hesitez pas a les poser en commentaire.

Le code source est disponible sur mon GitHub : **github.com/roodaa/Gogol**

Vous pouvez aussi me contacter :
- Par email : **romaric.dacosse@etu.utc.fr**
- Sur LinkedIn : **linkedin.com/in/romaric-dacosse**

A bientot pour de nouveaux projets !

---

## NOTES POUR LE MONTAGE

### Duree par slide (estimation)

| Slide | Contenu | Duree |
|-------|---------|-------|
| 1 | Titre + intro | 1m00 |
| 2 | Interface | 1m00 |
| 3 | Chiffres cles | 1m00 |
| 4 | Inspiration | 0m45 |
| 5-6 | Stack technique | 1m30 |
| 7 | Architecture | 1m30 |
| 8-11 | Crawling | 4m30 |
| 12-15 | Indexation/NLP | 5m00 |
| 16-18 | Moteur recherche | 3m00 |
| 19-20 | API/Interface | 2m30 |
| 21 | Conclusion | 1m00 |
| Demo | Demo live | 3m00 |
| **Total** | | **~26 min** |

### Conseils de montage

- **Musique** : Lo-fi ou electronique douce pendant les explications
- **Transitions** : Fondus enchaines entre les slides
- **Code** : Zoom sur les parties importantes, animations de surlignage
- **Demo** : Agrandir la taille de police du terminal (14pt minimum)

### Miniature YouTube (suggestion)

- Texte : "J'AI CODE MON PROPRE GOOGLE"
- Image : Screenshot de l'interface Gogol + logo Python/Angular
- Couleurs : Gradient violet (reprendre le design de l'app)
