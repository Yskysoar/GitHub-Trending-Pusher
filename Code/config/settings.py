import copy
import json
import os
from pathlib import Path

from loguru import logger

from models.evaluation import EvalWeights

DEFAULT_CONFIG_DIR = Path(__file__).parent
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "default_config.json"
APP_CONFIG_FILE = DEFAULT_CONFIG_DIR / "app_config.json"
ENV_FILE = DEFAULT_CONFIG_DIR.parent / ".env"

ENV_KEY_MAP = {
    "GITHUB_TOKEN": "github.token",
    "LLM_API_KEY": "llm.api_key",
    "LLM_BASE_URL": "llm.base_url",
    "LLM_MODEL": "llm.model",
    "LLM_PROVIDER": "llm.provider",
}


class Settings:
    """全局配置管理（单例模式）。

    负责配置加载、保存和环境变量覆盖。
    优先级：全局环境变量 < 项目.env文件 < app_config.json。

    Attributes:
        _config: 配置字典。
    """

    _instance: "Settings | None" = None

    def __init__(self):
        self._config: dict = {}
        self._env_values: dict[str, str] = {}
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
        if DEFAULT_CONFIG_FILE.exists():
            with open(DEFAULT_CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
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

    def _load_env_file(self) -> dict[str, str]:
        """从项目目录下的.env文件读取环境变量。

        Returns:
            环境变量字典。
        """
        env_values: dict[str, str] = {}
        if not ENV_FILE.exists():
            return env_values

        try:
            with open(ENV_FILE, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" not in line:
                        continue
                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip().strip("\"'")
                    if key in ENV_KEY_MAP:
                        env_values[key] = value
            if env_values:
                logger.info(f"已从.env文件加载 {len(env_values)} 个环境变量: {ENV_FILE}")
        except Exception as e:
            logger.warning(f".env文件读取失败: {e}")

        return env_values

    def _save_env_file(self, env_values: dict[str, str]) -> None:
        """保存环境变量到.env文件。"""
        existing: dict[str, str] = {}

        if ENV_FILE.exists():
            try:
                with open(ENV_FILE, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        if "=" in line:
                            key, _, value = line.partition("=")
                            existing[key.strip()] = value.strip().strip("\"'")
            except Exception:
                pass

        existing.update(env_values)

        try:
            with open(ENV_FILE, "w", encoding="utf-8") as f:
                f.write("# GitHub热点推送 环境变量配置\n")
                f.write("# 此文件包含敏感信息，请勿提交到版本控制\n\n")
                for key, value in existing.items():
                    f.write(f"{key}={value}\n")
            logger.info(f"环境变量已保存到: {ENV_FILE}")
        except Exception as e:
            logger.error(f".env文件保存失败: {e}")

    def _apply_env_overrides(self) -> None:
        """应用环境变量覆盖。

        优先级：全局环境变量(os.environ) < 项目.env文件 < app_config.json
        仅在配置文件中对应值为空时，才使用环境变量填充。
        """
        self._env_values = self._load_env_file()

        all_env: dict[str, str] = {}

        for env_key, config_path in ENV_KEY_MAP.items():
            os_value = os.environ.get(env_key, "")
            env_value = self._env_values.get(env_key, "")
            if env_value:
                all_env[env_key] = env_value
            elif os_value:
                all_env[env_key] = os_value

        for env_key, value in all_env.items():
            config_path = ENV_KEY_MAP[env_key]
            current_value = self.get(config_path, "")
            if not current_value:
                self.set(config_path, value)
                source = ".env文件" if env_key in self._env_values else "系统环境变量"
                logger.info(f"已从{source}填充 {config_path}")

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
        """保存当前配置到文件（同时更新.env文件）。"""
        self._save_json(self._config)

        env_values = {}
        github_token = self.get("github.token", "")
        if github_token:
            env_values["GITHUB_TOKEN"] = github_token
        llm_api_key = self.get("llm.api_key", "")
        if llm_api_key:
            env_values["LLM_API_KEY"] = llm_api_key

        if env_values:
            self._save_env_file(env_values)

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

    @property
    def github_token(self) -> str:
        return self.get("github.token", "")

    @property
    def llm_provider(self) -> str:
        return self.get("llm.provider", "volcengine")

    @property
    def llm_providers(self) -> dict:
        return self.get("llm.providers", {})

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
