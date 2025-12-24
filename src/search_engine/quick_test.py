from query_processor import QueryProcessor
from ranker import Ranker

# Initialiser
processor = QueryProcessor()
ranker = Ranker()

# Rechercher
query = "Emmanuel Macron président de la république française"
terms = processor.process(query)
results = ranker.rank(terms, top_k=10)

# Afficher
for doc_id, title, url, score in results:
    print(f"[{score:.3f}] {title}")