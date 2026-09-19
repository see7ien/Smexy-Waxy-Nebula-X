THEME = {
    "background": "#0A1B30",
    "surface": "#102944",
    "surface_muted": "#14304F",
    "text_primary": "#EEEDE6",
    "text_secondary": "#92A2B8",
    "border": "#22405E",
    "rail_red": "#E14B33",
    "rail_green": "#22A35A",
    "rail_orange": "#E8971F",
    "rail_blue": "#4A8FE0",
    "success": "#2FAE72",
    "warning": "#E0A72E",
}

ACCENT_MAP = {
    "door": {"color": "#D92B2B", "soft": "#FDE5E5"},
    "acv": {"color": "#009B4D", "soft": "#E8F6EE"},
    "rail_corrugation": {"color": "#F58220", "soft": "#FFF1E4"},
    "shm": {"color": "#1769C2", "soft": "#E9F1FF"},
}

SUBSYSTEMS = [
    {
        "key": "door",
        "index": "DOOR",
        "title": "Door",
        "icon": "🚪",
        "description": "Inspect door cycle health, fault timing, and abnormal opening behaviour across train events.",
        "status": "Model live",
        "model": "Firth logistic regression",
        "path": "pages/door.py",
    },
    {
        "key": "acv",
        "index": "ACV",
        "title": "ACV",
        "icon": "❄️",
        "description": "Locate refrigerant-leak faults from HVAC telemetry, ranked car by car.",
        "status": "Model live",
        "model": "Logistic regression (1 feature)",
        "path": "pages/acv.py",
    },
    {
        "key": "rail_corrugation",
        "index": "RAIL",
        "title": "Rail Corrugation",
        "icon": "🛤️",
        "description": "Assess track condition signals to flag rail corrugation and surface integrity concerns.",
        "status": "Model live",
        "model": "Embedded classifier (rail_predict.py)",
        "path": "pages/rail_corrugation.py",
    },
    {
        "key": "shm",
        "index": "SHM",
        "title": "SHM",
        "icon": "📡",
        "description": "Examine structural health measurements and vibration patterns to support monitoring workflows.",
        "status": "Model live",
        "model": "Rainflow fatigue proxy (learned constant)",
        "path": "pages/shm.py",
    },
]
