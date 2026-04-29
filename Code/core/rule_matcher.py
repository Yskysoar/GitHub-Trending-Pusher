import json
from datetime import datetime

from loguru import logger

from database.connection import DatabaseConnection
from database.crud import CrudOperations


class RuleMatcher:
    """规则匹配引擎。

    负责计算仓库与用户预设规则的匹配度，支持关键词、主题、语言三维度匹配。
    """

    def __init__(self, db: DatabaseConnection):
        self.db = db
        self.crud = CrudOperations(db)

    def match_rules(self, repos: list[dict], rules: list[dict]) -> list[dict]:
        """执行规则匹配。

        计算规则匹配度得分，标记每个仓库匹配的规则（含规则级min_stars信息），
        过滤不匹配任何启用规则的仓库。

        Args:
            repos: 候选仓库列表。
            rules: 启用的规则列表。

        Returns:
            匹配后的仓库列表（无启用规则时保留所有仓库）。
        """
        if not rules:
            logger.info("无启用规则，保留所有仓库，规则匹配度得分默认50")
            for repo in repos:
                repo["rule_match_score"] = 50.0
                repo["matched_rules"] = []
            return repos

        matched_repos = []
        all_match_records = []

        for repo in repos:
            best_score = 0.0
            best_rule_info = None
            repo_matched_rules = []

            for rule in rules:
                match_score = self._calculate_match_score(repo, rule)
                if match_score > 0:
                    priority = rule.get("priority", 5)
                    priority_bonus = 1 + (priority - 5) * 0.02
                    final_score = min(match_score * 100 * priority_bonus, 100)

                    keywords = json.loads(rule.get("keywords", "[]")) if isinstance(rule.get("keywords"), str) else rule.get("keywords", [])

                    rule_info = {
                        "id": rule["id"],
                        "name": rule.get("name", ""),
                        "base_match_ratio": match_score,
                        "priority_bonus": priority_bonus,
                        "min_stars": rule.get("min_stars", 0),
                    }
                    repo_matched_rules.append(rule_info)

                    if final_score > best_score:
                        best_score = final_score
                        best_rule_info = rule_info

            if best_score > 0:
                repo["rule_match_score"] = best_score
                repo["matched_rules"] = repo_matched_rules
                matched_repos.append(repo)

                for rule_info in repo_matched_rules:
                    all_match_records.append({
                        "rule_id": rule_info["id"],
                        "repo_id": repo.get("id", 0),
                        "match_score": rule_info["base_match_ratio"],
                    })
            else:
                logger.debug(f"仓库 {repo.get('full_name')} 不匹配任何规则，已过滤")

        if all_match_records:
            self.crud.save_match_records(all_match_records)

        logger.info(f"规则匹配完成: {len(repos)} 个候选 -> {len(matched_repos)} 个匹配")
        return matched_repos

    def _calculate_match_score(self, repo: dict, rule: dict) -> float:
        """计算单个仓库与单条规则的基础匹配度（0-1）。

        match_score = keyword_match_ratio × 0.5 + topic_match_ratio × 0.3 + language_match × 0.2
        """
        keywords = rule.get("keywords", [])
        if isinstance(keywords, str):
            keywords = json.loads(keywords)
        topics = rule.get("topics", [])
        if isinstance(topics, str):
            topics = json.loads(topics)
        rule_language = rule.get("language", "")

        keyword_ratio = self._calc_keyword_match_ratio(repo, keywords)
        topic_ratio = self._calc_topic_match_ratio(repo, topics)
        language_match = self._calc_language_match(repo, rule_language)

        score = keyword_ratio * 0.5 + topic_ratio * 0.3 + language_match * 0.2
        return score

    @staticmethod
    def _calc_keyword_match_ratio(repo: dict, keywords: list[str]) -> float:
        """计算关键词匹配比例。

        规则关键词在仓库信息（full_name + description + topics文本）中出现的数量 / 规则关键词总数。
        不区分大小写，部分匹配即可。
        空关键词列表时返回1.0（满分）。
        """
        if not keywords:
            return 1.0

        repo_text = " ".join([
            repo.get("full_name", ""),
            repo.get("description", ""),
            " ".join(repo.get("topics", [])),
        ]).lower()

        matched = 0
        for keyword in keywords:
            if keyword.strip().lower() in repo_text:
                matched += 1

        return matched / len(keywords)

    @staticmethod
    def _calc_topic_match_ratio(repo: dict, topics: list[str]) -> float:
        """计算主题匹配比例。

        规则topics与仓库topics的交集数量 / 规则topics总数。
        精确匹配，不区分大小写。
        空topics列表时返回1.0（满分）。
        """
        if not topics:
            return 1.0

        repo_topics = [t.lower() for t in repo.get("topics", [])]
        rule_topics = [t.lower() for t in topics]

        matched = sum(1 for t in rule_topics if t in repo_topics)
        return matched / len(rule_topics)

    @staticmethod
    def _calc_language_match(repo: dict, rule_language: str) -> float:
        """计算语言匹配。

        规则language非空时，与仓库language是否一致（不区分大小写）。
        规则language为空时取1（不限制）。
        """
        if not rule_language:
            return 1.0

        repo_language = repo.get("language", "")
        return 1.0 if repo_language.lower() == rule_language.lower() else 0.0
