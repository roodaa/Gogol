"""
Indexeur pour Gogol

Ce module implémente un indexeur qui:
1. Lit les documents JSON crawlés depuis data/raw/
2. Tokenise et normalise le texte français (stopwords, stemming)
3. Construit un index inversé avec scores TF-IDF
4. Stocke l'index dans une base de données SQLite
"""

import json
import logging
import math
import os
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple, Set

import nltk
from nltk.corpus import stopwords
from nltk.stem.snowball import FrenchStemmer
from nltk.tokenize import word_tokenize
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

from src.config import INDEXER_CONFIG, RAW_DATA_DIR, INDEXED_DATA_DIR, LOG_CONFIG
from src.indexer.models import Base, Document, Term, Posting, IndexMetadata


class Indexer:
    """
    Classe principale de l'indexeur.

    L'indexeur traite les documents crawlés et construit un index inversé
    avec scoring TF-IDF pour permettre la recherche par mots-clés.
    """

    def __init__(self):
        """
        Initialise l'indexeur avec:
        - Configuration depuis INDEXER_CONFIG
        - NLTK pour le traitement du français (tokenisation, stemming, stopwords)
        - Base de données SQLite via SQLAlchemy
        - Logger pour tracer l'activité
        """
        # Configuration de l'indexeur
        self.db_path = INDEXER_CONFIG["database_path"]
        self.min_word_length = INDEXER_CONFIG["min_word_length"]
        self.max_word_length = INDEXER_CONFIG["max_word_length"]

        # Compteurs
        self.docs_indexed = 0
        self.terms_indexed = 0

        # Assurer que le dossier de données existe
        INDEXED_DATA_DIR.mkdir(parents=True, exist_ok=True)

        # Configuration du logger (même pattern que Crawler)
        self._setup_logger()

        # Télécharger les données NLTK si nécessaire
        self._download_nltk_data()

        # Initialiser le stemmer et les stop words français
        self.stemmer = FrenchStemmer()
        self.stop_words = set(stopwords.words('french'))
        self.logger.info(f"Stop words français chargés: {len(self.stop_words)} mots")

        # Initialiser la base de données
        self._init_database()

        self.logger.info("Indexeur initialisé")

    def _setup_logger(self):
        """
        Configure le système de logging pour tracer l'activité de l'indexeur.
        Les logs sont écrits dans un fichier et affichés dans la console.
        """
        self.logger = logging.getLogger("Gogol.Indexer")
        self.logger.setLevel(LOG_CONFIG["level"])

        # Éviter les doublons de handlers
        if not self.logger.handlers:
            # Handler pour fichier
            file_handler = logging.FileHandler(LOG_CONFIG["file"])
            file_handler.setLevel(logging.INFO)

            # Handler pour console
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)

            # Format des logs
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)

            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)

    def _download_nltk_data(self):
        """
        Télécharge les ressources NLTK nécessaires si elles ne sont pas déjà présentes.

        Ressources requises:
        - stopwords: Liste des mots vides français
        - punkt: Tokenizer pour la segmentation
        - punkt_tab: Tables pour le tokenizer
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

    def _init_database(self):
        """
        Initialise la connexion à la base de données SQLite et crée les tables.

        Utilise SQLAlchemy ORM pour gérer la base de données.
        """
        # Créer l'engine SQLite
        self.engine = create_engine(f'sqlite:///{self.db_path}', echo=False)

        # Créer toutes les tables si elles n'existent pas
        Base.metadata.create_all(self.engine)

        # Créer une session factory
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

        self.logger.info(f"Base de données initialisée: {self.db_path}")

    def _load_document(self, json_path: Path) -> Dict:
        """
        Charge un document JSON depuis le système de fichiers.

        Args:
            json_path: Chemin vers le fichier JSON

        Returns:
            Dictionnaire avec les données du document: {url, title, text, links}
            Plus le hash MD5 du nom du fichier

        Raises:
            json.JSONDecodeError: Si le fichier JSON est invalide
            FileNotFoundError: Si le fichier n'existe pas
        """
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Ajouter le hash du fichier (MD5 du nom sans extension)
        data['doc_hash'] = json_path.stem

        return data

    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenise le texte en mots français.

        Args:
            text: Texte à tokeniser

        Returns:
            Liste de tokens (mots)
        """
        try:
            tokens = word_tokenize(text, language='french')
            return tokens
        except Exception as e:
            self.logger.warning(f"Erreur de tokenisation: {e}. Utilisation du split basique.")
            # Fallback: split basique si NLTK échoue
            return text.split()

    def _normalize_tokens(self, tokens: List[str]) -> List[Tuple[str, int]]:
        """
        Normalise les tokens: lowercase, filtrage, stop words, stemming.

        Étapes de normalisation:
        1. Lowercase
        2. Filtrer les non-alphabétiques
        3. Filtrer par longueur (min_word_length à max_word_length)
        4. Retirer les stop words français
        5. Appliquer le stemming français

        Args:
            tokens: Liste de tokens bruts

        Returns:
            Liste de tuples (terme_normalisé, position)
        """
        normalized = []

        for position, token in enumerate(tokens):
            # Lowercase
            token_lower = token.lower()

            # Filtrer: garder seulement les mots alphabétiques
            if not token_lower.isalpha():
                continue

            # Filtrer par longueur
            if len(token_lower) < self.min_word_length or len(token_lower) > self.max_word_length:
                continue

            # Retirer les stop words
            if token_lower in self.stop_words:
                continue

            # Stemming français
            stemmed = self.stemmer.stem(token_lower)

            normalized.append((stemmed, position))

        return normalized

    def _process_document(self, doc_data: Dict) -> Tuple[int, Dict[str, Dict]]:
        """
        Traite un document complet: tokenisation, normalisation, calcul des statistiques.

        Args:
            doc_data: Données du document {url, title, text, doc_hash}

        Returns:
            Tuple (doc_id, term_stats) où:
            - doc_id: ID du document dans la base
            - term_stats: Dict {term: {'frequency': int, 'positions': [int]}}
        """
        # Vérifier si le document existe déjà (par hash)
        existing_doc = self.session.query(Document).filter_by(doc_hash=doc_data['doc_hash']).first()
        if existing_doc:
            self.logger.debug(f"Document déjà indexé: {doc_data['doc_hash']}")
            return existing_doc.id, {}

        # Tokeniser le texte
        tokens = self._tokenize(doc_data['text'])

        # Normaliser les tokens
        normalized_tokens = self._normalize_tokens(tokens)

        # Calculer les statistiques par terme
        term_stats = defaultdict(lambda: {'frequency': 0, 'positions': []})

        for term, position in normalized_tokens:
            term_stats[term]['frequency'] += 1
            term_stats[term]['positions'].append(position)

        # Créer l'entrée du document dans la base
        doc = Document(
            url=doc_data['url'],
            title=doc_data['title'],
            doc_hash=doc_data['doc_hash'],
            text_length=len(doc_data['text']),
            term_count=len(term_stats)
        )

        self.session.add(doc)
        self.session.flush()  # Pour obtenir l'ID du document

        doc_id = doc.id

        # Traiter chaque terme unique du document
        for term, stats in term_stats.items():
            # Chercher ou créer le terme
            term_obj = self.session.query(Term).filter_by(term=term).first()

            if not term_obj:
                term_obj = Term(
                    term=term,
                    document_frequency=0,
                    total_occurrences=0
                )
                self.session.add(term_obj)
                self.session.flush()

            # Mettre à jour les statistiques du terme
            term_obj.document_frequency += 1
            term_obj.total_occurrences += stats['frequency']

            # Créer le posting (entrée dans l'index inversé)
            posting = Posting(
                term_id=term_obj.id,
                doc_id=doc_id,
                term_frequency=stats['frequency'],
                positions=json.dumps(stats['positions'])  # Stocker les positions en JSON
            )

            self.session.add(posting)

        # Commit pour ce document
        self.session.commit()

        return doc_id, term_stats

    def _calculate_tf_idf(self):
        """
        Calcule les scores TF-IDF pour tous les postings.

        Formules:
        - TF (Term Frequency) = term_frequency / total_terms_in_doc
        - IDF (Inverse Document Frequency) = log(total_docs / docs_containing_term)
        - TF-IDF = TF × IDF

        Met à jour la colonne tf_idf_score dans la table postings.
        """
        self.logger.info("Calcul des scores TF-IDF...")

        # Récupérer le nombre total de documents
        total_docs = self.session.query(func.count(Document.id)).scalar()

        if total_docs == 0:
            self.logger.warning("Aucun document dans la base, impossible de calculer TF-IDF")
            return

        # Pour chaque posting, calculer TF-IDF
        postings = self.session.query(Posting).all()

        for posting in postings:
            # Récupérer le document pour connaître le nombre total de termes
            doc = self.session.query(Document).filter_by(id=posting.doc_id).first()

            # Récupérer le terme pour connaître sa document_frequency
            term = self.session.query(Term).filter_by(id=posting.term_id).first()

            if doc and term:
                # Calculer TF (fréquence normalisée)
                # Note: on utilise term_count (nombre de termes uniques)
                # Pour une TF plus standard, on pourrait utiliser la longueur totale du texte
                tf = posting.term_frequency / max(doc.term_count, 1)

                # Calculer IDF
                idf = math.log(total_docs / term.document_frequency) if term.document_frequency > 0 else 0

                # Calculer TF-IDF
                tf_idf = tf * idf

                # Mettre à jour le posting
                posting.tf_idf_score = tf_idf

        # Commit tous les changements
        self.session.commit()

        self.logger.info(f"Scores TF-IDF calculés pour {len(postings)} postings")

        # Stocker les métadonnées
        self._update_metadata('total_docs', str(total_docs))
        self._update_metadata('last_tfidf_calculation', str(self.session.query(func.now()).scalar()))

    def _update_metadata(self, key: str, value: str):
        """
        Met à jour ou crée une entrée de métadonnées.

        Args:
            key: Clé de la métadonnée
            value: Valeur de la métadonnée
        """
        metadata = self.session.query(IndexMetadata).filter_by(key=key).first()

        if metadata:
            metadata.value = value
        else:
            metadata = IndexMetadata(key=key, value=value)
            self.session.add(metadata)

        self.session.commit()

    def build_index(self, force_rebuild: bool = False) -> Dict:
        """
        Lance l'indexation de tous les documents dans RAW_DATA_DIR.

        Cette méthode principale:
        1. Liste tous les fichiers JSON dans data/raw/
        2. Pour chaque document: charge, traite, stocke
        3. Calcule les scores TF-IDF
        4. Retourne les statistiques

        Args:
            force_rebuild: Si True, supprime et reconstruit l'index complet

        Returns:
            Dictionnaire avec les statistiques de l'indexation
        """
        if force_rebuild:
            self.logger.warning("Reconstruction forcée de l'index...")
            # Supprimer toutes les données
            self.session.query(Posting).delete()
            self.session.query(Term).delete()
            self.session.query(Document).delete()
            self.session.query(IndexMetadata).delete()
            self.session.commit()
            self.logger.info("Index existant supprimé")

        # Lister tous les fichiers JSON
        json_files = list(RAW_DATA_DIR.glob("*.json"))
        total_files = len(json_files)

        self.logger.info(f"Trouvé {total_files} fichiers JSON à indexer")

        if total_files == 0:
            self.logger.warning(f"Aucun fichier JSON trouvé dans {RAW_DATA_DIR}")
            return {
                'docs_indexed': 0,
                'unique_terms': 0,
                'postings': 0,
                'db_size': '0 MB'
            }

        # Indexer chaque document
        for idx, json_path in enumerate(json_files, 1):
            try:
                # Charger le document
                doc_data = self._load_document(json_path)

                # Traiter le document
                doc_id, term_stats = self._process_document(doc_data)

                if term_stats:  # Seulement si c'est un nouveau document
                    self.docs_indexed += 1
                    self.logger.info(f"[{idx}/{total_files}] Indexé: {json_path.name} - {len(term_stats)} termes uniques")
                else:
                    self.logger.debug(f"[{idx}/{total_files}] Ignoré (déjà indexé): {json_path.name}")

            except json.JSONDecodeError as e:
                self.logger.error(f"Fichier JSON invalide {json_path.name}: {e}")
                continue

            except Exception as e:
                self.logger.error(f"Erreur lors du traitement de {json_path.name}: {e}")
                continue

        # Calculer les scores TF-IDF
        if self.docs_indexed > 0:
            self._calculate_tf_idf()

        # Récupérer les statistiques finales
        stats = self.get_stats()

        # Afficher le résumé
        self.logger.info("="*50)
        self.logger.info("INDEXATION TERMINÉE")
        self.logger.info(f"Documents indexés: {stats['docs_indexed']}")
        self.logger.info(f"Termes uniques: {stats['unique_terms']}")
        self.logger.info(f"Postings créés: {stats['postings']}")
        self.logger.info(f"Taille de la base: {stats['db_size']}")
        self.logger.info("="*50)

        return stats

    def get_stats(self) -> Dict:
        """
        Récupère les statistiques de l'index.

        Returns:
            Dictionnaire avec les statistiques:
            - docs_indexed: Nombre de documents indexés
            - unique_terms: Nombre de termes uniques
            - postings: Nombre de postings (entrées dans l'index inversé)
            - db_size: Taille de la base de données
        """
        # Compter les documents
        docs_count = self.session.query(func.count(Document.id)).scalar() or 0

        # Compter les termes uniques
        terms_count = self.session.query(func.count(Term.id)).scalar() or 0

        # Compter les postings
        postings_count = self.session.query(func.count(Posting.id)).scalar() or 0

        # Taille de la base de données
        if self.db_path.exists():
            db_size_bytes = self.db_path.stat().st_size
            db_size = f"{db_size_bytes / (1024 * 1024):.2f} MB"
        else:
            db_size = "0 MB"

        return {
            'docs_indexed': docs_count,
            'unique_terms': terms_count,
            'postings': postings_count,
            'db_size': db_size
        }

    def __del__(self):
        """
        Destructeur: ferme proprement la session de base de données.
        """
        if hasattr(self, 'session'):
            self.session.close()
