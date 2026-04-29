import json

from database.connection import DatabaseConnection
from database.crud import CrudOperations
from models.errors import ErrorCode, RuleError


class RuleService:
    """规则管理服务。

    提供规则的CRUD操作和启禁用功能。
    """

    def __init__(self, db: DatabaseConnection):
        self.db = db
        self.crud = CrudOperations(db)

    def get_rules(self, enabled_only: bool = False) -> list[dict]:
        """获取规则列表。"""
        rules = self.crud.get_rules(enabled_only)
        return [self._format_rule(r) for r in rules]

    def add_rule(self, rule_data: dict) -> dict:
        """新增规则。"""
        self._validate_rule_data(rule_data)
        rule_id = self.crud.add_rule(
            name=rule_data["name"],
            keywords=rule_data["keywords"],
            topics=rule_data.get("topics", []),
            language=rule_data.get("language", ""),
            min_stars=rule_data.get("min_stars", 0),
            priority=rule_data.get("priority", 5),
            enabled=rule_data.get("enabled", True),
        )
        rule = self.crud.get_rule_by_id(rule_id)
        return self._format_rule(rule) if rule else {}

    def update_rule(self, rule_id: int, rule_data: dict) -> dict:
        """更新规则。"""
        rule = self.crud.get_rule_by_id(rule_id)
        if not rule:
            raise RuleError(ErrorCode.RULE_NOT_FOUND, f"规则不存在: ID {rule_id}")

        update_kwargs = {}
        for key in ("name", "keywords", "topics", "language", "min_stars", "priority", "enabled"):
            if key in rule_data and rule_data[key] is not None:
                update_kwargs[key] = rule_data[key]

        self.crud.update_rule(rule_id, **update_kwargs)
        updated = self.crud.get_rule_by_id(rule_id)
        return self._format_rule(updated) if updated else {}

    def delete_rule(self, rule_id: int) -> None:
        """删除规则（级联删除关联的match_records）。"""
        if not self.crud.delete_rule(rule_id):
            raise RuleError(ErrorCode.RULE_NOT_FOUND, f"规则不存在: ID {rule_id}")

    def toggle_rule(self, rule_id: int, enabled: bool) -> None:
        """启用/禁用规则。"""
        self.crud.toggle_rule(rule_id, enabled)

    @staticmethod
    def _validate_rule_data(data: dict) -> None:
        """校验规则数据。"""
        if not data.get("name", "").strip():
            raise RuleError(ErrorCode.RULE_INVALID, "规则名称不能为空")
        if not data.get("keywords"):
            raise RuleError(ErrorCode.RULE_INVALID, "关键词列表不能为空")
        priority = data.get("priority", 5)
        if not 1 <= priority <= 10:
            raise RuleError(ErrorCode.RULE_INVALID, "优先级必须在1-10之间")

    @staticmethod
    def _format_rule(rule: dict) -> dict:
        """格式化规则数据，将JSON字符串转为列表。"""
        if not rule:
            return {}
        result = dict(rule)
        for field in ("keywords", "topics"):
            value = result.get(field, "[]")
            if isinstance(value, str):
                try:
                    result[field] = json.loads(value)
                except json.JSONDecodeError:
                    result[field] = []
        result["enabled"] = bool(result.get("enabled", 0))
        return result
