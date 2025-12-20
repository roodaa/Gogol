"""
Modèles SQLAlchemy pour l'indexeur Gogol.

Ce module définit les 4 tables principales de l'index inversé:
- Document: Métadonnées des pages crawlées
- Term: Vocabulaire unique (mots normalisés/stemmés)
- Posting: Index inversé (terme -> documents) avec scores TF-IDF
- IndexMetadata: Statistiques globales de l'index
"""

from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Document(Base):
    """
    Table des documents indexés.

    Stocke les métadonnées de chaque page Wikipedia crawlée.
    """
    __tablename__ = 'documents'

    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String, unique=True, nullable=False, index=True)
    title = Column(String, nullable=False)
    doc_hash = Column(String, unique=True, nullable=False, index=True)
    text_length = Column(Integer)
    term_count = Column(Integer)
    indexed_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    postings = relationship("Posting", back_populates="document", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Document(id={self.id}, title='{self.title[:30]}...', url='{self.url[:50]}...')>"


class Term(Base):
    """
    Table des termes uniques (vocabulaire).

    Stocke chaque terme normalisé (lowercase, stemmé) avec ses statistiques globales.
    """
    __tablename__ = 'terms'

    id = Column(Integer, primary_key=True, autoincrement=True)
    term = Column(String, unique=True, nullable=False, index=True)
    document_frequency = Column(Integer, default=0)  # Nombre de docs contenant ce terme
    total_occurrences = Column(Integer, default=0)   # Total d'occurrences tous docs confondus

    # Relationship
    postings = relationship("Posting", back_populates="term", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Term(id={self.id}, term='{self.term}', df={self.document_frequency})>"


class Posting(Base):
    """
    Table de l'index inversé (postings list).

    Stocke la relation terme -> document avec fréquence et score TF-IDF pré-calculé.
    """
    __tablename__ = 'postings'

    id = Column(Integer, primary_key=True, autoincrement=True)
    term_id = Column(Integer, ForeignKey('terms.id'), nullable=False, index=True)
    doc_id = Column(Integer, ForeignKey('documents.id'), nullable=False, index=True)
    term_frequency = Column(Integer, nullable=False)  # Occurrences dans ce document
    tf_idf_score = Column(Float, index=True)          # Score TF-IDF pré-calculé
    positions = Column(Text)                           # JSON array des positions (pour v2.0)

    # Relationships
    term = relationship("Term", back_populates="postings")
    document = relationship("Document", back_populates="postings")

    def __repr__(self):
        return f"<Posting(term_id={self.term_id}, doc_id={self.doc_id}, tf={self.term_frequency}, tfidf={self.tf_idf_score:.4f})>"


# Index composite pour éviter les doublons (terme, document)
Index('idx_term_doc', Posting.term_id, Posting.doc_id, unique=True)


class IndexMetadata(Base):
    """
    Table des métadonnées de l'index.

    Stocke les statistiques globales: nombre total de documents, longueur moyenne, version, etc.
    """
    __tablename__ = 'index_metadata'

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String, unique=True, nullable=False)
    value = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<IndexMetadata(key='{self.key}', value='{self.value}')>"
