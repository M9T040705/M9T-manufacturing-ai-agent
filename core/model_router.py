"""
模型路由层 —— 按场景+问题复杂度自动选模型等级
轻量/标准/重型，省钱又高效
"""
import yaml
from pathlib import Path
from typing import Optional

CONFIG_PATH = Path(__file__).parent.parent / "vault" / "models" / "model_config.yaml"

class ModelRouter:
    """模型路由器：根据场景和问题复杂度，决定用哪级模型"""

    def __init__(self):
        self._config = self._load_config()

    def _load_config(self) -> dict:
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        return {}

    def reload(self):
        """热加载配置"""
        self._config = self._load_config()

    def get_model_level(self, scene: str, question: str = "") -> str:
        """
        获取该场景该问题应该用什么模型等级
        scene: 场景key（reconciliation/delivery/daily/kitting/equipment/quality）
        question: 用户问题（用于自动升级判断）
        """
        scene_cfg = self._config.get("scenes", {}).get(scene, {})
        level = scene_cfg.get("model_level", "standard")
        auto_upgrade = scene_cfg.get("auto_upgrade", False)

        # 自动升级判断：复杂问题自动升一级
        if auto_upgrade and question:
            upgraded = self._should_upgrade(scene, question, level)
            if upgraded:
                level = self._upgrade_level(level)

        return level

    def _should_upgrade(self, scene: str, question: str, current_level: str) -> bool:
        """判断是否需要自动升级模型等级"""
        q = question
        # 复杂问题的关键词
        complex_keywords = [
            "为什么", "原因", "根因", "分析", "怎么回事",
            "预测", "趋势", "对比", "哪些", "所有",
            "改进", "建议", "方案", "怎么办",
        ]
        # 简单问题的关键词
        simple_keywords = [
            "多少", "有没有", "是多少", "查一下", "状态",
        ]

        # 如果问题里有复杂关键词，且当前不是最高级，就升级
        if any(k in q for k in complex_keywords) and current_level != "heavy":
            return True
        # 如果问题很短很短，且当前是heavy，降一级（太简单的问题不用跑重型模型）
        if len(q) < 8 and current_level == "heavy" and not any(k in q for k in complex_keywords):
            return False
        return False

    def _upgrade_level(self, level: str) -> str:
        """升一级：light→standard→heavy"""
        order = ["light", "standard", "heavy"]
        idx = order.index(level) if level in order else 1
        if idx < len(order) - 1:
            return order[idx + 1]
        return level

    def get_level_info(self, level: str) -> dict:
        """获取某级模型的详细信息"""
        return self._config.get("model_levels", {}).get(level, {})

    def get_scene_config(self, scene: str) -> dict:
        """获取某场景的配置"""
        return self._config.get("scenes", {}).get(scene, {})

    def list_scenes_config(self) -> list[dict]:
        """列出所有场景的模型配置（管理页面用）"""
        result = []
        for scene, cfg in self._config.get("scenes", {}).items():
            level = cfg.get("model_level", "standard")
            level_info = self.get_level_info(level)
            result.append({
                "scene": scene,
                "department": cfg.get("department", ""),
                "description": cfg.get("description", ""),
                "model_level": level,
                "level_name": level_info.get("name", level),
                "auto_upgrade": cfg.get("auto_upgrade", False),
                "speed": level_info.get("speed", ""),
                "cost": level_info.get("cost", ""),
            })
        return result

    def update_scene_level(self, scene: str, new_level: str) -> bool:
        """更新某场景的模型等级（管理页面用）"""
        if new_level not in ["light", "standard", "heavy"]:
            return False
        if scene not in self._config.get("scenes", {}):
            return False
        self._config["scenes"][scene]["model_level"] = new_level
        # 写回文件
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            yaml.dump(self._config, f, allow_unicode=True, sort_keys=False)
        return True
