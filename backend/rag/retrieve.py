import os
import pickle

import faiss
import numpy as np
import ollama


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

VECTORSTORE_DIR = os.path.join(
    BASE_DIR,
    "data",
    "rag",
    "vectorstore"
)

INDEX_FILE = os.path.join(
    VECTORSTORE_DIR,
    "vectors.index"
)

CHUNKS_FILE = os.path.join(
    VECTORSTORE_DIR,
    "chunks.pkl"
)


# ============================================================
# MODEL SETTINGS
# ============================================================

EMBEDDING_MODEL = "nomic-embed-text"

TOP_K = 3


# ============================================================
# LOAD VECTOR STORE
# ============================================================

print("Loading FAISS vector store...")

index = faiss.read_index(
    INDEX_FILE
)

with open(
    CHUNKS_FILE,
    "rb"
) as file:

    chunks = pickle.load(file)

print(
    f"Loaded {index.ntotal} vectors."
)


# ============================================================
# CREATE QUERY EMBEDDING
# ============================================================

def create_query_embedding(query):

    response = ollama.embeddings(
        model=EMBEDDING_MODEL,
        prompt=query
    )

    embedding = np.array(
        [response["embedding"]],
        dtype="float32"
    )

    return embedding


# ============================================================
# RETRIEVE RELEVANT CHUNKS
# ============================================================

def retrieve(query, top_k=TOP_K):

    query_embedding = create_query_embedding(
        query
    )

    distances, indices = index.search(
        query_embedding,
        top_k
    )

    results = []

    for distance, idx in zip(
        distances[0],
        indices[0]
    ):

        if idx == -1:
            continue

        chunk = chunks[idx]

        results.append({
            "source": chunk["source"],
            "chunk_index": chunk["chunk_index"],
            "text": chunk["text"],
            "distance": float(distance)
        })

    return results


# ============================================================
# DISPLAY RESULTS
# ============================================================

def display_results(query):

    print("\n" + "=" * 60)
    print(f"QUESTION: {query}")
    print("=" * 60)

    results = retrieve(query)

    for number, result in enumerate(
        results,
        start=1
    ):

        print(
            f"\n--- RESULT {number} ---"
        )

        print(
            f"Source: {result['source']}"
        )

        print(
            f"Chunk: {result['chunk_index']}"
        )

        print(
            f"Distance: {result['distance']:.4f}"
        )

        print(
            f"\n{result['text']}"
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print("\nRAG retrieval system ready.")

    print(
        "Ask a question about the turf booking policies."
    )

    print(
        "Type 'exit' to quit."
    )

    while True:

        query = input("\nYou: ").strip()

        if query.lower() == "exit":

            print("Exiting...")

            break

        if not query:

            continue

        display_results(
            query
        )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()