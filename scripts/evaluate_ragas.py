"""
Evaluate the running RAG chatbot with RAGAS metrics.

Usage:
  python scripts/evaluate_ragas.py \
    --dataset data/eval/ragas_eval_dataset.json \
    --api-base http://127.0.0.1:8000
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import statistics
from typing import Any, Dict, List

import requests
from dotenv import load_dotenv


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run RAGAS evaluation against the FastAPI /chat endpoint")
    parser.add_argument(
        "--dataset",
        default="data/eval/ragas_eval_dataset.json",
        help="Path to evaluation dataset JSON file",
    )
    parser.add_argument(
        "--api-base",
        default="http://127.0.0.1:8000",
        help="Base URL of running backend",
    )
    parser.add_argument(
        "--chat-endpoint",
        default="/chat",
        help="Chat endpoint path",
    )
    parser.add_argument(
        "--model",
        default="gpt-4o-mini",
        help="OpenAI model for RAGAS judge LLM",
    )
    parser.add_argument(
        "--output-dir",
        default="data/eval/results",
        help="Directory to write result artifacts",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=60.0,
        help="HTTP timeout for each chat request in seconds",
    )
    return parser.parse_args()


def load_eval_samples(dataset_path: str) -> List[Dict[str, Any]]:
    with open(dataset_path, "r", encoding="utf-8") as file_handle:
        data = json.load(file_handle)

    if not isinstance(data, list) or not data:
        raise ValueError("Dataset must be a non-empty JSON array")

    required = {"question", "ground_truth"}
    for index, item in enumerate(data):
        if not required.issubset(item.keys()):
            missing = required - set(item.keys())
            raise ValueError(f"Dataset item #{index} missing required keys: {sorted(missing)}")

    return data


def call_chat_api(
    api_base: str,
    chat_endpoint: str,
    question: str,
    user_id: str,
    thread_id: str,
    timeout: float,
) -> Dict[str, Any]:
    payload = {
        "message": question,
        "user_id": user_id,
        "thread_id": thread_id,
        "return_tts": False,
    }

    response = requests.post(
        f"{api_base.rstrip('/')}{chat_endpoint}",
        json=payload,
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()


def extract_contexts(docs: Any) -> List[str]:
    contexts: List[str] = []
    if not isinstance(docs, list):
        return contexts

    for doc in docs:
        if not isinstance(doc, dict):
            continue

        answer = doc.get("answer")
        content = doc.get("content")
        question = doc.get("question")

        if answer and question:
            contexts.append(f"Q: {question}\nA: {answer}")
        elif answer:
            contexts.append(str(answer))
        elif content:
            contexts.append(str(content))

    return contexts


def build_ragas_dataset(
    samples: List[Dict[str, Any]],
    api_base: str,
    chat_endpoint: str,
    timeout: float,
) -> Any:
    from datasets import Dataset

    questions: List[str] = []
    answers: List[str] = []
    contexts: List[List[str]] = []
    ground_truths: List[str] = []

    for index, sample in enumerate(samples, start=1):
        question = sample["question"]
        ground_truth = sample["ground_truth"]
        user_id = sample.get("user_id", "ragas_eval_user")
        thread_id = sample.get("thread_id", f"ragas_eval_thread_{index}")

        chat_data = call_chat_api(
            api_base=api_base,
            chat_endpoint=chat_endpoint,
            question=question,
            user_id=user_id,
            thread_id=thread_id,
            timeout=timeout,
        )

        questions.append(question)
        answers.append(chat_data.get("response", ""))
        contexts.append(extract_contexts(chat_data.get("docs", [])))
        ground_truths.append(ground_truth)

    return Dataset.from_dict(
        {
            "question": questions,
            "answer": answers,
            "contexts": contexts,
            "ground_truth": ground_truths,
        }
    )


def build_ragas_dependencies(model_name: str):
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        raise RuntimeError("OPENAI_API_KEY is required for RAGAS judge metrics")

    from langchain_openai import ChatOpenAI, OpenAIEmbeddings

    llm = ChatOpenAI(model=model_name, temperature=0)
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    try:
        from ragas.llms import LangchainLLMWrapper
        from ragas.embeddings import LangchainEmbeddingsWrapper

        llm = LangchainLLMWrapper(llm)
        embeddings = LangchainEmbeddingsWrapper(embeddings)
    except Exception:
        pass

    return llm, embeddings


def resolve_metrics():
    from ragas.metrics import faithfulness, context_precision, context_recall

    try:
        from ragas.metrics import answer_relevancy

        answer_metric = answer_relevancy
    except Exception:
        from ragas.metrics import answer_relevance

        answer_metric = answer_relevance

    return [faithfulness, answer_metric, context_precision, context_recall]


def run_ragas_eval(dataset: Any, model_name: str) -> Dict[str, Any]:
    from ragas import evaluate

    metrics = resolve_metrics()
    llm, embeddings = build_ragas_dependencies(model_name=model_name)

    result = evaluate(dataset=dataset, metrics=metrics, llm=llm, embeddings=embeddings)
    return result


def to_serializable_results(result: Any) -> Dict[str, Any]:
    if hasattr(result, "to_pandas"):
        dataframe = result.to_pandas()
        row_dicts = dataframe.to_dict(orient="records")
    else:
        row_dicts = [dict(result)]

    keys: List[str] = []
    for row in row_dicts:
        keys.extend([key for key, value in row.items() if isinstance(value, (int, float))])

    numeric_keys = sorted(set(keys))
    summary: Dict[str, float] = {}

    for key in numeric_keys:
        values = [float(row[key]) for row in row_dicts if isinstance(row.get(key), (int, float))]
        if values:
            summary[key] = statistics.mean(values)

    return {
        "summary": summary,
        "rows": row_dicts,
    }


def save_outputs(output_dir: str, dataset: Any, results: Dict[str, Any]) -> None:
    output_path = pathlib.Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    used_dataset_file = output_path / "ragas_used_dataset.json"
    with open(used_dataset_file, "w", encoding="utf-8") as file_handle:
        json.dump(dataset.to_dict(), file_handle, indent=2, ensure_ascii=False)

    results_file = output_path / "ragas_results.json"
    with open(results_file, "w", encoding="utf-8") as file_handle:
        json.dump(results, file_handle, indent=2, ensure_ascii=False)


def main() -> None:
    load_dotenv()
    args = parse_args()

    samples = load_eval_samples(args.dataset)
    ragas_dataset = build_ragas_dataset(
        samples=samples,
        api_base=args.api_base,
        chat_endpoint=args.chat_endpoint,
        timeout=args.timeout,
    )

    ragas_result = run_ragas_eval(dataset=ragas_dataset, model_name=args.model)
    serialized = to_serializable_results(ragas_result)
    save_outputs(args.output_dir, ragas_dataset, serialized)

    print("✅ RAGAS evaluation complete")
    print("Summary metrics:")
    for metric, value in serialized["summary"].items():
        print(f"- {metric}: {value:.4f}")
    print(f"Artifacts written to: {args.output_dir}")


if __name__ == "__main__":
    main()
