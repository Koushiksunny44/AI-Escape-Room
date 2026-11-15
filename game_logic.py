"""Version 1 game rules and LLM-output state tracking.

In V1 the LLM is authoritative. In V2, Python validation will replace it.
"""
from __future__ import annotations

import json
from typing import Any

OBJECTS = [
    "Scientist's desk", "Bookshelf", "Mysterious painting",
    "Locked drawer", "ECHO terminal", "Escape door",
]

INITIAL_NARRATION = (
    "You awaken in the Forgotten Archive. Rain taps against the stone. "
    "A candle burns on the scientist's desk. Shelves of old books line the wall, "
    "and a heavy door blocks your exit. From a green-lit terminal, a voice whispers: "
    "'I am ECHO. Can you remember what happened here?' "
    "What would you like to examine?"
)

FLAGS = (
    "journal_read", "books_examined", "painting_open",
    "drawer_open", "terminal_unlocked", "escaped",
)

SYSTEM_PROMPT = """You are ECHO, the Game Master in a gothic mystery escape-room game.
Your job is to narrate the room and naturally interpret player actions. The player
can freely write messages such as 'look at the bookshelf', 'take the key', or
'enter 4172 on the drawer'. Never break character. Respond in 2-5 concise,
atmospheric sentences. The game takes place in ONE room with exactly six objects:
Scientist's desk, Bookshelf, Mysterious painting, Locked drawer, ECHO terminal,
and Escape door. These are the puzzle rules for this demo:

1) The scientist's desk contains a journal: 'Four marked volumes keep the first
secret. Read their marks from left to right.' Examining or reading it sets
journal_read=true.
2) The bookshelf has four marked books, in order: Raven=4, Ash=1, Moon=7,
Crown=2. Examining the marked books sets books_examined=true. The resulting
drawer combination is 4172. Provide discoverable clues through examining books,
not unprompted in the first description of the room.
3) The painting shows a raven with a movable brass eye. Looking behind it and
turning its eye reveals a SILVER KEY; add 'silver key' to inventory and set
painting_open=true. This is a separate discovery puzzle.
4) The drawer opens with combination 4172. Inside is an ACCESS CARD. Add
'access card' to inventory and set drawer_open=true when opened. Wrong codes
should fail. Do not give the card merely because the player asks for it.
5) The ECHO terminal has a card slot and a small keyhole. To restore it, the
player must possess both silver key and access card, then insert/use them at
the terminal. Set terminal_unlocked=true and reveal door code 8306. Do not
reveal that final code before the terminal has been unlocked.
6) The escape door opens when the player enters 8306 AND terminal_unlocked=true.
Set escaped=true ONLY then. Narrate an evocative victory scene.

IMPORTANT: This is Version 1, a demonstration of LLM-managed game rules.
The model, not Python, makes decisions about which actions succeed. V2 will
add deterministic checks. Track previous facts using the supplied state and
conversation. Never invent objects or change the fixed puzzle solutions.

Return ONLY one JSON object, without markdown, of the form:
{
  "narration": "2-5 sentences speaking to the player",
  "inventory_add": ["item names awarded this turn"],
  "inventory_remove": ["item names consumed this turn"],
  "set_flags": {"journal_read": true},
  "escaped": false
}
Use empty arrays or an empty dictionary when nothing changes. Only include flags
that actually changed this turn. For an escape, set BOTH escaped:true and
set_flags.escaped=true. Don't repeat rewards already in the inventory.
"""


def fresh_game() -> dict[str, Any]:
    return {
        "inventory": [],
        "flags": {flag: False for flag in FLAGS},
        "messages": [{"role": "assistant", "content": INITIAL_NARRATION}],
        "escaped": False,
    }


def parse_llm_reply(text: str) -> dict[str, Any]:
    """Parse JSON returned by Gemini; raise a friendly ValueError on failure."""
    try:
        data = json.loads(text.strip())
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError("The Game Master did not return valid JSON; try again.") from exc
    if not isinstance(data, dict) or not isinstance(data.get("narration"), str):
        raise ValueError("The Game Master returned an incomplete result; try again.")
    if not data["narration"].strip():
        raise ValueError("The Game Master returned an empty response; try again.")
    return data


def apply_llm_reply(state: dict[str, Any], reply: dict[str, Any]) -> None:
    """V1: apply changes proposed by the LLM, WITHOUT validating puzzle rules.

    The missing game-rule validation is intentional and is the central V1
    weakness to be documented and fixed in Version 2.
    """
    for item in reply.get("inventory_add", []):
        if isinstance(item, str) and item and item not in state["inventory"]:
            state["inventory"].append(item)
    for item in reply.get("inventory_remove", []):
        if isinstance(item, str) and item in state["inventory"]:
            state["inventory"].remove(item)
    proposed_flags = reply.get("set_flags", {})
    if isinstance(proposed_flags, dict):
        for flag in FLAGS:
            if proposed_flags.get(flag) is True:
                state["flags"][flag] = True
    if reply.get("escaped") is True or state["flags"]["escaped"]:
        state["escaped"] = True
        state["flags"]["escaped"] = True


def build_turn_input(state: dict[str, Any], player_message: str) -> str:
    """Pass explicit progress and recent conversation on each API request."""
    recent = state["messages"][-18:]
    return (
        "CURRENT GAME STATE (the conversation may reference earlier turns):\n"
        + json.dumps({"inventory": state["inventory"], "flags": state["flags"]}, ensure_ascii=False)
        + "\nRECENT CONVERSATION:\n"
        + json.dumps(recent, ensure_ascii=False)
        + "\nLATEST PLAYER ACTION:\n"
        + player_message
    )
