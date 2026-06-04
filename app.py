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
    page_title="Conga CPQ AI Agent",
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

/* ── BASE: layered dark surfaces ── */
/* App background */
.stApp {
    background: #09090B !important;
}

/* Left panel */
[data-testid="column"]:first-child > div:first-child {
    background: #ffffff !important;
    border-radius: 16px;
    padding: 16px;
    height: calc(100vh - 120px);
    overflow: auto;
}

/* Right panel */
[data-testid="column"]:last-child > div:first-child {
    background: #111118;
    border-radius: 16px;
    padding: 16px;
    height: calc(100vh - 120px);
    overflow: hidden;
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
.block-container { padding: 0 24px !important; max-width: 100% !important; }
section[data-testid="stSidebar"] { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }
.stAppHeader { display: none !important; }

/* ── NAV BAR ── */
.nav-bar {
    position: sticky; top: 0; z-index: 999;
    height: 60px;
    background: #111118;
    border-bottom: 1px solid rgba(132,108,248,0.25);
    display: flex; align-items: center;
    justify-content: space-between;
    padding: 0 20px;
    margin-bottom: 20px;
}

/* ── UNIFIED NAV — make the two st.columns look like one bar ── */
/* The wrapper row that holds both nav columns */
.nav-row-wrapper {
    position: relative;
}
.nav-row-wrapper [data-testid="stHorizontalBlock"] {
    gap: 0 !important;
    align-items: stretch !important;
}
/* Left column — remove Streamlit gap/padding */
.nav-row-wrapper [data-testid="stHorizontalBlock"] > [data-testid="column"]:first-child {
    flex: 1 1 auto !important;
}
.nav-row-wrapper [data-testid="stHorizontalBlock"] > [data-testid="column"]:first-child > div:first-child {
    padding: 0 !important;
}
/* Right column — overlay on top of nav bar, aligned to right */
.nav-row-wrapper [data-testid="stHorizontalBlock"] > [data-testid="column"]:last-child {
    position: absolute !important;
    right: 20px !important;
    top: 50% !important;
    transform: translateY(-50%) !important;
    width: auto !important;
    min-width: 120px !important;
    max-width: 180px !important;
    flex: 0 0 auto !important;
    z-index: 1000;
}
.nav-row-wrapper [data-testid="stHorizontalBlock"] > [data-testid="column"]:last-child > div:first-child {
    padding: 0 !important;
}
/* Tighten the inner button columns */
.nav-row-wrapper [data-testid="stHorizontalBlock"] > [data-testid="column"]:last-child [data-testid="stHorizontalBlock"] {
    gap: 6px !important;
}
.nav-brand { display: flex; align-items: center; gap: 10px; }
.nav-logo {
    width: 36px; height: 36px;
    background: #846cf8;
    border-radius: 9px;
    display: flex; align-items: center; justify-content: center;
    font-size: 18px; flex-shrink: 0;
    box-shadow: 0 0 10px rgba(132,108,248,0.35), 0 0 20px rgba(132,108,248,0.25), 0 0 40px rgba(132,108,248,0.15);
}
.nav-title { font-size: 32px; font-weight: 700; color: #ffffff; letter-spacing: -0.5px; }
.nav-pill {
    font-size: 10px; font-weight: 500;
    color: #846cf8; background: rgba(132,108,248,0.12);
    border: 1px solid rgba(132,108,248,0.35);
    border-radius: 20px; padding: 2px 8px;
    letter-spacing: 0.4px; text-transform: uppercase;
}
.nav-right { display: flex; align-items: center; gap: 8px; }
.status-dot {
    width: 6px; height: 6px;
    background: #22c55e; border-radius: 50%;
    box-shadow: 0 0 5px rgba(34,197,94,0.6);
}
.status-label { font-size: 12px; color: #ffffff; }

/* ── GROUPED HEADER ACTIONS ── */
.header-actions-group {
    display: flex; align-items: center; gap: 0;
    background: #18181F;
    border: 1px solid rgba(132,108,248,0.2);
    border-radius: 12px;
    padding: 4px 6px;
    box-shadow: 0 0 10px rgba(132,108,248,0.08);
    gap: 4px;
}

/* Theme icon button */

.st-key-theme_toggle button {
    width: 36px !important;
    height: 36px !important;
    min-width: 36px !important;
    max-width: 36px !important;

    border-radius: 50% !important;

    background: #000000 !important;
    border: 1px solid #ffffff !important;

    color: #ffffff !important;
    font-size: 15px !important;
    font-weight: 500 !important;

    padding: 0 !important;

    display: flex !important;
    align-items: center !important;
    justify-content: center !important;

    transition: all 0.2s ease !important;
}

.st-key-theme_toggle button:hover {
    background: #111118 !important;
    border-color: #ffffff !important;
    box-shadow: 0 0 8px rgba(255,255,255,0.15) !important;
}

/* ── USER AVATAR ── */
.user-avatar {
    width: 36px; height: 36px;
    border-radius: 50%;
    background: #000000;
    border: 1px solid #ffffff;
    display: inline-flex; align-items: center; justify-content: center;
    font-size: 14px; font-weight: 600; color: #ffffff;
    flex-shrink: 0; cursor: pointer;
    transition: box-shadow 0.2s ease;
}
.user-avatar:hover {
    box-shadow: 0 0 8px rgba(132,108,248,0.4);
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

/* ── LEFT & RIGHT PANEL SURFACES + SEPARATOR ── */
[data-testid="column"]:first-child > div:first-child {
    background: #111118;
    border-radius: 12px 0 0 12px;
    padding: 4px;
    border-right: 1px solid rgba(132,108,248,0.22);
}
[data-testid="column"]:last-child > div:first-child {
    background: #111118;
    border-radius: 0 12px 12px 0;
    padding: 4px;
}

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

/* Reset Session button — secondary style */
div[data-testid="column"] .stButton:nth-of-type(1) > button {
    background: #18181F !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 10px !important;
    color: #ffffff !important;
}
div[data-testid="column"] .stButton:nth-of-type(1) > button:hover {
    background: #232330 !important;
    box-shadow: 0 0 8px rgba(132,108,248,0.2) !important;
}

/* Disconnect button — destructive style */
button[kind="secondary"] {
    background: #18181F !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    color: #ffffff !important;
}

button[kind="secondary"]:hover {
    background: #232330 !important;
    border-color: rgba(255,255,255,0.3) !important;
    color: #ffffff !important;
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
/* The right column chat container needs a fixed height with flex layout */
[data-testid="column"]:last-child {
    display: flex;
    flex-direction: column;
    height: calc(100vh - 100px);
    overflow: hidden;
}

/* Scrollable messages area */
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

/* Fixed chat input at the bottom */
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

/* User message → right side */
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
    max-width: 80% !important;
    margin-left: auto !important;
    margin-right: 8px !important;
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] p {
    color: #ffffff !important;
}

/* Bot message → left side */
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
[data-testid="stChatMessageAvatarUser"] svg {
    display: none !important;
}
[data-testid="stChatMessageAvatarUser"]::after {
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'Inter', sans-serif;
    font-size: 12px;
    font-weight: 600;
    color: #ffffff;
    letter-spacing: 0.5px;
    text-transform: uppercase;
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
[data-testid="stChatMessageAvatarAssistant"] svg {
    display: none !important;
}
[data-testid="stChatMessageAvatarAssistant"]::after {
    content: "⚡" !important;
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
}


/* ── USER AVATAR BUTTON ── */
.st-key-avatar_btn button {
    width: 36px !important;
    height: 36px !important;
    min-width: 36px !important;
    max-width: 36px !important;
    border-radius: 50% !important;
    background: #000000 !important;
    border: 1px solid #ffffff !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    color: #ffffff !important;
    padding: 0 !important;
    cursor: pointer !important;
    transition: box-shadow 0.2s ease !important;
}
.st-key-avatar_btn button:hover {
    box-shadow: 0 0 8px rgba(132,108,248,0.4) !important;
    background: #111118 !important;
    border-color: #846cf8 !important;
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
    background: #000000;
    border: 1px solid #ffffff;
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

/* ── JSON VIEWER CONTAINER & FIXES ── */
[data-testid="stJson"] {
    background: #111118 !important;
    border-radius: 8px !important;
    border: 1px solid rgba(132,108,248,0.15) !important;
}

[data-testid="stJson"] div,
[data-testid="stJson"] pre,
[data-testid="stJson"] code {
    background: #111118 !important;
    color: #ffffff !important;
}

[data-testid="stJson"] .key,
[data-testid="stJson"] .string,
[data-testid="stJson"] .number,
[data-testid="stJson"] .boolean,
[data-testid="stJson"] .null,
[data-testid="stJson"] span,
[data-testid="stJson"] p,
[data-testid="stJson"] li {
    color: #ffffff !important;
    background: transparent !important;
}

[data-testid="stJson"] [role="button"],
[data-testid="stJson"] [role="button"] *,
[data-testid="stJson"] summary,
[data-testid="stJson"] summary * {
    background-color: #111118 !important;
    color: #ffffff !important;
}

[data-testid="stJson"] [role="button"]:hover,
[data-testid="stJson"] summary:hover {
    background-color: #18181F !important;
}

/* ── PRODUCT CARDS — surface level 3 ── */
.product-card {
    background: #1E1E28 !important;
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
    display: flex !important;
    align-items: center !important;
    gap: 8px !important;
}
.product-card-title {
    font-size: 16px !important;
    font-weight: 600 !important;
    color: #ffffff !important;
}
.product-card-subtitle {
    font-size: 13px !important;
    color: rgba(255,255,255,0.5) !important;
    margin-top: 2px !important;
    font-family: 'JetBrains Mono', monospace !important;
}
.product-card-body { padding: 10px 14px !important; }
.field-row {
    display: flex !important;
    justify-content: space-between !important;
    align-items: flex-start !important;
    padding: 5px 0 !important;
    border-bottom: 1px solid rgba(255,255,255,0.07) !important;
    gap: 10px !important;
}
.field-row:last-child { border-bottom: none !important; }
.field-key {
    font-size: 13px !important;
    color: rgba(255,255,255,0.5) !important;
    font-weight: 500 !important;
    flex-shrink: 0 !important;
    min-width: 100px !important;
}
.field-val {
    font-size: 13px !important;
    color: #e8e8f8 !important;
    text-align: right !important;
    word-break: break-word !important;
}
.badge-deployed {
    font-size: 12px !important;
    font-weight: 600 !important;
    padding: 3px 9px !important;
    border-radius: 20px !important;
    background: rgba(34,197,94,0.15) !important;
    color: #22c55e !important;
    white-space: nowrap !important;
}
.badge-draft {
    font-size: 12px !important;
    font-weight: 600 !important;
    padding: 3px 9px !important;
    border-radius: 20px !important;
    background: rgba(255,255,255,0.07) !important;
    color: rgba(255,255,255,0.5) !important;
    white-space: nowrap !important;
}

/* ── EDIT BUTTON on product cards ── */
.card-edit-btn {
    font-size: 11px !important;
    font-weight: 600 !important;
    padding: 2px 10px !important;
    border-radius: 6px !important;
    background: rgba(132,108,248,0.15) !important;
    color: #846cf8 !important;
    border: 1px solid rgba(132,108,248,0.35) !important;
    cursor: pointer !important;
    white-space: nowrap !important;
    transition: all 0.15s !important;
    text-decoration: none !important;
    display: inline-block !important;
}
.card-edit-btn:hover {
    background: #846cf8 !important;
    color: #ffffff !important;
    box-shadow: 0 0 8px rgba(132,108,248,0.35) !important;
}

/* Toggle styling */
.stToggle label { color: #ffffff !important; font-size: 13px !important; }
[data-testid="stToggleSwitch"] { accent-color: #846cf8 !important; }

/* ── EDIT MODAL DARK ── */

/* Black backdrop overlay */
[data-testid="stModal"],
.stModal,
div[data-testid="stModal"] {
    background: rgba(0,0,0,0.90) !important;
    backdrop-filter: blur(4px) !important;
}

/* Dialog container — force black background */
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

/* Force all nested containers inside dialog to be black */
[data-testid="stDialog"] .block-container,
[data-testid="stDialog"] [data-testid="stVerticalBlock"],
[data-testid="stDialog"] [data-testid="stForm"],
[data-testid="stDialog"] [data-testid="stFormContainer"] {
    background: #000000 !important;
    background-color: #000000 !important;
}

[data-testid="stDialog"] label,
[data-testid="stDialog"] h1,
[data-testid="stDialog"] h2,
[data-testid="stDialog"] h3,
[data-testid="stDialog"] p,
[data-testid="stDialog"] span {
    color: #ffffff !important;
}

[data-testid="stDialog"] input,
[data-testid="stDialog"] textarea,
[data-testid="stDialog"] select {
    background: #111118 !important;
    background-color: #111118 !important;
    color: #ffffff !important;
    border-color: rgba(132,108,248,0.25) !important;
}

[data-testid="stDialog"] button[kind="primary"],
[data-testid="stDialog"] button[kind="secondary"] {
    background: #846cf8 !important;
    color: #ffffff !important;
    border: none !important;
}
[data-testid="stDialog"] button[kind="primary"]:hover,
[data-testid="stDialog"] button[kind="secondary"]:hover {
    background: #6f56e0 !important;
}

</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# LIGHT THEME CSS (injected conditionally after session state is ready)
# ─────────────────────────────────────────────────────────────────────────────
LIGHT_CSS = """
<style>
/* ── LIGHT MODE: only change backgrounds and text colors ── */
.stApp, [data-testid="stAppViewContainer"] { background: #F0F2F8 !important; }
.stMarkdown p, .stMarkdown li, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 { color: #1a1a2e !important; }

.nav-bar { background: #ffffff !important; border-bottom-color: #ddd8f0 !important; }
.nav-title { color: #1a1a2e !important; }
.nav-pill { color: #5b2d8e !important; background: rgba(91,45,142,0.08) !important; border-color: rgba(91,45,142,0.25) !important; }
.status-label { color: #333 !important; }
.panel-label { color: #1a1a2e !important; border-bottom-color: rgba(91,45,142,0.2) !important; }

/* Inputs */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea { background: #fff !important; color: #1a1a2e !important; border-color: rgba(91,45,142,0.3) !important; }
.stTextInput label, .stSelectbox label, .stTextArea label, .stCheckbox label { color: #1a1a2e !important; }
.stSelectbox > div > div { background: #fff !important; color: #1a1a2e !important; }

/* Toggle */
.stToggle label { color: #1a1a2e !important; }

/* Chat */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) [data-testid="stChatMessageContent"] {
    background: #ffffff !important; color: #1a1a2e !important;
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) [data-testid="stChatMessageContent"] p { color: #1a1a2e !important; }
[data-testid="stChatMessageAvatarAssistant"] {
    background: #ffffff !important;
    border-color: rgba(91,45,142,0.25) !important;
    color: #5b2d8e !important;
}
[data-testid="stChatInput"] { background: #fff !important; border-color: #5b2d8e !important; }
[data-testid="stChatInput"] > div, [data-testid="stChatInput"] > div > div { background: #fff !important; }
[data-testid="stChatInput"] textarea { color: #1a1a2e !important; background: #fff !important; caret-color: #1a1a2e !important; }
[data-testid="stChatInput"] textarea::placeholder { color: rgba(0,0,0,0.35) !important; }

/* Profile */
.profile-card { background: #fff !important; }
.profile-card-header { background: rgba(91,45,142,0.05) !important; }
.profile-avatar { background: #ffffff !important; border-color: #1a1a2e !important; }
.profile-name { color: #1a1a2e !important; }
.profile-sub, .profile-key { color: #555 !important; }
.profile-val { color: #1a1a2e !important; }
.st-key-avatar_btn button {
    background: #ffffff !important;
    border-color: #1a1a2e !important;
    color: #1a1a2e !important;
}
.st-key-avatar_btn button:hover {
    background: #f0f2f8 !important;
    border-color: #5b2d8e !important;
}

/* Expanders */
[data-testid="stExpander"],
[data-testid="stExpander"] > div,
[data-testid="stExpander"] details,
[data-testid="stExpander"] details > div,
[data-testid="stExpander"] details summary { background: #ffffff !important; color: #1a1a2e !important; }

/* JSON */
[data-testid="stJson"],
[data-testid="stJson"] div,
[data-testid="stJson"] pre,
[data-testid="stJson"] code { background: #f8f8ff !important; color: #1a1a2e !important; }
[data-testid="stJson"] span, [data-testid="stJson"] p, [data-testid="stJson"] li { color: #1a1a2e !important; }
[data-testid="stJson"] [role="button"], [data-testid="stJson"] [role="button"] * { background: #f8f8ff !important; color: #1a1a2e !important; }

/* Metrics */
[data-testid="stMetricValue"] { color: #5b2d8e !important; }
[data-testid="stMetricLabel"] { color: #333 !important; }

/* Product cards — light overrides */
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

/* Theme toggle */

.st-key-theme_toggle button {
    background: #ffffff !important;
    border: 1px solid #000000 !important;
    color: #000000 !important;
}

.st-key-theme_toggle button:hover {
    background: #f5f5f5 !important;
    border-color: #000000 !important;
}
/* ── LIGHT: panel surfaces ── */
[data-testid="column"]:first-child > div:first-child {
    background: #ffffff !important;
}
[data-testid="column"]:last-child > div:first-child {
    background: #F0F2F8 !important;
}

/* ── EDIT MODAL LIGHT ── */

/* Light backdrop overlay */
[data-testid="stModal"],
.stModal,
div[data-testid="stModal"] {
    background: rgba(0,0,0,0.45) !important;
    backdrop-filter: blur(4px) !important;
}

/* Dialog container — force white background */
[data-testid="stDialog"] > div,
div[data-testid="stDialog"] > div,
[data-testid="stModal"] [data-testid="stDialog"] > div,
[data-testid="stDialog"] > div[role="dialog"],
[data-testid="stDialog"] [data-testid="stDialogContent"],
[data-testid="stDialog"] > div > div {
    background: #ffffff !important;
    background-color: #ffffff !important;
    border: 1px solid rgba(91,45,142,0.15) !important;
    border-radius: 16px !important;
    box-shadow: 0 4px 24px rgba(0,0,0,0.12) !important;
}

/* Force all nested containers inside dialog to be white */
[data-testid="stDialog"] .block-container,
[data-testid="stDialog"] [data-testid="stVerticalBlock"],
[data-testid="stDialog"] [data-testid="stForm"],
[data-testid="stDialog"] [data-testid="stFormContainer"] {
    background: #ffffff !important;
    background-color: #ffffff !important;
}

[data-testid="stDialog"] label,
[data-testid="stDialog"] h1,
[data-testid="stDialog"] h2,
[data-testid="stDialog"] h3,
[data-testid="stDialog"] p,
[data-testid="stDialog"] span {
    color: #1a1a2e !important;
}

[data-testid="stDialog"] input,
[data-testid="stDialog"] textarea,
[data-testid="stDialog"] select {
    background: #ffffff !important;
    background-color: #ffffff !important;
    color: #1a1a2e !important;
    border-color: rgba(91,45,142,0.25) !important;
}

[data-testid="stDialog"] button[kind="primary"],
[data-testid="stDialog"] button[kind="secondary"] {
    background: #5b2d8e !important;
    color: #ffffff !important;
    border: none !important;
}
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
    """Authenticate via username + password + security token using simple-salesforce.
    Always returns (result_dict, error_str) — one of them will be None.
    """
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
    st.session_state.selected_record = None  # tuple (obj_name, uuid) | None

if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True

if "show_technical" not in st.session_state:
    st.session_state.show_technical = False


# ─────────────────────────────────────────────────────────────────────────────
# SF CONNECTION CHECK — with full-screen splash loader
# ─────────────────────────────────────────────────────────────────────────────
if "sf_connected" not in st.session_state:
    _u = os.getenv("SF_USERNAME")
    _p = os.getenv("SF_PASSWORD")
    _t = os.getenv("SF_SECURITY_TOKEN")
    _d = os.getenv("SF_DOMAIN", "login")

    if _u and _p and _t:
        # Show splash loader
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
sf_username = st.session_state.get("sf_username", "")
sf_org_id = st.session_state.get("sf_org_id", "")
sf_instance_url = st.session_state.get("sf_instance_url", "")
sf_access_token = st.session_state.get("sf_access_token", "")
initials = get_initials(sf_username)
short_user = sf_username.split("@")[0] if sf_username else "User"

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

# ── TOP NAV (unified bar) ─────────────────────────────────────────────────────
st.markdown('<div class="nav-row-wrapper">', unsafe_allow_html=True)
nav_left, nav_right_col = st.columns([5, 1])
with nav_left:
    st.markdown(f"""
    <div class="nav-bar">
        <div class="nav-brand">
            <div class="nav-logo">⚡</div>
            <span class="nav-title">Conga CPQ Agentic Builder</span>
            <span class="nav-pill">AI Agent</span>
        </div>
        <div class="nav-right">
            <span class="status-dot"></span>
            <span class="status-label">Connected</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with nav_right_col:
    hc1, hc2 = st.columns([1, 1])
    with hc1:
        if st.button(
            "☀" if not st.session_state.dark_mode else "☾",
            key="theme_toggle",
            help="Switch to light mode" if st.session_state.dark_mode else "Switch to dark mode",
            use_container_width=True,
        ):
            st.session_state.dark_mode = not st.session_state.dark_mode
            st.rerun()
    with hc2:
        if st.button(f"{initials}", help="Account & settings", use_container_width=True, key="avatar_btn"):
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


# ═════════════════════════════════════════════════════════════════════════════
# ADJUSTABLE SPLIT PANEL — drag handle via JS injection
# ═════════════════════════════════════════════════════════════════════════════
# Inject resizable splitter JS + CSS (min 40%, max 70%, default 50%)
st.markdown("""
<style>
#split-drag-handle {
    width: 12px;
    background: transparent;
    position: relative;
    flex-shrink: 0;
}

#split-drag-handle::before {
    content: "";
    position: absolute;
    top: 20px;
    bottom: 20px;
    left: 50%;
    width: 1px;
    transform: translateX(-50%);
    background: rgba(132,108,248,0.22);
}

#split-drag-handle:hover::before {
    width: 2px;
    background: rgba(132,108,248,0.6);
}
#split-drag-handle:hover, #split-drag-handle.dragging {
    background: rgba(132,108,248,0.45);
}
</style>
<script>
(function() {
    function initSplitter() {
        var cols = window.parent.document.querySelectorAll('[data-testid="column"]');
        if (cols.length < 2) { setTimeout(initSplitter, 500); return; }
        var leftCol = cols[0], rightCol = cols[1];
        var container = leftCol.parentElement;
        if (!container || document.getElementById('split-drag-handle')) return;

        container.style.display = 'flex';
        container.style.flexDirection = 'row';

        var handle = window.parent.document.createElement('div');
        handle.id = 'split-drag-handle';
        handle.title = 'Drag to resize panels';
        container.insertBefore(handle, rightCol);

        var dragging = false, startX = 0, startLeftW = 0, totalW = 0;

        handle.addEventListener('mousedown', function(e) {
            dragging = true;
            startX = e.clientX;
            startLeftW = leftCol.getBoundingClientRect().width;
            totalW = container.getBoundingClientRect().width;
            handle.classList.add('dragging');
            window.parent.document.body.style.userSelect = 'none';
            window.parent.document.body.style.cursor = 'col-resize';
        });
        window.parent.document.addEventListener('mousemove', function(e) {
            if (!dragging) return;
            var delta = e.clientX - startX;
            var newLeftPct = ((startLeftW + delta) / totalW) * 100;
            newLeftPct = Math.min(70, Math.max(40, newLeftPct));
            leftCol.style.flex = '0 0 ' + newLeftPct + '%';
            leftCol.style.maxWidth = newLeftPct + '%';
            rightCol.style.flex = '0 0 ' + (100 - newLeftPct) + '%';
            rightCol.style.maxWidth = (100 - newLeftPct) + '%';
        });
        window.parent.document.addEventListener('mouseup', function() {
            if (dragging) {
                dragging = false;
                handle.classList.remove('dragging');
                window.parent.document.body.style.userSelect = '';
                window.parent.document.body.style.cursor = '';
            }
        });
    }
    setTimeout(initSplitter, 800);
})();
</script>
""", unsafe_allow_html=True)

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
    # Find the record in running_json
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

    _rec_name = _edit_rec.get("Name", obj_name)
    _schema_fields = _SCHEMA.get(obj_name, {}).get("fields", [])

    with st.form(key=f"edit_form_{obj_name}_{record_uuid}"):
        _updated_vals = {}

        # Determine which fields to show: schema fields if available, else record keys
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
                        st.text_input(
                            f"{flabel} (read-only)",
                            value=str(cur_val) if cur_val else "",
                            disabled=True,
                            key=f"ef_ro_{fname}"
                        )
                        _updated_vals[fname] = cur_val

                    elif ftype == "boolean":
                        _updated_vals[fname] = st.checkbox(
                            flabel,
                            value=bool(cur_val),
                            key=f"ef_{fname}"
                        )
                    elif ftype in ("double", "integer", "currency", "number"):
                        try:
                            _num_val = float(cur_val) if cur_val not in (None, "") else 0.0
                        except:
                            _num_val = 0.0

                        _updated_vals[fname] = st.number_input(
                            flabel,
                            value=_num_val,
                            key=f"ef_{fname}"
                        )

                    elif ftype == "textarea":
                        _updated_vals[fname] = st.text_area(
                            flabel,
                            value=str(cur_val) if cur_val else "",
                            key=f"ef_{fname}",
                            height=120
                        )

                    else:
                        _updated_vals[fname] = st.text_input(
                            flabel,
                            value=str(cur_val) if cur_val else "",
                            key=f"ef_{fname}"
                        )
        
                    _rendered += 1

        if _rendered == 0:
            st.info("No editable fields found for this record type.")

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        save_col, cancel_col = st.columns(2)
        with save_col:
            _save = st.form_submit_button("💾  Save Changes", use_container_width=True)
        with cancel_col:
            _cancel = st.form_submit_button("✕  Cancel", use_container_width=True)

        if _save:
            # Update the record in running_json
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
# STABLE COLUMNS LAYOUT
# ═════════════════════════════════════════════════════════════════════════════
col_left, col_right = st.columns([1, 1], gap="medium")


# ─────────────────────────────────────────────────────────────────────────────
# LEFT PANEL — Collapsible JSON Viewer & Interactivity Block Chart Diagram
# ─────────────────────────────────────────────────────────────────────────────
with col_left:
    lp_header, lp_toggle = st.columns([3, 2])
    with lp_header:
        st.markdown('<div class="panel-label">Product Configuration</div>', unsafe_allow_html=True)
    with lp_toggle:
        st.session_state.show_technical = st.toggle(
            "Technical details", value=st.session_state.show_technical, help="Show raw JSON for each record"
        )

    running_data = st.session_state.running_json
    has_data = any(records for records in running_data.values())

    # Object type → friendly icon + label
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

    # Fields to show prominently on each card
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

                    # Build visible field rows (skip internal/empty fields)
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
                        f'<span class="badge-text"></span>'  # spacer
                        f'<span class="{badge_cls}">{badge_txt}</span>'
                        '</div>'
                        '</div>'
                        '<div class="product-card-body">'
                        f'{field_rows_html if field_rows_html else fallback}'
                        '</div>'
                        '</div>'
                    )
                    st.markdown(card_html, unsafe_allow_html=True)

                    # Edit button rendered as a Streamlit button below the card HTML
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
# RIGHT PANEL — Chatbot Interaction Pipeline
# ─────────────────────────────────────────────────────────────────────────────
with col_right:
    st.markdown('<div class="panel-label">CPQ AI Assistant Engine</div>', unsafe_allow_html=True)

    chat_container = st.container(height=600, border=False)
    with chat_container:
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # ── Input always at the bottom of the right column ──
    if user_input := st.chat_input("Describe what you want to configure..."):
        st.session_state.chat_history.append({"role": "user", "content": user_input})

        try:
            with st.status("CPQ Agent is working...", expanded=True) as status:
                status.write("🔍  Understanding your request...")
                response_text = st.session_state.agent.chat(user_input)
                status.update(label="Response ready!", state="complete", expanded=False)

            st.session_state.chat_history.append({"role": "assistant", "content": response_text})
            sync_from_backend()
        except Exception as ex:
            err_msg = f"⚠️ Something went wrong:\n```\n{traceback.format_exc()}\n```"
            st.session_state.chat_history.append({"role": "assistant", "content": err_msg})

        st.rerun()