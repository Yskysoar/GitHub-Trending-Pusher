import copy
import json
import os
from pathlib import Path

from loguru import logger

from models.evaluation import EvalWeights

DEFAULT_CONFIG_DIR = Path(__file__).parent
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "default_config.json"
APP_CONFIG_FILE = DEFAULT_CONFIG_DIR / "app_config.json"


class Settings:
    """全局配置管理（单例模式）。

    负责配置加载、保存和环境变量覆盖。
    启动时从app_config.json加载，若不存在则从default_config.json模板复制生成。

    Attributes:
        _config: 配置字典。
    """

    _instance: "Settings | None" = None

    def __init__(self):
        self._config: dict = {}
        self._load_config()

    @classmethod
    def get_instance(cls) -> "Settings":
        """获取配置管理单例。"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """重置单例（仅用于测试）。"""
        cls._instance = None

    def _load_config(self) -> None:
        """加载配置文件。"""
        if not APP_CONFIG_FILE.exists():
            self._create_default_config()

        try:
            with open(APP_CONFIG_FILE, "r", encoding="utf-8") as f:
                self._config = json.load(f)
            logger.info(f"配置已加载: {APP_CONFIG_FILE}")
        except Exception as e:
            logger.error(f"配置加载失败: {e}")
            self._config = self._get_default_config()

        self._apply_env_overrides()

    def _create_default_config(self) -> None:
        """从默认配置模板复制生成app_config.json。"""
        if DEFAULT_CONFIG_FILE.exists():
            import shutil
            shutil.copy2(DEFAULT_CONFIG_FILE, APP_CONFIG_FILE)
            logger.info(f"已从模板创建配置文件: {APP_CONFIG_FILE}")
        else:
            default = self._get_default_config()
            self._save_json(default)
            logger.info(f"已创建默认配置文件: {APP_CONFIG_FILE}")

    def _get_default_config(self) -> dict:
        """获取默认配置字典。"""
        return {
            "github": {
                "token": "",
                "fetch_interval_hours": 24,
                "max_repos_per_fetch": 50,
                "trending_languages": ["python", "javascript", "typescript", "go", "rust"],
                "min_stars": 100,
                "growth_period": "daily",
            },
            "llm": {
                "provider": "volcengine",
                "base_url": "https://ark.cn-beijing.volces.com/api/v3",
                "api_key": "",
                "model": "GLM-4.7",
                "temperature": 0.7,
                "max_tokens": 4096,
            },
            "evaluation": {
                "top_n": 10,
                "weights": {
                    "rule_match": 0.3,
                    "star_threshold": 0.2,
                    "growth_speed": 0.2,
                    "learning_value": 0.3,
                },
            },
            "output": {
                "save_dir": "",
                "format": "markdown",
                "filename_template": "github_trending_{date}.md",
            },
            "scheduler": {
                "enabled": True,
                "run_time": "09:00",
                "timezone": "Asia/Shanghai",
            },
            "autostart": {
                "enabled": False,
            },
            "app": {
                "theme": "system",
                "language": "zh_CN",
                "minimize_to_tray": True,
            },
        }

    def _apply_env_overrides(self) -> None:
        """应用环境变量覆盖。环境变量优先级高于配置文件。"""
        github_token = os.environ.get("GITHUB_TOKEN")
        if github_token:
            self._config.setdefault("github", {})["token"] = github_token
            logger.info("已从环境变量覆盖GITHUB_TOKEN")

        volcengine_key = os.environ.get("VOLCENGINE_API_KEY")
        if volcengine_key:
            self._config.setdefault("llm", {})["api_key"] = volcengine_key
            logger.info("已从环境变量覆盖VOLCENGINE_API_KEY")

    def _save_json(self, config: dict) -> None:
        """保存配置到JSON文件。"""
        with open(APP_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

    def get(self, key_path: str, default=None):
        """获取配置值，支持点号分隔的路径。

        Args:
            key_path: 配置路径，如 "github.token"。
            default: 默认值。
        """
        keys = key_path.split(".")
        value = self._config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def set(self, key_path: str, value) -> None:
        """设置配置值，支持点号分隔的路径。"""
        keys = key_path.split(".")
        config = self._config
        for key in keys[:-1]:
            config = config.setdefault(key, {})
        config[keys[-1]] = value

    def save(self) -> None:
        """保存当前配置到文件。"""
        self._save_json(self._config)
        logger.info("配置已保存")

    def get_all(self) -> dict:
        """获取完整配置字典（深拷贝）。"""
        return copy.deepcopy(self._config)

    def update_all(self, config: dict) -> None:
        """更新完整配置并保存。"""
        self._config = config
        self.save()

    def restore_defaults(self) -> None:
        """恢复所有配置为默认值。"""
        self._config = self._get_default_config()
        self.save()
        logger.info("配置已恢复为默认值")

    # ==================== 便捷属性 ====================

    @property
    def github_token(self) -> str:
        return self.get("github.token", "")

    @property
    def llm_api_key(self) -> str:
        return self.get("llm.api_key", "")

    @property
    def llm_base_url(self) -> str:
        return self.get("llm.base_url", "")

    @property
    def llm_model(self) -> str:
        return self.get("llm.model", "GLM-4.7")

    @property
    def eval_top_n(self) -> int:
        return self.get("evaluation.top_n", 10)

    @property
    def eval_weights(self) -> EvalWeights:
        weights_dict = self.get("evaluation.weights", {})
        return EvalWeights(**weights_dict)

    @property
    def output_save_dir(self) -> str:
        save_dir = self.get("output.save_dir", "")
        if not save_dir:
            save_dir = str(Path(__file__).parent.parent / "output")
        return save_dir

    @property
    def app_data_dir(self) -> str:
        env_dir = os.environ.get("APP_DATA_DIR")
        if env_dir:
            return env_dir
        return str(Path(__file__).parent.parent)
