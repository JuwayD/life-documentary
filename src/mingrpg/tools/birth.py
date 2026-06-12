"""Birth setting tools — load predefined player starting templates."""
import copy
import os
from pathlib import Path

import yaml


_BIRTH_TEMPLATE_DIR = str(Path(__file__).parent.parent.parent.parent / "data" / "birth_templates")
_BIRTH_TEMPLATES_CACHE: list[dict] | None = None
_BIRTH_TEMPLATES_CACHE_DIR: str | None = None


def _reset_birth_templates_cache():
    global _BIRTH_TEMPLATES_CACHE, _BIRTH_TEMPLATES_CACHE_DIR
    _BIRTH_TEMPLATES_CACHE = None
    _BIRTH_TEMPLATES_CACHE_DIR = None


def _load_birth_templates() -> list[dict]:
    global _BIRTH_TEMPLATES_CACHE, _BIRTH_TEMPLATES_CACHE_DIR
    if _BIRTH_TEMPLATES_CACHE is not None and _BIRTH_TEMPLATES_CACHE_DIR == _BIRTH_TEMPLATE_DIR:
        return _BIRTH_TEMPLATES_CACHE

    templates: list[dict] = []
    if not os.path.isdir(_BIRTH_TEMPLATE_DIR):
        _BIRTH_TEMPLATES_CACHE = templates
        _BIRTH_TEMPLATES_CACHE_DIR = _BIRTH_TEMPLATE_DIR
        return templates

    for fname in sorted(os.listdir(_BIRTH_TEMPLATE_DIR)):
        if not (fname.endswith(".yaml") or fname.endswith(".yml")):
            continue
        path = os.path.join(_BIRTH_TEMPLATE_DIR, fname)
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or []
            if isinstance(data, list):
                templates.extend(data)

    templates.sort(key=lambda t: t.get("id", ""))
    _BIRTH_TEMPLATES_CACHE = templates
    _BIRTH_TEMPLATES_CACHE_DIR = _BIRTH_TEMPLATE_DIR
    return templates


def list_birth_templates() -> dict:
    """Return available birth templates as compact summaries."""
    templates = _load_birth_templates()
    return {"templates": [
        {
            "id": t.get("id"),
            "name": t.get("name"),
            "summary": t.get("summary", ""),
            "social_identity": t.get("attributes", {}).get("social_identity", ""),
            "money_wen": t.get("attributes", {}).get("money_wen", 0),
            "start": t.get("start", {}),
            "tags": t.get("tags", []),
        }
        for t in templates
    ]}


def get_birth_template(template_id: str) -> dict:
    """Return the full birth template by id."""
    for template in _load_birth_templates():
        if template.get("id") == template_id:
            return template
    return {
        "error": f"birth template '{template_id}' not found",
        "suggestion": "use list_birth_templates to discover valid ids",
    }


def apply_birth_template(world, template_id: str, entity_id: str = "player") -> dict:
    """Apply a birth template to the player entity for a new-game reset."""
    template = get_birth_template(template_id)
    if "error" in template:
        return template

    entity = world.get_entity(entity_id)
    if entity is None:
        return {
            "error": f"entity '{entity_id}' not found",
            "suggestion": "seed the world before applying a birth template",
        }

    old = {
        "name": entity.get("name"),
        "location": entity.get("location"),
        "pos": entity.get("pos"),
        "attributes": copy.deepcopy(entity.get("attributes", {})),
        "inventory": copy.deepcopy(entity.get("inventory", [])),
        "tags": copy.deepcopy(entity.get("tags", [])),
    }

    entity["name"] = template.get("name", entity.get("name"))
    entity["location"] = template.get("start", {}).get("location", entity.get("location"))
    entity["pos"] = list(template.get("start", {}).get("pos", entity.get("pos", [0, 0])))
    entity["attributes"] = copy.deepcopy(template.get("attributes", {}))
    entity["inventory"] = copy.deepcopy(template.get("inventory", []))
    entity["tags"] = list(dict.fromkeys(["protagonist", *template.get("tags", [])]))
    entity["status_effects"] = []
    world.save_entity(entity)

    birth_setting = {
        "template_id": template["id"],
        "name": template.get("name"),
        "summary": template.get("summary", ""),
        "entity_id": entity_id,
    }
    world.set_flag("birth_setting", birth_setting)
    event_id = world.append_event({
        "actor": entity_id,
        "type": "birth_template_applied",
        "summary": f"应用出生模板：{template.get('name', template_id)}",
        "template_id": template["id"],
    })

    return {
        "entity": entity_id,
        "template_id": template["id"],
        "name": template.get("name"),
        "old": old,
        "new": {
            "location": entity["location"],
            "pos": entity["pos"],
            "attributes": entity["attributes"],
            "inventory": entity["inventory"],
            "tags": entity["tags"],
        },
        "event_id": event_id,
    }
