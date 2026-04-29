import re
from datetime import datetime


def parse_github_date(date_str: str) -> str:
    """将GitHub API日期格式转换为ISO 8601格式。"""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
        return dt.isoformat()
    except (ValueError, TypeError):
        return date_str


def truncate_text(text: str, max_length: int = 4000, suffix: str = "…（内容已截断）") -> str:
    """截断文本到指定长度。"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + suffix


def extract_json_from_markdown(text: str) -> str:
    """从Markdown代码块中提取JSON内容。"""
    pattern = r"```json\s*([\s\S]*?)\s*```"
    match = re.search(pattern, text)
    if match:
        return match.group(1).strip()
    return text.strip()


def mask_sensitive(value: str, visible_chars: int = 4) -> str:
    """掩码敏感信息，仅显示前N个字符。"""
    if not value or len(value) <= visible_chars:
        return "••••••"
    return value[:visible_chars] + "••••••"


def format_stars(stars: int) -> str:
    """格式化star数量显示。"""
    if stars >= 10000:
        return f"{stars / 10000:.1f}w"
    if stars >= 1000:
        return f"{stars / 1000:.1f}k"
    return str(stars)


def sanitize_ascii(value: str) -> str:
    """清洗字符串，仅保留ASCII可打印字符。

    用于清洗Token/API Key等必须为ASCII的输入值，
    去除全角空格、中文标点等非ASCII字符。
    """
    if not value:
        return ""
    cleaned = value.strip()
    cleaned = re.sub(r'[^\x20-\x7E]', '', cleaned)
    return cleaned


def validate_weight_sum(weights: dict, tolerance: float = 0.01) -> bool:
    """校验评估权重之和是否为1.0。"""
    total = sum(weights.values())
    return abs(total - 1.0) < tolerance


def capitalize_language(language: str) -> str:
    """将小写语言名转为GitHub Trending URL所需的首字母大写格式。

    如 python -> Python, javascript -> JavaScript
    """
    special_cases = {
        "javascript": "JavaScript",
        "typescript": "TypeScript",
        "c++": "C++",
        "c#": "C%23",
        "f#": "F%23",
        "objective-c": "Objective-C",
        "html": "HTML",
        "css": "CSS",
        "sql": "SQL",
        "php": "PHP",
        "go": "Go",
        "rust": "Rust",
        "python": "Python",
        "java": "Java",
        "ruby": "Ruby",
        "swift": "Swift",
        "kotlin": "Kotlin",
        "dart": "Dart",
        "shell": "Shell",
        "vue": "Vue",
    }
    lower = language.lower().strip()
    if lower in special_cases:
        return special_cases[lower]
    return language.capitalize()
