import os
import json
from pathlib import Path
import time
from datasets import Dataset
from langchain_ollama import OllamaEmbeddings
from ragas import evaluate
from ragas.run_config import RunConfig
from .utils import setup_logger
import pandas as pd
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)

logger = setup_logger("eval.log", "eval")

from src.config import EVAL_DATASET_PATH, OUTPUT_EVAL_RESULTS_PATH_CSV, OUTPUT_EVAL_RESULTS_PATH_JSON
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file


def _validate_dataset(dataset: list[dict]) -> None:
    required_fields = {"question", "answer", "contexts", "ground_truth"}
    for index, item in enumerate(dataset):
        missing = required_fields - set(item.keys())
        if missing:
            raise ValueError(
                f"Dataset item {index} is missing required fields: {sorted(missing)}. "
                "Run the answer collection step first so each record includes an 'answer' field."
            )


def _require_google_api_key() -> str:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GOOGLE_API_KEY is not set. Add it to your environment or .env file before running eval."
        )
    return api_key

def eval(
    dataset_path: str,
    output_path: str,
    model_judge_name: str = "gemma-4-31b-it",
    model_embed_judge_name: str = "gemini-embedding-001",
):
    _require_google_api_key()

    # Set custom run config
    custom_run_config = RunConfig(
        timeout=1800,
        max_retries=3,
        max_workers=2,
        max_wait=60
    )

    # Set metric strictness levels to fix the issue between LLM and RAGAS
    answer_relevancy.strictness = 1

    judge_llm = ChatGoogleGenerativeAI(
        model=model_judge_name,
        temperature=0,
    )

    judge_embeddings = OllamaEmbeddings(
        model=model_embed_judge_name,
    )

    with open(dataset_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    if not isinstance(dataset, list):
        raise ValueError("Expected the evaluation dataset to be a JSON list of records.")

    _validate_dataset(dataset)

    dataset = Dataset.from_list(dataset)

    logger.info(f"Loaded dataset with {len(dataset)} records for evaluation.")

    logger.info("Starting evaluation with the following configuration:")

    all_results = []

    for i in range(len(dataset)):
        logger.info(f"Evaluating record {i+1}/{len(dataset)}: {dataset[i]['question']}")

        single_row_dataset = dataset.select([i])

        start_time = time.perf_counter()
        try:
            result = evaluate(
                dataset=single_row_dataset,
                llm=judge_llm,
                embeddings=judge_embeddings,
                metrics=[
                    faithfulness,
                    answer_relevancy,
                    context_precision,
                    context_recall,
                ],
                run_config=custom_run_config,
                raise_exceptions=False,  # Don't raise exceptions to allow evaluation to continue
            )

            all_results.append(result.to_pandas())
            logger.info(f"Evaluation for record {i+1} completed successfully: {result}")
        except Exception as e:
            logger.error(f"Error evaluating record {i+1}: {e}")
            all_results.append({
                "question": dataset[i]["question"],
                "error": str(e),
            })
        end_time = time.perf_counter()
        logger.info(f"Time taken for record {i+1}: {end_time - start_time:.2f} seconds")
        
        if i < len(dataset) - 1:
            logger.info("Waiting for 15 seconds before evaluating the next record to avoid rate limits.")
            time.sleep(15)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    if all_results:
        final_df = pd.concat(all_results, ignore_index=True)
        final_df.to_csv(output_path, index=False)
        logger.info(f"Saved evaluation results to {output_path}")
    else:
        logger.warning("No evaluation results to save.")
    # results = evaluate(
    #     dataset=dataset,
    #     llm=judge_llm,
    #     embeddings=judge_embeddings,
    #     metrics=[
    #         faithfulness,
    #         answer_relevancy,
    #         context_precision,
    #         context_recall,
    #     ],
    #     run_config=custom_run_config,
    #     raise_exceptions=True,
    # )

    # logger.info("Evaluation completed. Here are the results:")
    # logger.info(results)

    # # Save results to output path
    # Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    # df_results = results.to_pandas()
    # df_results.to_csv(output_path, index=False)
    # print(f"Saved evaluation results to {output_path}")


if __name__ == "__main__":

    time.start = time.perf_counter()

    dataset_path = EVAL_DATASET_PATH
    output_path = OUTPUT_EVAL_RESULTS_PATH_CSV

    eval(
        dataset_path=dataset_path,
        output_path=output_path,
        model_judge_name="gemma-4-31b-it",
        model_embed_judge_name="hf.co/CompendiumLabs/bge-m3-gguf:latest",
    )

    time.end = time.perf_counter()
    logger.info(f"Total evaluation time: {time.end - time.start:.2f} seconds")
