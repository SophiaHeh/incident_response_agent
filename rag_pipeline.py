import chromadb
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader
from langchain_community.embeddings import HuggingFaceEmbeddings

class IncidentKnowledgeBase:
    def __init__(self, persist_directory="./chroma_db"):
        """
        Initialize the ChromaDB RAG pipeline for historical incidents and runbooks.
        """
        self.chroma_client = chromadb.PersistentClient(path=persist_directory)
        
        # We use a fast local embedding model for cosine similarity
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        
        # Get or create the collection with cosine similarity
        self.collection = self.chroma_client.get_or_create_collection(
            name="incident_runbooks",
            metadata={"hnsw:space": "cosine"}
        )
        
    def populate_knowledge_base(self, docs_directory):
        """
        Load runbooks and past incident post-mortems using a sliding window chunking strategy.
        """
        loader = DirectoryLoader(docs_directory, glob="**/*.txt")
        documents = loader.load()
        
        # Sliding-window chunking:
        # We use a chunk size of 500 with an overlap of 100 to ensure context 
        # is not lost at the boundaries of the chunks.
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=100,
            separators=["\n\n", "\n", " ", ""]
        )
        
        chunks = text_splitter.split_documents(documents)
        
        # Prepare data for ChromaDB
        ids = [f"doc_{i}" for i in range(len(chunks))]
        texts = [chunk.page_content for chunk in chunks]
        metadatas = [chunk.metadata for chunk in chunks]
        
        # Only embed and add if we have texts
        if texts:
            embedded_vectors = self.embeddings.embed_documents(texts)
            self.collection.upsert(
                ids=ids,
                documents=texts,
                embeddings=embedded_vectors,
                metadatas=metadatas
            )
            print(f"Upserted {len(chunks)} chunks into ChromaDB.")

    def search_similar_incidents(self, query, n_results=3):
        """
        Query the RAG pipeline to find similar past issues or relevant runbook steps.
        """
        query_embedding = self.embeddings.embed_query(query)
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        retrieved_docs = []
        if results and results['documents']:
            for i in range(len(results['documents'][0])):
                retrieved_docs.append({
                    "content": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "distance": results['distances'][0][i]
                })
                
        return retrieved_docs
