from pydantic import BaseModel
from typing import List
from datetime import date


class MessageResponseSchema(BaseModel):
    message: str


class ActivitySchema(BaseModel):
    date: date
    commits: int
    authors: List[str]
