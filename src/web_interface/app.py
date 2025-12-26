"""
API FastAPI pour le moteur de recherche Gogol

Cette API expose des endpoints REST pour interagir avec le moteur de recherche.
Elle utilise le QueryProcessor et le Ranker pour traiter les requêtes et retourner les résultats.

Endpoints:
- GET /api/search?q=...&limit=... : Rechercher des documents
- GET /api/stats : Obtenir les statistiques de l'index
- GET /api/health : Vérifier le statut de l'API

Auteur: Romaric Dacosse
Projet: Gogol - Moteur de recherche éducatif
"""

import logging
from typing import List, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.search_engine.query_processor import QueryProcessor
from src.search_engine.ranker import Ranker


# ============================================================================
# Configuration du logging
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Gogol.API")


# ============================================================================
# Modèles Pydantic pour la validation des données
# ============================================================================

class SearchResult(BaseModel):
    """Modèle pour un résultat de recherche"""
    doc_id: int = Field(..., description="ID du document")
    title: str = Field(..., description="Titre du document")
    url: str = Field(..., description="URL du document")
    score: float = Field(..., ge=0.0, le=1.0, description="Score de pertinence (0-1)")

    class Config:
        json_schema_extra = {
            "example": {
                "doc_id": 42,
                "title": "Python Tutorial - Introduction",
                "url": "https://example.com/python-tutorial",
                "score": 0.8523
            }
        }


class SearchResponse(BaseModel):
    """Modèle pour la réponse de recherche complète"""
    query: str = Field(..., description="Requête originale")
    processed_terms: List[str] = Field(..., description="Termes normalisés (après stemming)")
    total_results: int = Field(..., ge=0, description="Nombre total de résultats trouvés")
    results: List[SearchResult] = Field(..., description="Liste des résultats")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "Comment apprendre Python ?",
                "processed_terms": ["comment", "apprend", "python"],
                "total_results": 5,
                "results": [
                    {
                        "doc_id": 42,
                        "title": "Python Tutorial",
                        "url": "https://example.com/tutorial",
                        "score": 0.95
                    }
                ]
            }
        }


class IndexStats(BaseModel):
    """Modèle pour les statistiques de l'index"""
    total_documents: int = Field(..., description="Nombre total de documents indexés")
    total_terms: int = Field(..., description="Nombre total de termes uniques")
    total_postings: int = Field(..., description="Nombre total d'entrées dans l'index inversé")
    db_path: str = Field(..., description="Chemin de la base de données")
    db_size_mb: float = Field(..., description="Taille de la base de données en MB")


class HealthResponse(BaseModel):
    """Modèle pour la réponse du health check"""
    status: str = Field(..., description="Statut de l'API (healthy/unhealthy)")
    message: str = Field(..., description="Message descriptif")
    index_ready: bool = Field(..., description="L'index est-il prêt ?")


# ============================================================================
# Initialisation de l'application FastAPI
# ============================================================================

app = FastAPI(
    title="Gogol Search API",
    description="API REST pour le moteur de recherche Gogol",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configuration CORS pour permettre les requêtes depuis Angular
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],  # Port par défaut d'Angular
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Initialisation des composants du moteur de recherche
# ============================================================================

query_processor: Optional[QueryProcessor] = None
ranker: Optional[Ranker] = None


@app.on_event("startup")
async def startup_event():
    """
    Initialise les composants du moteur de recherche au démarrage de l'API.
    """
    global query_processor, ranker

    logger.info("Démarrage de l'API Gogol...")

    try:
        # Initialisation du QueryProcessor
        query_processor = QueryProcessor()
        logger.info("QueryProcessor initialisé avec succès")

        # Initialisation du Ranker (connexion à la DB)
        ranker = Ranker()
        logger.info("Ranker initialisé avec succès")

        # Afficher les statistiques de l'index
        stats = ranker.get_index_stats()
        logger.info(f"Index prêt: {stats['total_documents']} documents, {stats['total_terms']} termes")

    except FileNotFoundError as e:
        logger.error(f"Base de données introuvable: {e}")
        logger.error("Vous devez d'abord lancer l'indexeur: python main.py index")

    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation: {e}", exc_info=True)


@app.on_event("shutdown")
async def shutdown_event():
    """
    Nettoie les ressources au shutdown de l'API.
    """
    logger.info("Arrêt de l'API Gogol...")


# ============================================================================
# Endpoints de l'API
# ============================================================================

@app.get("/", tags=["Root"])
async def root():
    """
    Endpoint racine - Redirige vers la documentation.
    """
    return {
        "message": "Bienvenue sur l'API Gogol",
        "version": "1.0.0",
        "documentation": "/api/docs"
    }


