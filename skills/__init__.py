"""skills包初始化：注册所有场景技能"""
from .procurement_reconciliation import handle as procurement_handle
from .delivery_quotation import handle as delivery_handle
from .daily_briefing import handle as daily_handle
from .material_kitting import handle as kitting_handle
from .equipment_maintenance import handle as equip_handle
from .quality_traceability import handle as quality_handle


def register_all_skills(engine):
    """把所有场景技能注册到Agent引擎"""
    engine.register_skill("procurement_reconciliation", procurement_handle)
    engine.register_skill("delivery_quotation", delivery_handle)
    engine.register_skill("daily_briefing", daily_handle)
    engine.register_skill("material_kitting", kitting_handle)
    engine.register_skill("equipment_maintenance", equip_handle)
    engine.register_skill("quality_traceability", quality_handle)
