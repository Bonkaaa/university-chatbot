from typing import Any

from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

from .model import get_llm
from .templates import answer_generation_prompt

class GenerateAnswerSchema(BaseModel):
    answer: str = Field(description="The generated answer to the user's question based on the retrieved documents.")
    confidence: float = Field(description="The confidence score of the generated answer, between 0 and 1.")
    intent: str = Field(description="The intent of the user's question, categorized into predefined categories such as 'admission', 'course_registration', 'scholarship', etc.")


def generate_answer_agent(
    model_name: str,
    temperature: float = 0.2,
) -> Any:
    llm = get_llm(model_name=model_name, temperature=temperature)

    parser = JsonOutputParser(pydantic_object=GenerateAnswerSchema)
    
    answer_agent = answer_generation_prompt | llm | parser

    return answer_agent
