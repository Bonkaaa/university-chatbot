from typing import List

from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field

from .model import get_llm
from .templates import multi_query_prompt



class MultiQuerySchema(BaseModel):
    queries: List[str] = Field(description="List of sub-queries generated from the main query.")


def get_multi_query_agent(
    model_name: str,
    temperature: float = 0.2,
) -> ChatOllama:
    llm = get_llm(model_name=model_name, temperature=temperature)
    
    multi_query_agent = multi_query_prompt | llm.with_structured_output(MultiQuerySchema)

    return multi_query_agent