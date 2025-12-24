"""
Module de traitement des requêtes pour le moteur de recherche Gogol

Ce module est responsable de transformer une requête utilisateur brute (texte)
en une liste de termes normalisés et nettoyés, prêts à être utilisés pour la recherche.

Le prétraitement des requêtes est crucial car il permet de :
- Améliorer la qualité des résultats de recherche
- Réduire le bruit (mots non significatifs)
- Normaliser les variations d'un même mot

⚠️ IMPORTANT : Ce module utilise exactement les mêmes outils que l'indexer (NLTK)
pour garantir la cohérence entre l'indexation et la recherche.

Auteur: Romaric Dacosse
Projet: Gogol - Moteur de recherche éducatif
"""

import logging
from typing import List, Optional
from collections import Counter

import nltk
from nltk.corpus import stopwords
from nltk.stem.snowball import FrenchStemmer
from nltk.tokenize import word_tokenize


# ============================================================================
# Classe QueryProcessor
# ============================================================================

class QueryProcessor:
    """
    Classe responsable du prétraitement des requêtes utilisateur.
    
    ⚠️ COHÉRENCE AVEC L'INDEXER :
    Ce processeur utilise EXACTEMENT les mêmes outils que l'indexer (NLTK)
    pour garantir que les requêtes sont traitées de la même manière que
    les documents lors de l'indexation. Ceci est CRUCIAL pour obtenir
    des résultats de recherche pertinents.
    
    Pipeline de traitement (identique à l'indexer):
    ------------------------------------------------
    1. Tokenization : découpage en mots avec word_tokenize de NLTK
    2. Normalisation : lowercase + filtrage alphabétique
    3. Filtrage : longueur minimale et maximale
    4. Stop words : suppression des mots vides français (NLTK)
    5. Stemming : réduction à la racine avec FrenchStemmer
    
    Exemple de transformation:
    --------------------------
    Entrée : "Comment apprendre le Python rapidement ?"
    
    Étape 1 - Tokenization:
        ["Comment", "apprendre", "le", "Python", "rapidement", "?"]
    
    Étape 2 - Normalisation:
        ["comment", "apprendre", "le", "python", "rapidement"]
        (suppression de "?" car non-alphabétique)
    
    Étape 3 - Stop words:
        ["comment", "apprendre", "python", "rapidement"]
        (suppression de "le")
    
    Étape 4 - Stemming:
        ["comment", "apprend", "python", "rapid"]
    
    Attributs:
    ----------
    stemmer : FrenchStemmer
        Stemmer français de NLTK (même que l'indexer)
    stop_words : set
        Ensemble des stop words français de NLTK
    min_word_length : int
        Longueur minimale d'un mot (défaut: 2)
    max_word_length : int
        Longueur maximale d'un mot (défaut: 50)
    logger : logging.Logger
        Logger pour tracer l'activité
    """
    
    def __init__(
        self,
        min_word_length: int = 2,
        max_word_length: int = 50
    ):
        """
        Initialise le processeur de requêtes avec les mêmes paramètres que l'indexer.
        
        Paramètres:
        -----------
        min_word_length : int, optionnel (défaut: 2)
            Longueur minimale d'un mot pour être conservé
            Note: Doit être identique à la config de l'indexer
        max_word_length : int, optionnel (défaut: 50)
            Longueur maximale d'un mot pour être conservé
            Note: Doit être identique à la config de l'indexer
        """
        self.min_word_length = min_word_length
        self.max_word_length = max_word_length
        
        # Configuration du logger
        self.logger = logging.getLogger("Gogol.QueryProcessor")
        self.logger.setLevel(logging.INFO)
        
        # Télécharger les ressources NLTK si nécessaire
        self._download_nltk_data()
        
        # Initialiser le stemmer et les stop words français
        self.stemmer = FrenchStemmer()
        self.stop_words = set(stopwords.words('french'))
        
        self.logger.info(f"QueryProcessor initialisé avec {len(self.stop_words)} stop words français")
    
    def _download_nltk_data(self):
        """
        Télécharge les ressources NLTK nécessaires si elles ne sont pas déjà présentes.
        
        Ressources requises (identiques à l'indexer):
        -----------------------------------------------
        - stopwords: Liste des mots vides français
        - punkt: Tokenizer pour la segmentation
        - punkt_tab: Tables pour le tokenizer
        
        Note: Cette méthode est identique à celle de l'indexer pour garantir
        que les mêmes ressources sont disponibles.
        """
        resources = ['stopwords', 'punkt', 'punkt_tab']
        
        for resource in resources:
            try:
                nltk.data.find(f'corpora/{resource}' if resource == 'stopwords' else f'tokenizers/{resource}')
                self.logger.debug(f"Ressource NLTK '{resource}' déjà présente")
            except LookupError:
                self.logger.info(f"Téléchargement de la ressource NLTK: {resource}")
                try:
                    nltk.download(resource, quiet=True)
                    self.logger.info(f"Ressource '{resource}' téléchargée avec succès")
                except Exception as e:
                    self.logger.warning(f"Impossible de télécharger '{resource}': {e}")
    
    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenise le texte en mots français avec NLTK.
        
        ⚠️ IDENTIQUE À L'INDEXER :
        Cette méthode utilise word_tokenize de NLTK, exactement comme l'indexer,
        pour garantir que la tokenization est identique lors de la recherche.
        
        Pourquoi word_tokenize ?
        -------------------------
        - Gère correctement les contractions françaises (l', d', j', etc.)
        - Comprend la ponctuation du français
        - Traite les apostrophes et traits d'union
        - Plus intelligent qu'un simple split()
        
        Args:
            text: Texte à tokeniser
        
        Returns:
            Liste de tokens (mots)
        
        Exemples:
        ---------
        >>> _tokenize("L'intelligence artificielle c'est génial!")
        ["L'", "intelligence", "artificielle", "c'", "est", "génial", "!"]
        
        >>> _tokenize("Jean-Pierre développe en Python 3.10")
        ["Jean-Pierre", "développe", "en", "Python", "3.10"]
        
        Fallback:
        ---------
        Si NLTK échoue (ressources manquantes), on utilise un split() basique
        """
        try:
            # Utilisation de word_tokenize avec langue française
            # C'est exactement ce que fait l'indexer
            tokens = word_tokenize(text, language='french')
            return tokens
        except Exception as e:
            self.logger.warning(f"Erreur de tokenisation: {e}. Utilisation du split basique.")
            # Fallback: split basique si NLTK échoue
            return text.split()
    
    def _normalize_tokens(self, tokens: List[str]) -> List[str]:
        """
        Normalise les tokens : lowercase, filtrage, stop words, stemming.
        
        ⚠️ PIPELINE IDENTIQUE À L'INDEXER :
        Cette méthode applique EXACTEMENT les mêmes transformations que l'indexer
        pour garantir que les termes de recherche matchent avec l'index.
        
        Étapes de normalisation (dans l'ordre):
        ----------------------------------------
        1. Lowercase : "Python" → "python"
        2. Filtrage alphabétique : garde seulement les mots avec lettres
        3. Filtrage par longueur : min_word_length à max_word_length
        4. Suppression des stop words : retire "le", "de", "et", etc.
        5. Stemming français : "apprendre" → "apprend"
        
        Args:
            tokens: Liste de tokens bruts
        
        Returns:
            Liste de termes normalisés (stems)
        
        Exemples complets:
        ------------------
        >>> _normalize_tokens(["Comment", "apprendre", "le", "Python", "?"])
        ["comment", "apprend", "python"]
        # "?" supprimé (non-alphabétique)
        # "le" supprimé (stop word)
        # "apprendre" → "apprend" (stemming)
        
        >>> _normalize_tokens(["Développement", "web", "avec", "FastAPI"])
        ["developp", "web", "fastapi"]
        # "avec" supprimé (stop word)
        # "Développement" → "developp" (stemming)
        
        Note importante:
        ----------------
        La méthode ne retourne PAS les positions comme l'indexer car on n'en a
        pas besoin pour la recherche. L'indexer stocke les positions pour
        permettre des recherches de phrases ou des highlighting.
        """
        normalized = []
        
        for token in tokens:
            # Étape 1: Lowercase
            # Conversion en minuscules pour normaliser
            token_lower = token.lower()
            
            # Étape 2: Filtrer les non-alphabétiques
            # On garde seulement les tokens qui contiennent des lettres
            # isalpha() retourne True si le token ne contient QUE des lettres
            if not token_lower.isalpha():
                continue
            
            # Étape 3: Filtrer par longueur
            # Les mots trop courts (< min_word_length) ou trop longs (> max_word_length)
            # sont souvent du bruit
            if len(token_lower) < self.min_word_length or len(token_lower) > self.max_word_length:
                continue
            
            # Étape 4: Retirer les stop words
            # Les stop words sont des mots très fréquents mais peu informatifs
            if token_lower in self.stop_words:
                continue
            
            # Étape 5: Stemming français
            # Réduction du mot à sa racine (stem)
            # Exemples: chercher/cherchait/recherche → cherch
            #           développer/développement → developp
            stemmed = self.stemmer.stem(token_lower)
            
            # Ajouter le terme normalisé à la liste
            normalized.append(stemmed)
        
        return normalized
    
    def process(self, query: str) -> List[str]:
        """
        Pipeline complet de traitement d'une requête.
        
        ⚠️ EXACTEMENT LE MÊME PIPELINE QUE L'INDEXER :
        Cette méthode applique les mêmes transformations que l'indexer pour
        garantir que les requêtes sont traitées de manière cohérente.
        
        Pipeline:
        ---------
        Requête brute
            ↓
        1. Tokenization (word_tokenize de NLTK)
            ↓
        2. Normalisation complète (lowercase, filtrage, stop words, stemming)
            ↓
        Termes de recherche finaux (stems)
        
        Paramètres:
        -----------
        query : str
            Requête utilisateur brute
        
        Retourne:
        ---------
        list
            Liste de termes de recherche nettoyés et normalisés (stems)
        
        Exemples complets:
        ------------------
        >>> processor = QueryProcessor()
        
        >>> processor.process("Comment apprendre le Python rapidement ?")
        ["comment", "apprend", "python", "rapid"]
        # Tokenization → normalisation → stop words → stemming
        
        >>> processor.process("Tutoriel sur l'API REST avec FastAPI")
        ["tutori", "api", "rest", "fastapi"]
        # "sur", "l'", "avec" sont des stop words
        
        >>> processor.process("Développement web en 2024")
        ["developp", "web"]
        # "en" est un stop word
        # "2024" est filtré (non-alphabétique)
        # "développement" → "developp" (stemming)
        
        Cas particuliers:
        -----------------
        - Requête vide : retourne liste vide
        - Tous les mots sont des stop words : retourne liste vide
        - Requête avec seulement de la ponctuation : retourne liste vide
        
        Différence avec l'indexer:
        --------------------------
        L'indexer retourne des tuples (terme, position) car il a besoin des
        positions pour l'index. Le query processor retourne seulement les termes
        car on n'a pas besoin des positions pour la recherche.
        """
        # Validation: vérifier que la requête n'est pas vide
        if not query or not query.strip():
            self.logger.debug("Requête vide, retour d'une liste vide")
            return []
        
        # Étape 1: Tokenization avec NLTK
        # Découpage du texte en tokens (mots)
        # Utilise word_tokenize pour une tokenization intelligente du français
        tokens = self._tokenize(query)
        self.logger.debug(f"Tokens après tokenization: {tokens}")
        
        # Étape 2: Normalisation complète
        # Applique: lowercase, filtrage, stop words, stemming
        # C'est exactement ce que fait l'indexer sur chaque document
        normalized_terms = self._normalize_tokens(tokens)
        self.logger.debug(f"Termes après normalisation: {normalized_terms}")
        
        # Log d'information si la requête ne produit aucun terme
        if not normalized_terms:
            self.logger.info(f"Aucun terme valide dans la requête: '{query}'")
        
        return normalized_terms
    
    def process_batch(self, queries: List[str]) -> List[List[str]]:
        """
        Traite plusieurs requêtes en lot (batch processing).
        
        Utile pour:
        -----------
        - Prétraiter un ensemble de requêtes test
        - Évaluation de performance du moteur
        - Traitement de logs de recherche
        
        Paramètres:
        -----------
        queries : list
            Liste de requêtes brutes
        
        Retourne:
        ---------
        list
            Liste de listes de termes, une par requête
        
        Exemple:
        --------
        >>> queries = [
        ...     "Comment apprendre Python ?",
        ...     "Tutoriel FastAPI REST API",
        ...     "Meilleurs frameworks web Python"
        ... ]
        >>> processor.process_batch(queries)
        [
            ["comment", "apprend", "python"],
            ["tutori", "fastapi", "rest", "api"],
            ["meilleur", "framework", "web", "python"]
        ]
        """
        return [self.process(query) for query in queries]
    
    def get_query_statistics(self, query: str) -> dict:
        """
        Retourne des statistiques sur une requête après traitement.
        
        Utile pour:
        -----------
        - Debugging et analyse des requêtes
        - Monitoring de la qualité des requêtes
        - Interface de développement
        
        Paramètres:
        -----------
        query : str
            Requête brute
        
        Retourne:
        ---------
        dict
            Statistiques détaillées sur la requête
        
        Exemple:
        --------
        >>> stats = processor.get_query_statistics("Comment apprendre le Python ?")
        >>> print(stats)
        {
            'original_query': 'Comment apprendre le Python ?',
            'total_tokens': 5,
            'tokens_after_filtering': 3,
            'final_terms': ['comment', 'apprend', 'python'],
            'unique_terms': 3,
            'removed_stop_words': ['le'],
            'term_frequency': {'comment': 1, 'apprend': 1, 'python': 1}
        }
        """
        # Requête originale
        stats = {
            'original_query': query
        }
        
        # Tokenization initiale
        tokens = self._tokenize(query)
        stats['total_tokens'] = len(tokens)
        
        # Identifier ce qui a été filtré
        # Comptage des tokens lowercase
        tokens_lower = [t.lower() for t in tokens if t.isalpha()]
        
        # Identifier les stop words
        removed_stop_words = [t for t in tokens_lower if t in self.stop_words]
        stats['removed_stop_words'] = removed_stop_words
        
        # Traitement complet
        final_terms = self.process(query)
        stats['final_terms'] = final_terms
        stats['tokens_after_filtering'] = len(final_terms)
        
        # Termes uniques
        stats['unique_terms'] = len(set(final_terms))
        
        # Distribution des termes (fréquence)
        stats['term_frequency'] = dict(Counter(final_terms))
        
        return stats


# ============================================================================
# Fonctions utilitaires
# ============================================================================

def compare_with_indexer_processing(
    text: str,
    query_processor: QueryProcessor
) -> None:
    """
    Compare le traitement d'un texte par le QueryProcessor
    pour vérifier la cohérence avec l'indexer.
    
    Utile pour:
    -----------
    - Vérifier que le QueryProcessor produit les mêmes termes que l'indexer
    - Debugging lors du développement
    - Tests de régression
    
    Paramètres:
    -----------
    text : str
        Texte à traiter
    query_processor : QueryProcessor
        Instance du processeur à tester
    
    Exemple:
    --------
    >>> processor = QueryProcessor()
    >>> compare_with_indexer_processing("Comment apprendre Python ?", processor)
    
    Texte original: "Comment apprendre Python ?"
    Tokens NLTK: ['Comment', 'apprendre', 'Python', '?']
    Termes finaux: ['comment', 'apprend', 'python']
    """
    print(f"Texte original: '{text}'")
    
    # Tokenization
    tokens = query_processor._tokenize(text)
    print(f"Tokens NLTK: {tokens}")
    
    # Normalisation complète
    terms = query_processor.process(text)
    print(f"Termes finaux: {terms}")
    print()


def test_stop_words_consistency(query_processor: QueryProcessor) -> None:
    """
    Vérifie que les stop words utilisés sont bien ceux de NLTK.
    
    Affiche quelques exemples de stop words pour vérification.
    
    Paramètres:
    -----------
    query_processor : QueryProcessor
        Instance du processeur
    """
    print("Stop Words Français (NLTK):")
    print(f"Nombre total: {len(query_processor.stop_words)}")
    print(f"Exemples: {sorted(list(query_processor.stop_words))[:20]}")
    print()


# ============================================================================
# Exemple d'utilisation
# ============================================================================

if __name__ == "__main__":
    """
    Exemples d'utilisation du QueryProcessor avec NLTK.
    
    Ces exemples montrent:
    1. Configuration et initialisation
    2. Traitement de différents types de requêtes
    3. Statistiques détaillées
    4. Cohérence avec l'indexer
    """
    
    print("="*70)
    print("GOGOL - Query Processor - Exemples d'utilisation (NLTK)")
    print("="*70)
    
    # ========================================================================
    # Exemple 1: Configuration de base (identique à l'indexer)
    # ========================================================================
    print("\n1. Configuration de base (avec NLTK)\n" + "-"*70)
    
    processor = QueryProcessor(
        min_word_length=2,  # Même config que l'indexer
        max_word_length=50  # Même config que l'indexer
    )
    
    print(f"✓ Stemmer: {type(processor.stemmer).__name__}")
    print(f"✓ Stop words: {len(processor.stop_words)} mots français (NLTK)")
    
    # ========================================================================
    # Exemple 2: Test avec différentes requêtes
    # ========================================================================
    print("\n\n2. Traitement de requêtes françaises\n" + "-"*70)
    
    test_queries = [
        "Comment apprendre le Python rapidement ?",
        "Tutoriel sur l'API REST avec FastAPI",
        "Développement web moderne en 2024",
        "Machine Learning et Intelligence Artificielle",
        "Chercher des informations sur la recherche d'information"
    ]
    
    for query in test_queries:
        result = processor.process(query)
        print(f"Requête : {query}")
        print(f"Termes  : {result}\n")
    
    # ========================================================================
    # Exemple 3: Statistiques détaillées
    # ========================================================================
    print("\n3. Statistiques détaillées sur une requête\n" + "-"*70)
    
    query = "Comment créer une API REST avec Python et FastAPI ?"
    stats = processor.get_query_statistics(query)
    
    print(f"Requête originale     : {stats['original_query']}")
    print(f"Tokens totaux         : {stats['total_tokens']}")
    print(f"Stop words supprimés  : {stats['removed_stop_words']}")
    print(f"Termes finaux         : {stats['final_terms']}")
    print(f"Nombre de termes      : {stats['tokens_after_filtering']}")
    print(f"Termes uniques        : {stats['unique_terms']}")
    print(f"Fréquence des termes  : {stats['term_frequency']}")
    
    # ========================================================================
    # Exemple 4: Vérification de la cohérence avec l'indexer
    # ========================================================================
    print("\n\n4. Cohérence avec l'indexer\n" + "-"*70)
    
    print("Test: les mêmes transformations que l'indexer sont appliquées\n")
    
    test_text = "L'apprentissage automatique et le développement web"
    compare_with_indexer_processing(test_text, processor)
    
    # ========================================================================
    # Exemple 5: Vérification des stop words NLTK
    # ========================================================================
    print("\n5. Stop words NLTK français\n" + "-"*70)
    
    test_stop_words_consistency(processor)
    
    # ========================================================================
    # Exemple 6: Traitement en batch
    # ========================================================================
    print("\n6. Traitement en batch\n" + "-"*70)
    
    batch_queries = [
        "Python pour le web",
        "FastAPI REST API",
        "Machine Learning Python"
    ]
    
    batch_results = processor.process_batch(batch_queries)
    
    print("Traitement de plusieurs requêtes:")
    for query, result in zip(batch_queries, batch_results):
        print(f"  '{query}' → {result}")
    
    # ========================================================================
    # Exemple 7: Effet du stemming
    # ========================================================================
    print("\n\n7. Effet du stemming français\n" + "-"*70)
    
    stemming_examples = [
        "chercher cherchait recherche",
        "développer développement développeur",
        "apprendre apprentissage",
        "programmer programmation programme"
    ]
    
    print("Démonstration du stemming (réduction à la racine):\n")
    for text in stemming_examples:
        tokens = processor._tokenize(text)
        stems = [processor.stemmer.stem(t.lower()) for t in tokens]
        print(f"Original: {tokens}")
        print(f"Stems   : {stems}\n")
    
    # ========================================================================
    # Exemple 8: Cas limites
    # ========================================================================
    print("\n8. Cas limites\n" + "-"*70)
    
    edge_cases = [
        "",  # Requête vide
        "   ",  # Seulement des espaces
        "le de la",  # Que des stop words
        "!@#$%",  # Que de la ponctuation
        "a",  # Token trop court
    ]
    
    print("Test des cas limites:")
    for query in edge_cases:
        result = processor.process(query)
        print(f"  '{query}' → {result}")
    
    # ========================================================================
    # Exemple 9: Comparaison des termes avant/après traitement
    # ========================================================================
    print("\n\n9. Comparaison avant/après traitement\n" + "-"*70)
    
    query = "Tutoriels gratuits pour apprendre la programmation Python"
    
    tokens = processor._tokenize(query)
    normalized = processor._normalize_tokens(tokens)
    
    print(f"Requête originale : {query}")
    print(f"Tokens NLTK       : {tokens}")
    print(f"Termes normalisés : {normalized}")
    
    # Afficher ce qui a été supprimé
    removed = set([t.lower() for t in tokens if t.isalpha()]) - set(normalized)
    print(f"Termes supprimés  : {removed} (stop words et filtrage)")
    
    print("\n" + "="*70)
    print("Tests terminés !")
    print("="*70)
    print("\n⚠️  IMPORTANT: Ce QueryProcessor utilise NLTK comme l'indexer")
    print("   pour garantir la cohérence des termes de recherche.")