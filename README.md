# The Forgotten Archive — Version 1

**Deep Learning & Generative AI mini-project:** A one-room, natural-language escape game, with Gemini as the Game Master.

## Features

- Streamlit web UI with Gemini conversational Game Master
- Six room objects, three discovery/logic puzzles, and final exit code
- Natural language actions: examine, collect, solve, enter a combination
- Session-scoped inventory, progress flags, and chat history
- Opening introduction, instructions, restart and escape screen
- Optional Blender render preview (`assets/room_preview.png`)

## Install (Windows PowerShell)

```powershell
cd AI_Escape_Room_V1
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Open `.env` and replace `put_your_api_key_here` with an API key created at https://aistudio.google.com/apikey. Never commit the `.env` file.

```powershell
python -m streamlit run app.py
```

Choose a model that your AI Studio project can access. The default is `gemini-3.8-flash`. To change it, edit `GEMINI_MODEL` inside `.env` and restart the app. Free access and daily quotas vary by project/model; check https://ai.google.dev/gemini-api/docs/rate-limits.

## Gameplay path (spoilers)

1. Read scientist's desk journal.
2. Investigate the marked books: Raven 4, Ash 1, Moon 7, Crown 2.
3. Turn the raven's eye in the painting and take the silver key.
4. Enter `4172` on locked drawer to find the access card.
5. Insert the key and access card into the ECHO terminal to learn `8306`.
6. Enter `8306` at the door; win.

## Important assignment distinction

**Version 1 is intentionally LLM-managed:** Gemini decides which game actions succeeded and sends state updates for Streamlit to remember. Although it tries to follow game rules, it can be manipulated into inconsistent outcomes. This is **the baseline limitation** that the assignment's Version 2 must fix: in Version 2, Python functions will validate each action and update game state before Gemini narrates it.

There is no actual 3D interaction in Version 1: the Blender render is optional and visual only. Next phase: wire selectable 3D objects to the same Python action pipeline.

## Tests

```powershell
python -m pytest -q
```

Tests exercise local state and explicitly demonstrate that V1 can mistakenly accept an LLM claim of escape. Live Gemini requests require your own API key and are not exercised by tests.
