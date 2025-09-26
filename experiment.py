import os
from dotenv import load_dotenv
load_dotenv()
import re
from pandas import DataFrame
# Local Libs
from schemas.sql_query import SqlQuery
from src.bq import GcpBigQuery
from prompts.prompts import SQL_REACT_PROMPT_WITH_FORMAT_INSTRUCTIONS, CIMIE_SQL_SYSTEM_PROMPT, CIMIE_SQL_HUMAN_PROMPT
# Langchain
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_google_vertexai import ChatVertexAI
from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain.agents import AgentType
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers.pydantic import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda
# SQL Alchemy
from sqlalchemy import create_engine
from src.sql import execute_query

def clean_output(output: str) -> str:
    """
    Cleans LLM output by removing code block wrappers like ```json, ```sql, or ````.
    Works for any number of backticks >= 3.
    """
    # Remove code block start with optional language hint (```json, ```sql, ````)
    cleaned = re.sub(r"^`{3,}\w*\s*", "", output)   # remove leading ```json / ```` etc.
    cleaned = re.sub(r"`{3,}\s*$", "", cleaned)      # remove trailing ``` or ```` etc.
    return cleaned.strip()


def safe_parse(output: str, output_parser, retries: int = 2):
    last_exception = None
    for _ in range(retries):
        try:
            return output_parser.parse(output)
        except Exception as e:
            last_exception = e
            output = clean_output(output)
    raise last_exception

def sql_agent(prompt: str, db: SQLDatabase) -> str:
    """An agent to perform text2sql"""
    # Initialize LLM
    llm = ChatVertexAI(
        temperature=0, 
        model="gemini-2.5-flash-lite"
    )
    
    # Create SQL AgentExecutor 
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    toolkit.get_tools()
    
    output_parser = PydanticOutputParser(pydantic_object=SqlQuery)
    
    react_prompt_with_format_instruction = PromptTemplate(
        template=SQL_REACT_PROMPT_WITH_FORMAT_INSTRUCTIONS,
        input_variables=["input", "agent_scratchpad", "tool_names"]
    ).partial(format_instructions=output_parser.get_format_instructions())
    
    agent_executor = create_sql_agent(
        llm=llm,
        toolkit=toolkit,
        agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        prompt=react_prompt_with_format_instruction,
        top_k=1000,
    )
    
    extract_output = RunnableLambda(lambda x: x["output"])
    parse_output = RunnableLambda(lambda x: safe_parse(x, output_parser))

    try:
        # Chaining
        chain = ( {"input": lambda x: x["input"]} | agent_executor | extract_output | parse_output)
        response = chain.invoke({
            "input": prompt
        })
        return response
    except Exception as e:
        return e
    

def response_agent(query_result: str) -> str:
    """An agent that helps to answer users' questions on their data within their databases"""
    
    prompt_template = ChatPromptTemplate.from_messages(
        [
            ("system", CIMIE_SQL_SYSTEM_PROMPT),
            ("human", CIMIE_SQL_HUMAN_PROMPT)
        ]
    )
    
    # Initialize LLM
    llm = ChatVertexAI(
        temperature=0, 
        model="gemini-2.5-flash-lite"
    )
    
    extract_output = RunnableLambda(lambda x: x.content)
    
    chain = ( 
             {
              "query_result": lambda x: x["query_result"]
             } 
             | prompt_template
             | llm 
             | extract_output 
            )
    
    try:
        # Chaining
        chain = ( 
                {
                "query_result": lambda x: x["query_result"]
                } 
                | prompt_template
                | llm 
                | extract_output 
                )
        response = chain.invoke({
            "query_result": query_result
            
        })
        return response
    except Exception as e:
        return e

if __name__ == "__main__":
    
    # Big Query Environments -------
    project_id: str = os.getenv("PROJECT_ID")
    location: str = os.getenv("LOCATION")
    dataset_id: str = os.getenv("DATASET_ID")
    table_name: str = "mrodata"
    # ------------------------------

    # Initiate database connection -
    big_query = GcpBigQuery(
        project_id=project_id,
        location=location,
        dataset_id=dataset_id
    )
    bq_client = big_query.bq_client()
    table_uri: str = f"bigquery://{project_id}/{dataset_id}"
    bqengine = create_engine(table_uri)
    db = SQLDatabase(bqengine)
    # ------------------------------
     
    
    while True:
        prompt: str = str(input("What do you wanna know?: "))
        if prompt == "exit":
            print("\n...Exiting session\n")
            break
        
        # 1. Sql_agent considers an user question and returns a query (check syntax correctness + ignore sql injection)
        sql_response: SqlQuery = sql_agent(prompt=prompt, db=db)
        
        context: str = ""
        # In case of ignoring sql injection
        if len(sql_response.query_syntax) != 0:
            # 2. **[Optional only for Big Query]** add dataset id in front of the table name for a valid syntax
            valid_sql_response: str = sql_response.query_syntax.replace(table_name, f"{dataset_id}.{table_name}")
            
            # 3. Execute sql query
            retrived_data: DataFrame = execute_query(bq_client, valid_sql_response)
            context = retrived_data.to_markdown()
        else:
            context = sql_response.answer
        
        # 4. Send data from db to the response agent to get an answer as a natural language 
        answer: str = response_agent(context)
        print("\n" + answer + "\n")