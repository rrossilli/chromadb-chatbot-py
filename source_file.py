from chromadb.config import Settings
from utils import save_file, source_document
from uuid import uuid4
from time import time
import chromadb

from consts import (
    CHROMADB_COLLECTION,
    PATH_CHROMADB,
    PATH_DB_LOGS,
)


# instantiate ChromaDB
chroma_client = chromadb.PersistentClient(path=PATH_CHROMADB)
collection = chroma_client.get_or_create_collection(
    name=CHROMADB_COLLECTION)


if __name__ == '__main__':
    filepath = input(
        "Please provide the path to the file you want to source into the KB: ")
    document_content = source_document(filepath)

    # Check if the document content is already in the KB
    results = collection.query(query_texts=[document_content], n_results=1)
    if results['documents'] and document_content in results['documents'][0][0]:
        print("This document content is already present in the KB.")
    else:
        # Add the document content to the KB
        new_id = str(uuid4())
        collection.add(documents=[document_content], ids=[new_id])
        save_file(PATH_DB_LOGS + '/log_%s_add.txt' %
                  time(), 'Added document %s:\n%s' % (new_id, document_content))
        print(f"Document content saved successfully to KB with ID: {new_id}")
