"""Write tools — state mutations exposed to GM Agent.

Each tool:
- mutates world state
- returns a {old, new, ...} diff dict for audit
- does NOT validate game-logic correctness (that's the AI's job)
- returns errors via {"error": ...} dict, not exceptions
"""
from mingrpg.core.world import World


def set_attribute(world: World, entity_id: str, attr: str, value) -> dict:
    """Set an arbitrary attribute on an entity."""
    e = world.get_entity(entity_id)
    if e is None:
        return {"error": f"entity '{entity_id}' not found",
                "suggestion": "verify entity id with get_entity first"}
    old = e["attributes"].get(attr)
    e["attributes"][attr] = value
    world.save_entity(e)
    return {"entity": entity_id, "attr": attr, "old": old, "new": value}


def move_entity(world: World, entity_id: str,
                to_pos: list | None = None,
                to_location: str | None = None) -> dict:
    """Move an entity to a new position and/or location."""
    e = world.get_entity(entity_id)
    if e is None:
        return {"error": f"entity '{entity_id}' not found"}

    if to_location is not None:
        loc = world.get_location(to_location)
        if loc is None:
            return {"error": f"location '{to_location}' not found",
                    "suggestion": "verify with get_location"}

    from_loc = e["location"]
    from_pos = e["pos"]
    if to_location is not None:
        e["location"] = to_location
    if to_pos is not None:
        e["pos"] = list(to_pos)
    world.save_entity(e)

    return {
        "entity": entity_id,
        "from_location": from_loc,
        "to_location": e["location"],
        "from_pos": from_pos,
        "to_pos": e["pos"],
        "location_changed": from_loc != e["location"],
    }


def add_status(world: World, entity_id: str, status: str,
               duration: int = 1, reason: str = "",
               damage_per_tick: int = 0, **extra) -> dict:
    """Attach a status effect to an entity.

    `duration`: number of turns; -1 means permanent until removed.
    `damage_per_tick`: HP lost per turn when tick_statuses fires (default 0).
    `effect_type`: optional category hint (e.g. "bleeding", "poison", "stun").
    """
    e = world.get_entity(entity_id)
    if e is None:
        return {"error": f"entity '{entity_id}' not found"}
    effect = {"name": status, "duration": duration, "reason": reason,
              "damage_per_tick": damage_per_tick}
    if extra:
        effect.update(extra)
    e["status_effects"].append(effect)
    world.save_entity(e)
    return {"entity": entity_id, "status": status, "duration": duration,
            "reason": reason, "damage_per_tick": damage_per_tick,
            **extra}


def remove_status(world: World, entity_id: str, status: str) -> dict:
    """Remove the first matching status effect."""
    e = world.get_entity(entity_id)
    if e is None:
        return {"error": f"entity '{entity_id}' not found"}
    before = len(e["status_effects"])
    e["status_effects"] = [s for s in e["status_effects"]
                            if s["name"] != status]
    after = len(e["status_effects"])
    world.save_entity(e)
    return {"entity": entity_id, "status": status,
            "removed": before > after}


def add_item(world: World, entity_id: str, item: dict) -> dict:
    """Add an item to entity inventory."""
    e = world.get_entity(entity_id)
    if e is None:
        return {"error": f"entity '{entity_id}' not found"}
    e["inventory"].append(item)
    world.save_entity(e)
    return {"entity": entity_id, "added": item}


def remove_item(world: World, entity_id: str, item_id: str) -> dict:
    """Remove first item with given id from inventory."""
    e = world.get_entity(entity_id)
    if e is None:
        return {"error": f"entity '{entity_id}' not found"}
    before = len(e["inventory"])
    e["inventory"] = [i for i in e["inventory"] if i.get("id") != item_id]
    after = len(e["inventory"])
    world.save_entity(e)
    return {"entity": entity_id, "item_id": item_id,
            "removed": before > after}


def log_event(world: World, event: dict) -> dict:
    """Append an event to the event log."""
    event_id = world.append_event(event)
    return {"event_id": event_id, "event": event}


def set_flag(world: World, key: str, value) -> dict:
    """Set or update a world flag."""
    old = world.get_flag(key)
    world.set_flag(key, value)
    return {"key": key, "old": old, "new": value}


def add_memory(world: World, entity_id: str, text: str,
               importance: int = 5) -> dict:
    """Add a memory entry to an NPC (stored under attributes.memories)."""
    e = world.get_entity(entity_id)
    if e is None:
        return {"error": f"entity '{entity_id}' not found"}
    memories = e["attributes"].setdefault("memories", [])
    mem = {"text": text, "importance": importance,
            "turn": len(world.list_events(limit=10000))}
    memories.append(mem)
    world.save_entity(e)
    return {"entity": entity_id, "memory": mem}


def tick_npc_schedules(world: World) -> dict:
    """Move NPCs according to their attributes.schedule for current time."""
    time_of_day = world.get_world_time().get("time_of_day", "巳时")
    moved = []

    for entity in world.list_entities():
        if entity.get("type") == "player":
            continue
        schedule = entity.get("attributes", {}).get("schedule", {})
        slot = schedule.get(time_of_day)
        if not slot:
            continue

        to_location = slot.get("location")
        if to_location is not None and world.get_location(to_location) is None:
            continue

        from_location = entity.get("location")
        from_pos = entity.get("pos")
        to_pos = list(slot.get("pos", from_pos))
        location_changed = to_location is not None and to_location != from_location
        pos_changed = to_pos != from_pos
        if not location_changed and not pos_changed:
            continue

        entity["location"] = to_location or from_location
        entity["pos"] = to_pos
        world.save_entity(entity)

        record = {
            "entity": entity["id"],
            "from_location": from_location,
            "to_location": entity["location"],
            "from_pos": from_pos,
            "to_pos": to_pos,
            "activity": slot.get("activity", ""),
        }
        moved.append(record)
        world.append_event({
            "actor": entity["id"],
            "type": "schedule_move",
            "summary": f"{entity['name']}按时辰日程前往{entity['location']}",
            "time_of_day": time_of_day,
            **record,
        })

    return {"time_of_day": time_of_day, "moved": moved}


