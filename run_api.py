"""
Script pour lancer l'API Gogol depuis la racine du projet
"""

import uvicorn

if __name__ == "__main__":
    print("\n" + "="*70)
    print("GOGOL - API FastAPI")
    print("="*70)
    print("\nDémarrage du serveur...")
    print("URL: http://127.0.0.1:8000")
    print("Documentation: http://127.0.0.1:8000/api/docs")
    print("\nAppuyez sur Ctrl+C pour arrêter")
    print("="*70 + "\n")

    uvicorn.run(
        "src.web_interface.app:app",
        host="127.0.0.1",
        port=8000,
        reload=False,  # Désactivé pour éviter les problèmes sous Windows
        log_level="info"
    )
