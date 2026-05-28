import json
from pathlib import Path


_TEMPLATES = None


def load_templates():
    global _TEMPLATES
    if _TEMPLATES is None:
        tmpl_path = Path(__file__).parent.parent.parent / "templates" / "reasons_zh.json"
        with open(tmpl_path, "r", encoding="utf-8") as f:
            _TEMPLATES = json.load(f)
    return _TEMPLATES
