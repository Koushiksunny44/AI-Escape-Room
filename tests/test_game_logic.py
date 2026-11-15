import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from game_logic import fresh_game, parse_llm_reply, apply_llm_reply, build_turn_input


def test_new_game_starts_with_six_flags_and_empty_inventory():
    state = fresh_game()
    assert state["inventory"] == []
    assert len(state["flags"]) == 6
    assert not state["escaped"]


def test_llm_result_updates_inventory_and_flag():
    state = fresh_game()
    result = parse_llm_reply(json.dumps({
        "narration": "You find a small silver key.",
        "inventory_add": ["silver key"],
        "inventory_remove": [],
        "set_flags": {"painting_open": True},
        "escaped": False,
    }))
    apply_llm_reply(state, result)
    assert "silver key" in state["inventory"]
    assert state["flags"]["painting_open"] is True


def test_history_and_state_included_in_prompt():
    state = fresh_game()
    state["inventory"] = ["silver key"]
    prompt = build_turn_input(state, "inspect ECHO terminal")
    assert "silver key" in prompt
    assert "inspect ECHO terminal" in prompt
    assert "CURRENT GAME STATE" in prompt


def test_v1_weakness_llm_can_falsely_claim_escape():
    state = fresh_game()
    apply_llm_reply(state, {"escaped": True, "set_flags": {}, "inventory_add": [], "inventory_remove": []})
    assert state["escaped"] is True  # Version 2 will prevent this.
