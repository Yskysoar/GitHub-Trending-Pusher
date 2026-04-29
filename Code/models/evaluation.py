from pydantic import BaseModel, Field


class EvalWeights(BaseModel):
    """评估权重模型。"""

    rule_match: float = 0.3
    star_threshold: float = 0.2
    growth_speed: float = 0.2
    learning_value: float = 0.3

    def validate_sum(self) -> bool:
        """校验权重之和是否为1.0（允许0.01误差）。"""
        total = self.rule_match + self.star_threshold + self.growth_speed + self.learning_value
        return abs(total - 1.0) < 0.01


class EvaluationConfig(BaseModel):
    """评估配置模型。"""

    top_n: int = 10
    weights: EvalWeights = Field(default_factory=EvalWeights)


class EvalDetails(BaseModel):
    """评估详情模型（对应eval_details JSON结构）。"""

    rule_match_score: float = 0.0
    star_threshold_score: float = 0.0
    growth_speed_score: float = 0.0
    learning_value_score: float = 0.0
    initial_score: float = 0.0
    final_score: float = 0.0
    matched_rules: list[dict] = Field(default_factory=list)
    effective_min_stars: int = 0
    learning_value_detail: dict | None = None
    growth_source: str = "trending"
    parse_error: str | None = None
