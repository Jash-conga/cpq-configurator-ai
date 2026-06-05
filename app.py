import sys
import os
import subprocess
import json
from pathlib import Path
import traceback
from copy import deepcopy

root_path = Path(__file__).resolve().parent
sys.path.insert(0, str(root_path))
sys.path.insert(0, str(root_path / "backend"))

if sys.platform == "win32":
    sys.stdout.reconfigure(errors="backslashreplace")
    sys.stderr.reconfigure(errors="backslashreplace")

import streamlit as st
from dotenv import load_dotenv
load_dotenv()

st.set_page_config(
    page_title="Conga CPQ Agentic Builder",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,100..900;1,14..32,100..900&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, .stApp, .stApp input, .stApp button, .stApp select, .stApp textarea {
    font-family: 'Inter', sans-serif;
}

/* ═══════════════════════════════════════════════════════════════
   100VH — lock whole app, no page scroll
═══════════════════════════════════════════════════════════════ */
html, body {
    height: 100vh !important;
    max-height: 100vh !important;
    overflow: hidden !important;
}
.stApp {
    background: #060608 !important;
    height: 100vh !important;
    max-height: 100vh !important;
    overflow: hidden !important;
}
[data-testid="stAppViewContainer"] {
    height: 100vh !important;
    max-height: 100vh !important;
    overflow: hidden !important;
}
/* 1. Completely hide the empty Streamlit top header bar */
header[data-testid="stHeader"] {
    display: none !important;
    height: 0px !important;
}

/* 2. Force all possible main container wrappers to consistent top padding */
.block-container, 
[data-testid="stAppViewBlockContainer"], 
.stMainBlockContainer {
    padding-top: 5px !important; 
    margin-top: 0px !important;
}

/* Scoped exclusively to the right chat panel layout wrapper */
.panel-scroll-right div[data-testid="stVerticalBlockBorderWrapper"] > div,
.panel-scroll-right [data-testid="stChatMessageContainer"] {
    background: #ffffff !important;  /* <-- CHANGE THIS TO YOUR DESIRED CHAT BACKGROUND COLOR */
}
/* Main block container — no scrolling at this level */
.block-container {
    padding-top: 0 !important;
    margin-top: 0 !important;
    padding-bottom: 0 !important;
    max-width: 100% !important;
    overflow: hidden !important;
}


/* ═══════════════════════════════════════════════════════════════
   SPLIT PANE — JS stamps .split-left / .split-right / #split-divider
   directly on the column elements; CSS targets those classes.
═══════════════════════════════════════════════════════════════ */

/* The stHorizontalBlock that wraps the two main columns */
.main-split-row {
    display: flex !important;
    flex-direction: row !important;
    width: 100% !important;
    height: calc(100vh - 84px) !important;
    gap: 0 !important;
    overflow: hidden !important;
    align-items: stretch !important;
}

/* Column wrappers — JS stamps .split-left / .split-right on the [data-testid="column"] elements */
.split-left {
    flex-shrink: 0 !important;
    height: 100% !important;
    overflow: hidden !important;
    display: flex !important;
    flex-direction: column !important;
}
.split-right {
    flex: 1 !important;
    min-width: 0 !important;
    height: 100% !important;
    overflow: hidden !important;
    display: flex !important;
    flex-direction: column !important;
}
/* All intermediate wrappers between column and scroll surface must pass height through */
.split-left > div, .split-left > div > div,
.split-right > div, .split-right > div > div {
    height: 100% !important;
    min-height: 0 !important;
    overflow: hidden !important;
    display: flex !important;
    flex-direction: column !important;
    flex: 1 !important;
}

/* JS walks the DOM and stamps .panel-scroll-left / .panel-scroll-right
   directly on whatever stVerticalBlock it finds — no depth assumptions */
.panel-scroll-left {
    flex: 1 !important;
    min-height: 0 !important;
    height: unset !important;
    overflow-y: auto !important;
    overflow-x: hidden !important;
    background: #0D0D16 !important;
    border-radius: 12px 0 0 12px !important;
    padding: 16px !important;
    border-right: 2px solid rgba(255,255,255,0.22) !important;
    box-shadow: 2px 0 8px rgba(132,108,248,0.18) !important;
    scrollbar-width: thin !important;
    scrollbar-color: rgba(132,108,248,0.55) rgba(132,108,248,0.07) !important;
}
.panel-scroll-left::-webkit-scrollbar { width: 6px; }
.panel-scroll-left::-webkit-scrollbar-track { background: rgba(132,108,248,0.07); border-radius: 3px; }
.panel-scroll-left::-webkit-scrollbar-thumb { background: rgba(132,108,248,0.55); border-radius: 3px; }
.panel-scroll-left::-webkit-scrollbar-thumb:hover { background: rgba(132,108,248,0.8); }

.panel-scroll-right {
    flex: 1 !important;
    min-height: 0 !important;
    height: unset !important;
    overflow-y: auto !important;
    overflow-x: hidden !important;
    background: #ffffff !important;
    border-radius: 0 12px 12px 0 !important;
    padding: 16px !important;
    scrollbar-width: thin !important;
    scrollbar-color: rgba(132,108,248,0.4) rgba(132,108,248,0.05) !important;
}
.panel-scroll-right::-webkit-scrollbar { width: 6px; }
.panel-scroll-right::-webkit-scrollbar-track { background: rgba(132,108,248,0.05); border-radius: 3px; }
.panel-scroll-right::-webkit-scrollbar-thumb { background: rgba(132,108,248,0.4); border-radius: 3px; }
.panel-scroll-right::-webkit-scrollbar-thumb:hover { background: rgba(132,108,248,0.65); }

/* ── DRAGGABLE DIVIDER ── */
#split-divider {
    width: 12px !important;
    flex-shrink: 0 !important;
    background: rgba(255,255,255,0.04) !important;
    cursor: col-resize !important;
    position: relative !important;
    z-index: 999 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    transition: background 0.15s !important;
    /* Always-visible track line */
    border-left: 1px solid rgba(255,255,255,0.14) !important;
    border-right: 1px solid rgba(255,255,255,0.06) !important;
}
#split-divider::after {
    content: '' !important;
    display: block !important;
    width: 4px !important;
    height: 48px !important;
    background: rgba(255,255,255,0.3) !important;
    border-radius: 4px !important;
    transition: all 0.15s !important;
}
#split-divider:hover {
    background: rgba(132,108,248,0.12) !important;
    border-left-color: rgba(132,108,248,0.6) !important;
}
#split-divider:hover::after,
#split-divider.is-dragging::after {
    background: #846cf8 !important;
    height: 72px !important;
    box-shadow: 0 0 10px rgba(132,108,248,0.6) !important;
}
#split-divider.is-dragging {
    background: rgba(132,108,248,0.15) !important;
    border-left-color: #846cf8 !important;
}

