from elasticsearch import Elasticsearch

# Connect to Elasticsearch
es = Elasticsearch()

def search_products(query):
    results = es.search(index="products", body={"query": {"match": {"name": query}}})
    return results["hits"]["hits"]

# Example usage
search_results = search_products("laptop")
print(search_results)