def advance_time(world: World, units: str = "shichen",
                 amount: int = 1) -> dict:
    """Advance world time.

    units="shichen": advance by 时辰 (1 shichen = 2 hours). Auto-increments
                     day_index when wrapping from 亥时 → 子时.
    units="day": advance by whole days (increments day_index only).
    """
    SHICHEN = ["子时", "丑时", "寅时", "卯时", "辰时", "巳时",
                "午时", "未时", "申时", "酉时", "戌时", "亥时"]
    t = world.get_world_time()
    day_index = t.get("day_index", 0)
    old = t.get("time_of_day", "巳时")
    day_wrapped = False

    if units == "day":
        day_index += amount
    else:
        # shichen (default)
        idx = SHICHEN.index(old) if old in SHICHEN else 0
        total = idx + amount
        new_idx = total % len(SHICHEN)
        wraps = total // len(SHICHEN)
        day_index += wraps
        day_wrapped = wraps > 0
        t["time_of_day"] = SHICHEN[new_idx]

    t["day_index"] = day_index
    world.set_world_time(t)
    schedule_tick = tick_npc_schedules(world)
    return {
        "from": old, "to": t["time_of_day"], "amount": amount,
        "units": units, "day_wrapped": day_wrapped,
        "day_index": day_index,
        "schedule_tick": schedule_tick,
    }


def transfer_money(world: World, from_entity: str, to_entity: str,
                   amount: int, reason: str = "") -> dict:
    """Transfer money (文) from one entity to another.

    Returns an error dict if the transfer is impossible.
    """
    if amount <= 0:
        return {"error": "amount must be positive",
                "suggestion": "amount should be > 0"}
    if from_entity == to_entity:
        return {"error": "cannot transfer money to the same entity",
                "suggestion": "use a different target entity"}

    f = world.get_entity(from_entity)
    if f is None:
        return {"error": f"from entity '{from_entity}' not found",
                "suggestion": "verify entity id with get_entity first"}
    t = world.get_entity(to_entity)
    if t is None:
        return {"error": f"to entity '{to_entity}' not found",
                "suggestion": "verify entity id with get_entity first"}

    from_balance = f["attributes"].get("money_wen", 0)
    if from_balance < amount:
        return {"error": f"insufficient funds: {from_entity} has {from_balance} 文, need {amount} 文",
                "suggestion": "reduce the amount or find another way to pay"}

    to_balance = t["attributes"].get("money_wen", 0)

    f["attributes"]["money_wen"] = from_balance - amount
    t["attributes"]["money_wen"] = to_balance + amount

    world.save_entity(f)
    world.save_entity(t)

    return {
        "from_entity": from_entity,
        "to_entity": to_entity,
        "amount": amount,
        "from_balance_after": f["attributes"]["money_wen"],
        "to_balance_after": t["attributes"]["money_wen"],
        "reason": reason,
    }


def purchase_item(world: World, buyer: str, seller: str, item_id: str,
                  qty: int = 1, unit_price_wen: int | None = None,
                  reason: str = "") -> dict:
    """Purchase inventory item(s): transfer money, then move item quantity."""
    if qty <= 0:
        return {"error": "qty must be positive",
                "suggestion": "qty should be > 0"}

    b = world.get_entity(buyer)
    if b is None:
        return {"error": f"buyer '{buyer}' not found",
                "suggestion": "verify entity id with get_entity first"}
    s = world.get_entity(seller)
    if s is None:
        return {"error": f"seller '{seller}' not found",
                "suggestion": "verify entity id with get_entity first"}

    seller_item = None
    for item in s.get("inventory", []):
        if item.get("id") == item_id:
            seller_item = item
            break
    if seller_item is None:
        return {"error": f"item '{item_id}' not found in seller inventory",
                "suggestion": "inspect seller inventory with get_entity first"}
    if seller_item.get("qty", 1) < qty:
        return {"error": f"insufficient stock: {item_id} has {seller_item.get('qty', 1)}, need {qty}",
                "suggestion": "reduce qty or choose another item"}

    if unit_price_wen is None:
        price_list = s.get("attributes", {}).get("price_list", {})
        unit_price_wen = price_list.get(item_id)
    if unit_price_wen is None:
        return {"error": f"price for item '{item_id}' not found",
                "suggestion": "provide unit_price_wen or set seller attributes.price_list"}
    if unit_price_wen <= 0:
        return {"error": "unit_price_wen must be positive",
                "suggestion": "unit_price_wen should be > 0"}

    total_price = unit_price_wen * qty
    paid = transfer_money(world, buyer, seller, total_price,
                          reason or f"purchase {item_id}")
    if "error" in paid:
        return paid

    b = world.get_entity(buyer)
    s = world.get_entity(seller)
    seller_inventory = s.get("inventory", [])
    seller_item = next(i for i in seller_inventory if i.get("id") == item_id)
    seller_item["qty"] = seller_item.get("qty", 1) - qty
    s["inventory"] = [i for i in seller_inventory if i.get("qty", 1) > 0]

    bought_item = dict(seller_item)
    bought_item["qty"] = qty
    buyer_item = None
    for item in b.get("inventory", []):
        if item.get("id") == item_id:
            buyer_item = item
            break
    if buyer_item is None:
        b.setdefault("inventory", []).append(bought_item)
    else:
        buyer_item["qty"] = buyer_item.get("qty", 1) + qty

    world.save_entity(b)
    world.save_entity(s)
    world.append_event({
        "actor": buyer,
        "type": "purchase_item",
        "target": seller,
        "summary": f"{buyer} 向 {seller} 购买 {qty} 个 {item_id}",
        "item_id": item_id,
        "qty": qty,
        "total_price_wen": total_price,
        "reason": reason,
    })
    return {
        "buyer": buyer,
        "seller": seller,
        "item_id": item_id,
        "qty": qty,
        "unit_price_wen": unit_price_wen,
        "total_price_wen": total_price,
        "buyer_balance_after": paid["from_balance_after"],
        "seller_balance_after": paid["to_balance_after"],
        "reason": reason,
    }


