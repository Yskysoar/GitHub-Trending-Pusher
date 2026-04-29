import httpx

from config.settings import Settings
from database.connection import DatabaseConnection
from models.errors import ErrorCode, GitHubAPIError, LLMError
from models.evaluation import EvalWeights, EvaluationConfig
from utils.autostart import AutoStart
from utils.helpers import mask_sensitive, sanitize_ascii


class SettingsService:
    """设置管理服务。

    提供配置读写、连接测试、自启动管理和评估配置功能。
    """

    def __init__(self, db: DatabaseConnection, settings: Settings | None = None):
        self.db = db
        self._settings = settings or Settings.get_instance()

    def get_settings(self) -> dict:
        """获取当前完整配置（敏感字段已脱敏，用于非编辑场景）。"""
        config = self._settings.get_all()
        config["github"]["token"] = mask_sensitive(config.get("github", {}).get("token", ""))
        config["llm"]["api_key"] = mask_sensitive(config.get("llm", {}).get("api_key", ""))
        return config

    def get_settings_for_edit(self) -> dict:
        """获取当前完整配置（敏感字段保留原值，用于编辑表单）。"""
        return self._settings.get_all()

    def save_settings(self, settings_data: dict) -> None:
        """保存配置。"""
        current = self._settings.get_all()
        if "github" in settings_data and "token" in settings_data["github"]:
            settings_data["github"]["token"] = sanitize_ascii(settings_data["github"]["token"])
        if "llm" in settings_data and "api_key" in settings_data["llm"]:
            settings_data["llm"]["api_key"] = sanitize_ascii(settings_data["llm"]["api_key"])

        merged = self._deep_merge(current, settings_data)
        self._settings.update_all(merged)

    def restore_default_settings(self) -> None:
        """恢复所有配置为默认值。"""
        self._settings.restore_defaults()

    def test_github_connection(self, token: str | None = None) -> dict:
        """测试GitHub连接。

        Args:
            token: 可选的Token值，若提供则使用此值测试（不保存），
                   若不提供则使用已保存的Token。
        """
        if token is not None:
            token = sanitize_ascii(token)
        else:
            token = self._settings.github_token
            if token:
                token = sanitize_ascii(token)

        if not token:
            return {"success": False, "message": "GitHub Token未配置", "latency_ms": -1}

        try:
            import time
            start = time.time()
            headers = {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json",
            }
            response = httpx.get(
                "https://api.github.com/user",
                headers=headers,
                timeout=10.0,
            )
            latency = int((time.time() - start) * 1000)

            if response.status_code == 200:
                data = response.json()
                login = data.get("login", "Unknown")
                return {
                    "success": True,
                    "message": f"连接成功，用户: {login}",
                    "latency_ms": latency,
                }
            elif response.status_code == 401:
                return {"success": False, "message": "Token无效或已过期", "latency_ms": latency}
            elif response.status_code == 403:
                return {"success": False, "message": "API速率限制，请稍后重试", "latency_ms": latency}
            else:
                return {"success": False, "message": f"连接失败: HTTP {response.status_code}", "latency_ms": latency}
        except UnicodeEncodeError:
            return {"success": False, "message": "Token包含非ASCII字符，请检查输入", "latency_ms": -1}
        except Exception as e:
            return {"success": False, "message": f"连接失败: {e}", "latency_ms": -1}

    def test_llm_connection(self, api_key: str | None = None) -> dict:
        """测试LLM连接。

        Args:
            api_key: 可选的API Key值，若提供则使用此值测试（不保存），
                     若不提供则使用已保存的API Key。
        """
        base_url = self._settings.llm_base_url
        model = self._settings.llm_model

        if api_key is not None:
            api_key = sanitize_ascii(api_key)
        else:
            api_key = self._settings.llm_api_key
            if api_key:
                api_key = sanitize_ascii(api_key)

        if not api_key:
            return {"success": False, "message": "LLM API Key未配置", "latency_ms": -1}

        try:
            import time
            start = time.time()
            url = f"{base_url.rstrip('/')}/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            }
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": "Hi"}],
                "max_tokens": 5,
            }
            response = httpx.post(url, headers=headers, json=payload, timeout=15.0)
            latency = int((time.time() - start) * 1000)

            if response.status_code == 200:
                return {"success": True, "message": f"连接成功，模型: {model}", "latency_ms": latency}
            elif response.status_code == 401:
                return {"success": False, "message": "API Key无效", "latency_ms": latency}
            else:
                return {"success": False, "message": f"连接失败: HTTP {response.status_code}", "latency_ms": latency}
        except UnicodeEncodeError:
            return {"success": False, "message": "API Key包含非ASCII字符，请检查输入", "latency_ms": -1}
        except Exception as e:
            return {"success": False, "message": f"连接失败: {e}", "latency_ms": -1}

    def set_autostart(self, enabled: bool) -> None:
        """设置开机自启动。"""
        AutoStart.set_autostart(enabled)
        self._settings.set("autostart.enabled", enabled)
        self._settings.save()

    def get_evaluation_config(self) -> dict:
        """获取评估配置。"""
        return {
            "top_n": self._settings.eval_top_n,
            "weights": self._settings.eval_weights.model_dump(),
        }

    def save_evaluation_config(self, config: dict) -> None:
        """保存评估配置。"""
        if "top_n" in config:
            self._settings.set("evaluation.top_n", config["top_n"])
        if "weights" in config:
            weights = EvalWeights(**config["weights"])
            if not weights.validate_sum():
                from models.errors import EvalError
                raise EvalError(ErrorCode.EVAL_WEIGHT_INVALID, "权重之和必须为1.0")
            self._settings.set("evaluation.weights", weights.model_dump())
        self._settings.save()

    @staticmethod
    def _deep_merge(base: dict, override: dict) -> dict:
        """深度合并字典。"""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = SettingsService._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
