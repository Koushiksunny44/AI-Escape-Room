"""Run: python -m streamlit run app_v2.py. V1 remains app.py."""
import os
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv
from google import genai
from v2_engine import GameState, Action, apply_action, public_state
from v2_ai import parse_player, narrate
from visual_views import VIEWS

load_dotenv()
KEY=os.getenv('GEMINI_API_KEY','').strip()
MODEL=os.getenv('GEMINI_MODEL','gemini-3.8-flash')
ASSETS=Path(__file__).resolve().parent/'assets'
INTRO='You awaken in the Forgotten Archive. ECHO flickers on the old terminal. Examine the objects, collect the key and card, restore ECHO, and unlock the exit. You can type natural-language actions or select a view.'
st.set_page_config(page_title='The Forgotten Archive | Version 2',page_icon='🔐',layout='wide')
st.markdown('''<style>.stApp {background:radial-gradient(circle at 70% 5%,#29251e,#15191a 55%,#0e1112);} h1,h2,h3 {letter-spacing:.04em;} [data-testid="stChatMessage"] {border:1px solid #4a4031;border-radius:12px;}</style>''',unsafe_allow_html=True)

def reset():
    st.session_state.v2_state=GameState(); st.session_state.v2_view='room'
    st.session_state.v2_messages=[('assistant',INTRO,'')]
if 'v2_state' not in st.session_state: reset()
s=st.session_state.v2_state

def submit(message, action=None):
    flavor=''
    if action is None:
        try:
            client=genai.Client(api_key=KEY)
            action=parse_player(client,MODEL,s,message)
        except Exception:
            # Avoid printing SDK exception strings which could contain private configuration.
            st.error('Gemini could not interpret your request. Check your model, key or quota privately and retry.')
            return
    result=apply_action(s,action,message)
    if result.view in VIEWS: st.session_state.v2_view=result.view
    if KEY:
        try: flavor=narrate(genai.Client(api_key=KEY),MODEL,result,s)
        except Exception: flavor=''
    st.session_state.v2_messages.extend([('user',message,''),('assistant',result.text,flavor)])
    st.rerun()

st.title('🔐 THE FORGOTTEN ARCHIVE')
st.caption('VERSION 2 · Gemini language interaction · Python-validated gameplay')
left,right=st.columns([1.25,1],gap='large')
with left:
    st.subheader('The Archive')
    label,filename=VIEWS[st.session_state.v2_view]
    if (ASSETS/filename).is_file(): st.image(str(ASSETS/filename),caption=label,use_container_width=True)
    else: st.info('Missing image: '+filename)
    st.caption('Inspect objects using the controls or natural language. Every action is validated by Python.')
    cols=st.columns(3)
    for i,(target,(name,_)) in enumerate(VIEWS.items()):
        with cols[i%3]:
            if st.button(name,key='v2_'+target,use_container_width=True,disabled=s.escaped):
                submit('Inspect '+name,Action('inspect',target))
    st.subheader('Inventory')
    st.write(' · '.join(sorted(s.inventory)) or 'Empty')
    st.subheader('Progress')
    for flag,name in [('journal_read','Journal discovered'),('books_examined','Marked books examined'),('painting_open','Silver key found'),('drawer_open','Access card found'),('terminal_unlocked','ECHO restored'),('escaped','Escaped')]:
        st.write(('✅ ' if getattr(s,flag) else '○ ')+name)
    if st.button('Restart game',use_container_width=True): reset();st.rerun()
with right:
    st.subheader('ECHO — AI Game Master')
    if not KEY: st.warning('Configure GEMINI_API_KEY privately in .env and restart. Visual inspection still works.')
    for role,content,flavor in st.session_state.v2_messages:
        with st.chat_message(role):
            if flavor: st.caption(flavor)
            st.write(content)
    if s.escaped: st.success('YOU ESCAPED THE FORGOTTEN ARCHIVE!')
    if message:=st.chat_input('What would you like to do?',disabled=not KEY or s.escaped):
        with st.spinner('ECHO is listening…'):
            submit(message.strip()[:1200])
