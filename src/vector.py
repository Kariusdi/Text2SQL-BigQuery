from langchain_google_genai import GoogleGenerativeAIEmbeddings
import duckdb
from langchain_community.vectorstores import DuckDB
from langchain_community.document_loaders import DataFrameLoader
import pandas as pd
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config.gcp import initialize_gcs_client
initialize_gcs_client()
from dotenv import load_dotenv
load_dotenv()
from utils.const import EMBEDDING_MODEL

def embeddings():
    # 1. Load your CSV with all column descriptions and sample values
    des_df = pd.read_csv('data/mro_db_column_description.csv')
    print(des_df.head())

    # 2. Make sure your CSV has a 'content' column, or create it
    if 'content' not in des_df.columns:
        def create_content(x):
            return f"""table_name : {x['table_name']}
    column_name : {x['column_name']}
    description : {x['description']}
    sample_values : {x['sample_values']}
    """

        des_df['content'] = des_df.apply(create_content, axis=1)

        print(des_df.head())
        
    # 3. Load into LangChain documents
    loader = DataFrameLoader(des_df, page_content_column="content")
    documents = loader.load()

    # 4. Create embeddings
    embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL)

    # 5. Store embeddings in DuckDB
    # Ensure the directory exists
    os.makedirs('embeddings', exist_ok=True)
    with duckdb.connect(database='embeddings/mro_db_column_description.db') as conn:
        _ = DuckDB.from_documents(documents, embeddings, connection=conn)

def similar_search(vectore_db: str, search_input: str, k: int = 10):
    # Re-create embeddings every call to avoid stale references
    embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL)

    # Ensure the path is absolute or correct relative to notebook
    db_path = f'../embeddings/{vectore_db}.db'

    with duckdb.connect(database=db_path) as conn:
        vectorstore = DuckDB(connection=conn, embedding=embeddings).as_retriever(
            search_kwargs={"k": k}
        )
        result = vectorstore.invoke(search_input)

    # Return only page_content
    search_result = [doc.page_content for doc in result]
    return search_result
