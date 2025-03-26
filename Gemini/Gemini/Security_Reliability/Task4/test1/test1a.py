from elasticsearch_dsl import Search, Q
from elasticsearch import Elasticsearch

es = Elasticsearch()

class Product(Document):
    id = Field(type='integer')
    name = Field(type='text')
    description = Field(type='text')
    price = Field(type='integer')

    class Index:
        name = 'products'

def search_products(query):
    s = Search(using=es, index="products")
    s = s.query(Q("match", name=query) | Q("match", description=query))
    s = s.sort('-_score')  # Sort by Elasticsearch's relevance score
    return s.execute()

# Example usage
results = search_products("blue jeans")
for hit in results:
    print(hit.name, hit.price)