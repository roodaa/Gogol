"""
Point d'entrée principal pour Gogol

Ce script permet de lancer les différents composants du moteur de recherche:
- Crawler: Télécharge des pages web
- Indexer: Construit l'index inversé avec TF-IDF
- Search: Interface de recherche (à venir)
"""

import argparse
import sys
from pathlib import Path

from src.crawler.crawler import Crawler
from src.indexer.indexer import Indexer


def crawl_command(args):
    """
    Lance le crawler avec les paramètres spécifiés.
    
    Args:
        args: Arguments de la ligne de commande
    """
    # Créer le crawler avec max_pages personnalisé si spécifié
    if args.max_pages:
        crawler = Crawler(max_pages=args.max_pages)
    else:
        crawler = Crawler()  # Utilise la valeur par défaut de config.py
    
    # Lancer le crawling
    print(f"\n🕷️  Crawling de {args.url}")
    if args.max_pages:
        print(f"   Limite: {args.max_pages} pages")
    print()
    
    results = crawler.crawl(args.url)
    
    # Afficher le résumé
    print("\n" + "="*60)
    print("RÉSUMÉ DU CRAWLING")
    print("="*60)
    print(f"Pages crawlées    : {results['pages_crawled']}")
    print(f"Pages sauvegardées: {results['pages_saved']}")
    print(f"Erreurs           : {results['errors']}")
    print("="*60)


def index_command(args):
    """
    Lance l'indexeur pour créer l'index inversé.
    
    Args:
        args: Arguments de la ligne de commande
    """
    print("\n📚 Indexation des documents")
    print()
    
    indexer = Indexer()
    
    # Forcer la reconstruction si demandé
    force_rebuild = args.force if hasattr(args, 'force') else False
    
    stats = indexer.build_index(force_rebuild=force_rebuild)
    
    print("\n✓ Indexation terminée!")


def search_command(args):
    """
    Lance une recherche (à implémenter).
    
    Args:
        args: Arguments de la ligne de commande
    """
    from src.search_engine.query_processor import QueryProcessor
    from src.search_engine.ranker import Ranker
    
    print(f"\n🔍 Recherche: '{args.query}'")
    print()
    
    # Initialiser le moteur
    processor = QueryProcessor()
    ranker = Ranker()
    
    # Traiter la requête
    terms = processor.process(args.query)
    print(f"Termes normalisés: {terms}")
    
    if not terms:
        print("⚠️  Aucun terme valide dans la requête")
        return
    
    # Rechercher
    results = ranker.rank(terms, top_k=args.top if hasattr(args, 'top') else 10)
    
    # Afficher les résultats
    if results:
        print(f"\nRésultats ({len(results)} trouvés):\n")
        for i, (doc_id, title, url, score) in enumerate(results, 1):
            print(f"{i}. [{score:.4f}] {title}")
            print(f"   {url}\n")
    else:
        print("❌ Aucun résultat trouvé")


def main():
    """
    Point d'entrée principal avec parsing des arguments.
    """
    parser = argparse.ArgumentParser(
        description='Gogol - Moteur de recherche éducatif',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  # Crawler 50 pages depuis Wikipedia
  python main.py crawl --url https://fr.wikipedia.org/wiki/Python --max-pages 50
  
  # Crawler avec la limite par défaut (100 pages)
  python main.py crawl --url https://fr.wikipedia.org/wiki/France
  
  # Indexer les documents crawlés
  python main.py index
  
  # Forcer la reconstruction de l'index
  python main.py index --force
  
  # Rechercher
  python main.py search "Python programming"
  
  # Rechercher avec plus de résultats
  python main.py search "machine learning" --top 20
        """
    )
    
    # Sous-commandes
    subparsers = parser.add_subparsers(dest='command', help='Commande à exécuter')
    
    # ========================================================================
    # Commande: crawl
    # ========================================================================
    crawl_parser = subparsers.add_parser(
        'crawl',
        help='Crawler des pages web'
    )
    crawl_parser.add_argument(
        '--url',
        type=str,
        required=True,
        help="URL de départ pour le crawling"
    )
    crawl_parser.add_argument(
        '--max-pages',
        type=int,
        default=None,
        help="Nombre maximum de pages à crawler (défaut: 100)"
    )
    
    # ========================================================================
    # Commande: index
    # ========================================================================
    index_parser = subparsers.add_parser(
        'index',
        help='Indexer les documents crawlés'
    )
    index_parser.add_argument(
        '--force',
        action='store_true',
        help="Forcer la reconstruction de l'index (supprime l'ancien)"
    )
    
    # ========================================================================
    # Commande: search
    # ========================================================================
    search_parser = subparsers.add_parser(
        'search',
        help='Effectuer une recherche'
    )
    search_parser.add_argument(
        'query',
        type=str,
        help="Requête de recherche"
    )
    search_parser.add_argument(
        '--top',
        type=int,
        default=10,
        help="Nombre de résultats à afficher (défaut: 10)"
    )
    
    # Parser les arguments
    args = parser.parse_args()
    
    # Exécuter la commande appropriée
    if args.command == 'crawl':
        crawl_command(args)
    elif args.command == 'index':
        index_command(args)
    elif args.command == 'search':
        search_command(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
