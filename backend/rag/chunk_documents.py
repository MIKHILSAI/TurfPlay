import os
import json


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

KNOWLEDGE_BASE_DIR = os.path.join(
    BASE_DIR,
    "data",
    "knowledge_base"
)

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "data",
    "rag"
)

OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "chunks.json"
)


# ============================================================
# CHUNK SETTINGS
# ============================================================

CHUNK_SIZE = 500
CHUNK_OVERLAP = 100


# ============================================================
# READ DOCUMENT
# ============================================================

def read_document(file_path):

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as file:

        return file.read()


# ============================================================
# CREATE CHUNKS
# ============================================================

def create_chunks(text):

    text = text.strip()

    if not text:
        return []

    chunks = []

    start = 0

    while start < len(text):

        end = start + CHUNK_SIZE

        chunk = text[start:end]

        chunk = chunk.strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        start = end - CHUNK_OVERLAP

    return chunks


# ============================================================
# LOAD ALL DOCUMENTS
# ============================================================

def load_documents():

    documents = []

    if not os.path.exists(KNOWLEDGE_BASE_DIR):

        raise FileNotFoundError(
            f"Knowledge base folder not found:\n"
            f"{KNOWLEDGE_BASE_DIR}"
        )

    for filename in sorted(os.listdir(KNOWLEDGE_BASE_DIR)):

        if not filename.lower().endswith(".txt"):
            continue

        file_path = os.path.join(
            KNOWLEDGE_BASE_DIR,
            filename
        )

        text = read_document(file_path)

        chunks = create_chunks(text)

        for index, chunk in enumerate(chunks):

            documents.append({
                "chunk_id": f"{filename}_{index}",
                "source": filename,
                "chunk_index": index,
                "text": chunk
            })

        print(
            f"{filename}: "
            f"{len(chunks)} chunks"
        )

    return documents


# ============================================================
# SAVE CHUNKS
# ============================================================

def save_chunks(chunks):

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            chunks,
            file,
            indent=4,
            ensure_ascii=False
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("RAG DOCUMENT CHUNKING")
    print("=" * 60)

    print(
        f"\nKnowledge base:\n"
        f"{KNOWLEDGE_BASE_DIR}"
    )

    chunks = load_documents()

    save_chunks(chunks)

    print("\n" + "=" * 60)
    print("CHUNKING COMPLETED")
    print("=" * 60)

    print(
        f"\nTotal chunks: {len(chunks)}"
    )

    print(
        f"Saved to:\n"
        f"{OUTPUT_FILE}"
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()