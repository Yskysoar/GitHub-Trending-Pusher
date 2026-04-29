import re
from datetime import datetime, timedelta
from typing import Any

import httpx
from bs4 import BeautifulSoup
from github import Github, GithubException
from loguru import logger

from config.settings import Settings
from models.errors import ErrorCode, GitHubAPIError
from utils.helpers import capitalize_language, sanitize_ascii, truncate_text


class GitHubFetcher:
    """GitHub热门项目数据抓取器。

    负责从GitHub Search API和Trending页面获取热门开源项目数据，
    支持按语言、主题、star数等多维度筛选，并自动处理API速率限制。

    Attributes:
        token: GitHub Personal Access Token，用于API认证。
        client: httpx同步客户端实例（耗时操作在后台线程中执行，无需异步）。
    """

    def __init__(self, settings: Settings | None = None):
        self._settings = settings or Settings.get_instance()
        self.token = sanitize_ascii(self._settings.github_token)
        self.client = httpx.Client(
            timeout=httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=10.0),
            headers={
                "User-Agent": "GitHub-Trending-Pusher/1.0",
                "Accept": "application/vnd.github.v3+json",
            },
            follow_redirects=True,
        )
        self._github_client: Github | None = None

    @property
    def github_client(self) -> Github:
        """获取PyGitHub客户端实例（懒加载）。"""
        if self._github_client is None:
            if self.token:
                self._github_client = Github(self.token)
            else:
                self._github_client = Github()
        return self._github_client

    def fetch_trending_repos(self, languages: list[str] | None = None,
                             since: str = "daily") -> list[dict]:
        """获取GitHub趋势项目列表。

        通过抓取GitHub Trending页面获取指定时间段内star增长最快的项目列表。
        当Trending页面抓取失败时，自动降级为Search API查询。

        Args:
            languages: 编程语言筛选列表，None或空列表表示所有语言。
            since: 时间范围，可选 daily/weekly/monthly。

        Returns:
            包含仓库信息的字典列表，每个字典包含 full_name、description、
            url、homepage、stars、stars_growth、forks、language、topics、
            fetched_at 等字段。

        Raises:
            GitHubAPIError: 当Trending抓取和Search API降级方案都失败时抛出。
        """
        if languages is None:
            languages = self._settings.get("github.trending_languages", [])

        all_repos = []
        target_languages = languages if languages else [None]

        for lang in target_languages:
            try:
                repos = self._fetch_trending_page(lang, since)
                all_repos.extend(repos)
            except Exception as e:
                logger.warning(f"Trending页面抓取失败 (lang={lang}): {e}")
                try:
                    repos = self._fallback_search(lang, since)
                    for repo in repos:
                        repo["stars_growth"] = 0
                    all_repos.extend(repos)
                except Exception as fallback_e:
                    logger.error(f"Search API降级也失败 (lang={lang}): {fallback_e}")

        now = datetime.now().isoformat()
        for repo in all_repos:
            repo["fetched_at"] = now

        logger.info(f"Trending抓取完成: {len(all_repos)} 个项目")
        return all_repos

    def search_repos_by_query(self, keywords: list[str], topics: list[str] | None = None,
                              language: str = "", min_stars: int = 0) -> list[dict]:
        """按规则条件搜索仓库。

        内部调用私有方法_build_search_query()构造GitHub Search API查询语句，
        执行搜索并返回结果。

        Args:
            keywords: 关键词列表。
            topics: GitHub主题标签列表。
            language: 编程语言筛选。
            min_stars: 最低star数。

        Returns:
            搜索结果仓库列表。
        """
        query = self._build_search_query(keywords, topics, language, min_stars)
        if not query.strip():
            return []

        try:
            repos = self._search_api(query)
            now = datetime.now().isoformat()
            for repo in repos:
                repo["fetched_at"] = now
                repo.setdefault("stars_growth", 0)
            logger.info(f"Search API搜索完成: query='{query}', {len(repos)} 个结果")
            return repos
        except Exception as e:
            logger.error(f"Search API搜索失败: {e}")
            raise GitHubAPIError(ErrorCode.GITHUB_API_ERROR, f"搜索失败: {e}")

    def get_readme_content(self, full_name: str) -> str:
        """获取仓库README内容（截取前4000字符）。

        Args:
            full_name: 仓库全名（owner/repo）。
        """
        try:
            repo = self.github_client.get_repo(full_name)
            readme = repo.get_readme()
            content = readme.decoded_content.decode("utf-8", errors="replace")
            return truncate_text(content, 4000)
        except GithubException as e:
            logger.warning(f"获取README失败 ({full_name}): {e}")
            return ""
        except Exception as e:
            logger.warning(f"获取README异常 ({full_name}): {e}")
            return ""

    def _build_search_query(self, keywords: list[str], topics: list[str] | None = None,
                            language: str = "", min_stars: int = 0) -> str:
        """构造GitHub Search API查询语句。"""
        parts = []

        if keywords:
            keyword_part = " ".join(keywords)
            parts.append(keyword_part)

        if topics:
            for topic in topics:
                parts.append(f"topic:{topic}")

        if language:
            parts.append(f"language:{language}")

        if min_stars > 0:
            parts.append(f"stars:>{min_stars}")

        return " ".join(parts)

    def _fetch_trending_page(self, language: str | None, since: str) -> list[dict]:
        """抓取GitHub Trending页面。"""
        url = "https://github.com/trending"
        if language:
            url += f"/{capitalize_language(language)}"
        url += f"?since={since}"

        headers = {}
        if self.token:
            headers["Authorization"] = f"token {self.token}"

        response = self.client.get(url, headers=headers)
        response.raise_for_status()

        return self._parse_trending_html(response.text, language)

    def _parse_trending_html(self, html: str, language: str | None) -> list[dict]:
        """解析GitHub Trending页面HTML。"""
        soup = BeautifulSoup(html, "html.parser")
        repos = []

        articles = soup.select("article.Box-row")
        if not articles:
            articles = soup.select("article")

        for article in articles:
            try:
                repo = self._parse_trending_article(article)
                if repo:
                    repos.append(repo)
            except Exception as e:
                logger.warning(f"解析Trending项目失败: {e}")
                continue

        logger.info(f"解析Trending页面: {len(repos)} 个项目 (lang={language})")
        return repos

    def _parse_trending_article(self, article) -> dict | None:
        """解析单个Trending项目。"""
        h2 = article.select_one("h2 a")
        if not h2:
            return None

        href = h2.get("href", "")
        full_name = href.strip("/")

        description_elem = article.select_one("p")
        description = description_elem.get_text(strip=True) if description_elem else ""

        stars_elem = article.select_one("a.Link--muted[href*='/stargazers']")
        stars_text = stars_elem.get_text(strip=True) if stars_elem else "0"
        stars = self._parse_number(stars_text)

        today_elem = article.select_one("span.d-inline-block.float-sm-right")
        stars_growth = 0
        if today_elem:
            growth_text = today_elem.get_text(strip=True)
            stars_growth = self._parse_number(growth_text)

        lang_elem = article.select_one("span[itemprop='programmingLanguage']")
        lang = lang_elem.get_text(strip=True) if lang_elem else ""

        forks_elem = article.select_one("a.Link--muted[href*='/forks']")
        forks_text = forks_elem.get_text(strip=True) if forks_elem else "0"
        forks = self._parse_number(forks_text)

        topic_elems = article.select("a.topic-tag")
        topics = [t.get_text(strip=True) for t in topic_elems]

        return {
            "full_name": full_name,
            "description": description,
            "url": f"https://github.com/{full_name}",
            "homepage": "",
            "stars": stars,
            "stars_growth": stars_growth,
            "forks": forks,
            "language": lang,
            "topics": topics,
        }

    def _search_api(self, query: str, sort: str = "stars",
                    max_results: int = 30) -> list[dict]:
        """调用GitHub Search API搜索仓库。"""
        url = "https://api.github.com/search/repositories"
        headers = {"Accept": "application/vnd.github.v3+json"}
        if self.token:
            headers["Authorization"] = f"token {self.token}"

        params = {
            "q": query,
            "sort": sort,
            "order": "desc",
            "per_page": min(max_results, 100),
        }

        response = self.client.get(url, headers=headers, params=params)

        if response.status_code == 403:
            raise GitHubAPIError(ErrorCode.GITHUB_RATE_LIMIT, "GitHub API速率限制")
        if response.status_code == 401:
            raise GitHubAPIError(ErrorCode.GITHUB_TOKEN_INVALID, "GitHub Token无效")

        response.raise_for_status()
        data = response.json()

        repos = []
        for item in data.get("items", []):
            repos.append({
                "full_name": item.get("full_name", ""),
                "description": item.get("description", "") or "",
                "url": item.get("html_url", ""),
                "homepage": item.get("homepage", "") or "",
                "stars": item.get("stargazers_count", 0),
                "stars_growth": 0,
                "forks": item.get("forks_count", 0),
                "language": item.get("language", "") or "",
                "topics": item.get("topics", []),
            })

        return repos

    def _fallback_search(self, language: str | None, since: str) -> list[dict]:
        """Trending抓取失败时的Search API降级方案。"""
        query_parts = ["stars:>100"]
        if language:
            query_parts.append(f"language:{language}")

        pushed_days = {"daily": 1, "weekly": 7, "monthly": 30}.get(since, 1)
        pushed_date = (datetime.now() - timedelta(days=pushed_days)).strftime("%Y-%m-%d")
        query_parts.append(f"pushed:>{pushed_date}")

        query = " ".join(query_parts)
        return self._search_api(query, max_results=30)

    @staticmethod
    def _parse_number(text: str) -> int:
        """解析数字文本（如 '1,234' -> 1234, '5.2k' -> 5200）。"""
        text = text.replace(",", "").strip()
        match = re.match(r"([\d.]+)\s*k", text, re.IGNORECASE)
        if match:
            return int(float(match.group(1)) * 1000)
        match = re.match(r"([\d.]+)", text)
        if match:
            return int(float(match.group(1)))
        return 0

    def close(self) -> None:
        """关闭HTTP客户端。"""
        self.client.close()
        if self._github_client:
            self._github_client.close()
