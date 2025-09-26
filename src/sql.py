from pandas import DataFrame
from src.bq import GcpBigQuery

def execute_query(bq_client: GcpBigQuery, query_syntax: str) -> DataFrame:
    """A function to execute a sql query on the Big Query"""
    return bq_client.query(query_syntax).to_dataframe()