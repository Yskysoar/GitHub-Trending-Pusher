from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class Rule(BaseModel):
    """规则数据模型。"""

    id: int | None = None
    name: str
    keywords: list[str]
    topics: list[str] = Field(default_factory=list)
    language: str = ""
    min_stars: int = 0
    priority: int = 5
    enabled: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class RuleCreate(BaseModel):
    """规则创建数据模型。"""

    name: str
    keywords: list[str]
    topics: list[str] = Field(default_factory=list)
    language: str = ""
    min_stars: int = 0
    priority: int = 5
    enabled: bool = True

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: int) -> int:
        if not 1 <= v <= 10:
            raise ValueError("优先级必须在1-10之间")
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("规则名称不能为空")
        return v.strip()

    @field_validator("keywords")
    @classmethod
    def validate_keywords(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("关键词列表不能为空")
        return [kw.strip() for kw in v if kw.strip()]


class RuleUpdate(BaseModel):
    """规则更新数据模型。"""

    name: str | None = None
    keywords: list[str] | None = None
    topics: list[str] | None = None
    language: str | None = None
    min_stars: int | None = None
    priority: int | None = None
    enabled: bool | None = None

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: int | None) -> int | None:
        if v is not None and not 1 <= v <= 10:
            raise ValueError("优先级必须在1-10之间")
        return v