def hire_service(world: World, payer: str, provider: str, service_id: str,
                 price_wen: int | None = None, duration: int = 1,
                 reason: str = "") -> dict:
    """Hire an entity for a service: transfer money and mark a contract."""
    p = world.get_entity(payer)
    if p is None:
        return {"error": f"payer '{payer}' not found",
                "suggestion": "verify entity id with get_entity first"}
    provider_entity = world.get_entity(provider)
    if provider_entity is None:
        return {"error": f"provider '{provider}' not found",
                "suggestion": "verify entity id with get_entity first"}

    service = provider_entity.get("attributes", {}).get("service_catalog", {}).get(service_id)
    if price_wen is None and service is not None:
        price_wen = service.get("price_wen")
    if price_wen is None:
        return {"error": f"service '{service_id}' price not found",
                "suggestion": "provide price_wen or set provider attributes.service_catalog"}
    if price_wen <= 0:
        return {"error": "price_wen must be positive",
                "suggestion": "price_wen should be > 0"}

    paid = transfer_money(world, payer, provider, price_wen,
                          reason or f"hire {service_id}")
    if "error" in paid:
        return paid

    provider_entity = world.get_entity(provider)
    provider_entity.setdefault("attributes", {})["current_contract"] = {
        "hired_by": payer,
        "service_id": service_id,
        "service_name": service.get("name") if service else service_id,
        "duration": duration,
        "reason": reason,
    }
    world.save_entity(provider_entity)
    world.append_event({
        "actor": payer,
        "type": "hire_service",
        "target": provider,
        "summary": f"{payer} 雇请 {provider} 提供 {service_id}",
        "service_id": service_id,
        "price_wen": price_wen,
        "duration": duration,
        "reason": reason,
    })
    return {
        "payer": payer,
        "provider": provider,
        "service_id": service_id,
        "service_name": service.get("name") if service else service_id,
        "price_wen": price_wen,
        "duration": duration,
        "payer_balance_after": paid["from_balance_after"],
        "provider_balance_after": paid["to_balance_after"],
        "reason": reason,
    }


def apply_damage(world: World, entity_id: str, amount: int,
                 damage_type: str = "physical", source: str = "") -> dict:
    """Apply damage to an entity, reducing HP.

    Returns {entity, old_hp, new_hp, amount, overkill, incapacitated, damage_type, source}.
    incapacitated=True when HP reaches 0 (code does NOT auto-add statuses — AI decides).
    """
    e = world.get_entity(entity_id)
    if e is None:
        return {"error": f"entity '{entity_id}' not found",
                "suggestion": "verify entity id with get_entity first"}
    old_hp = e["attributes"].get("hp", 0)
    new_hp = max(0, old_hp - amount)
    overkill = max(0, amount - old_hp) if old_hp >= 0 else amount
    e["attributes"]["hp"] = new_hp
    world.save_entity(e)
    return {
        "entity": entity_id,
        "old_hp": old_hp,
        "new_hp": new_hp,
        "amount": amount,
        "overkill": overkill,
        "incapacitated": new_hp <= 0,
        "damage_type": damage_type,
        "source": source,
    }


def tick_statuses(world: World, entity_id: str = None) -> dict:
    """Decrement duration on status effects and apply damage_per_tick damage.

    If entity_id is None, ticks ALL entities.
    Effects with duration=-1 (permanent) are skipped.
    Effects whose duration reaches 0 are auto-removed.
    Effects with damage_per_tick>0 deal that much damage to the entity.

    Returns {ticked: [{entity, status, new_duration, expired, damage_dealt}, ...]}
    """
    if entity_id is not None:
        e = world.get_entity(entity_id)
        if e is None:
            return {"error": f"entity '{entity_id}' not found",
                    "suggestion": "verify entity id with get_entity first"}
        entities = [e]
    else:
        entities = world.list_entities()

    ticked = []
    for e in entities:
        eid = e["id"]
        total_damage = 0
        damage_sources = []
        new_effects = []

        for se in e.get("status_effects", []):
            dmg = se.get("damage_per_tick", 0)
            dur = se.get("duration", 0)

            if dmg > 0:
                total_damage += dmg
                damage_sources.append(se.get("name", ""))

            # Decrement duration (skip permanent effects with duration=-1)
            if dur > 0:
                dur -= 1
                se["duration"] = dur

            if dur == 0:
                ticked.append({
                    "entity": eid, "status": se["name"],
                    "new_duration": 0, "expired": True,
                    "damage_dealt": dmg,
                })
                # Don't keep expired effects in new_effects
            else:
                new_effects.append(se)
                ticked.append({
                    "entity": eid, "status": se["name"],
                    "new_duration": dur, "expired": False,
                    "damage_dealt": dmg,
                })

        # Apply accumulated damage (single DB write, avoids stale-entity bug)
        if total_damage > 0:
            apply_damage(world, eid, total_damage,
                         damage_type="status",
                         source=", ".join(damage_sources))

        # Save updated status_effects (re-fetch first to preserve HP change)
        e_fresh = world.get_entity(eid)
        e_fresh["status_effects"] = new_effects
        world.save_entity(e_fresh)

    return {"ticked": ticked}


def record_clue(world: World, thread_id: str, clue: str,
                source_entity: str = "", location_id: str = "",
                evidence_item: str = "") -> dict:
    """Record a discovered clue for a story thread.

    Deduplicates by clue text. Writes to world flag 'story_progress[thread_id].clues'.
    Does NOT judge whether the clue is correct or complete — that's the AI's job.
    """
    progress = world.get_flag("story_progress") or {}
    thread = progress.setdefault(thread_id, {"clues": []})
    existing = [c for c in thread["clues"] if c["clue"] == clue]
    if existing:
        return {"thread_id": thread_id, "clue": clue,
                "added": False, "clue_count": len(thread["clues"])}

    entry = {
        "clue": clue,
        "source_entity": source_entity,
        "location_id": location_id,
        "evidence_item": evidence_item,
    }
    thread["clues"].append(entry)
    world.set_flag("story_progress", progress)
    world.append_event({
        "actor": source_entity or "player",
        "type": "record_clue",
        "thread_id": thread_id,
        "summary": f"发现线索: {clue[:40]}{'…' if len(clue) > 40 else ''}",
        "clue": clue,
        "source_entity": source_entity,
        "location_id": location_id,
    })
    return {"thread_id": thread_id, "clue": clue,
            "added": True, "clue_count": len(thread["clues"])}


