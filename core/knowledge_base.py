"""
知识库模块 —— vault文件系统版
对应Ha7ch经验：知识用文件系统，markdown是真相源，git可审计。
规则带版本号，工作流开始时冻结版本。
"""
import re
from pathlib import Path
from typing import Optional


class KnowledgeBase:
    """
    从vault目录加载知识。
    vault/rules/*.md    —— 业务规则（带frontmatter版本号）
    vault/experience/*.md —— 老师傅经验/质量案例
    """

    def __init__(self, vault_path: str = None):
        self.vault = Path(vault_path) if vault_path else Path(__file__).parent.parent / "vault"
        self._rules: dict = {}        # topic -> list[str]
        self._rule_meta: dict = {}    # topic -> {version, approved_by, ...}
        self._experience: dict = {} # key -> dict
        self._load_all()

    def _parse_frontmatter(self, text: str) -> tuple[dict, str]:
        """解析markdown frontmatter"""
        meta = {}
        body = text
        if text.startswith("---"):
            parts = text.split("---", 2)
            if len(parts) >= 3:
                for line in parts[1].strip().split("\n"):
                    if ":" in line:
                        k, v = line.split(":", 1)
                        meta[k.strip()] = v.strip().strip('"').strip("'")
                body = parts[2].strip()
        return meta, body

    def _load_all(self):
        """从vault目录加载所有规则和经验"""
        rules_dir = self.vault / "rules"
        if rules_dir.exists():
            for f in rules_dir.glob("*.md"):
                text = f.read_text(encoding="utf-8")
                meta, body = self._parse_frontmatter(text)
                topic = meta.get("topic", f.stem)
                # 从body提取列表项
                items = []
                for line in body.split("\n"):
                    line = line.strip()
                    if line.startswith("- "):
                        items.append(line[2:])
                self._rules[topic] = items
                self._rule_meta[topic] = meta

        exp_dir = self.vault / "experience"
        if exp_dir.exists():
            for f in exp_dir.glob("*.md"):
                text = f.read_text(encoding="utf-8")
                meta, body = self._parse_frontmatter(text)
                key = meta.get("equip_id") or meta.get("product", "") + meta.get("issue", "") or f.stem
                self._experience[key] = {"meta": meta, "body": body}

    def reload(self):
        """重新加载vault（规则更新后调用）"""
        self._rules.clear()
        self._rule_meta.clear()
        self._experience.clear()
        self._load_all()

    def query_rule(self, topic: str) -> list[str]:
        return self._rules.get(topic, [])

    def query_rule_meta(self, topic: str) -> dict:
        return self._rule_meta.get(topic, {})

    def query_experience(self, key: str) -> Optional[dict]:
        return self._experience.get(key)

    def search(self, keyword: str) -> dict:
        """按关键词搜索规则和经验"""
        results = {"rules": [], "experience": {}, "rule_versions": {}}
        for topic, rules in self._rules.items():
            if keyword in topic or any(keyword in r for r in rules):
                results["rules"].extend(rules)
                results["rule_versions"][topic] = self._rule_meta.get(topic, {})
        for key, exp in self._experience.items():
            if keyword in key or keyword in exp.get("body", ""):
                results["experience"][key] = exp
        return results

    def list_rules(self) -> list[dict]:
        """列出所有规则及其元信息"""
        return [
            {"topic": t, "version": self._rule_meta[t].get("version", "?"),
             "approved_by": self._rule_meta[t].get("approved_by", "?")}
            for t in self._rules
        ]
