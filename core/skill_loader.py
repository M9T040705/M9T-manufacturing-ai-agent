"""
技能插件加载器 —— 借鉴DeepSeek Harness"一切皆插件"理念。
技能定义在vault/skills/*.yaml，Python处理器在skills/*.py。
加新场景：写yaml + 写处理函数，不用改核心代码。
"""
import importlib
from pathlib import Path

import yaml

SKILLS_DIR = Path(__file__).parent.parent / "vault" / "skills"


class SkillPlugin:
    """单个技能插件"""
    def __init__(self, config: dict):
        self.id = config.get("id")
        self.name = config.get("name")
        self.icon = config.get("icon", "📄")
        self.page_key = config.get("page_key", self.id)
        self.description = config.get("description", "")
        self.triggers = config.get("triggers", [])
        self.data_sources = config.get("data_sources", [])
        self.risk_level = config.get("risk_level", "low")
        self.handler_name = config.get("handler", self.id)
        self.output_template = config.get("output_template", "")
        self._handler = None  # 懒加载

    @property
    def handler(self):
        """懒加载Python处理器"""
        if self._handler is None:
            mod = importlib.import_module(f"skills.{self.handler_name}")
            self._handler = mod.handle
        return self._handler

    def to_dict(self) -> dict:
        return {
            "id": self.id, "name": self.name, "icon": self.icon,
            "page_key": self.page_key, "description": self.description,
            "triggers": self.triggers, "data_sources": self.data_sources,
            "risk_level": self.risk_level,
        }


class SkillRegistry:
    """技能注册表：从yaml加载所有技能"""

    def __init__(self):
        self.skills: dict[str, SkillPlugin] = {}
        self.reload()

    def reload(self):
        """扫描vault/skills/*.yaml，加载所有技能"""
        self.skills.clear()
        if not SKILLS_DIR.exists():
            return
        for f in sorted(SKILLS_DIR.glob("*.yaml")):
            try:
                with open(f, encoding="utf-8") as fp:
                    config = yaml.safe_load(fp)
                plugin = SkillPlugin(config)
                self.skills[plugin.id] = plugin
            except Exception as e:
                print(f"⚠️ 技能加载失败 {f.name}: {e}")

    def get(self, skill_id: str) -> SkillPlugin | None:
        return self.skills.get(skill_id)

    def list_all(self) -> list[dict]:
        """列出所有技能元信息（给前端用）"""
        return [s.to_dict() for s in self.skills.values()]

    def match_trigger(self, question: str) -> str | None:
        """根据用户问题匹配技能（触发词命中）"""
        best_id = None
        best_hits = 0
        for sid, skill in self.skills.items():
            hits = sum(1 for kw in skill.triggers if kw in question)
            if hits > best_hits:
                best_hits = hits
                best_id = sid
        return best_id if best_hits > 0 else None

    def register_to_engine(self, engine):
        """把所有技能注册到Agent引擎"""
        for skill in self.skills.values():
            engine.register_skill(skill.id, skill.handler)
