from pydantic import BaseModel
from typing import Any, Optional

class TaskResult(BaseModel):
    error: bool
    message: Optional[str] = None
    results: Optional[Any] = None
    already_exists: Optional[bool] = None
    dataset_id: Optional[int] = None
    dataset_name: Optional[str] = None
    bucket_name: Optional[str] = None 