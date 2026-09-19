import os
import json
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

CHUNKS_FILE = os.path.join(
    BASE_DIR,
    "data",
    "rag",
    "chunks.json"
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

CHUNKS_OUTPUT_FILE = os.path.join(
    VECTORSTORE_DIR,
    "chunks.pkl"
)


# ============================================================
# MODEL
# ============================================================

EMBEDDING_MODEL = "nomic-embed-text"


# ============================================================
# LOAD CHUNKS
# ============================================================

def load_chunks():

    if not os.path.exists(CHUNKS_FILE):

        raise FileNotFoundError(
            f"chunks.json not found:\n{CHUNKS_FILE}"
        )

    with open(
        CHUNKS_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        chunks = json.load(file)

    return chunks


# ============================================================
# CREATE EMBEDDING
# ============================================================

def create_embedding(text):

    response = ollama.embeddings(
        model=EMBEDDING_MODEL,
        prompt=text
    )

    return response["embedding"]


# ============================================================
# CREATE FAISS VECTOR STORE
# ============================================================

def create_vectorstore(chunks):

    os.makedirs(
        VECTORSTORE_DIR,
        exist_ok=True
    )

    embeddings = []

    print("\nCreating embeddings...\n")

    for index, chunk in enumerate(chunks):

        print(
            f"[{index + 1}/{len(chunks)}] "
            f"{chunk['chunk_id']}"
        )

        embedding = create_embedding(
            chunk["text"]
        )

        embeddings.append(
            embedding
        )

    # --------------------------------------------------------
    # Convert embeddings to NumPy
    # --------------------------------------------------------

    embeddings = np.array(
        embeddings,
        dtype="float32"
    )

    # --------------------------------------------------------
    # Create FAISS index
    #
    # IndexFlatL2 = simple exact similarity search
    # --------------------------------------------------------

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatL2(
        dimension
    )

    # --------------------------------------------------------
    # Add embeddings
    # --------------------------------------------------------

    index.add(
        embeddings
    )

    # --------------------------------------------------------
    # Save FAISS index
    # --------------------------------------------------------

    faiss.write_index(
        index,
        INDEX_FILE
    )

    # --------------------------------------------------------
    # Save chunks + metadata
    # --------------------------------------------------------

    with open(
        CHUNKS_OUTPUT_FILE,
        "wb"
    ) as file:

        pickle.dump(
            chunks,
            file
        )

    return index


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("CREATING FAISS VECTOR DATABASE")
    print("=" * 60)

    print(
        f"\nChunks file:"
        f"\n{CHUNKS_FILE}"
    )

    print(
        f"\nVector store:"
        f"\n{VECTORSTORE_DIR}"
    )

    # --------------------------------------------------------
    # Load chunks
    # --------------------------------------------------------

    chunks = load_chunks()

    print(
        f"\nTotal chunks loaded: "
        f"{len(chunks)}"
    )

    # --------------------------------------------------------
    # Create vector store
    # --------------------------------------------------------

    index = create_vectorstore(
        chunks
    )

    # --------------------------------------------------------
    # Result
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("FAISS VECTOR DATABASE CREATED")
    print("=" * 60)

    print(
        f"\nEmbedding dimension: "
        f"{index.d}"
    )

    print(
        f"Vectors stored: "
        f"{index.ntotal}"
    )

    print(
        f"\nFAISS index:"
        f"\n{INDEX_FILE}"
    )

    print(
        f"\nChunk data:"
        f"\n{CHUNKS_OUTPUT_FILE}"
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()