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
        print("Module indexer - À implémenter")
        # from src.indexer import Indexer
        # indexer = Indexer()
        # indexer.build_index()

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
