"""
自进化闭环 —— FDE第五层能力
1. 反馈多了自动优化规则提示
2. 案例积累自动生成技能建议
3. 效果指标看板（准确率/满意度趋势）
"""
from datetime import datetime, timedelta
from typing import Optional


class SelfEvolution:
    """自进化引擎：反馈学习 → 规则优化 → 效果度量"""

    def __init__(self, state_store):
        self.state = state_store

    # ── 1. 反馈分析：自动提示规则优化 ──────────────────
    def analyze_feedback(self) -> dict:
        """
        分析用户反馈，找出"用户老说不对"的场景
        提示管理员优化规则
        """
        stats = self.state.get_feedback_stats()
        total = stats.get("total", 0)
        good = stats.get("good", 0)
        bad = stats.get("bad", 0)

        suggestions = []
        if total < 10:
            return {"status": "not_enough_data", "message": "反馈数据还不够，再用一段时间", "suggestions": []}

        # 差评率超过30%，提示优化规则
        bad_rate = bad / total if total > 0 else 0
        if bad_rate > 0.3:
            suggestions.append({
                "type": "rule_optimize",
                "severity": "high",
                "message": f"差评率 {bad_rate:.0%} 太高，建议检查规则文件",
                "action": "去知识规则页面看看，是不是规则过时了",
            })

        # 好评率超过70%，说明效果不错
        good_rate = good / total if total > 0 else 0
        if good_rate > 0.7:
            suggestions.append({
                "type": "good_performance",
                "severity": "low",
                "message": f"好评率 {good_rate:.0%}，运行良好",
                "action": "继续保持",
            })

        return {
            "status": "analyzed",
            "total": total,
            "good": good,
            "bad": bad,
            "good_rate": good_rate,
            "bad_rate": bad_rate,
            "suggestions": suggestions,
        }

    # ── 2. 案例积累：自动生成新技能建议 ──────────────────
    def suggest_new_skills(self) -> list[dict]:
        """
        分析用户常问但系统回答不好的问题
        自动建议要不要加新技能插件
        """
        suggestions = []

        # 如果差评多，建议加新技能
        analysis = self.analyze_feedback()
        if analysis.get("bad_rate", 0) > 0.4:
            suggestions.append({
                "type": "new_skill",
                "severity": "high",
                "message": "差评率高，建议分析高频问题，添加新的技能插件",
                "action": "看看用户最常问什么问题，是不是现有技能覆盖不到",
            })

        return suggestions

    # ── 3. 效果指标：越用越准的趋势 ──────────────────
    def get_effect_metrics(self) -> dict:
        """获取自进化效果指标"""
        stats = self.state.get_feedback_stats()
        total = stats.get("total", 0)
        good = stats.get("good", 0)
        bad = stats.get("bad", 0)

        # 满意度
        satisfaction = good / total if total > 0 else 0

        # 系统成熟度评级
        if total < 5:
            maturity = "起步期"
            desc = "刚上线，再用一段时间积累数据"
        elif total < 20:
            maturity = "成长期"
            desc = "已有一定反馈，系统在学习中"
        elif satisfaction > 0.7:
            maturity = "成熟期"
            desc = "好评率高，系统运行良好"
        else:
            maturity = "待优化"
            desc = "差评较多，建议检查规则"

        return {
            "total_feedback": total,
            "good_count": good,
            "bad_count": bad,
            "satisfaction_rate": satisfaction,
            "maturity": maturity,
            "maturity_desc": desc,
            "can_self_evolve": total >= 10,
        }

    # ── 综合自进化报告 ──────────────────
    def get_full_report(self) -> dict:
        """完整自进化报告"""
        analysis = self.analyze_feedback()
        skills = self.suggest_new_skills()
        metrics = self.get_effect_metrics()

        all_suggestions = analysis.get("suggestions", []) + skills

        return {
            "metrics": metrics,
            "analysis": analysis,
            "suggestions": all_suggestions,
            "time": datetime.now().isoformat(),
        }
