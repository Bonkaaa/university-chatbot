import os
from typing import List

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

def get_llm(
    model_name: str,
    temperature: float = 0.2,
) -> ChatOpenAI:
    return ChatOpenAI(
        model=model_name,
        temperature=temperature,
        base_url="https://openrouter.ai/api/v1",
        max_tokens=4096,
        api_key=os.environ.get("OPENROUTER_API_KEY"),
        max_retries=2
    )
