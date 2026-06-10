import asyncio
import json
from pathlib import Path

from src.agent.graph import RAGAgent
from src.config import MODEL_NAME, EMBED_MODEL_NAME, CONVERSATION_DB_DIR, RAW_DOCS_DIR, RAW_DATASET_PATH, EVAL_DATASET_PATH

agent = RAGAgent(
    conversation_db_path=CONVERSATION_DB_DIR,
    path_to_docs=RAW_DOCS_DIR,
    embed_model=EMBED_MODEL_NAME,
    main_model=MODEL_NAME,
)

async def collect_answer_and_retrieved_contexts(question: str, thread_id: str) -> tuple[str, list[str]]:
    full_text = ""
    final_answer = None
    retrieved_contexts = []

    async for event in agent.astream_chat(question, thread_id):
        if event.get("type") == "token":
            token = event.get("content", "")
            if token:
                full_text += token
        elif event.get("type") == "final":
            final_answer = event.get("final_answer")
            retrieved_contexts = event.get("retrieved_contexts", [])

    if isinstance(final_answer, dict):
        return final_answer.get("answer", full_text) or full_text, retrieved_contexts

    return full_text, retrieved_contexts

async def evaluate_on_dataset(dataset, limit=10):
    results = []

    for idx, item in enumerate(dataset[:limit]):
        question = item["question"]
        ground_truth = item["ground_truth"]

        generated_answer, retrieved_contexts = await collect_answer_and_retrieved_contexts(question=question, thread_id=f"eval-{idx}")

        results.append({
            "question": question,
            "answer": generated_answer,
            "contexts": retrieved_contexts,
            "ground_truth": ground_truth,
        })

    return results

def load_dataset(dataset_path: Path):
    with open(dataset_path, "r", encoding="utf-8") as f:
        return json.load(f)

if __name__ == "__main__":
    dataset_path = Path(RAW_DATASET_PATH)
    output_path = Path(EVAL_DATASET_PATH)

    dataset = load_dataset(dataset_path)
    print(f"Loaded {len(dataset)} items from the dataset at {dataset_path}")
    results = asyncio.run(evaluate_on_dataset(dataset, limit=10))

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(results)} evaluation results to {output_path}")