import json
import re
from datetime import datetime

import httpx
from loguru import logger

from config.settings import Settings
from models.errors import ErrorCode, LLMError
from utils.file_manager import FileManager
from utils.helpers import extract_json_from_markdown, sanitize_ascii, truncate_text
from database.connection import DatabaseConnection
from database.crud import CrudOperations


EVAL_SYSTEM_PROMPT = """你是一个专业的开源项目分析师。请对提供的GitHub仓库进行学习价值评估。

从以下四个维度打分（每项0-10分，保留一位小数）：
- 技术创新性：项目是否采用了新技术、新架构或创新思路
- 代码质量：项目代码结构、文档完整性、测试覆盖等
- 实用性：项目在实际开发中的应用价值和学习参考价值
- 社区活跃度：Issue处理速度、PR合并频率、贡献者数量

同时为每个项目提供1-2句话的功能概述（summary）。

请严格按以下JSON格式返回评估结果，不要输出其他内容。
```json
[
  {
    "repo": "owner/repo",
    "summary": "1-2句话描述项目的主要功能和用途",
    "scores": {
      "innovation": 8.5,
      "code_quality": 7.0,
      "practicality": 9.0,
      "community": 6.5
    },
    "average_score": 7.8,
    "brief_reason": "1-2句话概括学习价值"
  }
]
```"""

EVAL_USER_TEMPLATE = """请评估以下GitHub项目的学习价值：

{repos_content}

请严格按系统提示中定义的JSON格式返回评估结果，不要输出其他内容。"""

SUMMARY_SYSTEM_PROMPT = """你是一个专业的开源项目分析师。请根据提供的GitHub仓库信息和评估结果，生成结构化的总结报告。

报告要求：

- 为每个项目生成结构化总结，包含：仓库链接、项目介绍（2-3句话）、学习价值说明（1-2句话）、实际应用举例（2-3个场景）
- 语言简洁专业，突出项目亮点和实用价值
- 如果多个项目属于同一领域，可以在末尾添加领域趋势分析"""

SUMMARY_USER_TEMPLATE = """请为以下{count}个GitHub热门项目生成总结报告：

{repos_content_with_eval}

请按照以下格式生成总结报告：

# GitHub热点推送 - {date}

## 推荐项目

### 1. {{repo_name}}

- **仓库链接**：{{repo_url}}
- **综合评分**：{{eval_score}}/100
- **项目介绍**：{{description}}
- **学习价值说明**：{{learning_value}}
- **实际应用举例**：
  1. {{use_case_1}}
  2. {{use_case_2}}

...

## 趋势总结

{{trend_summary}}"""


