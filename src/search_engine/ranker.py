"""
Module de ranking pour le moteur de recherche Gogol

Ce module implémente les algorithmes de ranking qui permettent d'ordonner
les résultats de recherche par pertinence. Il utilise principalement la
similarité cosinus (cosine similarity) pour comparer les documents aux requêtes.

⚠️ COHÉRENCE AVEC L'INDEXER :
Ce ranker utilise directement la base de données SQLite créée par l'indexer
et les scores TF-IDF pré-calculés pour optimiser les performances.

Auteur: Romaric Dacosse
Projet: Gogol - Moteur de recherche éducatif
"""

import math
import logging
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.indexer.models import Document, Term, Posting
from src.config import INDEXER_CONFIG


class Ranker:
    """
    Classe responsable du calcul des scores de pertinence et du ranking des documents.
    
    ⚠️ INTÉGRATION AVEC L'INDEXER :
    Le Ranker se connecte à la base de données SQLite créée par l'indexer et utilise
    directement les scores TF-IDF pré-calculés. Ceci permet d'éviter de recalculer
    les scores à chaque recherche et améliore considérablement les performances.
    
    Le ranking est basé sur la similarité cosinus entre le vecteur TF-IDF de la requête
    et les vecteurs TF-IDF des documents indexés.
    
    Concepts clés:
    --------------
    - Vecteur TF-IDF : Représentation numérique d'un texte où chaque dimension
      correspond à un terme, et la valeur est son score TF-IDF
    
    - Cosine Similarity : Mesure l'angle entre deux vecteurs. Plus l'angle est
      petit (cosinus proche de 1), plus les documents sont similaires.
      Formule: cos(θ) = (A · B) / (||A|| × ||B||)
    
    - Scores pré-calculés : L'indexer a déjà calculé les scores TF-IDF pour
      tous les termes de tous les documents. On les réutilise directement.
    
    Attributs:
    ----------
    db_path : Path
        Chemin vers la base de données SQLite
    engine : sqlalchemy.Engine
        Moteur de connexion à la base de données
    session : sqlalchemy.Session
        Session pour les requêtes à la base de données
    document_norms : dict
        Normes (longueurs) des vecteurs de documents, pré-calculées pour optimisation
        Structure: {doc_id: norme}
    term_cache : dict
        Cache des IDs de termes pour éviter les requêtes répétées
        Structure: {terme: term_id}
    logger : logging.Logger
        Logger pour tracer l'activité
    """
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialise le ranker en se connectant à la base de données de l'indexer.
        
        Paramètres:
        -----------
        db_path : Path, optionnel
            Chemin vers la base de données SQLite
            Si None, utilise le chemin de la configuration (INDEXER_CONFIG)
        
        Raises:
        -------
        FileNotFoundError
            Si la base de données n'existe pas (l'indexeur doit être lancé d'abord)
        """
        # Chemin de la base de données
        self.db_path = db_path if db_path is not None else INDEXER_CONFIG["database_path"]
        
        # Configuration du logger
        self.logger = logging.getLogger("Gogol.Ranker")
        self.logger.setLevel(logging.INFO)
        
        # Vérifier que la base de données existe
        if not self.db_path.exists():
            raise FileNotFoundError(
                f"Base de données introuvable: {self.db_path}\n"
                "Vous devez d'abord lancer l'indexeur pour créer l'index."
            )
        
        # Connexion à la base de données
        self._init_database()
        
        # Cache pour les IDs de termes (optimisation)
        # Évite de requêter la DB à chaque fois pour trouver un term_id
        self.term_cache = {}
        
        # Pré-calcul des normes des documents pour optimiser les calculs de similarité
        # La norme d'un vecteur est sa "longueur" : ||v|| = sqrt(v1² + v2² + ... + vn²)
        self.document_norms = self._compute_document_norms()
        
        self.logger.info(f"Ranker initialisé avec {len(self.document_norms)} documents")
    
    def _init_database(self):
        """
        Initialise la connexion à la base de données SQLite.
        
        Utilise SQLAlchemy ORM pour se connecter à la même base de données
        que l'indexer. Ceci garantit la cohérence des données.
        """
        # Créer l'engine SQLite (même configuration que l'indexer)
        self.engine = create_engine(f'sqlite:///{self.db_path}', echo=False)
        
        # Créer une session factory
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
        self.logger.info(f"Connecté à la base de données: {self.db_path}")
    
    def _compute_document_norms(self) -> Dict[int, float]:
        """
        Calcule et retourne les normes de tous les documents.
        
        La norme (ou magnitude) d'un document est la racine carrée de la somme
        des carrés de tous ses scores TF-IDF. Cette valeur représente la "longueur"
        du vecteur document dans l'espace multidimensionnel des termes.
        
        ⚠️ UTILISATION DES SCORES PRÉ-CALCULÉS :
        On utilise directement les scores TF-IDF de la table Posting, qui ont été
        calculés par l'indexer. Ceci évite de recalculer TF-IDF à chaque recherche.
        
        Pourquoi pré-calculer ?
        ------------------------
        Les normes des documents ne changent pas entre les requêtes, donc on les
        calcule une seule fois au démarrage pour accélérer les recherches.
        
        Formule:
        --------
        ||doc|| = sqrt(Σ(tf_idf_i²)) pour tous les termes i du document
        
        Retourne:
        ---------
        dict
            Dictionnaire {doc_id: norme}
        
        Exemple:
        --------
        Document contenant les mots "python" et "java" avec scores TF-IDF:
        - python: 0.8
        - java: 0.6
        
        Norme = sqrt(0.8² + 0.6²) = sqrt(0.64 + 0.36) = sqrt(1.0) = 1.0
        """
        self.logger.info("Calcul des normes des documents...")
        
        document_norms = defaultdict(float)
        
        # Requête SQL pour récupérer tous les postings avec leurs scores TF-IDF
        # On itère sur tous les postings pour calculer la norme de chaque document
        postings = self.session.query(Posting).all()
        
        for posting in postings:
            # Vérifier que le score TF-IDF existe
            if posting.tf_idf_score is not None:
                # Ajouter le carré du score TF-IDF à la somme pour ce document
                # (on appliquera la racine carrée à la fin)
                document_norms[posting.doc_id] += posting.tf_idf_score ** 2
        
        # Application de la racine carrée pour obtenir la norme finale
        # Utilisation de math.sqrt car plus rapide que **0.5
        for doc_id in document_norms:
            document_norms[doc_id] = math.sqrt(document_norms[doc_id])
        
        self.logger.info(f"Normes calculées pour {len(document_norms)} documents")
        
        return dict(document_norms)
    
    def _get_term_id(self, term: str) -> Optional[int]:
        """
        Récupère l'ID d'un terme depuis la base de données (avec cache).
        
        ⚠️ OPTIMISATION :
        Utilise un cache en mémoire pour éviter de requêter la base de données
        à chaque fois. Lors d'une recherche, on va chercher l'ID de chaque terme
        de la requête, donc le cache améliore significativement les performances.
        
        Paramètres:
        -----------
        term : str
            Terme normalisé (stem) à chercher
        
        Retourne:
        ---------
        int ou None
            ID du terme dans la base de données, ou None si le terme n'existe pas
        
        Note:
        -----
        Si un terme n'existe pas dans la base, cela signifie qu'aucun document
        indexé ne contient ce terme. Dans ce cas, on retourne None et ce terme
        ne contribuera pas au score.
        """
        # Vérifier le cache d'abord
        if term in self.term_cache:
            return self.term_cache[term]
        
        # Requête à la base de données si pas dans le cache
        term_obj = self.session.query(Term).filter_by(term=term).first()
        
        if term_obj:
            # Ajouter au cache pour les prochaines fois
            self.term_cache[term] = term_obj.id
            return term_obj.id
        
        # Terme inexistant dans l'index
        return None
    
    def _compute_query_vector(self, query_terms: List[str]) -> Tuple[Dict[str, float], float]:
        """
        Calcule le vecteur TF-IDF de la requête et sa norme.
        
        Pour une requête, on utilise une version simplifiée du TF-IDF:
        - TF : fréquence du terme dans la requête
        - IDF : on réutilise les scores TF-IDF moyens des documents de l'index
        
        ⚠️ COHÉRENCE AVEC L'INDEXER :
        Les termes de la requête ont déjà été normalisés (stemming) par le
        QueryProcessor, donc ils sont dans le même format que dans l'index.
        
        Paramètres:
        -----------
        query_terms : list
            Liste des termes de la requête (déjà normalisés/stemmés)
        
        Retourne:
        ---------
        tuple
            (vecteur_requête, norme_requête)
            - vecteur_requête : dict {terme: tf_idf_score}
            - norme_requête : float, magnitude du vecteur requête
        
        Exemple:
        --------
        Requête: "python tutorial python"
        Termes normalisés: ["python", "tutori", "python"]
        
        TF pour "python" = 2/3 = 0.667 (apparaît 2 fois sur 3 termes)
        TF pour "tutori" = 1/3 = 0.333 (apparaît 1 fois sur 3 termes)
        """
        # Dictionnaire pour stocker les scores TF-IDF de la requête
        query_vector = {}
        
        # Comptage des occurrences de chaque terme dans la requête (TF)
        term_frequencies = defaultdict(int)
        for term in query_terms:
            term_frequencies[term] += 1
        
        # Calcul du TF-IDF pour chaque terme de la requête
        query_length = len(query_terms)  # Nombre total de termes dans la requête
        
        for term, freq in term_frequencies.items():
            # Récupérer l'ID du terme dans la base de données
            term_id = self._get_term_id(term)
            
            # Si le terme n'existe pas dans l'index, on l'ignore
            if term_id is None:
                self.logger.debug(f"Terme '{term}' absent de l'index, ignoré")
                continue
            
            # TF : fréquence normalisée du terme dans la requête
            tf = freq / query_length if query_length > 0 else 0
            
            # IDF : on utilise la moyenne des scores TF-IDF des documents contenant ce terme
            # C'est une approximation qui fonctionne bien en pratique
            postings = self.session.query(Posting).filter_by(term_id=term_id).all()
            
            if postings:
                # Moyenne des scores TF-IDF pour ce terme
                avg_tfidf = sum(p.tf_idf_score for p in postings if p.tf_idf_score) / len(postings)
                
                # Score de la requête pour ce terme
                query_vector[term] = tf * avg_tfidf
            else:
                # Pas de documents contenant ce terme (ne devrait pas arriver car term_id existe)
                query_vector[term] = 0.0
        
        # Calcul de la norme du vecteur requête
        # ||query|| = sqrt(Σ(tf_idf_i²))
        query_norm = math.sqrt(sum(score ** 2 for score in query_vector.values()))
        
        return query_vector, query_norm
    
    def cosine_similarity(
        self, 
        query_vector: Dict[str, float], 
        query_norm: float,
        doc_id: int
    ) -> float:
        """
        Calcule la similarité cosinus entre une requête et un document.
        
        La similarité cosinus mesure l'angle entre deux vecteurs dans un espace
        multidimensionnel. Elle est indépendante de la longueur des documents,
        ce qui est idéal pour comparer des textes de tailles différentes.
        
        ⚠️ UTILISATION DES SCORES PRÉ-CALCULÉS :
        On récupère directement les scores TF-IDF depuis la table Posting de la
        base de données, évitant ainsi tout recalcul.
        
        Formule mathématique:
        ---------------------
        cos(θ) = (A · B) / (||A|| × ||B||)
        
        Où:
        - A · B est le produit scalaire (dot product) des vecteurs
        - ||A|| et ||B|| sont les normes (magnitudes) des vecteurs
        
        Interprétation des valeurs:
        ---------------------------
        - 1.0  : Documents identiques (angle de 0°)
        - 0.5  : Documents moyennement similaires (angle de 60°)
        - 0.0  : Documents sans termes en commun (angle de 90°)
        - -1.0 : Documents opposés (angle de 180°, rare en recherche textuelle)
        
        Paramètres:
        -----------
        query_vector : dict
            Vecteur TF-IDF de la requête {terme: score}
        query_norm : float
            Norme (magnitude) du vecteur requête
        doc_id : int
            ID du document à comparer
        
        Retourne:
        ---------
        float
            Score de similarité entre 0 et 1 (généralement)
        
        Exemple de calcul:
        ------------------
        Requête: ["python", "tutorial"] avec vecteur [0.8, 0.6]
        Document: contient aussi ["python", "tutorial"] avec vecteur [0.7, 0.5]
        
        Produit scalaire = 0.8*0.7 + 0.6*0.5 = 0.56 + 0.30 = 0.86
        ||query|| = 1.0 (normalisé)
        ||doc|| = sqrt(0.7² + 0.5²) = 0.86
        
        Similarité = 0.86 / (1.0 * 0.86) = 1.0 (très similaires)
        """
        # Vérification: le document doit exister dans nos normes pré-calculées
        if doc_id not in self.document_norms:
            return 0.0
        
        # Récupération de la norme du document (pré-calculée)
        doc_norm = self.document_norms[doc_id]
        
        # Cas particulier: si l'une des normes est nulle, la similarité est 0
        # (évite une division par zéro)
        if query_norm == 0 or doc_norm == 0:
            return 0.0
        
        # Calcul du produit scalaire (dot product) entre requête et document
        # On ne calcule que pour les termes communs (optimisation importante!)
        dot_product = 0.0
        
        for term, query_score in query_vector.items():
            # Récupérer l'ID du terme
            term_id = self._get_term_id(term)
            
            if term_id is None:
                continue
            
            # Récupérer le posting pour ce terme et ce document
            posting = self.session.query(Posting).filter_by(
                term_id=term_id,
                doc_id=doc_id
            ).first()
            
            if posting and posting.tf_idf_score is not None:
                # Contribution au produit scalaire
                dot_product += query_score * posting.tf_idf_score
        
        # Calcul final de la similarité cosinus
        # cos(θ) = produit_scalaire / (norme_query × norme_doc)
        similarity = dot_product / (query_norm * doc_norm)
        
        return similarity
    
    def rank(
        self, 
        query_terms: List[str], 
        top_k: int = 10
    ) -> List[Tuple[int, str, str, float]]:
        """
        Classe les documents par pertinence pour une requête donnée.
        
        ⚠️ RETOUR ENRICHI :
        Contrairement au ranker basique qui retournait seulement (doc_id, score),
        cette version retourne aussi le titre et l'URL du document pour faciliter
        l'affichage des résultats.
        
        Algorithme:
        -----------
        1. Construire le vecteur TF-IDF de la requête
        2. Identifier les documents candidats (contenant au moins un terme)
        3. Calculer la similarité cosinus avec tous les candidats
        4. Trier les documents par score décroissant
        5. Récupérer les métadonnées (titre, URL) depuis la DB
        6. Retourner les top_k meilleurs résultats
        
        Optimisations:
        --------------
        - On ne calcule la similarité que pour les documents contenant au moins
          un terme de la requête (les autres auront forcément un score de 0)
        - Les normes des documents sont pré-calculées
        - Les scores TF-IDF sont pré-calculés par l'indexer
        - Cache des IDs de termes pour éviter les requêtes répétées
        
        Paramètres:
        -----------
        query_terms : list
            Liste des termes de la requête (normalisés par QueryProcessor)
        top_k : int, optionnel (défaut: 10)
            Nombre de résultats à retourner
        
        Retourne:
        ---------
        list
            Liste de tuples (doc_id, title, url, score) triés par score décroissant
            Limité aux top_k meilleurs résultats
        
        Exemple:
        --------
        >>> ranker.rank(["python", "tutori"], top_k=5)
        [
            (123, "Python Tutorial", "https://...", 0.95),  # Très pertinent
            (456, "Learn Python", "https://...", 0.87),     # Très pertinent
            (789, "Python Basics", "https://...", 0.72),    # Moyennement pertinent
            (12, "Intro to Python", "https://...", 0.45),   # Peu pertinent
            (345, "Python Guide", "https://...", 0.23)      # Peu pertinent
        ]
        """
        self.logger.info(f"Recherche pour: {query_terms}")
        
        # Étape 1: Construction du vecteur requête et calcul de sa norme
        query_vector, query_norm = self._compute_query_vector(query_terms)
        
        # Si la requête est vide ou ne contient aucun terme connu, retourner liste vide
        if not query_vector or query_norm == 0:
            self.logger.warning("Requête vide ou aucun terme dans l'index")
            return []
        
        self.logger.debug(f"Vecteur requête: {query_vector}")
        
        # Étape 2: Identification des documents candidats
        # (documents contenant au moins un terme de la requête)
        candidate_docs = set()
        
        for term in query_vector.keys():
            term_id = self._get_term_id(term)
            
            if term_id is None:
                continue
            
            # Récupérer tous les documents contenant ce terme
            postings = self.session.query(Posting).filter_by(term_id=term_id).all()
            
            for posting in postings:
                candidate_docs.add(posting.doc_id)
        
        # Si aucun document candidat, retourner liste vide
        if not candidate_docs:
            self.logger.info("Aucun document trouvé pour cette requête")
            return []
        
        self.logger.info(f"{len(candidate_docs)} documents candidats trouvés")
        
        # Étape 3: Calcul des scores de similarité pour tous les candidats
        doc_scores = []
        for doc_id in candidate_docs:
            # Calcul de la similarité cosinus entre requête et document
            similarity = self.cosine_similarity(query_vector, query_norm, doc_id)
            
            # Ajout du résultat uniquement si le score est supérieur à 0
            # (optimisation: évite de stocker des résultats non pertinents)
            if similarity > 0:
                doc_scores.append((doc_id, similarity))
        
        # Étape 4: Tri des résultats par score décroissant
        # key=lambda x: x[1] signifie "trier selon le 2ème élément du tuple (le score)"
        # reverse=True donne l'ordre décroissant (meilleurs scores en premier)
        doc_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Étape 5: Récupération des métadonnées des documents (titre, URL)
        # et limitation aux top_k résultats
        results = []
        for doc_id, score in doc_scores[:top_k]:
            # Requête pour récupérer les infos du document
            doc = self.session.query(Document).filter_by(id=doc_id).first()
            
            if doc:
                results.append((doc_id, doc.title, doc.url, score))
            else:
                # Ne devrait pas arriver, mais par sécurité
                self.logger.warning(f"Document {doc_id} introuvable dans la base")
        
        self.logger.info(f"{len(results)} résultats retournés")
        
        return results
    
    def get_index_stats(self) -> dict:
        """
        Retourne des statistiques sur l'index.
        
        Utile pour:
        -----------
        - Monitoring de l'état de l'index
        - Debugging
        - Interface d'administration
        
        Retourne:
        ---------
        dict
            Statistiques de l'index (nombre de documents, termes, etc.)
        """
        stats = {
            'total_documents': self.session.query(Document).count(),
            'total_terms': self.session.query(Term).count(),
            'total_postings': self.session.query(Posting).count(),
            'db_path': str(self.db_path),
            'db_size_mb': self.db_path.stat().st_size / (1024 * 1024) if self.db_path.exists() else 0
        }
        
        return stats
    
    def __del__(self):
        """
        Destructeur: ferme proprement la session de base de données.
        """
        if hasattr(self, 'session'):
            self.session.close()


# ============================================================================
# Fonctions utilitaires pour le ranking
# ============================================================================

def print_ranked_results(
    ranked_results: List[Tuple[int, str, str, float]],
    max_display: int = 10
) -> None:
    """
    Affiche les résultats de ranking de manière lisible.
    
    Utile pour le debugging et la visualisation des résultats.
    
    Paramètres:
    -----------
    ranked_results : list
        Liste de tuples (doc_id, title, url, score)
    max_display : int, optionnel (défaut: 10)
        Nombre maximum de résultats à afficher
    
    Exemple d'affichage:
    --------------------
    Résultats de recherche (5 documents trouvés):
    
    1. Python Tutorial - Introduction to Python
       https://example.com/python-tutorial
       Score: 0.9523
       ████████████████████░ 95.23%
    
    2. Learn Python Programming
       https://example.com/learn-python
       Score: 0.8745
       █████████████████░░░░ 87.45%
    """
    print(f"\nRésultats de recherche ({len(ranked_results)} documents trouvés):\n")
    
    for i, (doc_id, title, url, score) in enumerate(ranked_results[:max_display], 1):
        # Barre de progression visuelle
        bar_length = 20
        filled_length = int(bar_length * score)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        
        # Tronquer le titre s'il est trop long
        display_title = title[:60] + "..." if len(title) > 60 else title
        
        print(f"{i}. {display_title}")
        print(f"   {url}")
        print(f"   Score: {score:.4f}")
        print(f"   {bar} {score*100:.2f}%\n")


# ============================================================================
# Exemple d'utilisation
# ============================================================================

if __name__ == "__main__":
    """
    Exemple d'utilisation du Ranker avec la base de données de l'indexer.
    
    Cet exemple montre comment:
    1. Initialiser le Ranker (connexion à la DB)
    2. Effectuer une recherche
    3. Afficher les résultats
    
    ⚠️ PRÉREQUIS :
    L'indexeur doit avoir été lancé au moins une fois pour créer la base de données.
    """
    
    print("="*70)
    print("GOGOL - Ranker - Test avec la base de données")
    print("="*70)
    
    try:
        # Initialisation du ranker (connexion à la DB)
        print("\n1. Initialisation du Ranker...\n" + "-"*70)
        ranker = Ranker()
        
        # Affichage des statistiques de l'index
        stats = ranker.get_index_stats()
        print(f"Base de données  : {stats['db_path']}")
        print(f"Taille           : {stats['db_size_mb']:.2f} MB")
        print(f"Documents indexés: {stats['total_documents']}")
        print(f"Termes uniques   : {stats['total_terms']}")
        print(f"Postings         : {stats['total_postings']}")
        
        # Affichage des normes des documents (échantillon)
        print(f"\nNormes des documents (échantillon de 5):")
        for doc_id, norm in list(ranker.document_norms.items())[:5]:
            print(f"  Document {doc_id}: {norm:.4f}")
        
        # Exemple de recherche
        # Note: Les termes doivent être normalisés (stemming) comme le fait le QueryProcessor
        print("\n\n2. Exemple de recherche\n" + "-"*70)
        
        # Simulation de termes normalisés (en réalité, ils viendraient du QueryProcessor)
        # Par exemple: "python tutorial" -> ["python", "tutori"] après stemming
        query_terms = ["python", "programm"]
        
        print(f"Requête (termes normalisés): {query_terms}")
        print("\nRecherche en cours...\n")
        
        results = ranker.rank(query_terms, top_k=10)
        
        if results:
            print_ranked_results(results)
        else:
            print("Aucun résultat trouvé.")
            print("\nSuggestions:")
            print("- Vérifiez que des documents ont été indexés")
            print("- Essayez d'autres termes de recherche")
            print("- Les termes doivent être normalisés (stemming)")
        
        print("\n" + "="*70)
        print("Test terminé !")
        print("="*70)
        
    except FileNotFoundError as e:
        print(f"\n❌ ERREUR: {e}")
        print("\nVous devez d'abord lancer l'indexeur:")
        print("  python main.py --index")
        
    except Exception as e:
        print(f"\n❌ ERREUR inattendue: {e}")
        import traceback
        traceback.print_exc()
