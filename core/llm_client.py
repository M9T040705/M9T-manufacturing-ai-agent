"""
大模型客户端 —— DeepSeek API封装
简单问题走规则，复杂问题调DeepSeek
"""
import json
import requests
from pathlib import Path

CONFIG_PATH = Path(__file__).parent.parent / "config" / "llm.json"
CONFIG_PATH.parent.mkdir(exist_ok=True)

DEFAULT_CONFIG = {
    "provider": "deepseek",
    "api_key": "",  # 在这里填你的DeepSeek API Key
    "base_url": "https://api.deepseek.com/v1",
    "model": "deepseek-chat",
    "max_tokens": 2000,
    "temperature": 0.3,
    "enabled": False,  # 没填API Key就自动关闭
}

def _load_config() -> dict:
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return DEFAULT_CONFIG

def _save_default_config():
    if not CONFIG_PATH.exists():
        CONFIG_PATH.write_text(json.dumps(DEFAULT_CONFIG, ensure_ascii=False, indent=2), encoding="utf-8")

_save_default_config()


class LLMClient:
    """大模型客户端（DeepSeek/OpenAI兼容格式）"""

    def __init__(self):
        self.config = _load_config()

    @property
    def enabled(self) -> bool:
        """是否启用大模型（有API Key才启用）"""
        return self.config.get("enabled", False) and bool(self.config.get("api_key"))

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        """
        调大模型对话
        system_prompt: 系统提示词（告诉模型它是谁、有什么规则）
        user_prompt: 用户的问题 + 上下文数据
        返回：模型的回答
        """
        if not self.enabled:
            return ""

        url = f"{self.config['base_url']}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config['api_key']}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.config["model"],
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": self.config.get("max_tokens", 2000),
            "temperature": self.config.get("temperature", 0.3),
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"[LLM] 调用失败: {e}")
            return ""

    def reload(self):
        """热加载配置"""
        self.config = _load_config()

    def get_status(self) -> dict:
        """当前大模型状态"""
        return {
            "enabled": self.enabled,
            "provider": self.config.get("provider"),
            "model": self.config.get("model"),
            "has_api_key": bool(self.config.get("api_key")),
        }