class LLMSummarizer:
    """LLM总结生成器。

    负责学习价值评估和总结报告生成，通过OpenAI兼容协议调用GLM-4.7。
    """

    def __init__(self, db: DatabaseConnection, settings: Settings | None = None):
        self.db = db
        self.crud = CrudOperations(db)
        self._settings = settings or Settings.get_instance()
        self.client = httpx.Client(
            timeout=httpx.Timeout(connect=10.0, read=60.0, write=10.0, pool=10.0),
        )

    def evaluate_learning_value(self, repos: list[dict]) -> list[dict]:
        """评估项目学习价值。

        调用GLM-4.7对TOP N项目进行四维度评分，每批最多5个项目。

        Args:
            repos: 待评估项目列表。

        Returns:
            LLM评估结果列表。
        """
        all_results = []
        batch_size = 5

        for i in range(0, len(repos), batch_size):
            batch = repos[i:i + batch_size]
            try:
                results = self._call_llm_eval(batch)
                all_results.extend(results)
            except Exception as e:
                logger.error(f"LLM评估批次 {i // batch_size + 1} 失败: {e}")
                for repo in batch:
                    all_results.append({
                        "repo": repo.get("full_name", ""),
                        "summary": repo.get("description", "暂无简介"),
                        "scores": {"innovation": 5.0, "code_quality": 5.0, "practicality": 5.0, "community": 5.0},
                        "average_score": 5.0,
                        "brief_reason": "评估信息不完整",
                    })

        return all_results

    def generate_summary(self, top_repos: list[dict]) -> str:
        """生成总结报告。

        Args:
            top_repos: 最终排名的TOP N项目列表。

        Returns:
            Markdown格式的总结报告。
        """
        if not top_repos:
            date = datetime.now().strftime("%Y-%m-%d")
            return f"# GitHub热点推送 - {date}\n\n本次抓取无符合条件的项目。\n"

        repos_content = self._build_summary_content(top_repos)
        date = datetime.now().strftime("%Y-%m-%d")

        user_prompt = SUMMARY_USER_TEMPLATE.format(
            count=len(top_repos),
            repos_content_with_eval=repos_content,
            date=date,
        )

        try:
            response_text = self._call_llm(
                system_prompt=SUMMARY_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                temperature=self._settings.get("llm.temperature", 0.7),
                max_tokens=self._settings.get("llm.max_tokens", 4096),
            )
            return response_text
        except Exception as e:
            logger.error(f"LLM总结生成失败: {e}")
            return self._generate_fallback_summary(top_repos, date)

    def save_summary(self, content: str, top_repos: list[dict],
                     candidate_count: int = 0, matched_count: int = 0) -> int:
        """保存总结日志。

        Args:
            content: 日志内容。
            top_repos: 推荐项目列表。
            candidate_count: 候选项目数。
            matched_count: 匹配仓库数。

        Returns:
            日志ID。
        """
        save_dir = self._settings.output_save_dir
        filename = FileManager.generate_filename(
            self._settings.get("output.filename_template", "github_trending_{date}.md")
        )
        file_path = FileManager.save_summary(content, f"{save_dir}/{filename}")

        date = datetime.now().strftime("%Y-%m-%d")
        log_data = {
            "title": f"GitHub热点推送 - {date}",
            "content": content,
            "file_path": file_path,
            "repo_count": len(top_repos),
            "candidate_count": candidate_count,
            "matched_count": matched_count,
            "generated_at": datetime.now().isoformat(),
        }

        repo_ids = [r.get("id") for r in top_repos if r.get("id")]
        summary_id = self.crud.save_summary_log(log_data, repo_ids)
        return summary_id

    def _call_llm_eval(self, repos: list[dict]) -> list[dict]:
        """调用LLM进行学习价值评估。"""
        repos_content = self._build_eval_content(repos)

        user_prompt = EVAL_USER_TEMPLATE.format(repos_content=repos_content)

        response_text = self._call_llm(
            system_prompt=EVAL_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=0.3,
            max_tokens=2048,
        )

        return self._parse_eval_response(response_text, repos)

    def _call_llm(self, system_prompt: str, user_prompt: str,
                  temperature: float = 0.3, max_tokens: int = 2048) -> str:
        """调用LLM API。"""
        base_url = self._settings.llm_base_url.rstrip("/")
        url = f"{base_url}/chat/completions"

        api_key = sanitize_ascii(self._settings.llm_api_key)
        model = self._settings.llm_model

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }

        response = self.client.post(url, headers=headers, json=payload)

        if response.status_code == 401:
            raise LLMError(ErrorCode.LLM_API_KEY_INVALID, "LLM API Key无效")
        if response.status_code == 429:
            raise LLMError(ErrorCode.LLM_API_ERROR, "LLM API速率限制")

        response.raise_for_status()
        data = response.json()

        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        if not content:
            raise LLMError(ErrorCode.LLM_API_ERROR, "LLM返回空内容")

        return content

    def _parse_eval_response(self, response_text: str, repos: list[dict]) -> list[dict]:
        """解析LLM评估响应，含容错处理。"""
        json_text = extract_json_from_markdown(response_text)

        try:
            results = json.loads(json_text)
        except json.JSONDecodeError as e:
            logger.warning(f"LLM评估JSON解析失败: {e}, 尝试重试...")
            try:
                repos_content = self._build_eval_content(repos)
                user_prompt = EVAL_USER_TEMPLATE.format(repos_content=repos_content)
                retry_text = self._call_llm(EVAL_SYSTEM_PROMPT, user_prompt, 0.3, 2048)
                retry_json = extract_json_from_markdown(retry_text)
                results = json.loads(retry_json)
            except Exception:
                logger.error("LLM评估重试仍失败，使用默认评分")
                return [
                    {
                        "repo": r.get("full_name", ""),
                        "summary": r.get("description", "暂无简介"),
                        "scores": {"innovation": 5.0, "code_quality": 5.0, "practicality": 5.0, "community": 5.0},
                        "average_score": 5.0,
                        "brief_reason": "评估信息不完整",
                    }
                    for r in repos
                ]

        if not isinstance(results, list):
            results = [results]

        for result in results:
            scores = result.get("scores", {})
            for dim in ("innovation", "code_quality", "practicality", "community"):
                val = scores.get(dim, 5.0)
                scores[dim] = max(0, min(10, float(val)))

            if not result.get("summary"):
                result["summary"] = next(
                    (r.get("description", "暂无简介") for r in repos if r.get("full_name") == result.get("repo")),
                    "暂无简介",
                )
            if not result.get("brief_reason"):
                result["brief_reason"] = "评估信息不完整"

        return results

    @staticmethod
    def _build_eval_content(repos: list[dict]) -> str:
        """构造学习价值评估的项目信息文本。"""
        parts = []
        for repo in repos:
            readme = repo.get("_readme_content", "")
            if not readme:
                readme = "暂无README内容"
            part = (
                f"仓库：{repo.get('full_name', '')}\n"
                f"描述：{repo.get('description', '')}\n"
                f"Stars：{repo.get('stars', 0)}\n"
                f"Forks：{repo.get('forks', 0)}\n"
                f"标签：{', '.join(repo.get('topics', []))}\n"
                f"语言：{repo.get('language', '')}\n"
                f"README内容（截取）：{readme}"
            )
            parts.append(part)
        return "\n---\n".join(parts)

    @staticmethod
    def _build_summary_content(repos: list[dict]) -> str:
        """构造总结报告的项目信息文本。"""
        parts = []
        for repo in repos:
            eval_details = repo.get("eval_details", {})
            learning_detail = eval_details.get("learning_value_detail", {}) if isinstance(eval_details, dict) else {}
            part = (
                f"仓库：{repo.get('full_name', '')}\n"
                f"描述：{repo.get('description', '')}\n"
                f"Stars：{repo.get('stars', 0)} | Forks：{repo.get('forks', 0)} | 语言：{repo.get('language', '')}\n"
                f"标签：{', '.join(repo.get('topics', []))}\n"
                f"综合评分：{repo.get('eval_score', 0)}/100\n"
                f"评估详情：技术创新性{learning_detail.get('innovation', 'N/A')}, "
                f"代码质量{learning_detail.get('code_quality', 'N/A')}, "
                f"实用性{learning_detail.get('practicality', 'N/A')}, "
                f"社区活跃度{learning_detail.get('community', 'N/A')}\n"
                f"学习价值：{learning_detail.get('brief_reason', 'N/A')}"
            )
            parts.append(part)
        return "\n---\n".join(parts)

    @staticmethod
    def _generate_fallback_summary(repos: list[dict], date: str) -> str:
        """LLM生成失败时的降级总结模板。"""
        lines = [f"# GitHub热点推送 - {date}\n"]
        lines.append("## 推荐项目\n")
        for i, repo in enumerate(repos, 1):
            lines.append(f"### {i}. {repo.get('full_name', 'Unknown')}\n")
            lines.append(f"- **仓库链接**：{repo.get('url', '')}")
            lines.append(f"- **综合评分**：{repo.get('eval_score', 0)}/100")
            lines.append(f"- **项目介绍**：{repo.get('description', '暂无描述')}")
            lines.append(f"- **Stars**：{repo.get('stars', 0)} | **语言**：{repo.get('language', '')}")
            lines.append("")
        lines.append("## 趋势总结\n")
        lines.append("*LLM生成失败，趋势总结暂不可用*\n")
        return "\n".join(lines)

    def close(self) -> None:
        """关闭HTTP客户端。"""
        self.client.close()
