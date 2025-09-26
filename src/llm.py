# Langchain
from langchain_google_vertexai import ChatVertexAI
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
# Type Guide
from langchain_core.language_models import BaseChatModel
from pydantic import BaseModel

def init_agent_model(prompt: str, model_config: dict[str], parser: BaseModel | None) -> BaseChatModel:
    """Initialize an agent model"""
    
    # Initialize llm model
    llm = ChatVertexAI(**model_config)
    
    # If there is a parser then return it with that parser
    if parser:
        parser= JsonOutputParser(pydantic_object=parser)
        prompt= ChatPromptTemplate.from_messages(prompt).partial(format_instructions=parser.get_format_instructions())
    # Else return it as a normal string
    else:
        parser= StrOutputParser()
        prompt= ChatPromptTemplate.from_messages(prompt)
        
    return prompt | llm | parser
        