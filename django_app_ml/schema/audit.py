from pydantic import BaseModel, Field, RootModel
from typing import Dict, List, Any, Optional

class BasicInfo(BaseModel):
    row_count: int
    column_count: int
    column_names: List[str]
    column_types: Dict[str, str]
    memory_usage: int

class MissingValues(RootModel[Dict[str, int]]):
    pass

class DescriptiveStatsColumn(BaseModel):
    mean: float
    std: float
    min: float
    max: float
    median: float

class DescriptiveStats(RootModel[Dict[str, DescriptiveStatsColumn]]):
    pass

class CategoricalStatsColumn(BaseModel):
    unique_count: int
    top_values: Dict[str, int]

class CategoricalStats(RootModel[Dict[str, CategoricalStatsColumn]]):
    pass

class AuditReport(BaseModel):
    dataset_path: str
    auditor_type: str = Field(default="pandas")
    basic_info: BasicInfo
    missing_values: MissingValues
    descriptive_stats: DescriptiveStats
    categorical_stats: CategoricalStats 