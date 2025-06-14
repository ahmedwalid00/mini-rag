from pydantic import BaseModel
from typing import Optional

class ProcessRequest(BaseModel):
    file_id : str = None
    chunk_size : Optional[int] = 100
    chunk_overlap : Optional[int] = 20
    do_reset : Optional[int] = 0