.stMarkdown p { color: #ffffff !important; font-size: 14px !important; font-weight: 400 !important; line-height: 1.6 !important; }

/* ── TYPOGRAPHY SCALE ── */
.app-title    { font-size: 32px !important; font-weight: 700 !important; color: #ffffff !important; }
.section-header { font-size: 20px !important; font-weight: 600 !important; color: #ffffff !important; }
.card-title   { font-size: 16px !important; font-weight: 600 !important; color: #ffffff !important; }
.body-text    { font-size: 14px !important; font-weight: 400 !important; color: #ffffff !important; }
.meta-label   { font-size: 13px !important; font-weight: 500 !important; color: rgba(255,255,255,0.7) !important; }
.badge-text   { font-size: 12px !important; font-weight: 600 !important; }

#MainMenu, footer, header { visibility: hidden !important; display: none !important; }
.block-container { padding: 0 24px !important; padding-top: 0 !important; margin-top: 0 !important; max-width: 100% !important; overflow: hidden !important; }
section[data-testid="stSidebar"] { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }
.stAppHeader { display: none !important; }

/* ═══════════════════════════════════════════════════════════════
   UNIFIED NAVBAR — single st.columns row styled as one bar
   The entire [nav_left | nav_right] horizontal block gets the
   navbar background/border via CSS, making it look like one bar.
═══════════════════════════════════════════════════════════════ */

/* Target the navbar columns wrapper — give the whole row the bar style */
.navbar-row [data-testid="stHorizontalBlock"] {
    background: #111118 !important;
    border: 1px solid rgba(132,108,248,0.2) !important;
    border-radius: 14px !important;
    height: 64px !important;
    margin-top: -100px !important;
    align-items: center !important;
    padding: 0 8px 0 20px !important;
    margin-bottom: 16px !important;
    box-shadow: 0 2px 20px rgba(0,0,0,0.4) !important;
    gap: 0 !important;
}

/* Strip column inner padding so content sits flush in the bar */
.navbar-row [data-testid="stHorizontalBlock"] > [data-testid="column"] > div:first-child {
    padding: 0 !important;
    display: flex !important;
    align-items: center !important;
    height: 64px !important;
}

/* Left column: brand takes all available space */
.navbar-row [data-testid="stHorizontalBlock"] > [data-testid="column"]:first-child {
    flex: 1 1 auto !important;
}

/* Right columns: shrink to button size */
.navbar-row [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(2),
.navbar-row [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(3) {
    flex: 0 0 44px !important;
    max-width: 44px !important;
    min-width: 44px !important;
}

/* Override the Streamlit column background inside the navbar */
.navbar-row [data-testid="column"] > div:first-child {
    background: transparent !important;
    border-radius: 0 !important;
    height: 64px !important;
    overflow: visible !important;
}

/* ── NAV BRAND (inside left column) ── */
.nav-brand {
    display: flex;
    align-items: center;
    gap: 12px;
}
.nav-logo {
    width: 36px; height: 36px;
    background: linear-gradient(135deg, #5b2d8e, #846cf8);
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 17px; flex-shrink: 0;
    box-shadow: 0 0 12px rgba(132,108,248,0.35), 0 0 24px rgba(132,108,248,0.15);
}
.nav-title {
    font-size: 36px;
    font-weight: 700;
    color: #ffffff;
    letter-spacing: -0.3px;
    white-space: nowrap;
}
.nav-pill {
    font-size: 10px; font-weight: 600;
    color: #846cf8;
    background: rgba(132,108,248,0.12);
    border: 1px solid rgba(132,108,248,0.35);
    border-radius: 20px;
    padding: 3px 9px;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    white-space: nowrap;
}
.nav-status {
    display: flex;
    align-items: center;
    gap: 7px;
    margin-left: auto;
    padding-right: 16px;
}
.status-dot {
    width: 7px; height: 7px;
    background: #22c55e;
    border-radius: 50%;
    box-shadow: 0 0 6px rgba(34,197,94,0.7);
    animation: pulse-dot 2s ease-in-out infinite;
    flex-shrink: 0;
}
@keyframes pulse-dot {
    0%, 100% { box-shadow: 0 0 6px rgba(34,197,94,0.7); }
    50%       { box-shadow: 0 0 12px rgba(34,197,94,1); }
}
.status-label {
    font-size: 12px;
    color: rgba(255,255,255,0.55);
    font-weight: 500;
    white-space: nowrap;
}

/* ── Theme toggle button ── */
.st-key-theme_toggle button {
    width: 36px !important;
    height: 36px !important;
    min-width: 36px !important;
    max-width: 36px !important;
    border-radius: 50% !important;
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.14) !important;
    color: #ffffff !important;
    font-size: 15px !important;
    padding: 0 !important;
    transition: all 0.2s ease !important;
}
.st-key-theme_toggle button:hover {
    background: rgba(132,108,248,0.18) !important;
    border-color: #846cf8 !important;
    box-shadow: 0 0 10px rgba(132,108,248,0.3) !important;
}

/* ── Avatar button ── */
.st-key-avatar_btn button {
    width: 36px !important;
    height: 36px !important;
    min-width: 36px !important;
    max-width: 36px !important;
    border-radius: 50% !important;
    background: #846cf8 !important;
    border: 2px solid rgba(132,108,248,0.45) !important;
    font-size: 12px !important;
    font-weight: 700 !important;
    color: #ffffff !important;
    padding: 0 !important;
    letter-spacing: 0.3px !important;
    transition: all 0.2s ease !important;
}
.st-key-avatar_btn button:hover {
    background: #9b87ff !important;
    box-shadow: 0 0 12px rgba(132,108,248,0.5) !important;
    transform: scale(1.05) !important;
}

/* ── RESET SESSION BUTTON ── */
.reset-btn {
    background: #18181F !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 10px !important;
    color: #ffffff !important;
    font-size: 12px !important; font-weight: 500 !important;
    padding: 5px 12px !important;
    transition: all 0.2s ease !important;
}
.reset-btn:hover {
    background: #232330 !important;
    box-shadow: 0 0 8px rgba(132,108,248,0.2) !important;
}

/* ── DISCONNECT BUTTON ── */
.disconnect-btn {
    background: #18181F !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    color: #ffffff !important;
}
.disconnect-btn:hover {
    background: #232330 !important;
    border-color: rgba(255,255,255,0.3) !important;
    color: #ffffff !important;
}

/* ── PANEL LABEL ── */
.panel-label {
    font-size: 20px; font-weight: 600;
    color: #ffffff; margin-bottom: 16px; padding-bottom: 8px;
    border-bottom: 1px solid rgba(132,108,248,0.2);
}

/* ── (separator & divider styles moved to split-pane section above) ── */

/* ── EDIT PANEL ── */
.edit-panel {
    background: #000000;
    border: 1px solid rgba(132,108,248,0.3);
    border-radius: 10px;
    margin-top: 14px;
    overflow: hidden;
}
.edit-panel-header {
    display: flex; align-items: center; justify-content: space-between;
    padding: 12px 16px;
    background: rgba(132,108,248,0.1);
    border-bottom: 1px solid rgba(132,108,248,0.2);
}
.edit-panel-title { font-size: 13px; font-weight: 600; color: #846cf8; }
.edit-panel-sub { font-size: 10px; color: #ffffff; font-family: 'JetBrains Mono', monospace; }
.edit-panel-body { padding: 16px; }


/* Ensure the parent container can hold absolute items */
[data-testid="stVerticalBlock"] {
    position: relative;
}

/* ── FORM INPUTS ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: #18181F !important;
    border: 1px solid rgba(132,108,248,0.3) !important;
    border-radius: 7px !important;
    color: #ffffff !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 13px !important;
    padding: 7px 10px !important;
    transition: border-color 0.15s !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #846cf8 !important;
    box-shadow: 0 0 0 2px rgba(132,108,248,0.15), 0 0 8px rgba(132,108,248,0.2) !important;
}
.stSelectbox > div > div {
    background: #18181F !important;
    border: 1px solid rgba(132,108,248,0.3) !important;
    border-radius: 7px !important;
    color: #ffffff !important;
    font-size: 13px !important;
}

/* Input labels */
.stTextInput label, .stSelectbox label, .stCheckbox label, .stTextArea label {
    font-size: 13px !important; font-weight: 500 !important;
    color: rgba(255,255,255,0.7) !important; letter-spacing: 0.2px !important;
    margin-bottom: 4px !important;
}

/* ── BUTTONS ── */
.stButton > button {
    background: rgba(132,108,248,0.12) !important;
    border: 1px solid rgba(132,108,248,0.35) !important;
    border-radius: 10px !important;
    color: #846cf8 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important; font-weight: 500 !important;
    padding: 6px 16px !important;
    transition: all 0.2s !important;
    height: 36px !important;
}
.stButton > button:hover {
    background: #846cf8 !important;
    border-color: #846cf8 !important;
    color: #ffffff !important;
    box-shadow: 0 0 10px rgba(132,108,248,0.35), 0 0 20px rgba(132,108,248,0.15) !important;
}

.stFormSubmitButton > button {
    background: #846cf8 !important;
    border: 1px solid #846cf8 !important;
    border-radius: 10px !important;
    color: #ffffff !important;
    font-weight: 600 !important;
    width: 100% !important;
    box-shadow: 0 0 10px rgba(132,108,248,0.35) !important;
}
.stFormSubmitButton > button:hover {
    background: #6e56e0 !important;
    box-shadow: 0 0 14px rgba(132,108,248,0.5) !important;
}

/* ── CHAT PANEL: scrollable messages, fixed input ── */
/* (height & overflow now handled by the split-pane layout above) */

.chat-messages-scroll {
    flex: 1;
    overflow-y: auto;
    overflow-x: hidden;
    padding: 0 4px 12px 4px;
    display: flex;
    flex-direction: column;
    gap: 4px;
    scrollbar-width: thin;
    scrollbar-color: rgba(132,108,248,0.3) transparent;
}
.chat-messages-scroll::-webkit-scrollbar { width: 4px; }
.chat-messages-scroll::-webkit-scrollbar-track { background: transparent; }
.chat-messages-scroll::-webkit-scrollbar-thumb { background: rgba(132,108,248,0.3); border-radius: 4px; }

.chat-input-fixed {
    flex-shrink: 0;
    padding-top: 8px;
    border-top: 1px solid rgba(132,108,248,0.15);
}

/* ── CHAT MESSAGES: bubble alignment ── */
[data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
    padding: 6px 0 !important;
}

[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
    flex-direction: row-reverse !important;
    justify-content: flex-start !important;
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] {
    background: #846cf8 !important;
    border: none !important;
    border-radius: 18px 18px 4px 18px !important;
    padding: 10px 16px !important;
    color: #ffffff !important;
    
    /* 1. Shrink bubble tightly around the text */
    width: fit-content !important;
    max-width: 82% !important;
    flex: 0 1 auto !important; /* Overrides Streamlit's full-width stretch */
    
    /* 2. Push the bubble to the far right side */
    margin-left: auto !important;
    margin-right: 8px !important;
}

[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] p {
    color: #ffffff !important;
}

[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {
    flex-direction: row !important;
    justify-content: flex-start !important;
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) [data-testid="stChatMessageContent"] {
    background: #18181F !important;
    border: 1px solid rgba(132,108,248,0.2) !important;
    border-radius: 18px 18px 18px 4px !important;
    padding: 10px 16px !important;
    color: #ffffff !important;
    max-width: 80% !important;
    margin-right: auto !important;
    margin-left: 8px !important;
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) [data-testid="stChatMessageContent"] p {
    color: #ffffff !important;
    font-size: 14px !important;
}

/* Avatars */
[data-testid="stChatMessageAvatarUser"] {
    background: #846cf8 !important;
    border-radius: 50% !important;
    flex-shrink: 0;
    position: relative;
    overflow: hidden;
    width: 32px !important;
    height: 32px !important;
    display: flex !important;
    align-items: center;
    justify-content: center;
}
[data-testid="stChatMessageAvatarUser"] svg { display: none !important; }
[data-testid="stChatMessageAvatarUser"]::after {
    position: absolute; inset: 0;
    display: flex; align-items: center; justify-content: center;
    font-family: 'Inter', sans-serif;
    font-size: 12px; font-weight: 600; color: #ffffff;
    letter-spacing: 0.5px; text-transform: uppercase;
}
[data-testid="stChatMessageAvatarAssistant"] {
    background: #18181F !important;
    border: 1px solid rgba(132,108,248,0.25) !important;
    border-radius: 8px !important;
    flex-shrink: 0;
    position: relative;
    overflow: hidden;
    width: 32px !important;
    height: 32px !important;
    display: flex !important;
    align-items: center;
    justify-content: center;
}
[data-testid="stChatMessageAvatarAssistant"] svg { display: none !important; }
[data-testid="stChatMessageAvatarAssistant"]::after {
    content: "⚡" !important;
    position: absolute; inset: 0;
    display: flex; align-items: center; justify-content: center;
    font-size: 14px;
}

/* Code inside chat */
[data-testid="stChatMessageContent"] code {
    background: rgba(132,108,248,0.12) !important;
    border: 1px solid rgba(132,108,248,0.2) !important;
    border-radius: 4px !important;
    color: #ffffff !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 12px !important;
    padding: 1px 5px !important;
}
[data-testid="stChatMessageContent"] pre {
    background: #1E1E28 !important;
    border: 1px solid rgba(132,108,248,0.15) !important;
    border-radius: 8px !important;
    padding: 12px !important;
}

/* ── CHAT INPUT BOX ── */
[data-testid="stChatInput"] {
    background: #18181F !important;
    border: 1px solid rgba(132,108,248,0.3) !important;
    border-radius: 12px !important;
    overflow: hidden !important;
}
[data-testid="stChatInput"] > div,
[data-testid="stChatInput"] > div > div {
    background: #18181F !important;
    border: none !important;
    box-shadow: none !important;
    border-radius: 11px !important;
}
[data-testid="stChatInput"]:focus-within {
    border-color: #846cf8 !important;
    box-shadow: 0 0 8px rgba(132,108,248,0.25) !important;
}
[data-testid="stChatInput"]:focus-within > div,
[data-testid="stChatInput"]:focus-within > div > div {
    border: none !important;
    box-shadow: none !important;
}
[data-testid="stChatInput"] textarea {
    color: #ffffff !important;
    background: #18181F !important;
    caret-color: #ffffff !important;
    font-size: 14px !important;
}
[data-testid="stChatInput"] textarea::placeholder {
    color: rgba(255,255,255,0.35) !important;
}
[data-testid="stChatInput"] button {
    background: #846cf8 !important;
    border-radius: 8px !important;
    color: #ffffff !important;
}

/* ── PROFILE DROPDOWN CARD ── */
.profile-card {
    background: #18181F;
    border: 1px solid rgba(132,108,248,0.25);
    border-radius: 12px;
    overflow: hidden;
    margin-bottom: 12px;
}
.profile-card-header {
    display: flex; align-items: center; gap: 12px;
    padding: 16px;
    background: rgba(132,108,248,0.08);
    border-bottom: 1px solid rgba(132,108,248,0.15);
}
.profile-avatar {
    width: 36px; height: 36px;
    border-radius: 50%;
    background: #846cf8;
    display: flex; align-items: center; justify-content: center;
    font-size: 14px; font-weight: 600; color: #ffffff;
}
.profile-name { font-size: 14px; font-weight: 600; color: #ffffff; }
.profile-sub { font-size: 12px; color: #ffffff; opacity: 0.6; margin-top: 2px; }
.profile-body { padding: 12px 16px; }
.profile-row {
    display: flex; justify-content: space-between; align-items: center;
    padding: 6px 0; border-bottom: 1px solid rgba(255,255,255,0.05);
}
.profile-key { font-size: 13px; color: #ffffff; opacity: 0.5; font-weight: 500; }
.profile-val { font-size: 12px; color: #ffffff; font-family: 'JetBrains Mono', monospace; }

/* ── EXPANDERS & MISC ── */
[data-testid="stExpander"],
[data-testid="stExpander"] > div,
[data-testid="stExpander"] details,
[data-testid="stExpander"] details > div {
    background: #111118 !important;
    border: 1px solid rgba(132,108,248,0.15) !important;
    border-radius: 8px !important;
    margin-bottom: 8px !important;
}
[data-testid="stExpander"] details summary {
    background: #111118 !important;
    color: #ffffff !important;
    font-size: 14px !important;
    font-weight: 600 !important;
}

/* Metrics */
[data-testid="stMetric"] { color: #ffffff !important; }
[data-testid="stMetricValue"] { color: #846cf8 !important; }
[data-testid="stMetricLabel"] { color: #ffffff !important; }

/* Caption / small text */
.stMarkdown small, .stMarkdown .small, [data-testid="stCaptionContainer"] p {
    color: #ffffff !important; opacity: 0.6 !important;
}

/* ── JSON VIEWER ── */
[data-testid="stJson"] {
    background: #111118 !important;
    border-radius: 8px !important;
    border: 1px solid rgba(132,108,248,0.15) !important;
}
[data-testid="stJson"] div,
[data-testid="stJson"] pre,
[data-testid="stJson"] code { background: #111118 !important; color: #ffffff !important; }
[data-testid="stJson"] .key, [data-testid="stJson"] .string, [data-testid="stJson"] .number,
[data-testid="stJson"] .boolean, [data-testid="stJson"] .null,
[data-testid="stJson"] span, [data-testid="stJson"] p, [data-testid="stJson"] li {
    color: #ffffff !important; background: transparent !important;
}
[data-testid="stJson"] [role="button"], [data-testid="stJson"] [role="button"] *,
[data-testid="stJson"] summary, [data-testid="stJson"] summary * {
    background-color: #111118 !important; color: #ffffff !important;
}
[data-testid="stJson"] [role="button"]:hover, [data-testid="stJson"] summary:hover {
    background-color: #18181F !important;
}

/* ── PRODUCT CARDS ── */
.product-card {
    background: #1A1A24 !important;
    border: 1px solid rgba(132,108,248,0.3) !important;
    border-radius: 10px !important;
    margin-bottom: 10px !important;
    overflow: hidden !important;
}
.product-card-header {
    display: flex !important;
    align-items: center !important;
    justify-content: space-between !important;
    padding: 12px 14px !important;
    background: rgba(132,108,248,0.15) !important;
    border-bottom: 1px solid rgba(132,108,248,0.2) !important;
}
.product-card-header-right {
    display: flex !important; align-items: center !important; gap: 8px !important;
}
.product-card-title { font-size: 16px !important; font-weight: 600 !important; color: #ffffff !important; }
.product-card-subtitle { font-size: 13px !important; color: rgba(255,255,255,0.5) !important; margin-top: 2px !important; font-family: 'JetBrains Mono', monospace !important; }
.product-card-body { padding: 10px 14px !important; }
.field-row {
    display: flex !important; justify-content: space-between !important;
    align-items: flex-start !important; padding: 5px 0 !important;
    border-bottom: 1px solid rgba(255,255,255,0.07) !important; gap: 10px !important;
}
.field-row:last-child { border-bottom: none !important; }
.field-key { font-size: 13px !important; color: rgba(255,255,255,0.5) !important; font-weight: 500 !important; flex-shrink: 0 !important; min-width: 100px !important; }
.field-val { font-size: 13px !important; color: #e8e8f8 !important; text-align: right !important; word-break: break-word !important; }
.badge-deployed { font-size: 12px !important; font-weight: 600 !important; padding: 3px 9px !important; border-radius: 20px !important; background: rgba(34,197,94,0.15) !important; color: #22c55e !important; white-space: nowrap !important; }
.badge-draft { font-size: 12px !important; font-weight: 600 !important; padding: 3px 9px !important; border-radius: 20px !important; background: rgba(255,255,255,0.07) !important; color: rgba(255,255,255,0.5) !important; white-space: nowrap !important; }

.card-edit-btn {
    font-size: 11px !important; font-weight: 600 !important; padding: 2px 10px !important;
    border-radius: 6px !important; background: rgba(132,108,248,0.15) !important;
    color: #846cf8 !important; border: 1px solid rgba(132,108,248,0.35) !important;
    cursor: pointer !important; white-space: nowrap !important; transition: all 0.15s !important;
    text-decoration: none !important; display: inline-block !important;
}
.card-edit-btn:hover { background: #846cf8 !important; color: #ffffff !important; box-shadow: 0 0 8px rgba(132,108,248,0.35) !important; }

.stToggle label { color: #ffffff !important; font-size: 13px !important; }
[data-testid="stToggleSwitch"] { accent-color: #846cf8 !important; }

/* ── EDIT MODAL DARK ── */
[data-testid="stModal"], .stModal, div[data-testid="stModal"] {
    background: rgba(0,0,0,0.90) !important;
    backdrop-filter: blur(4px) !important;
}
[data-testid="stDialog"] > div,
div[data-testid="stDialog"] > div,
[data-testid="stModal"] [data-testid="stDialog"] > div,
[data-testid="stDialog"] > div[role="dialog"],
[data-testid="stDialog"] [data-testid="stDialogContent"],
[data-testid="stDialog"] > div > div {
    background: #000000 !important;
    background-color: #000000 !important;
    border: 1px solid rgba(132,108,248,0.3) !important;
    border-radius: 16px !important;
    box-shadow: 0 0 40px rgba(132,108,248,0.18) !important;
}
[data-testid="stDialog"] .block-container,
[data-testid="stDialog"] [data-testid="stVerticalBlock"],
[data-testid="stDialog"] [data-testid="stForm"],
[data-testid="stDialog"] [data-testid="stFormContainer"] {
    background: #000000 !important; background-color: #000000 !important;
}
[data-testid="stDialog"] label, [data-testid="stDialog"] h1, [data-testid="stDialog"] h2,
[data-testid="stDialog"] h3, [data-testid="stDialog"] p, [data-testid="stDialog"] span {
    color: #ffffff !important;
}
[data-testid="stDialog"] input, [data-testid="stDialog"] textarea, [data-testid="stDialog"] select {
    background: #111118 !important; background-color: #111118 !important;
    color: #ffffff !important; border-color: rgba(132,108,248,0.25) !important;
}
[data-testid="stDialog"] button[kind="primary"],
[data-testid="stDialog"] button[kind="secondary"] {
    background: #846cf8 !important; color: #ffffff !important; border: none !important;
}
[data-testid="stDialog"] button[kind="primary"]:hover,
[data-testid="stDialog"] button[kind="secondary"]:hover { background: #6f56e0 !important; }

/* ── Duplicate layout fix ── */
.cpq-duplicate { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# DRAGGABLE SPLIT PANE — via streamlit.components.v1.html
# This is the only reliable way to execute JS in Streamlit.
# components.html renders inside an iframe that has access to window.parent.
# ─────────────────────────────────────────────────────────────────────────────
import streamlit.components.v1 as _components

_components.html("""
<script>
(function() {
  var doc = window.parent.document;

  // Walk down from a column element to find the deepest stVerticalBlock
  function findScrollTarget(col) {
    var all = col.querySelectorAll('[data-testid="stVerticalBlock"]');
    // The last one in DOM order is the innermost / deepest
    return all.length ? all[all.length - 1] : null;
  }

  // Make every element in the chain from col down to target flex-column
  // so height flows through without any element clipping it
  function makeFlexChain(col, target) {
    var el = target;
    while (el && el !== col.parentElement) {
      el.style.setProperty('display', 'flex', 'important');
      el.style.setProperty('flex-direction', 'column', 'important');
      el.style.setProperty('min-height', '0', 'important');
      if (el !== target) {
        el.style.setProperty('flex', '1', 'important');
        el.style.setProperty('overflow', 'hidden', 'important');
      }
      el = el.parentElement;
    }
  }

  function init() {
    var blocks = doc.querySelectorAll('[data-testid="stHorizontalBlock"]');
    var row = null;
    for (var i = 0; i < blocks.length; i++) {
      if (blocks[i].querySelector('.panel-label')) {
        var cols = blocks[i].querySelectorAll('[data-testid="column"]');
        if (cols.length === 2) { row = blocks[i]; break; }
      }
    }
    if (!row) return false;
    if (row.dataset.splitDone) return true;
    row.dataset.splitDone = '1';

    var leftCol  = cols[0];
    var rightCol = cols[1];

    // Stamp layout classes on the column wrappers
    row.classList.add('main-split-row');
    leftCol.classList.add('split-left');
    rightCol.classList.add('split-right');

    // Walk to the actual content container and stamp scroll classes
    var leftScroll  = findScrollTarget(leftCol);
    var rightScroll = findScrollTarget(rightCol);

    if (leftScroll) {
      makeFlexChain(leftCol, leftScroll);
      leftScroll.classList.add('panel-scroll-left');
    }
    if (rightScroll) {
      makeFlexChain(rightCol, rightScroll);
      rightScroll.classList.add('panel-scroll-right');
    }

    // Insert the draggable divider between the two columns
    var divider = doc.createElement('div');
    divider.id = 'split-divider';
    row.insertBefore(divider, rightCol);

    var leftPct = 50;
    var MIN = 40, MAX = 70;

    function apply(pct) {
      leftCol.style.width  = pct + '%';
      leftCol.style.flex   = 'none';
      rightCol.style.width = (100 - pct) + '%';
      rightCol.style.flex  = 'none';
    }
    apply(leftPct);

    var dragging = false, startX = 0, startPct = 0;

    divider.addEventListener('mousedown', function(e) {
      dragging = true;
      startX   = e.clientX;
      startPct = leftPct;
      divider.classList.add('is-dragging');
      doc.body.style.cursor        = 'col-resize';
      doc.body.style.userSelect    = 'none';
      doc.body.style.pointerEvents = 'none';
      divider.style.pointerEvents  = 'auto';
      e.preventDefault();
    });

    doc.addEventListener('mousemove', function(e) {
      if (!dragging) return;
      var totalW = row.getBoundingClientRect().width;
      var dPct   = ((e.clientX - startX) / totalW) * 100;
      leftPct    = Math.min(MAX, Math.max(MIN, startPct + dPct));
      apply(leftPct);
    });

    doc.addEventListener('mouseup', function() {
      if (!dragging) return;
      dragging = false;
      divider.classList.remove('is-dragging');
      doc.body.style.cursor        = '';
      doc.body.style.userSelect    = '';
      doc.body.style.pointerEvents = '';
    });

    return true;
  }

  var tries = 0;
  var iv = setInterval(function() {
    tries++;
    if (init() || tries > 60) clearInterval(iv);
  }, 200);
})();
</script>
""", height=0)


# ─────────────────────────────────────────────────────────────────────────────
# LIGHT THEME CSS (injected conditionally after session state is ready)
# ─────────────────────────────────────────────────────────────────────────────
LIGHT_CSS = """
<style>
.stApp, [data-testid="stAppViewContainer"] { background: #ECEEF5 !important; }
.stMarkdown p, .stMarkdown li, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 { color: #1a1a2e !important; }

/* Light navbar */
.navbar-row [data-testid="stHorizontalBlock"] {
    background: #ffffff !important;
    border-color: #ddd8f0 !important;
    box-shadow: 0 2px 12px rgba(0,0,0,0.08) !important;
    margin-top: -100px !important;
}
.nav-title { color: #1a1a2e !important;font-size: 36px }
.nav-pill { color: #5b2d8e !important; background: rgba(91,45,142,0.08) !important; border-color: rgba(91,45,142,0.25) !important; }
.status-label { color: #888 !important; }
.st-key-theme_toggle button {
    background: rgba(0,0,0,0.05) !important;
    border-color: rgba(0,0,0,0.2) !important;
    color: #1a1a2e !important;
}
.st-key-theme_toggle button:hover {
    background: rgba(91,45,142,0.1) !important;
    border-color: #5b2d8e !important;
}
.st-key-avatar_btn button {
    background: #5b2d8e !important;
    border-color: rgba(91,45,142,0.5) !important;
}

/* Light panels */
.panel-scroll-left {
    background: #ffffff !important;
    border-right: 2px solid rgba(91,45,142,0.22) !important;
    box-shadow: 2px 0 8px rgba(91,45,142,0.10) !important;
    scrollbar-color: rgba(91,45,142,0.4) rgba(91,45,142,0.05) !important;
}
.panel-scroll-right { background: #ECEEF5 !important; }

.panel-label { color: #1a1a2e !important; border-bottom-color: rgba(91,45,142,0.2) !important; }

/* Inputs */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea { background: #fff !important; color: #1a1a2e !important; border-color: rgba(91,45,142,0.3) !important; }
.stTextInput label, .stSelectbox label, .stTextArea label, .stCheckbox label { color: #1a1a2e !important; }
.stSelectbox > div > div { background: #fff !important; color: #1a1a2e !important; }
.stToggle label { color: #1a1a2e !important; }

/* Chat */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) [data-testid="stChatMessageContent"] {
    background: #ffffff !important; color: #1a1a2e !important;
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) [data-testid="stChatMessageContent"] p { color: #1a1a2e !important; }
[data-testid="stChatMessageAvatarAssistant"] { background: #ffffff !important; border-color: rgba(91,45,142,0.25) !important; }
[data-testid="stChatInput"] { background: #fff !important; border-color: #5b2d8e !important; }
[data-testid="stChatInput"] > div, [data-testid="stChatInput"] > div > div { background: #fff !important; }
[data-testid="stChatInput"] textarea { color: #1a1a2e !important; background: #fff !important; caret-color: #1a1a2e !important; }
[data-testid="stChatInput"] textarea::placeholder { color: rgba(0,0,0,0.35) !important; }

/* Profile */
.profile-card { background: #fff !important; }
.profile-card-header { background: rgba(91,45,142,0.05) !important; }
.profile-avatar { background: #5b2d8e !important; }
.profile-name { color: #1a1a2e !important; }
.profile-sub, .profile-key { color: #555 !important; }
.profile-val { color: #1a1a2e !important; }



/* Expanders */
[data-testid="stExpander"], [data-testid="stExpander"] > div,
[data-testid="stExpander"] details, [data-testid="stExpander"] details > div,
[data-testid="stExpander"] details summary { background: #ffffff !important; color: #1a1a2e !important; }

/* JSON */
[data-testid="stJson"], [data-testid="stJson"] div, [data-testid="stJson"] pre,
[data-testid="stJson"] code { background: #f8f8ff !important; color: #1a1a2e !important; }
[data-testid="stJson"] span, [data-testid="stJson"] p, [data-testid="stJson"] li { color: #1a1a2e !important; }
[data-testid="stJson"] [role="button"], [data-testid="stJson"] [role="button"] * { background: #f8f8ff !important; color: #1a1a2e !important; }

/* Metrics */
[data-testid="stMetricValue"] { color: #5b2d8e !important; }
[data-testid="stMetricLabel"] { color: #333 !important; }

/* Product cards */
.product-card { background: #ffffff !important; border-color: rgba(91,45,142,0.25) !important; }
.product-card-header { background: rgba(91,45,142,0.07) !important; border-bottom-color: rgba(91,45,142,0.12) !important; }
.product-card-title { color: #1a1a2e !important; }
.product-card-subtitle { color: #6b6b8a !important; }
.field-key { color: #6b6b8a !important; }
.field-val { color: #1a1a2e !important; }
.field-row { border-bottom-color: rgba(0,0,0,0.06) !important; }
.badge-draft { background: rgba(0,0,0,0.06) !important; color: #555 !important; }
.badge-deployed { background: rgba(34,197,94,0.12) !important; color: #15803d !important; }
.card-edit-btn { background: rgba(91,45,142,0.12) !important; color: #5b2d8e !important; border-color: rgba(91,45,142,0.3) !important; }
.card-edit-btn:hover { background: #5b2d8e !important; color: #ffffff !important; }

/* Light edit modal */
[data-testid="stModal"], .stModal, div[data-testid="stModal"] {
    background: rgba(0,0,0,0.45) !important; backdrop-filter: blur(4px) !important;
}
[data-testid="stDialog"] > div, div[data-testid="stDialog"] > div,
[data-testid="stModal"] [data-testid="stDialog"] > div,
[data-testid="stDialog"] > div[role="dialog"],
[data-testid="stDialog"] [data-testid="stDialogContent"],
[data-testid="stDialog"] > div > div {
    background: #ffffff !important; background-color: #ffffff !important;
    border: 1px solid rgba(91,45,142,0.15) !important;
    border-radius: 16px !important; box-shadow: 0 4px 24px rgba(0,0,0,0.12) !important;
}
[data-testid="stDialog"] .block-container, [data-testid="stDialog"] [data-testid="stVerticalBlock"],
[data-testid="stDialog"] [data-testid="stForm"], [data-testid="stDialog"] [data-testid="stFormContainer"] {
    background: #ffffff !important; background-color: #ffffff !important;
}
[data-testid="stDialog"] label, [data-testid="stDialog"] h1, [data-testid="stDialog"] h2,
[data-testid="stDialog"] h3, [data-testid="stDialog"] p, [data-testid="stDialog"] span { color: #1a1a2e !important; }
[data-testid="stDialog"] input, [data-testid="stDialog"] textarea, [data-testid="stDialog"] select {
    background: #ffffff !important; background-color: #ffffff !important;
    color: #1a1a2e !important; border-color: rgba(91,45,142,0.25) !important;
}
[data-testid="stDialog"] button[kind="primary"],
[data-testid="stDialog"] button[kind="secondary"] { background: #5b2d8e !important; color: #ffffff !important; border: none !important; }
</style>
"""

# ─────────────────────────────────────────────────────────────────────────────
# BACKEND IMPORTS
# ─────────────────────────────────────────────────────────────────────────────
from agents.cpq_agent import CPQAgent
from schema import schema_loader
import state.running_json as rj


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def login_with_password(username, password, security_token, domain="login"):
    try:
        from simple_salesforce import Salesforce
        sf = Salesforce(
            username=username,
            password=password,
            security_token=security_token,
            domain=domain,
        )
        return {
            "username": username,
            "instanceUrl": sf.base_url.split("/services")[0],
            "accessToken": sf.session_id,
            "orgId": sf.org_id,
        }, None
    except Exception as e:
        return None, str(e)


def validate_sf_session(instance_url, access_token):
    import requests
    try:
        r = requests.get(
            f"{instance_url}/services/data/v58.0/",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        return (True, "OK") if r.status_code == 200 else (False, f"HTTP {r.status_code}")
    except Exception as e:
        return False, str(e)


def save_sf_credentials(username, instance_url, access_token, org_id):
    env_path = root_path / ".env"
    lines = []
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    keys = {"SF_USERNAME": username, "SF_INSTANCE_URL": instance_url,
            "SF_ACCESS_TOKEN": access_token, "SF_ORG_ID": org_id}
    new_lines, seen = [], set()
    for line in lines:
        s = line.strip()
        if not s or s.startswith("#"):
            new_lines.append(line); continue
        if "=" in s:
            k = s.split("=", 1)[0].strip()
            if k in keys:
                new_lines.append(f"{k}={keys[k]}\n"); seen.add(k)
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)
    for k, v in keys.items():
        if k not in seen:
            new_lines.append(f"{k}={v}\n")
    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    for k, v in keys.items():
        os.environ[k] = str(v) if v is not None else ""


def get_initials(username: str) -> str:
    if not username:
        return "SF"
    parts = username.split("@")[0].replace(".", " ").replace("_", " ").split()
    return (parts[0][0] + parts[1][0]).upper() if len(parts) >= 2 else username[:2].upper()


def sync_from_backend():
    st.session_state.running_json = rj.get_state()


def sync_to_backend():
    rj._store = deepcopy(st.session_state.running_json)


# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────────────────────────────────────
if "agent" not in st.session_state:
    st.session_state.agent = CPQAgent()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = [{
        "role": "assistant",
        "content": (
            "Hi! I'm your **CPQ AI Agent**. I can help you build and configure:\n\n"
            "- Product option groups & option components\n"
            "- Price lists & price list items\n"
            "- Product attribute groups & constraint rules\n"
            "- Products and full CPQ configurations\n\n"
            "Just describe what you need and I'll handle the rest. You can also click any record in the tree on the left to view or edit it."
        )
    }]

if "running_json" not in st.session_state:
    sync_from_backend()

if "profile_open" not in st.session_state:
    st.session_state.profile_open = False

if "selected_record" not in st.session_state:
    st.session_state.selected_record = None

if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True

if "show_technical" not in st.session_state:
    st.session_state.show_technical = False

if "pending_input" not in st.session_state:
    st.session_state.pending_input = None


# ─────────────────────────────────────────────────────────────────────────────
# SF CONNECTION CHECK — with full-screen splash loader
# ─────────────────────────────────────────────────────────────────────────────
if "sf_connected" not in st.session_state:
    _u = os.getenv("SF_USERNAME")
    _p = os.getenv("SF_PASSWORD")
    _t = os.getenv("SF_SECURITY_TOKEN")
    _d = os.getenv("SF_DOMAIN", "login")

    if _u and _p and _t:
        _loader = st.empty()
        _loader.markdown(
"<style>"
"#MainMenu,footer,header,[data-testid='stToolbar'],[data-testid='stDecoration'],.stAppHeader{display:none!important}"
".block-container{padding:0!important}"
".splash{position:fixed;inset:0;z-index:9999;background:#000;display:flex;flex-direction:column;align-items:center;justify-content:center}"
".splash-logo-wrap{display:flex;align-items:center;gap:14px;margin-bottom:32px}"
".splash-icon{width:52px;height:52px;background:linear-gradient(135deg,#5b2d8e,#846cf8);border-radius:14px;display:flex;align-items:center;justify-content:center;font-size:26px;animation:glow 2s ease-in-out infinite alternate}"
"@keyframes glow{from{box-shadow:0 0 20px rgba(132,108,248,0.3)}to{box-shadow:0 0 40px rgba(132,108,248,0.7)}}"
".splash-brand-name{font-size:32px;font-weight:800;color:#fff;letter-spacing:-0.5px;line-height:1;font-family:sans-serif}"
".splash-brand-name span{color:#846cf8}"
".splash-brand-sub{font-size:12px;color:rgba(255,255,255,0.45);letter-spacing:2px;text-transform:uppercase;margin-top:4px;font-family:sans-serif}"
".splash-divider{width:1px;height:44px;background:rgba(132,108,248,0.3);margin:0 10px}"
".splash-product-name{font-size:18px;font-weight:600;color:#fff;font-family:sans-serif}"
".splash-product-tag{font-size:11px;color:#846cf8;letter-spacing:1.5px;text-transform:uppercase;margin-top:5px;font-family:sans-serif}"
".splash-status{font-size:13px;color:rgba(255,255,255,0.5);margin-bottom:16px;font-family:sans-serif}"
".splash-status span{color:#846cf8;font-weight:600}"
".splash-bar-track{width:320px;height:3px;background:rgba(132,108,248,0.15);border-radius:4px;overflow:hidden}"
".splash-bar-fill{height:100%;background:linear-gradient(90deg,#5b2d8e,#846cf8,#a78bfa);border-radius:4px;animation:loader 1.8s ease-in-out infinite}"
"@keyframes loader{0%{transform:translateX(-100%)}100%{transform:translateX(200%)}}"
".splash-dots{display:flex;gap:6px;margin-top:28px}"
".splash-dot{width:5px;height:5px;border-radius:50%;background:#846cf8;animation:dotpulse 1.4s ease-in-out infinite}"
".splash-dot:nth-child(2){animation-delay:0.2s}"
".splash-dot:nth-child(3){animation-delay:0.4s}"
"@keyframes dotpulse{0%,100%{opacity:0.2;transform:scale(0.8)}50%{opacity:1;transform:scale(1.2)}}"
"</style>"
"<div class='splash'>"
"<div class='splash-logo-wrap'>"
"<div class='splash-icon'>⚡</div>"
"<div><div class='splash-brand-name'>conga<span>.</span></div><div class='splash-brand-sub'>Revenue Lifecycle</div></div>"
"<div class='splash-divider'></div>"
"<div><div class='splash-product-name'>CPQ Configurator</div><div class='splash-product-tag'>AI Agent · Hackathon</div></div>"
"</div>"
"<div class='splash-status'>Connecting to <span>Salesforce</span>…</div>"
"<div class='splash-bar-track'><div class='splash-bar-fill'></div></div>"
"<div class='splash-dots'><div class='splash-dot'></div><div class='splash-dot'></div><div class='splash-dot'></div></div>"
"</div>",
unsafe_allow_html=True)

        _res, _err = login_with_password(_u, _p, _t, _d)
        _loader.empty()

        if _res and not isinstance(_res, tuple):
            save_sf_credentials(_res["username"], _res["instanceUrl"], _res["accessToken"], _res["orgId"])
            st.session_state.sf_username = _res["username"]
            st.session_state.sf_instance_url = _res["instanceUrl"]
            st.session_state.sf_access_token = _res["accessToken"]
            st.session_state.sf_org_id = _res["orgId"]
            st.session_state.sf_connected = True
        else:
            st.session_state.sf_connected = False
    else:
        st.session_state.sf_connected = False


# ═════════════════════════════════════════════════════════════════════════════
# LOGIN PAGE
# ═════════════════════════════════════════════════════════════════════════════
if not st.session_state.get("sf_connected", False):
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("""
        <div style="padding-top: 80px; text-align: center;">
            <div style="width:60px;height:60px;background:linear-gradient(135deg,#5b5bd6,#8b5cf6);
                border-radius:14px;font-size:26px;display:flex;align-items:center;
                justify-content:center;margin:0 auto 20px;">⚡</div>
            <h1 style="font-size:22px;font-weight:600;color:#e8e8f0;margin-bottom:8px;">Conga CPQ AI Agent</h1>
            <p style="color:#404058;font-size:13px;margin-bottom:28px;">Connect your Salesforce org to begin</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="background:#111118;border:1px solid rgba(91,91,214,0.15);border-radius:12px;padding:28px;">
            <p style="color:#505070;font-size:13px;line-height:1.65;text-align:center;margin-bottom:20px;">
                Authenticate via the Salesforce CLI. A browser tab will open for secure login —
                your session is retrieved automatically when complete.
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        with st.form("sf_login_form"):
            _username = st.text_input("Username", value=os.getenv("SF_USERNAME", ""))
            _password = st.text_input("Password", type="password", value=os.getenv("SF_PASSWORD", ""))
            _token    = st.text_input("Security Token", type="password", value=os.getenv("SF_SECURITY_TOKEN", ""))
            _domain   = st.selectbox("Domain", ["login", "test"], index=0)
            submitted = st.form_submit_button("Connect to Salesforce", use_container_width=True)

        if submitted:
            with st.spinner("Connecting to Salesforce…"):
                _res, _err = login_with_password(_username, _password, _token, _domain)
                if _res and not isinstance(_res, tuple):
                    save_sf_credentials(_res["username"], _res["instanceUrl"], _res["accessToken"], _res["orgId"])
                    st.session_state.sf_username = _res["username"]
                    st.session_state.sf_instance_url = _res["instanceUrl"]
                    st.session_state.sf_access_token = _res["accessToken"]
                    st.session_state.sf_org_id = _res["orgId"]
                    st.session_state.sf_connected = True
                    st.success("Connected!")
                    st.rerun()
                else:
                    st.error(f"Login failed: {_err}")
    st.stop()


# ═════════════════════════════════════════════════════════════════════════════
# MAIN APP RUNTIME
# ═════════════════════════════════════════════════════════════════════════════
sf_username     = st.session_state.get("sf_username", "")
sf_org_id       = st.session_state.get("sf_org_id", "")
sf_instance_url = st.session_state.get("sf_instance_url", "")
sf_access_token = st.session_state.get("sf_access_token", "")
initials        = get_initials(sf_username)
short_user      = sf_username.split("@")[0] if sf_username else "User"

# Inject initials into the custom chat user avatar content
st.markdown(f"""
<style>
[data-testid="stChatMessageAvatarUser"]::after {{
    content: "{initials}" !important;
}}
</style>
""", unsafe_allow_html=True)

# Inject light theme CSS if needed
if not st.session_state.dark_mode:
    st.markdown(LIGHT_CSS, unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# UNIFIED NAVBAR — single st.columns row, CSS makes it look like one bar
# ═════════════════════════════════════════════════════════════════════════════
theme_icon = "☀" if not st.session_state.dark_mode else "☾"

st.markdown('<div class="navbar-row">', unsafe_allow_html=True)
_nav_left, _nav_theme, _nav_avatar = st.columns([1, 0.06, 0.06])

with _nav_left:
    st.markdown(f"""
    <div class="nav-brand">
        <div class="nav-logo">⚡</div>
        <span class="nav-title">Conga CPQ Agentic Builder</span>
        <span class="nav-pill">AI Agent</span>
        <div class="nav-status">
            <span class="status-dot"></span>
            <span class="status-label">Connected · {short_user}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with _nav_theme:
    if st.button(theme_icon, key="theme_toggle",
                 help="Light mode" if st.session_state.dark_mode else "Dark mode",
                 use_container_width=True):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()

with _nav_avatar:
    if st.button(initials, key="avatar_btn",
                 help="Account & settings",
                 use_container_width=True):
        st.session_state.profile_open = not st.session_state.profile_open

st.markdown('</div>', unsafe_allow_html=True)


# ── PROFILE DROPDOWN ──────────────────────────────────────────────────────────
if st.session_state.profile_open:
    token_preview = (sf_access_token[:20] + "…") if sf_access_token else "—"
    st.markdown(f"""
    <div class="profile-card">
        <div class="profile-card-header">
            <div class="profile-avatar">{initials}</div>
            <div>
                <div class="profile-name">{short_user}</div>
                <div class="profile-sub">{sf_username}</div>
            </div>
        </div>
        <div class="profile-body">
            <div class="profile-row">
                <span class="profile-key">Org ID</span>
                <span class="profile-val">{"00DHu00000R8K6m" or sf_org_id}</span>
            </div>
            <div class="profile-row">
                <span class="profile-key">Instance</span>
                <span class="profile-val">{sf_instance_url or "—"}</span>
            </div>
            <div class="profile-row">
                <span class="profile-key">Token</span>
                <span class="profile-val">{token_preview}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    pc1, pc2 = st.columns(2)
    with pc1:
        if st.button("↺  Reset Session", use_container_width=True, key="reset_session_btn"):
            st.session_state.agent.reset()
            rj.clear_state()
            sync_from_backend()
            st.session_state.chat_history = [{"role": "assistant", "content": "Session cleared. Ready for a fresh start!"}]
            st.session_state.selected_record = None
            st.session_state.profile_open = False
            st.toast("Session reset.")
            st.rerun()
    with pc2:
        if st.button("⏻  Disconnect", use_container_width=True, key="disconnect_btn", type="secondary"):
            try:
                subprocess.run("sf org logout --target-org cpqOrg --no-prompt", shell=True, capture_output=True)
            except Exception:
                pass
            save_sf_credentials("", "", "", "")
            for k in ["sf_connected", "sf_username", "sf_instance_url", "sf_access_token", "sf_org_id"]:
                st.session_state.pop(k, None)
            st.session_state.profile_open = False
            st.toast("Disconnected.")
            st.rerun()

    st.markdown("<hr>", unsafe_allow_html=True)



# ── Edit dialog session state ──
if "edit_dialog_open" not in st.session_state:
    st.session_state.edit_dialog_open = False
if "edit_dialog_obj" not in st.session_state:
    st.session_state.edit_dialog_obj = None
if "edit_dialog_uuid" not in st.session_state:
    st.session_state.edit_dialog_uuid = None

# Load schema.json for the Edit dialog
_schema_path = root_path / "config" / "schema.json"
_SCHEMA = {}
if _schema_path.exists():
    try:
        with open(_schema_path, "r", encoding="utf-8") as _sf:
            _SCHEMA = json.load(_sf)
    except Exception:
        _SCHEMA = {}


@st.dialog("Edit Record", width="large", dismissible=False)
def edit_record_dialog(obj_name, record_uuid):

    _edit_rec = None
    for r in st.session_state.running_json.get(obj_name, []):
        if r.get("uuid") == record_uuid:
            _edit_rec = r
            break

    if _edit_rec is None:
        st.session_state.edit_dialog_open = False
        st.session_state.edit_dialog_obj  = None
        st.session_state.edit_dialog_uuid = None
        st.rerun()
        return

    # ─── DIALOG STYLING ───────────────────────────────────────────────────────
    st.markdown("""
    <style>
    /* Center Streamlit dialog */
    div[data-testid="stDialog"] {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }

    /* Reset dialog positioning */
    div[data-testid="stDialog"] > div {
        position: relative !important;
        top: auto !important;
        left: auto !important;
        transform: none !important;
        margin: auto !important;
    }
    </style>
    """, unsafe_allow_html=True)

    _, close_col = st.columns([20, 1])

    with close_col:
        st.markdown("""
        <style>
        /* Close button */
        div[data-testid="stButton"] button[kind="secondary"] {
            background: linear-gradient(
                135deg,
                rgba(138, 99, 255, 0.95),
                rgba(168, 130, 255, 0.95)
            ) !important;

            color: var(--text-color) !important;

            border: 1px solid rgba(255,255,255,0.15) !important;
            border-radius: 12px !important;

            width: 42px !important;
            min-width: 42px !important;
            height: 42px !important;

            padding: 0 !important;
            font-size: 18px !important;
            font-weight: 600 !important;

            box-shadow:
                0 0 12px rgba(138,99,255,0.35),
                0 0 24px rgba(138,99,255,0.15) !important;

            transition: all 0.2s ease !important;
        }

        /* Hover */
        div[data-testid="stButton"] button[kind="secondary"]:hover {
            transform: translateY(-1px) scale(1.04) !important;

            box-shadow:
                0 0 18px rgba(138,99,255,0.45),
                0 0 36px rgba(138,99,255,0.20) !important;
        }

        /* Active */
        div[data-testid="stButton"] button[kind="secondary"]:active {
            transform: scale(0.98) !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        if st.button("✕", key="top_right_close_modal_x"):
            st.session_state.edit_dialog_open = False
            st.session_state.edit_dialog_obj = None
            st.session_state.edit_dialog_uuid = None
            st.rerun()

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    # ─────────────────────────────────────────────────────────────────────────
    _schema_fields = _SCHEMA.get(obj_name, {}).get("fields", [])

    with st.form(key=f"edit_form_{obj_name}_{record_uuid}"):
        _updated_vals = {}

        if _schema_fields:
            fields_to_render = _schema_fields
        else:
            fields_to_render = [
                {"name": k, "label": k, "type": "string", "required": False}
                for k in _edit_rec.keys()
                if k not in {"uuid", "attributes"}
            ]

        _skip_edit = {"uuid", "Id", "attributes"}
        _rendered = 0

        for i in range(0, len(fields_to_render), 2):
            cols = st.columns(2)
            for col_idx, fdef in enumerate(fields_to_render[i:i+2]):
                with cols[col_idx]:
                    fname  = fdef.get("name", "")
                    flabel = fdef.get("label", fname)
                    ftype  = fdef.get("type", "string").lower()

                    if fname in _skip_edit:
                        continue

                    cur_val = _edit_rec.get(fname, "")

                    if ftype in ("id", "reference"):
                        st.text_input(f"{flabel} (read-only)", value=str(cur_val) if cur_val else "", disabled=True, key=f"ef_ro_{fname}")
                        _updated_vals[fname] = cur_val
                    elif ftype == "boolean":
                        _updated_vals[fname] = st.checkbox(flabel, value=bool(cur_val), key=f"ef_{fname}")
                    elif ftype in ("double", "integer", "currency", "number"):
                        try:
                            _num_val = float(cur_val) if cur_val not in (None, "") else 0.0
                        except:
                            _num_val = 0.0
                        _updated_vals[fname] = st.number_input(flabel, value=_num_val, key=f"ef_{fname}")
                    elif ftype == "textarea":
                        _updated_vals[fname] = st.text_area(flabel, value=str(cur_val) if cur_val else "", key=f"ef_{fname}", height=120)
                    else:
                        _updated_vals[fname] = st.text_input(flabel, value=str(cur_val) if cur_val else "", key=f"ef_{fname}")

                    _rendered += 1

        if _rendered == 0:
            st.info("No editable fields found for this record type.")

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        save_col, cancel_col = st.columns(2)
        with save_col:
            _save = st.form_submit_button("Save Changes", use_container_width=True)
        with cancel_col:
            _cancel = st.form_submit_button("Cancel", use_container_width=True)

        if _save:
            for r in st.session_state.running_json.get(obj_name, []):
                if r.get("uuid") == record_uuid:
                    for k, v in _updated_vals.items():
                        if k not in {"uuid", "Id", "attributes"}:
                            r[k] = v
                    break
            sync_to_backend()
            st.session_state.edit_dialog_open = False
            st.session_state.edit_dialog_obj  = None
            st.session_state.edit_dialog_uuid = None
            st.toast("✅ Record updated successfully.")
            st.rerun()

        if _cancel:
            st.session_state.edit_dialog_open = False
            st.session_state.edit_dialog_obj  = None
            st.session_state.edit_dialog_uuid = None
            st.rerun()

# ═════════════════════════════════════════════════════════════════════════════
# MAIN TWO-COLUMN LAYOUT
# ═════════════════════════════════════════════════════════════════════════════
col_left, col_right = st.columns([1, 1], gap="small")


# ─────────────────────────────────────────────────────────────────────────────
# LEFT PANEL — Product Configuration
# ─────────────────────────────────────────────────────────────────────────────
with col_left:
    lp_header, lp_toggle = st.columns([3, 2])
    with lp_header:
        st.markdown('<div class="panel-label">Product Configuration</div>', unsafe_allow_html=True)
    with lp_toggle:
        st.session_state.show_technical = st.toggle(
            "Technical details", value=st.session_state.show_technical, help="Show raw JSON for each record"
        )
    with st.container(height=600, border=False):
        running_data = st.session_state.running_json
        has_data = any(records for records in running_data.values())

        OBJ_META = {
            "Product2":              ("📦", "Product"),
            "PricebookEntry":        ("💲", "Price Book Entry"),
            "Pricebook2":            ("📋", "Price Book"),
            "SBQQ__ProductOption__c":("🔧", "Product Option"),
            "SBQQ__OptionGroup__c":  ("🗂️",  "Option Group"),
            "SBQQ__ProductFeature__c":("✨", "Product Feature"),
            "SBQQ__ConfigurationAttribute__c": ("⚙️", "Config Attribute"),
            "SBQQ__ConfigurationRule__c":      ("📐", "Config Rule"),
        }

        DISPLAY_FIELDS = ["Name", "ProductCode", "Description", "Family",
                        "IsActive", "UnitPrice", "CurrencyIsoCode", "Type__c"]

        if not has_data:
            st.markdown("""
            <div style="text-align:center; padding: 48px 16px; opacity:0.5;">
                <div style="font-size:40px; margin-bottom:12px;">📭</div>
                <div style="font-size:14px;">No products configured yet.<br>Use the chat to start building.</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            chart_dataset = {k: len(v) for k, v in running_data.items() if v}
            if chart_dataset:
                m1, m2 = st.columns(2)
                m1.metric("Object Types", len(chart_dataset))
                m2.metric("Total Records", sum(chart_dataset.values()))

            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

            for obj_name, records in running_data.items():
                if not records:
                    continue

                icon, friendly = OBJ_META.get(obj_name, ("📄", obj_name))

                with st.expander(f"{icon}  {friendly}  ({len(records)})", expanded=True):
                    for rec in records:
                        rec_name    = rec.get("Name", f"Record {rec.get('uuid','')[:6]}")
                        rec_uuid    = rec.get("uuid", "")
                        is_deployed = bool(rec.get("Id"))
                        badge_cls   = "badge-deployed" if is_deployed else "badge-draft"
                        badge_txt   = "🟢 Deployed" if is_deployed else "⚪ Draft"

                        skip = {"uuid", "Id", "attributes"}
                        field_rows_html = ""
                        for k, v in rec.items():
                            if k in skip or v is None or v == "":
                                continue
                            if k not in DISPLAY_FIELDS and not st.session_state.show_technical:
                                continue
                            field_rows_html += (
                                f'<div class="field-row">'
                                f'<span class="field-key">{k}</span>'
                                f'<span class="field-val">{v}</span>'
                                f'</div>'
                            )

                        fallback = '<div class="field-row"><span class="field-key">No displayable fields yet</span></div>'
                        card_html = (
                            '<div class="product-card">'
                            '<div class="product-card-header">'
                            '<div>'
                            f'<div class="product-card-title">{rec_name}</div>'
                            f'<div class="product-card-subtitle">{obj_name}</div>'
                            '</div>'
                            '<div class="product-card-header-right">'
                            f'<span class="{badge_cls}">{badge_txt}</span>'
                            '</div>'
                            '</div>'
                            '<div class="product-card-body">'
                            f'{field_rows_html if field_rows_html else fallback}'
                            '</div>'
                            '</div>'
                        )
                        st.markdown(card_html, unsafe_allow_html=True)

                        edit_col, _ = st.columns([1, 4])
                        with edit_col:
                            if st.button(f"✏️ Edit", key=f"edit_{obj_name}_{rec_uuid}", use_container_width=False):
                                st.session_state.edit_dialog_open = True
                                st.session_state.edit_dialog_obj  = obj_name
                                st.session_state.edit_dialog_uuid = rec_uuid
                                st.rerun()

                        if st.session_state.show_technical:
                            st.json(rec)


# ─────────────────────────────────────────────────────────────────────────────
# EDIT RECORD DIALOG
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.get("edit_dialog_open") and st.session_state.edit_dialog_obj and st.session_state.edit_dialog_uuid:
    edit_record_dialog(st.session_state.edit_dialog_obj, st.session_state.edit_dialog_uuid)


# ─────────────────────────────────────────────────────────────────────────────
# RIGHT PANEL — Chat
# ─────────────────────────────────────────────────────────────────────────────
with col_right:
    st.markdown('<div class="panel-label">CPQ AI Assistant Engine</div>', unsafe_allow_html=True)

    chat_container = st.container(height=600, border=False)
    with chat_container:
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # Phase 2 — agent is thinking: show spinner inside the chat stream
        if st.session_state.pending_input:
            with st.chat_message("assistant"):
                with st.spinner("CPQ Agent is working..."):
                    try:
                        response_text = st.session_state.agent.chat(st.session_state.pending_input)
                        sync_from_backend()
                    except Exception:
                        response_text = f"⚠️ Something went wrong:\n```\n{traceback.format_exc()}\n```"
            st.session_state.chat_history.append({"role": "assistant", "content": response_text})
            st.session_state.pending_input = None
            st.rerun()

    # Phase 1 — user submits: store message + set pending, rerun immediately to show it
    if user_input := st.chat_input("Describe what you want to configure..."):
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        st.session_state.pending_input = user_input
        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# JS: hide duplicate layout only
# Must use components.html — st.markdown strips <script> tags.
# ─────────────────────────────────────────────────────────────────────────────
import streamlit.components.v1 as _c
_c.html("""<script>
(function () {
  var doc = window.parent.document;

  function hideDuplicates() {
    var all = doc.querySelectorAll('[data-testid="stHorizontalBlock"]');
    for (var i = 0; i < all.length; i++) {
      var b = all[i];
      if (b.closest('[data-testid="stColumn"]')) continue;
      var cols = b.querySelectorAll(':scope > [data-testid="stColumn"]');
      if (cols.length !== 2 || !b.querySelector('.panel-label')) continue;
      // This is the real layout — hide everything that comes after it
      var wrapper = b.closest('[data-testid="stLayoutWrapper"]');
      if (!wrapper) continue;
      var sib = wrapper.nextElementSibling;
      while (sib) {
        if (sib.getAttribute('data-testid') === 'stLayoutWrapper') {
          sib.classList.add('cpq-duplicate');
        }
        sib = sib.nextElementSibling;
      }
      break;
    }
  }

  setInterval(hideDuplicates, 500);
  hideDuplicates();
})();
</script>""", height=0, scrolling=False)