from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

from rag_step1_load import load_documents, split_documents


MODEL_NAME = "BAAI/bge-small-zh-v1.5"
VECTOR_STORE_DIR = "rag_demo/vector_store"
COLLECTION_NAME = "company_documents"


def build_vector_store():
    print("正在读取并切分文档...")
    documents = load_documents()
    chunks = split_documents(documents)

    print("正在加载 Embedding 模型...")
    model = SentenceTransformer(MODEL_NAME)

    texts = [chunk["content"] for chunk in chunks]

    print("正在将文本转换为向量...")
    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=True,
    ).tolist()

    client = chromadb.PersistentClient(path=VECTOR_STORE_DIR)

    # 每次重新构建时，先删除同名旧索引，防止重复写入。
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = client.create_collection(name=COLLECTION_NAME)

    collection.add(
        ids=[f"chunk_{index}" for index in range(len(chunks))],
        documents=texts,
        embeddings=embeddings,
        metadatas=[
            {
                "source": chunk["source"],
                "chunk_id": chunk["chunk_id"],
            }
            for chunk in chunks
        ],
    )

    print("\n向量库构建完成。")
    print(f"文档数：{len(documents)}")
    print(f"文本块数：{len(chunks)}")
    print(f"向量库目录：{VECTOR_STORE_DIR}")


if __name__ == "__main__":
    build_vector_store()