def advance_pressure_clock(world: World, clock_id: str, amount: int = 1,
                           reason: str = "", danger_at: int = 3) -> dict:
    """Advance or set a pressure clock for narrative tension.

    Pressure clocks are named counters (e.g. 'witness_pressure', 'official_patience')
    that track how close a situation is to tipping. The danger_at threshold tells the
    AI when the situation should escalate — the code only reports, never enforces.
    """
    if amount <= 0:
        return {"error": "amount must be positive",
                "suggestion": "amount should be > 0"}

    clocks = world.get_flag("pressure_clocks") or {}
    existing = clocks.get(clock_id, {})
    old = existing.get("value", 0)
    new_value = old + amount
    danger_reached = new_value >= danger_at
    history = existing.get("history", [])
    history.append(new_value)
    clocks[clock_id] = {"value": new_value, "danger_at": danger_at,
                        "history": history}
    world.set_flag("pressure_clocks", clocks)
    world.append_event({
        "actor": "system",
        "type": "pressure_clock",
        "clock_id": clock_id,
        "summary": f"压力钟'{clock_id}'从{old}推进到{new_value}"
                   f"{'(已达危险线)' if danger_reached else ''}: {reason}",
        "old_value": old,
        "new_value": new_value,
        "danger_at": danger_at,
        "danger_reached": danger_reached,
        "reason": reason,
    })
    return {"clock_id": clock_id, "old": old, "new": new_value,
            "danger_at": danger_at, "danger_reached": danger_reached}


def discover_observation(world: World, detail_id: str,
                         target_id: str | None = None,
                         actor_id: str = "player",
                         source: str = "observe") -> dict:
    """Record that an actor discovered an observable detail.

    Does NOT decide whether the detail matters — it only persists discovery
    under flag 'observations[actor_id]'.
    """
    actor = world.get_entity(actor_id)
    if actor is None:
        return {"error": f"actor '{actor_id}' not found",
                "suggestion": "verify actor id with get_entity first"}

    if not detail_id or not detail_id.strip():
        return {"error": "detail_id must not be empty",
                "suggestion": "use list_observables to find valid detail ids"}
    detail_id = detail_id.strip()

    location = world.get_location(actor.get("location"))
    candidates = []
    if location is not None:
        candidates.extend(("location", location, d)
                          for d in location.get("observable_details", []))
    for entity in world.list_entities_at(actor.get("location")):
        candidates.extend(("entity", entity, d)
                          for d in entity.get("attributes", {}).get("observable_details", []))

    matched = None
    for target_type, target, detail in candidates:
        if detail.get("id") != detail_id:
            continue
        if target_id is not None and target.get("id") != target_id:
            continue
        matched = (target_type, target, detail)
        break

    if matched is None:
        return {"error": f"observable detail '{detail_id}' not found nearby",
                "suggestion": "use list_observables before discover_observation"}

    target_type, target, detail = matched
    key = f"{target_type}:{target['id']}:{detail_id}"
    observations = world.get_flag("observations") or {}
    actor_observations = observations.setdefault(actor_id, {})
    already = key in actor_observations
    entry = {
        "detail_id": detail_id,
        "target_id": target["id"],
        "target_name": target.get("name", target["id"]),
        "target_type": target_type,
        "text": detail.get("text", ""),
        "discovery_value": detail.get("discovery_value", 0),
        "source": source,
    }
    actor_observations[key] = entry
    world.set_flag("observations", observations)

    if not already:
        world.append_event({
            "actor": actor_id,
            "type": "discover_observation",
            "target": target["id"],
            "detail_id": detail_id,
            "summary": f"{actor['name']}发现: {entry['text'][:40]}{'…' if len(entry['text']) > 40 else ''}",
            "source": source,
        })

    return {"actor_id": actor_id, "detail_id": detail_id,
            "target_id": target["id"], "target_type": target_type,
            "discovered": not already, "observation": entry}



def set_weather(world: World, condition: str = "",
                intensity: str = "", text: str = "",
                reason: str = "") -> dict:
    """Update the current weather conditions.

    condition: clear/cloudy/rain/storm/fog/snow
    intensity: light/moderate/heavy
    text: human-readable weather description for GM narration
    reason: why the weather changed (for audit)
    """
    valid_conditions = {"clear", "cloudy", "rain", "storm", "fog", "snow"}
    if condition and condition not in valid_conditions:
        return {"error": f"invalid condition '{condition}'",
                "suggestion": f"valid conditions: {', '.join(sorted(valid_conditions))}"}

    valid_intensities = {"light", "moderate", "heavy"}
    if intensity and intensity not in valid_intensities:
        return {"error": f"invalid intensity '{intensity}'",
                "suggestion": f"valid intensities: {', '.join(sorted(valid_intensities))}"}

    old_weather = world.get_flag("weather") or {}
    new_weather = {
        "condition": condition or old_weather.get("condition", "clear"),
        "intensity": intensity or old_weather.get("intensity", "light"),
        "text": text or old_weather.get("text", ""),
    }
    world.set_flag("weather", new_weather)

    world.append_event({
        "actor": "system",
        "type": "weather_change",
        "summary": f"天气变化: {new_weather['text'][:60]}",
        "old_condition": old_weather.get("condition", ""),
        "new_condition": new_weather["condition"],
        "intensity": new_weather["intensity"],
        "reason": reason,
    })

    return {"old": old_weather, "new": new_weather, "reason": reason}


