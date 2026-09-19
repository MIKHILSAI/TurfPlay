from backend.agents.knowledge.knowledge_crew import process_knowledge_request
from backend.rag.rag_service import ask_question


# ============================================================
# KNOWLEDGE PROCESS
# ============================================================

def process_knowledge_request_with_details(user_message):
    """
    Process a knowledge request.

    Flow:

    User Question
        ↓
    Knowledge Agent
        ↓
    Extract Question
        ↓
    FAISS RAG
        ↓
    Groq
        ↓
    Final Answer
    """

    # --------------------------------------------------------
    # Run Knowledge Agent
    # --------------------------------------------------------

    agent_result = process_knowledge_request(
        user_message
    )

    print()
    print("Knowledge Agent Result:")
    print("-" * 60)
    print(agent_result)
    print("-" * 60)

    # --------------------------------------------------------
    # Extract the question
    # --------------------------------------------------------

    question = user_message

    for line in agent_result.splitlines():

        line = line.strip()

        if line.lower().startswith("question:"):

            question = line.split(
                ":", 1
            )[1].strip()

            break

    # --------------------------------------------------------
    # Send question to existing RAG
    # --------------------------------------------------------

    result = ask_question(question)

    return {
        "success": True,
        "question": question,
        "answer": result["answer"],
        "sources": result["sources"]
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("TURF BOOKING - KNOWLEDGE PROCESS")
    print("=" * 60)

    user_message = input("You: ").strip()

    if user_message:

        try:

            result = process_knowledge_request_with_details(
                user_message
            )

            print()
            print("Final Knowledge Answer:")
            print("-" * 60)
            print(result["answer"])
            print("-" * 60)

            print()
            print("Sources:")

            for source in result["sources"]:
                print(f"- {source}")

        except Exception as e:

            print()
            print(f"Error: {e}")