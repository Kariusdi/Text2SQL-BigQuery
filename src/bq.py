from google.cloud import bigquery
import pandas as pd
from config.gcp import initialize_gcs_client

class GcpBigQuery():
    
    def __init__(self, project_id: str, location: str, dataset_id: str):
        # Initialize GCP
        initialize_gcs_client()
        # Variables
        self.PROJECT_ID = project_id
        self.LOCATION = location
        self.DATASET_ID = dataset_id
        self.client = bigquery.Client(project=project_id)
        
    def bq_client(self):
        return self.client
        
    # A getter function 
    def getter(self):
        return {
            "project_id": self.PROJECT_ID,
            "location": self.LOCATION,
            "dataset_id": self.DATASET_ID,
        }
    
    def create_dataset(self) -> None:
        """Function to create BigQuery Dataset on your project"""
        dataset_id = "{}.{}".format(self.client.project, self.DATASET_ID)
        dataset = bigquery.Dataset(dataset_id)
        dataset.location = self.LOCATION

        # Create the dataset
        try:
            dataset = self.client.create_dataset(dataset, timeout=30)
            print(f'Dataset {dataset_id} create successfully.')
            self.DATASET_ID = dataset_id
        except Exception as e:
            print(f'Dataset {dataset_id} already exists.\n{e}')
        
    def import_csv_to_bq(self, filepath, table_id) -> None:
        """Function to import csv to BigQuery"""
        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.CSV, skip_leading_rows=1, autodetect=True,
                write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE)

        df = pd.read_csv(filepath, delimiter=',', )
        load_job = self.client.load_table_from_dataframe(dataframe=df,
                                                destination=table_id,
                                                    job_config=job_config)  # Make an API request.


        load_job.result()  # Waits for the job to complete.
        table = self.client.get_table(table_id)  # Make an API request.
        print(
            "Loaded {} rows and {} columns to {}".format(
                table.num_rows, len(table.schema), table_id
            )
        )
    
    def execute_query(self, query_syntax: str) -> pd.DataFrame:
        """A function to execute a sql query on the Big Query"""
        return self.client.query(query_syntax).to_dataframe()
        
# dataset_id: str = big_query.getter()["dataset_id"]
# table_name: str = "mrodata"
# table_id = "{}.{}".format(dataset_id, table_name)
# csv_data: str = "/Users/k./Documents/Coding/DX/text2bq/data/mockup_data.csv"
# big_query.create_dataset()
# big_query.import_csv_to_bq(csv_data, table_id)
# bq_client = big_query.bq_client()
# dataset_id: str = big_query.getter()["dataset_id"]
# table_name: str = "mrodata"
# table_id = "{}.{}".format(dataset_id, table_name)

# Preview imported data
# print(bq_client.query("SELECT * FROM " + "`" + table_id + "`").to_dataframe())