"""The Forgotten Archive — Version 1 LLM-managed escape room."""
import os

import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types

from game_logic import (
    OBJECTS,
    SYSTEM_PROMPT,
    apply_llm_reply,
    build_turn_input,
    fresh_game,
    parse_llm_reply,
)

load_dotenv()
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

st.set_page_config(page_title="The Forgotten Archive | AI Escape Room", page_icon="🔐", layout="wide")
st.markdown(
    """<style>
    .stApp {background: radial-gradient(circle at 70% 5%, #22282a 0%, #141718 48%, #0e1112 100%);}
    h1, h2, h3 {letter-spacing: 0.03em;}
    [data-testid="stChatMessage"] {border: 1px solid #4a4031; border-radius: 12px;}
    </style>""",
    unsafe_allow_html=True,
)

if "archive_v1" not in st.session_state:
    st.session_state.archive_v1 = fresh_game()
state = st.session_state.archive_v1

st.title("🔐 THE FORGOTTEN ARCHIVE")
st.caption("VERSION 1 · A natural-language escape room powered by Gemini")

chat_col, info_col = st.columns([1.8, 1], gap="large")

with info_col:
    st.subheader("🏰 The Archive")
    preview = "assets/room_preview.png"
    if os.path.isfile(preview):
        st.image(preview, caption="Our Blender environment", use_container_width=True)
    else:
        st.info("Your Blender room will be shown here. Add an optional render at assets/room_preview.png.")

    st.markdown("**Objects you can investigate**")
    for name in OBJECTS:
        st.write("• " + name)

    st.markdown("**🎒 Inventory**")
    if state["inventory"]:
        for item in state["inventory"]:
            st.write("• " + item.title())
    else:
        st.caption("Empty — examine the room for useful items.")

    st.markdown("**🧩 Progress**")
    progress_labels = {
        "journal_read": "Journal discovered",
        "books_examined": "Marked books examined",
        "painting_open": "Painting secret found",
        "drawer_open": "Drawer unlocked",
        "terminal_unlocked": "ECHO terminal restored",
        "escaped": "Escaped the archive",
    }
    for flag, label in progress_labels.items():
        st.write(("✅ " if state["flags"][flag] else "○ ") + label)

    if st.button("↻ Restart game", use_container_width=True):
        st.session_state.archive_v1 = fresh_game()
        st.rerun()

    with st.expander("How to play"):
        st.write(
            "Use natural language: 'examine the desk', 'look behind the painting', "
            "'take the key', or 'enter a code on the door'. Explore six objects, "
            "solve three linked clues, and unlock the exit."
        )

with chat_col:
    st.subheader("ECHO — AI Game Master")
    if not API_KEY:
        st.warning("Add GEMINI_API_KEY to a .env file, then restart Streamlit to enable Gemini chat.")
    for message in state["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if state["escaped"]:
        st.success("YOU ESCAPED THE FORGOTTEN ARCHIVE! Press 'Restart game' to play again.")
        st.balloons()

    player_input = st.chat_input(
        "What would you like to do?",
        disabled=(not API_KEY or state["escaped"]),
    )

    if player_input and player_input.strip():
        player_input = player_input.strip()[:1200]
        turn_input = build_turn_input(state, player_input)
        with st.chat_message("user"):
            st.markdown(player_input)
        with st.chat_message("assistant"):
            with st.spinner("ECHO is thinking..."):
                try:
                    client = genai.Client(api_key=API_KEY)
                    response = client.models.generate_content(
                        model=MODEL,
                        contents=turn_input,
                        config=types.GenerateContentConfig(
                            system_instruction=SYSTEM_PROMPT,
                            response_mime_type="application/json",
                            temperature=0.4,
                            max_output_tokens=800,
                        ),
                    )
                    reply = parse_llm_reply(response.text or "")
                except Exception as exc:
                    st.error("Gemini request failed. Check your key, model access, and quota. "
                             f"Details: {type(exc).__name__}: {exc}")
                else:
                    # Only commit user action and progress after a successful API reply.
                    apply_llm_reply(state, reply)
                    state["messages"].append({"role": "user", "content": player_input})
                    state["messages"].append({"role": "assistant", "content": reply["narration"]})
                    st.markdown(reply["narration"])
                    st.rerun()
