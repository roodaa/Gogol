"""
Point d'entrée principal de Gogol
"""
import argparse
from src.config import WEB_CONFIG

def main():
    parser = argparse.ArgumentParser(description="Gogol - Moteur de Recherche")
    parser.add_argument(
        "command",
        choices=["crawl", "index", "search", "web"],
        help="Commande à exécuter"
    )
    parser.add_argument(
        "--url",
        help="URL à crawler (pour la commande crawl)"
    )
    parser.add_argument(
        "--query",
        help="Requête de recherche (pour la commande search)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force la reconstruction complète de l'index (pour la commande index)"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Afficher les statistiques de l'index (pour la commande index)"
    )

    args = parser.parse_args()

    if args.command == "crawl":
        if not args.url:
            print("Erreur: L'argument --url est requis pour la commande crawl")
            print("Exemple: python main.py crawl --url https://example.com")
            return

        from src.crawler import Crawler
        crawler = Crawler()
        results = crawler.crawl(args.url)

        print("\n" + "="*50)
        print("Résumé du crawling:")
        print(f"  Pages crawlées: {results['pages_crawled']}")
        print(f"  URLs visitées: {results['urls_visited']}")
        print(f"  URLs en attente: {results['urls_pending']}")
        print("="*50)

    elif args.command == "index":
        from src.indexer import Indexer

        indexer = Indexer()

        # Si --stats uniquement, afficher les statistiques
        if args.stats and not args.force:
            stats = indexer.get_stats()
            print("\n" + "="*50)
            print("STATISTIQUES DE L'INDEX")
            print("="*50)
            print(f"Documents indexés: {stats['docs_indexed']}")
            print(f"Termes uniques: {stats['unique_terms']}")
            print(f"Postings créés: {stats['postings']}")
            print(f"Taille de la base: {stats['db_size']}")
            print("="*50)
        else:
            # Lancer l'indexation
            force = args.force
            stats = indexer.build_index(force_rebuild=force)

            print("\n" + "="*50)
            print("INDEXATION TERMINÉE")
            print("="*50)
            print(f"Documents indexés: {stats['docs_indexed']}")
            print(f"Termes uniques: {stats['unique_terms']}")
            print(f"Postings créés: {stats['postings']}")
            print(f"Taille de la base: {stats['db_size']}")
            print("="*50)

    elif args.command == "search":
        print("Module search - À implémenter")
        # from src.search_engine import SearchEngine
        # engine = SearchEngine()
        # results = engine.search(args.query)
        # print(results)

    elif args.command == "web":
        print(f"Démarrage de l'interface web sur {WEB_CONFIG['host']}:{WEB_CONFIG['port']}")
        print("Interface web - À implémenter")
        # import uvicorn
        # from src.web_interface.app import app
        # uvicorn.run(app, host=WEB_CONFIG['host'], port=WEB_CONFIG['port'])

if __name__ == "__main__":
    main()