@app.get("/api/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Vérifie le statut de l'API et de l'index.

    Retourne:
    - status: "healthy" si tout fonctionne, "unhealthy" sinon
    - message: description du statut
    - index_ready: True si l'index est prêt pour des recherches
    """
    if query_processor is None or ranker is None:
        return HealthResponse(
            status="unhealthy",
            message="Moteur de recherche non initialisé. Lancez l'indexeur d'abord.",
            index_ready=False
        )

    try:
        stats = ranker.get_index_stats()

        if stats['total_documents'] == 0:
            return HealthResponse(
                status="unhealthy",
                message="Index vide. Aucun document indexé.",
                index_ready=False
            )

        return HealthResponse(
            status="healthy",
            message=f"API opérationnelle. {stats['total_documents']} documents indexés.",
            index_ready=True
        )

    except Exception as e:
        logger.error(f"Erreur lors du health check: {e}", exc_info=True)
        return HealthResponse(
            status="unhealthy",
            message=f"Erreur: {str(e)}",
            index_ready=False
        )


@app.get("/api/stats", response_model=IndexStats, tags=["Statistics"])
async def get_stats():
    """
    Retourne les statistiques de l'index de recherche.

    Informations retournées:
    - Nombre de documents indexés
    - Nombre de termes uniques dans l'index
    - Nombre d'entrées dans l'index inversé
    - Chemin et taille de la base de données
    """
    if ranker is None:
        raise HTTPException(
            status_code=503,
            detail="Moteur de recherche non initialisé. Lancez l'indexeur d'abord."
        )

    try:
        stats = ranker.get_index_stats()
        return IndexStats(**stats)

    except Exception as e:
        logger.error(f"Erreur lors de la récupération des stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")


@app.get("/api/search", response_model=SearchResponse, tags=["Search"])
async def search(
    q: str = Query(..., description="Requête de recherche", min_length=1),
    limit: int = Query(10, ge=1, le=100, description="Nombre maximum de résultats")
):
    """
    Effectue une recherche dans l'index.

    Paramètres:
    - q: Requête de recherche (texte libre en français)
    - limit: Nombre maximum de résultats à retourner (1-100, défaut: 10)

    Retourne:
    - query: Requête originale
    - processed_terms: Termes après traitement (tokenisation, stemming, etc.)
    - total_results: Nombre de résultats trouvés
    - results: Liste des résultats classés par pertinence décroissante

    Exemples de requêtes:
    - /api/search?q=Python tutorial
    - /api/search?q=Comment apprendre le machine learning ?&limit=5
    """
    # Vérifier que le moteur est initialisé
    if query_processor is None or ranker is None:
        raise HTTPException(
            status_code=503,
            detail="Moteur de recherche non initialisé. Lancez l'indexeur d'abord."
        )

    try:
        # Étape 1: Traitement de la requête (normalisation, stemming)
        logger.info(f"Recherche: '{q}'")
        processed_terms = query_processor.process(q)

        # Si aucun terme valide après traitement
        if not processed_terms:
            logger.warning(f"Aucun terme valide dans la requête: '{q}'")
            return SearchResponse(
                query=q,
                processed_terms=[],
                total_results=0,
                results=[]
            )

        logger.debug(f"Termes traités: {processed_terms}")

        # Étape 2: Recherche et ranking
        ranked_results = ranker.rank(processed_terms, top_k=limit)

        # Étape 3: Formatage des résultats
        results = [
            SearchResult(
                doc_id=doc_id,
                title=title,
                url=url,
                score=round(score, 4)  # Arrondir pour lisibilité
            )
            for doc_id, title, url, score in ranked_results
        ]

        logger.info(f"Résultats trouvés: {len(results)}")

        return SearchResponse(
            query=q,
            processed_terms=processed_terms,
            total_results=len(results),
            results=results
        )

    except Exception as e:
        logger.error(f"Erreur lors de la recherche: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")


# ============================================================================
# Point d'entrée pour lancer l'API en développement
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    print("\n" + "="*70)
    print("GOGOL - API FastAPI")
    print("="*70)
    print("\nDémarrage du serveur de développement...")
    print("URL: http://127.0.0.1:8000")
    print("Documentation: http://127.0.0.1:8000/api/docs")
    print("\n" + "="*70 + "\n")

    uvicorn.run(
        "app:app",
        host="127.0.0.1",
        port=8000,
        reload=True,  # Auto-reload en développement
        log_level="info"
    )
