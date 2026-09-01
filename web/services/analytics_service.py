"""Current-session analytics; no synthetic history or unmeasured efficiency."""
from core.application_context import ApplicationContext

class AnalyticsService:
    def __init__(self, ctx=None):
        self.ctx = ctx

    def get_analytics_summary(self):
        ctx = self.ctx or ApplicationContext.get_instance()
        lanes = list((ctx.latest_snapshot or {}).get("payload", {}).get("lanes", {}).values())
        return {"total_vehicles_today": sum(n.get("historicalCount", 0) for n in lanes),
            "avg_wait_time_sec": sum(n.get("wait", 0) for n in lanes) / len(lanes) if lanes else 0,
            "peak_pce_score": max((n.get("pce", 0) for n in lanes), default=0),
            "efficiency_score": None, "scope": "current_session", "hourly_flow": [],
            "queue_trends": [], "vehicle_split": [], "phase_efficiency": []}
