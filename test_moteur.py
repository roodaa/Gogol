"""
Script de test simple pour le moteur de recherche Gogol
À placer à la racine du projet (même niveau que main.py)
"""

from src.search_engine.query_processor import QueryProcessor
from src.search_engine.ranker import Ranker


def main():
    print("\n" + "="*70)
    print("TEST DU MOTEUR DE RECHERCHE GOGOL")
    print("="*70)
    
    # 1. Initialisation
    print("\n[1] Initialisation du moteur...")
    try:
        processor = QueryProcessor()
        ranker = Ranker()
        print("    ✓ QueryProcessor initialisé")
        print("    ✓ Ranker initialisé")
    except FileNotFoundError as e:
        print(f"    ❌ Erreur: {e}")
        print("\n    💡 Solution:")
        print("       1. Lance le crawler: python main.py --crawl")
        print("       2. Lance l'indexer: python main.py --index")
        return
    except Exception as e:
        print(f"    ❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 2. Vérifier l'index
    print("\n[2] Statistiques de l'index...")
    stats = ranker.get_index_stats()
    print(f"    Documents : {stats['total_documents']}")
    print(f"    Termes    : {stats['total_terms']}")
    print(f"    Postings  : {stats['total_postings']}")
    print(f"    DB        : {stats['db_size_mb']:.2f} MB")
    
    if stats['total_documents'] == 0:
        print("\n    ⚠️  Aucun document indexé!")
        print("       Lance: python main.py --index")
        return
    
    # 3. Tes requêtes de test
    print("\n[3] Recherches de test")
    print("-"*70)
    
    # 🔥 MODIFIE CES REQUÊTES SELON TES BESOINS
    mes_requetes = [
        "Emmanuel Macron président de la république française",   
        "colonies françaises",
        "Victor Hugo"
    ]
    
    for query in mes_requetes:
        print(f"\n🔍 Requête: '{query}'")
        
        # Traitement de la requête
        termes = processor.process(query)
        print(f"   Termes normalisés: {termes}")
        
        if not termes:
            print("   ⚠️  Aucun terme valide dans la requête")
            continue
        
        # Recherche
        resultats = ranker.rank(termes, top_k=5)
        
        # Affichage des résultats
        if resultats:
            print(f"   Résultats trouvés: {len(resultats)}\n")
            for i, (doc_id, titre, url, score) in enumerate(resultats, 1):
                print(f"   {i}. Score: {score:.4f}")
                print(f"      Titre: {titre[:70]}")
                print(f"      URL  : {url[:70]}")
                print()
        else:
            print("   ❌ Aucun résultat trouvé\n")
    
    print("="*70)
    print("✓ Tests terminés!")
    print("="*70)


if __name__ == "__main__":
    main()