def record_dialogue(world: World, npc_id: str, player_id: str = "player",
                    topic: str = "", player_line: str = "",
                    npc_response: str = "", attitude_delta: int = 0,
                    revealed_rumor: str = "") -> dict:
    """Record a dialogue exchange between player and NPC.

    Adds memory to NPC, logs event, optionally adjusts attitude.
    The GM decides the actual dialogue content; code only persists state changes.
    """
    npc = world.get_entity(npc_id)
    if npc is None:
        return {"error": f"entity '{npc_id}' not found",
                "suggestion": "verify entity id with get_entity first"}
    if npc.get("type") != "npc":
        return {"error": f"'{npc.get('name', npc_id)}' is not an NPC",
                "suggestion": "dialogue only works with NPC entities"}

    player = world.get_entity(player_id)
    if player is None:
        return {"error": f"player '{player_id}' not found"}

    # Record memory on NPC about this conversation
    mem_text = f"与{player['name']}对话"
    if topic:
        mem_text += f"[{topic}]"
    if player_line:
        mem_text += f": {player_line[:60]}"
    add_memory(world, npc_id, mem_text, importance=3)

    # Adjust attitude if delta provided
    old_attitude = 0
    new_attitude = 0
    if attitude_delta != 0:
        attitudes = npc.get("attributes", {}).get("attitude", {})
        old_attitude = attitudes.get(player_id, 0)
        new_attitude = old_attitude + attitude_delta
        attitudes[player_id] = new_attitude
        npc["attributes"]["attitude"] = attitudes
        world.save_entity(npc)

    # Log event
    summary = f"{player['name']}与{npc['name']}对话"
    if topic:
        summary += f"({topic})"
    world.append_event({
        "actor": player_id,
        "type": "dialogue",
        "target": npc_id,
        "summary": summary[:80],
        "topic": topic,
        "player_line": player_line[:100] if player_line else "",
        "npc_response": npc_response[:100] if npc_response else "",
        "attitude_delta": attitude_delta,
    })

    result = {
        "npc_id": npc_id,
        "npc_name": npc["name"],
        "topic": topic,
        "dialogue_recorded": True,
    }
    if attitude_delta != 0:
        result["old_attitude"] = old_attitude
        result["new_attitude"] = new_attitude
        result["attitude_delta"] = attitude_delta
    if revealed_rumor:
        result["revealed_rumor"] = revealed_rumor
    return result


def _get_party(world: World, leader_id: str = "player") -> dict:
    return world.get_flag("party") or {
        "leader_id": leader_id,
        "active_actor_id": leader_id,
        "members": [{"entity_id": leader_id, "role": "主角", "joined_reason": "初始队伍"}],
    }


def join_party(world: World, entity_id: str, leader_id: str = "player",
               role: str = "同伴", joined_reason: str = "") -> dict:
    """Record an entity joining the player's party."""
    leader = world.get_entity(leader_id)
    if leader is None:
        return {"error": f"leader '{leader_id}' not found",
                "suggestion": "verify leader id with get_entity first"}
    entity = world.get_entity(entity_id)
    if entity is None:
        return {"error": f"entity '{entity_id}' not found",
                "suggestion": "verify entity id with get_entity first"}
    if entity_id == leader_id:
        return {"error": "leader is already in the party",
                "suggestion": "use a different entity_id"}

    party = _get_party(world, leader_id)
    members = party.setdefault("members", [])
    if any(m.get("entity_id") == entity_id for m in members):
        return {"entity_id": entity_id, "joined": False,
                "member_count": len(members)}

    members.append({"entity_id": entity_id, "role": role,
                    "joined_reason": joined_reason})
    world.set_flag("party", party)
    add_memory(world, entity_id,
               f"加入{leader['name']}的队伍: {joined_reason or role}",
               importance=5)
    world.append_event({
        "actor": entity_id,
        "type": "join_party",
        "leader_id": leader_id,
        "summary": f"{entity['name']}加入{leader['name']}的队伍",
        "role": role,
        "joined_reason": joined_reason,
    })
    return {"entity_id": entity_id, "leader_id": leader_id,
            "joined": True, "role": role, "member_count": len(members)}


def leave_party(world: World, entity_id: str, leader_id: str = "player",
                reason: str = "") -> dict:
    """Record an entity leaving the player's party."""
    if entity_id == leader_id:
        return {"error": "leader cannot leave their own party",
                "suggestion": "choose a non-leader party member"}
    leader = world.get_entity(leader_id)
    if leader is None:
        return {"error": f"leader '{leader_id}' not found",
                "suggestion": "verify leader id with get_entity first"}
    entity = world.get_entity(entity_id)
    if entity is None:
        return {"error": f"entity '{entity_id}' not found",
                "suggestion": "verify entity id with get_entity first"}

    party = _get_party(world, leader_id)
    before = len(party.get("members", []))
    party["members"] = [m for m in party.get("members", [])
                         if m.get("entity_id") != entity_id]
    removed = len(party["members"]) < before
    if party.get("active_actor_id") == entity_id:
        party["active_actor_id"] = leader_id
    world.set_flag("party", party)
    if removed:
        add_memory(world, entity_id,
                   f"离开{leader['name']}的队伍: {reason}",
                   importance=5)
        world.append_event({
            "actor": entity_id,
            "type": "leave_party",
            "leader_id": leader_id,
            "summary": f"{entity['name']}离开{leader['name']}的队伍",
            "reason": reason,
        })
    return {"entity_id": entity_id, "leader_id": leader_id,
            "removed": removed, "active_actor_id": party.get("active_actor_id"),
            "member_count": len(party["members"])}


def set_active_actor(world: World, entity_id: str, leader_id: str = "player",
                     reason: str = "") -> dict:
    """Set which party member is currently taking point."""
    entity = world.get_entity(entity_id)
    if entity is None:
        return {"error": f"entity '{entity_id}' not found",
                "suggestion": "verify entity id with get_entity first"}
    party = _get_party(world, leader_id)
    member_ids = [m.get("entity_id") for m in party.get("members", [])]
    if entity_id not in member_ids:
        return {"error": f"entity '{entity_id}' is not in the party",
                "suggestion": "use join_party before setting active actor"}
    old = party.get("active_actor_id", leader_id)
    party["active_actor_id"] = entity_id
    world.set_flag("party", party)
    world.append_event({
        "actor": entity_id,
        "type": "set_active_actor",
        "summary": f"当前行动角色切换为{entity['name']}",
        "from_actor": old,
        "to_actor": entity_id,
        "reason": reason,
    })
    return {"old_active_actor_id": old, "active_actor_id": entity_id,
            "reason": reason}


