from chromadb.config import Settings
from pprint import pprint as pp
import chromadb

chroma_client = chromadb.PersistentClient(path="chromadb")
collection = chroma_client.get_or_create_collection(name="knowledge_base")


print('KB presently has %s entries' % collection.count())
print('\n\nBelow are the top 10 entries:')
results = collection.peek()
pp(results)
