import chromadb
from sentence_transformers import SentenceTransformer


MODEL_NAME = "BAAI/bge-small-zh-v1.5"
VECTOR_STORE_DIR = "rag_demo/vector_store"
COLLECTION_NAME = "company_documents"

embedding_model = None
collection = None


def get_embedding_model():
    global embedding_model

    if embedding_model is None:
        print("首次加载 Embedding 模型...")
        embedding_model = SentenceTransformer(
    MODEL_NAME,
    local_files_only=True,
)

    return embedding_model


def get_collection():
    global collection

    if collection is None:
        print("首次连接本地向量库...")
        client = chromadb.PersistentClient(path=VECTOR_STORE_DIR)
        collection = client.get_collection(COLLECTION_NAME)

    return collection


def search_documents(question, top_k=2):
    model = get_embedding_model()
    vector_collection = get_collection()

    question_embedding = model.encode(
        question,
        normalize_embeddings=True,
    ).tolist()

    results = vector_collection.query(
        query_embeddings=[question_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    return results