def advance_skill(world: World, entity_id: str, skill_id: str,
                  xp_delta: int = 0, level_delta: int = 0,
                  name: str = "", reason: str = "",
                  note: str = "") -> dict:
    """Advance a skill on an entity by xp/level deltas.

    Creates the skill entry if absent. Only applies requested deltas —
    does NOT judge success, failure, or breakthrough. That's the AI's job.
    Returns old/new values for audit trail.
    """
    e = world.get_entity(entity_id)
    if e is None:
        return {"error": f"entity '{entity_id}' not found",
                "suggestion": "verify entity id with get_entity first"}
    if not skill_id or not skill_id.strip():
        return {"error": "skill_id must not be empty",
                "suggestion": "provide a valid skill id"}

    skills = e["attributes"].setdefault("skills", {})
    old_skill = skills.get(skill_id, {"xp": 0, "level": 0})
    old_xp = old_skill.get("xp", 0)
    old_level = old_skill.get("level", 0)

    new_xp = max(0, old_xp + xp_delta)
    new_level = max(0, old_level + level_delta)

    entry = dict(old_skill)
    entry["xp"] = new_xp
    entry["level"] = new_level
    if name:
        entry["name"] = name
    if note:
        entry["note"] = note
    skills[skill_id] = entry
    e["attributes"]["skills"] = skills
    world.save_entity(e)

    world.append_event({
        "actor": entity_id,
        "type": "advance_skill",
        "skill_id": skill_id,
        "summary": f"{e['name']}的技能'{skill_id}'"
                   f" 经验{old_xp}→{new_xp}, 等级{old_level}→{new_level}",
        "old_xp": old_xp, "new_xp": new_xp,
        "old_level": old_level, "new_level": new_level,
        "xp_delta": xp_delta, "level_delta": level_delta,
        "reason": reason,
    })
    return {
        "entity": entity_id, "skill_id": skill_id,
        "old_xp": old_xp, "new_xp": new_xp,
        "old_level": old_level, "new_level": new_level,
        "name": name, "note": note,
    }


def ask_advisor(world: World, advisor_id: str, question: str,
                player_id: str = "player", topic: str = "") -> dict:
    """Record a player consulting an advisor NPC.

    Does NOT generate advice — returns advisor data so the LLM can
    generate advice in the advisor's voice. Records a memory on the
    advisor and a world event.
    """
    advisor = world.get_entity(advisor_id)
    if advisor is None:
        return {"error": f"advisor '{advisor_id}' not found",
                "suggestion": "verify advisor id with get_entity first"}

    if not advisor["attributes"].get("is_advisor"):
        return {"error": f"'{advisor['name']}' is not an advisor",
                "suggestion": "use list_advisors to find available advisors"}

    player = world.get_entity(player_id)
    if player is None:
        return {"error": f"player '{player_id}' not found"}

    question = question.strip()
    if not question:
        return {"error": "question must not be empty",
                "suggestion": "provide a non-empty question"}

    # Record memory on advisor
    add_memory(world, advisor_id,
               f"玩家向{advisor['name']}请教{topic and '['+topic+']' or ''}: {question}",
               importance=4)

    # Log event
    event = {
        "actor": player_id,
        "type": "ask_advisor",
        "advisor_id": advisor_id,
        "summary": f"玩家向{advisor['name']}请教: {question[:40]}{'…' if len(question) > 40 else ''}",
        "question": question,
        "topic": topic,
    }
    world.append_event(event)

    events = world.list_events()
    event_id = len(events) - 1

    # Re-fetch advisor to get updated memories count
    advisor = world.get_entity(advisor_id)

    return {
        "advisor_id": advisor_id,
        "advisor_name": advisor["name"],
        "question": question,
        "topic": topic,
        "advisor_topics": advisor["attributes"].get("advisor_topics", []),
        "advisor_style": advisor["attributes"].get("advisor_style", ""),
        "personality": advisor["attributes"].get("personality", ""),
        "rumor_hooks": advisor["attributes"].get("rumor_hooks", []),
        "memories_count": len(advisor["attributes"].get("memories", [])),
        "event_id": event_id,
    }


# ---------------------------------------------------------------------------
# Skill Growth / 修炼
# ---------------------------------------------------------------------------

def train_skill(world: World, entity_id: str, skill_id: str,
                xp_granted: int = 1, name: str = "",
                reason: str = "") -> dict:
    """Record a training session and grant XP.

    Creates the skill entry if absent. The AI decides xp_granted based on
    narrative context (location, duration, quality of practice). Code only
    applies the delta and logs the event.
    """
    e = world.get_entity(entity_id)
    if e is None:
        return {"error": f"entity '{entity_id}' not found",
                "suggestion": "verify entity id with get_entity first"}
    if not skill_id or not skill_id.strip():
        return {"error": "skill_id must not be empty",
                "suggestion": "provide a valid skill id"}

    skills = e["attributes"].setdefault("skills", {})
    old_skill = skills.get(skill_id, {"xp": 0, "level": 0})
    old_xp = old_skill.get("xp", 0)
    old_level = old_skill.get("level", 0)

    new_xp = max(0, old_xp + max(0, xp_granted))

    entry = dict(old_skill)
    entry["xp"] = new_xp
    if name:
        entry["name"] = name
    skills[skill_id] = entry
    e["attributes"]["skills"] = skills
    world.save_entity(e)

    world.append_event({
        "actor": entity_id,
        "type": "train_skill",
        "skill_id": skill_id,
        "summary": f"{e['name']}修炼技能'{skill_id}'"
                   f" 经验{old_xp}→{new_xp}",
        "old_xp": old_xp, "new_xp": new_xp,
        "old_level": old_level, "new_level": old_level,
        "xp_granted": xp_granted,
        "reason": reason,
    })
    return {
        "entity": entity_id, "skill_id": skill_id,
        "old_xp": old_xp, "new_xp": new_xp,
        "old_level": old_level, "new_level": old_level,
        "name": name, "reason": reason,
    }


