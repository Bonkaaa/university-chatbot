from typing import List

from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field

from .model import get_llm
from .templates import answer_generation_prompt

# def generate_answer(query: str, retrieved_docs: list[str], llm) -> str:
#     prompt = ChatPromptTemplate.from_template(answer_generation_template)

#     answer_pipeline = (
#         prompt
#         | llm
#         | StrOutputParser()
#     )

#     return answer_pipeline.invoke({
#         "question": query,
#         "retrieved_docs": "\n\n".join(retrieved_docs),
#     })

class GenerateAnswerSchema(BaseModel):
    answer: str = Field(description="The generated answer based on the question and retrieved documents.")

def generate_answer_agent(
    model_name: str,
    temperature: float = 0.2,
) -> ChatOllama:
    llm = get_llm(model_name=model_name, temperature=temperature)
    
    answer_agent = answer_generation_prompt | llm.with_structured_output(GenerateAnswerSchema)

    return answer_agent
