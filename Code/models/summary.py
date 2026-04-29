from datetime import datetime

from pydantic import BaseModel, Field


class SummaryLog(BaseModel):
    """总结日志模型。"""

    id: int | None = None
    title: str
    content: str
    file_path: str
    repo_count: int = 0
    candidate_count: int = 0
    matched_count: int = 0
    generated_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class SummaryRepo(BaseModel):
    """日志-仓库关联模型。"""

    id: int | None = None
    summary_id: int
    repo_id: int
    rank: int = 0