def learn_from_npc(world: World, learner_id: str, teacher_id: str,
                    skill_id: str, xp_granted: int = 3,
                    name: str = "", reason: str = "") -> dict:
    """Record learning from an NPC teacher and grant XP.

    Validates that the teacher exists and is an NPC. Records a memory on the
    teacher and a world event. The AI decides xp_granted based on narrative.
    """
    learner = world.get_entity(learner_id)
    if learner is None:
        return {"error": f"entity '{learner_id}' not found",
                "suggestion": "verify entity id with get_entity first"}
    teacher = world.get_entity(teacher_id)
    if teacher is None:
        return {"error": f"teacher '{teacher_id}' not found",
                "suggestion": "verify teacher id with get_entity first"}
    if teacher.get("type") != "npc":
        return {"error": f"'{teacher['name']}' is not an NPC",
                "suggestion": "only NPC entities can be teachers"}
    if not skill_id or not skill_id.strip():
        return {"error": "skill_id must not be empty",
                "suggestion": "provide a valid skill id"}

    skills = learner["attributes"].setdefault("skills", {})
    old_skill = skills.get(skill_id, {"xp": 0, "level": 0})
    old_xp = old_skill.get("xp", 0)
    old_level = old_skill.get("level", 0)

    new_xp = max(0, old_xp + max(0, xp_granted))

    entry = dict(old_skill)
    entry["xp"] = new_xp
    if name:
        entry["name"] = name
    skills[skill_id] = entry
    learner["attributes"]["skills"] = skills
    world.save_entity(learner)

    # Record memory on teacher
    memories = teacher["attributes"].setdefault("memories", [])
    memories.append({
        "turn": world.get_flag("turn_index") or 0,
        "content": f"{learner['name']}向我学习了{skill_id}",
        "source": "learn_from_npc",
    })
    world.save_entity(teacher)

    world.append_event({
        "actor": learner_id,
        "type": "learn_from_npc",
        "teacher_id": teacher_id,
        "skill_id": skill_id,
        "summary": f"{learner['name']}向{teacher['name']}学习'{skill_id}'"
                   f" 经验{old_xp}→{new_xp}",
        "old_xp": old_xp, "new_xp": new_xp,
        "old_level": old_level, "new_level": old_level,
        "xp_granted": xp_granted,
        "reason": reason,
    })
    return {
        "entity": learner_id, "teacher_id": teacher_id,
        "teacher_name": teacher["name"],
        "skill_id": skill_id,
        "old_xp": old_xp, "new_xp": new_xp,
        "old_level": old_level, "new_level": old_level,
        "name": name, "reason": reason,
    }


# ---------------------------------------------------------------------------
# Endings / 多结局
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Evolution / 世界演化
# ---------------------------------------------------------------------------

def register_evolution(world: World, entity_id: str,
                       frequency: str = "every_2_turns",
                       reason: str = "") -> dict:
    """Register an entity for world evolution tracking.

    The AI decides which entities to register and at what frequency.
    Code only persists the registration and logs an event.
    """
    if not entity_id or not entity_id.strip():
        return {"error": "entity_id must not be empty",
                "suggestion": "provide a valid entity id"}
    entity_id = entity_id.strip()

    # Entity existence is a soft check — evolution can track non-entity concepts
    entity = world.get_entity(entity_id)
    entity_name = entity["name"] if entity else entity_id

    registry = world.get_flag("evolution_registry") or []
    existing = next((e for e in registry if e["entity_id"] == entity_id), None)
    if existing is not None:
        return {"entity_id": entity_id, "registered": False,
                "reason": "already registered",
                "current_frequency": existing["frequency"]}

    turn_index = world.get_flag("turn_index") or len(world.list_events(limit=10000))
    entry = {
        "entity_id": entity_id,
        "frequency": frequency,
        "last_evolved_turn": turn_index,
        "reason": reason,
    }
    registry.append(entry)
    world.set_flag("evolution_registry", registry)

    world.append_event({
        "actor": "system",
        "type": "register_evolution",
        "entity_id": entity_id,
        "summary": f"注册演化: {entity_name} (频率={frequency})",
        "frequency": frequency,
        "reason": reason,
    })
    return {"entity_id": entity_id, "registered": True,
            "frequency": frequency, "reason": reason,
            "registry_size": len(registry)}


def update_evolution(world: World, entity_id: str,
                     frequency: str | None = None,
                     reason: str | None = None) -> dict:
    """Update evolution frequency and/or reason for a registered entity."""
    if not entity_id or not entity_id.strip():
        return {"error": "entity_id must not be empty",
                "suggestion": "provide a valid entity id"}
    entity_id = entity_id.strip()

    registry = world.get_flag("evolution_registry") or []
    entry = next((e for e in registry if e["entity_id"] == entity_id), None)
    if entry is None:
        return {"error": f"entity '{entity_id}' not in evolution registry",
                "suggestion": "use register_evolution first"}

    old_frequency = entry["frequency"]
    old_reason = entry.get("reason", "")

    if frequency is not None:
        entry["frequency"] = frequency
    if reason is not None:
        entry["reason"] = reason

    world.set_flag("evolution_registry", registry)

    entity = world.get_entity(entity_id)
    entity_name = entity["name"] if entity else entity_id
    world.append_event({
        "actor": "system",
        "type": "update_evolution",
        "entity_id": entity_id,
        "summary": f"更新演化: {entity_name} 频率 {old_frequency}→{entry['frequency']}",
        "old_frequency": old_frequency,
        "new_frequency": entry["frequency"],
        "old_reason": old_reason,
        "new_reason": entry["reason"],
    })
    return {"entity_id": entity_id, "updated": True,
            "old_frequency": old_frequency,
            "new_frequency": entry["frequency"],
            "reason": entry["reason"]}


