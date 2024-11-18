from pydantic import BaseModel
from typing import Optional


class RepoSchema(BaseModel):
    repo: str
    owner: str
    position_cur: Optional[int]
    position_prev: Optional[int]
    stars: int
    watchers: int
    forks: int
    open_issues: int
    language: Optional[str]
