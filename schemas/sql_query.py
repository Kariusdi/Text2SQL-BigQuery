from typing import List, Generic, TypeVar, Optional
from pydantic import BaseModel, Field

class MroSchema(BaseModel):
    """Schema for a result from querying in MRO database"""
    plant: Optional[int] = Field(None, description="Plant number/location of the machine")
    dept: Optional[str] = Field(None, description="Group/department of the machine")
    machine_code: Optional[str] = Field(None, description="Name/code of the machine")
    service_type: Optional[str] = Field(None, description="Type of service, e.g., Q2 means preventive maintenance (PM) performed during shutdown")
    sympton: Optional[str] = Field(None, description="Description of which part of the machine (MachineCode) was inspected (does not indicate an actual symptom/problem)")
    cause: Optional[str] = Field(None, description="Period of time when the machine was shut down")
    report_by: Optional[str] = Field(None, description="Person who made the report")
    file: Optional[str] = Field(None, description="Scanned report files")
    
# T = TypeVar("T", bound=BaseModel)
# , Generic[T]
class SqlQuery(BaseModel):
    """Schema for an agent response with a sql query syntax result"""
    answer: str = Field(description="The agent's answer to the query")
    query_syntax: str = Field(description="The answer of the SQL query")
    
