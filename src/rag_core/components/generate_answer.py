from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field

from .model import get_llm
from .templates import answer_generation_prompt

class GenerateAnswerSchema(BaseModel):
    answer: str = Field(description="The generated answer based on the question and retrieved documents.")

def generate_answer_agent(
    model_name: str,
    temperature: float = 0.2,
) -> ChatOllama:
    llm = get_llm(model_name=model_name, temperature=temperature)
    
    answer_agent = answer_generation_prompt | llm.with_structured_output(GenerateAnswerSchema)

    return answer_agent
