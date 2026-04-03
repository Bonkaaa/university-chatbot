from typing import List

from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field
from .templates import multi_query_prompt


def get_llm(
    model_name: str,
    temperature: float = 0.2,
) -> ChatOllama:
    return ChatOllama(
        model=model_name,
        temperature=temperature,
        validate_model_on_init=True,
    )