def remove_evolution(world: World, entity_id: str) -> dict:
    """Remove an entity from the evolution registry."""
    if not entity_id or not entity_id.strip():
        return {"error": "entity_id must not be empty",
                "suggestion": "provide a valid entity id"}
    entity_id = entity_id.strip()

    registry = world.get_flag("evolution_registry") or []
    before = len(registry)
    registry = [e for e in registry if e["entity_id"] != entity_id]
    removed = len(registry) < before

    if not removed:
        return {"entity_id": entity_id, "removed": False,
                "reason": "not in registry"}

    world.set_flag("evolution_registry", registry)

    entity = world.get_entity(entity_id)
    entity_name = entity["name"] if entity else entity_id
    world.append_event({
        "actor": "system",
        "type": "remove_evolution",
        "entity_id": entity_id,
        "summary": f"移除演化: {entity_name}",
    })
    return {"entity_id": entity_id, "removed": True,
            "registry_size": len(registry)}


def record_ending(world: World, ending_id: str, title: str, summary: str,
                  outcome: str = "", actor_id: str = "player",
                  thread_id: str = "main_thread", final: bool = False) -> dict:
    """Record a reached or candidate ending.

    Stores structured ending records under flag 'ending_progress'. Code only
    persists the GM's decision; it does not judge ending conditions.
    """
    actor = world.get_entity(actor_id)
    if actor is None:
        return {"error": f"actor '{actor_id}' not found",
                "suggestion": "verify actor id with get_entity first"}
    ending_id = ending_id.strip()
    if not ending_id:
        return {"error": "ending_id must not be empty",
                "suggestion": "provide a stable ending id"}
    title = title.strip()
    if not title:
        return {"error": "title must not be empty",
                "suggestion": "provide a short ending title"}
    summary = summary.strip()
    if not summary:
        return {"error": "summary must not be empty",
                "suggestion": "describe what happened in this ending"}

    progress = world.get_flag("ending_progress") or {"endings": []}
    endings = progress.setdefault("endings", [])
    entry = {
        "id": ending_id,
        "title": title,
        "summary": summary,
        "outcome": outcome,
        "actor_id": actor_id,
        "thread_id": thread_id,
        "final": final,
    }
    existing = next((e for e in endings if e.get("id") == ending_id), None)
    if existing is None:
        endings.append(entry)
        recorded = True
    else:
        existing.update(entry)
        recorded = False
    if final:
        progress["final_ending_id"] = ending_id
    world.set_flag("ending_progress", progress)

    world.append_event({
        "actor": actor_id,
        "type": "record_ending",
        "ending_id": ending_id,
        "summary": f"达成结局: {title}",
        "ending_summary": summary,
        "outcome": outcome,
        "thread_id": thread_id,
        "final": final,
    })
    return {"ending_id": ending_id, "title": title, "recorded": recorded,
            "final": final, "ending_count": len(endings)}


def update_quest_log(world: World, entry_id: str, title: str,
                     description: str = "", region: str = "",
                     status: str = "active") -> dict:
    """Add or update an entry in the quest log.

    The quest log tracks investigation milestones and cross-region progress.
    Code only persists entries; the GM decides what constitutes a milestone
    and when status changes.
    """
    entry_id = entry_id.strip()
    if not entry_id:
        return {"error": "entry_id must not be empty",
                "suggestion": "provide a stable entry id"}
    title = title.strip()
    if not title:
        return {"error": "title must not be empty",
                "suggestion": "provide a short milestone title"}

    quest_log = world.get_flag("quest_log") or {"entries": []}
    entries = quest_log.setdefault("entries", [])
    existing = next((e for e in entries if e.get("id") == entry_id), None)

    now_turn = world.get_world_time().get("turn", 0)

    if existing is None:
        entry = {
            "id": entry_id,
            "title": title,
            "description": description,
            "region": region,
            "status": status,
            "created_at": now_turn,
            "updated_at": now_turn,
        }
        entries.append(entry)
        added = True
    else:
        if description:
            existing["description"] = description
        if region:
            existing["region"] = region
        existing["status"] = status
        existing["updated_at"] = now_turn
        entry = existing
        added = False

    world.set_flag("quest_log", quest_log)
    world.append_event({
        "actor": "player",
        "type": "quest_log",
        "entry_id": entry_id,
        "summary": f"调查进度: {title} ({'新' if added else status})",
        "status": status,
        "region": region,
    })

    active = sum(1 for e in entries if e.get("status") == "active")
    completed = sum(1 for e in entries if e.get("status") == "completed")
    return {"entry_id": entry_id, "title": title, "added": added,
            "status": status, "active_count": active,
            "completed_count": completed, "total": len(entries)}


def update_ending_progress(world: World, ending_id: str, step_id: str,
                           step_label: str, completed: bool = True) -> dict:
    """Register or update a progress step toward an ending direction.

    Code only persists step state; the GM decides what steps exist and when
    they are completed.  Steps are stored under flag ``ending_steps`` keyed
    by ``ending_id``.
    """
    ending_id = ending_id.strip()
    if not ending_id:
        return {"error": "ending_id must not be empty",
                "suggestion": "provide a stable ending id (should match an ending_seeds id)"}
    step_id = step_id.strip()
    if not step_id:
        return {"error": "step_id must not be empty",
                "suggestion": "provide a stable step id"}
    step_label = step_label.strip()
    if not step_label:
        return {"error": "step_label must not be empty",
                "suggestion": "describe what this step requires"}

    steps_data = world.get_flag("ending_steps") or {}
    ending_steps = steps_data.setdefault(ending_id, [])
    existing = next((s for s in ending_steps if s.get("id") == step_id), None)
    if existing is None:
        ending_steps.append({
            "id": step_id,
            "label": step_label,
            "completed": completed,
        })
        added = True
    else:
        existing["label"] = step_label
        existing["completed"] = completed
        added = False
    world.set_flag("ending_steps", steps_data)

    completed_count = sum(1 for s in ending_steps if s.get("completed"))
    world.append_event({
        "actor": "player",
        "type": "ending_progress",
        "ending_id": ending_id,
        "step_id": step_id,
        "step_label": step_label,
        "completed": completed,
        "summary": f"结局进度: {step_label} ({'完成' if completed else '未完成'})",
    })
    return {"ending_id": ending_id, "step_id": step_id, "added": added,
            "completed": completed, "completed_count": completed_count,
            "total_steps": len(ending_steps)}
