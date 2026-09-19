import os
import pickle
import re

import faiss
import ollama
import numpy as np

from dotenv import load_dotenv
from groq import Groq


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# CONFIGURATION
# ============================================================

EMBEDDING_MODEL = "nomic-embed-text"

LLM_MODEL = "openai/gpt-oss-20b"

TOP_K = 3

GROQ_API_KEY = os.getenv("GROQ_API_KEY")


if not GROQ_API_KEY:
    raise ValueError(
        "GROQ_API_KEY is not set in .env"
    )


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)


VECTORSTORE_DIR = os.path.join(
    BASE_DIR,
    "data",
    "rag",
    "vectorstore"
)


INDEX_PATH = os.path.join(
    VECTORSTORE_DIR,
    "vectors.index"
)


CHUNKS_PATH = os.path.join(
    VECTORSTORE_DIR,
    "chunks.pkl"
)


# ============================================================
# GROQ CLIENT
# ============================================================

groq_client = Groq(
    api_key=GROQ_API_KEY
)


# ============================================================
# LOAD FAISS INDEX
# ============================================================

index = faiss.read_index(
    INDEX_PATH
)


# ============================================================
# LOAD CHUNKS
# ============================================================

with open(
    CHUNKS_PATH,
    "rb"
) as f:

    chunks = pickle.load(f)


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
# RETRIEVE RELEVANT CHUNKS
# ============================================================

def retrieve_chunks(
    question,
    top_k=TOP_K
):

    query_embedding = create_embedding(
        question
    )

    query_vector = np.array(
        [query_embedding],
        dtype="float32"
    )

    distances, indices = index.search(
        query_vector,
        top_k
    )

    results = []

    for distance, idx in zip(
        distances[0],
        indices[0]
    ):

        if idx < 0 or idx >= len(chunks):
            continue

        chunk = chunks[idx]

        results.append(
            {
                "text": chunk["text"],
                "source": chunk["source"],
                "chunk_id": chunk.get("chunk_id"),
                "distance": float(distance)
            }
        )

    return results


# ============================================================
# BUILD CONTEXT
# ============================================================

def build_context(results):

    context_parts = []

    for result in results:

        context_parts.append(
            f"Source: {result['source']}\n"
            f"Content:\n{result['text']}"
        )

    return "\n\n---\n\n".join(
        context_parts
    )


# ============================================================
# REMOVE THINKING FROM MODEL OUTPUT
# ============================================================

def clean_llm_answer(answer):

    if not answer:
        return ""

    answer = answer.strip()

    # --------------------------------------------------------
    # Remove complete <think>...</think> blocks
    # --------------------------------------------------------

    answer = re.sub(
        r"<think>.*?</think>",
        "",
        answer,
        flags=re.DOTALL | re.IGNORECASE
    )

    # --------------------------------------------------------
    # Remove incomplete <think> block
    # --------------------------------------------------------

    if "<think>" in answer.lower():

        answer = re.split(
            r"<think>",
            answer,
            maxsplit=1,
            flags=re.IGNORECASE
        )[0]

    # --------------------------------------------------------
    # Remove leftover </think>
    # --------------------------------------------------------

    answer = re.sub(
        r"</think>",
        "",
        answer,
        flags=re.IGNORECASE
    )

    return answer.strip()


# ============================================================
# GENERATE ANSWER
# ============================================================

def generate_answer(
    question,
    context
):

    system_prompt = """
You are a Turf Booking Assistant.

Answer the user's question ONLY using the
provided facility knowledge base context.

IMPORTANT RULES:

1. Use ONLY information present in the context.
2. Do NOT use outside knowledge.
3. Do NOT invent information.
4. If the answer is not present in the context,
   say exactly:

I could not find this information in the facility knowledge base.

5. Answer using short bullet points.
6. Do not write long paragraphs.
7. Do not explain your reasoning.
8. Do not output thinking.
9. Do not output <think> tags.
10. Return ONLY the final answer.
11. Do not perform bookings.
12. Do not check availability.
13. Do not calculate booking prices.
14. Do not cancel bookings.
15. Do not reschedule bookings.
"""

    user_prompt = f"""
Knowledge Base Context:

{context}

User Question:

{question}

Answer ONLY from the knowledge base.

Return only the final answer.
"""


    response = groq_client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        temperature=0,
        max_tokens=500,
        reasoning_effort="low"
    )


    answer = response.choices[0].message.content

    answer = clean_llm_answer(
        answer
    )

    return answer


# ============================================================
# ASK QUESTION
# ============================================================

def ask_question(question):

    results = retrieve_chunks(
        question
    )


    if not results:

        return {
            "answer": (
                "I could not find this information "
                "in the facility knowledge base."
            ),
            "sources": []
        }


    context = build_context(
        results
    )


    answer = generate_answer(
        question,
        context
    )


    # --------------------------------------------------------
    # Collect retrieved sources
    # --------------------------------------------------------

    sources = []

    for result in results:

        source = result["source"]

        if source not in sources:

            sources.append(
                source
            )


    return {
        "answer": answer,
        "sources": sources
    }


# ============================================================
# TERMINAL TEST
# ============================================================

def main():

    print("=" * 60)
    print("TURF BOOKING RAG")
    print("=" * 60)

    print()

    print("RAG system ready.")

    print(
        "Type 'exit' to quit."
    )

    print()


    while True:

        question = input(
            "You: "
        ).strip()


        if question.lower() == "exit":

            print(
                "Goodbye!"
            )

            break


        if not question:

            continue


        try:

            result = ask_question(
                question
            )


            print()

            print("Assistant:")

            print()

            print(
                result["answer"]
            )


            print()

            print("Sources:")

            for source in result["sources"]:

                print(
                    f"- {source}"
                )

            print()


        except Exception as e:

            print()

            print(
                f"Error: {e}"
            )

            print()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()