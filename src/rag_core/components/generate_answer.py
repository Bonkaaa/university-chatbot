from typing import List, Dict, Any

from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field

from .model import get_llm
from .templates import answer_generation_prompt

class GenerateAnswerSchema(BaseModel):
    answer: str= Field(description="The generated answer to the user's question based on the retrieved documents."),
    confidence: float = Field(description="The confidence score of the generated answer, between 0 and 1.")
    follow_up_question: List[str] = Field(description="A list of follow-up questions that the user might ask based on the generated answer.")
    intent: str = Field(description="The intent of the user's question, categorized into predefined categories such as 'admission', 'course_registration', 'scholarship', etc.")


def generate_answer_agent(
    model_name: str,
    temperature: float = 0.2,
) -> ChatOllama:
    llm = get_llm(model_name=model_name, temperature=temperature)
    
    answer_agent = answer_generation_prompt | llm.with_structured_output(GenerateAnswerSchema)

    return answer_agent
