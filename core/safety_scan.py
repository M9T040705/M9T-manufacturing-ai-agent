"""
出站安全扫描 —— 对应Ha7ch经验：Model last
Agent输出给用户前，扫描敏感信息（密钥/密码/连接串/token），命中即替换。
只过滤凭据，不因为内容是代码而过滤。
"""
import re

# 敏感信息正则模式
SECRET_PATTERNS = [
    (re.compile(r'(api[_-]?key|apikey)["\']?\s*[:=]\s*["\']?[a-zA-Z0-9_\-]{20,}', re.I), "[API_KEY_REDACTED]"),
    (re.compile(r'(bearer|authorization)["\']?\s*[:=]\s*["\']?[a-zA-Z0-9_\-\.]{20,}', re.I), "[TOKEN_REDACTED]"),
    (re.compile(r'password\s*[:=]\s*\S+', re.I), "[PASSWORD_REDACTED]"),
    (re.compile(r'(mongodb|mysql|postgresql|redis)://[^\s"\'<>]+', re.I), "[CONN_STRING_REDACTED]"),
    (re.compile(r'sk-[a-zA-Z0-9]{20,}'), "[OPENAI_KEY_REDACTED]"),
    (re.compile(r'secret[_-]?key["\']?\s*[:=]\s*["\']?[a-zA-Z0-9_\-]{16,}', re.I), "[SECRET_REDACTED]"),
]


def scan_output(text: str) -> str:
    """扫描输出文本，替换敏感信息。返回净化后的文本。"""
    cleaned = text
    for pattern, replacement in SECRET_PATTERNS:
        cleaned = pattern.sub(replacement, cleaned)
    return cleaned


def has_secret(text: str) -> bool:
    """检查是否包含敏感信息"""
    for pattern, _ in SECRET_PATTERNS:
        if pattern.search(text):
            return True
    return False
