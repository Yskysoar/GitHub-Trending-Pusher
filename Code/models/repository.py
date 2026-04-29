from datetime import datetime

from pydantic import BaseModel, Field


class Repository(BaseModel):
    """仓库数据模型。"""

    id: int | None = None
    full_name: str
    description: str = ""
    url: str
    homepage: str = ""
    stars: int = 0
    stars_growth: int = 0
    forks: int = 0
    language: str = ""
    topics: list[str] = Field(default_factory=list)
    readme_summary: str = ""
    eval_score: float = 0.0
    eval_details: str = "{}"
    fetched_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class RepositoryCreate(BaseModel):
    """仓库创建数据模型（不含id和默认值字段）。"""

    full_name: str
    description: str = ""
    url: str
    homepage: str = ""
    stars: int = 0
    stars_growth: int = 0
    forks: int = 0
    language: str = ""
    topics: list[str] = Field(default_factory=list)
    fetched_at: str = Field(default_factory=lambda: datetime.now().isoformat())
