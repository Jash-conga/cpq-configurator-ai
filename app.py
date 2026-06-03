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
@import url('https://fonts.googleapis.com/css2?family=Inter:wght=300;400;500;600&family=JetBrains+Mono:wght=400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }

/* ── BASE: pure black, white text ── */
.stApp { background: #000000 !important; }
.stMarkdown p { color: #ffffff !important; font-size: 15px !important; line-height: 1.6 !important; }

#MainMenu, footer, header { visibility: hidden !important; display: none !important; }
.block-container { padding: 0 24px !important; max-width: 100% !important; }
section[data-testid="stSidebar"] { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }
.stAppHeader { display: none !important; }

/* ── NAV BAR ── */
.nav-bar {
    position: sticky; top: 0; z-index: 999;
    height: 52px;
    background: #000000;
    border-bottom: 1px solid rgba(132,108,248,0.25);
    display: flex; align-items: center;
    justify-content: space-between;
    padding: 0 20px;
    margin-bottom: 20px;
}
.nav-brand { display: flex; align-items: center; gap: 10px; }
.nav-logo {
    width: 30px; height: 30px;
    background: #846cf8;
    border-radius: 7px;
    display: flex; align-items: center; justify-content: center;
    font-size: 15px; flex-shrink: 0;
}
.nav-title { font-size: 24px; font-weight: 600; color: #ffffff; letter-spacing: -0.2px; }
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

/* ── PANEL LABEL ── */
.panel-label {
    font-size: 11px; font-weight: 600;
    letter-spacing: 1px; text-transform: uppercase;
    color: #846cf8; margin-bottom: 16px; padding-bottom: 6px;
    border-bottom: 1px solid rgba(132,108,248,0.2);
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
.edit-panel-title { font-size: 12px; font-weight: 600; color: #846cf8; }
.edit-panel-sub { font-size: 10px; color: #ffffff; font-family: 'JetBrains Mono', monospace; }
.edit-panel-body { padding: 16px; }

/* ── FORM INPUTS ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: #000000 !important;
    border: 1px solid rgba(132,108,248,0.3) !important;
    border-radius: 7px !important;
    color: #ffffff !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 12px !important;
    padding: 7px 10px !important;
    transition: border-color 0.15s !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #846cf8 !important;
    box-shadow: 0 0 0 2px rgba(132,108,248,0.15) !important;
}
.stSelectbox > div > div {
    background: #000000 !important;
    border: 1px solid rgba(132,108,248,0.3) !important;
    border-radius: 7px !important;
    color: #ffffff !important;
    font-size: 12px !important;
}

/* Input labels */
.stTextInput label, .stSelectbox label, .stCheckbox label, .stTextArea label {
    font-size: 11px !important; font-weight: 500 !important;
    color: #ffffff !important; letter-spacing: 0.2px !important;
    margin-bottom: 4px !important;
}

/* ── BUTTONS ── */
.stButton > button {
    background: rgba(132,108,248,0.12) !important;
    border: 1px solid rgba(132,108,248,0.35) !important;
    border-radius: 7px !important;
    color: #846cf8 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 12px !important; font-weight: 500 !important;
    padding: 5px 14px !important;
    transition: all 0.15s !important;
    height: 34px !important;
}
.stButton > button:hover {
    background: #846cf8 !important;
    border-color: #846cf8 !important;
    color: #ffffff !important;
}

button[kind="secondary"] {
    background: rgba(200,50,50,0.07) !important;
    border-color: rgba(200,50,50,0.3) !important;
    color: #ff6b6b !important;
}
button[kind="secondary"]:hover {
    background: rgba(200,50,50,0.18) !important;
    color: #ffffff !important;
}

.stFormSubmitButton > button {
    background: #846cf8 !important;
    border: 1px solid #846cf8 !important;
    border-radius: 7px !important;
    color: #ffffff !important;
    font-weight: 600 !important;
    width: 100% !important;
}
.stFormSubmitButton > button:hover {
    background: #6e56e0 !important;
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
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    flex-direction: row-reverse !important;
    justify-content: flex-start !important;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) [data-testid="stChatMessageContent"] {
    background: #846cf8 !important;
    border: none !important;
    border-radius: 18px 18px 4px 18px !important;
    padding: 10px 16px !important;
    color: #ffffff !important;
    max-width: 80% !important;
    margin-left: auto !important;
    margin-right: 8px !important;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) [data-testid="stChatMessageContent"] p {
    color: #ffffff !important;
}

/* Bot message → left side */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
    flex-direction: row !important;
    justify-content: flex-start !important;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) [data-testid="stChatMessageContent"] {
    background: #111111 !important;
    border: 1px solid rgba(132,108,248,0.2) !important;
    border-radius: 18px 18px 18px 4px !important;
    padding: 10px 16px !important;
    color: #ffffff !important;
    max-width: 80% !important;
    margin-right: auto !important;
    margin-left: 8px !important;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) [data-testid="stChatMessageContent"] p {
    color: #ffffff !important;
}

/* Avatars */
[data-testid="chatAvatarIcon-user"] {
    background: #846cf8 !important;
    border-radius: 50% !important;
    flex-shrink: 0;
    position: relative;
    overflow: hidden;
}
/* Hide the default user SVG icon */
[data-testid="chatAvatarIcon-user"] svg {
    display: none !important;
}
/* Inject initials via pseudo-element */
[data-testid="chatAvatarIcon-user"]::after {
    content: attr(data-initial);
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'Inter', sans-serif;
    font-size: 13px;
    font-weight: 600;
    color: #ffffff;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}
[data-testid="chatAvatarIcon-assistant"] {
    background: #111111 !important;
    border: 1px solid rgba(132,108,248,0.25) !important;
    border-radius: 8px !important;
    flex-shrink: 0;
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
    background: #0a0a0a !important;
    border: 1px solid rgba(132,108,248,0.15) !important;
    border-radius: 8px !important;
    padding: 12px !important;
}

/* ── CHAT INPUT BOX ── */
/* Base container: Added overflow: hidden to clip internal corners perfectly */
[data-testid="stChatInput"] {
    background: #000000 !important;
    border: 1px solid #ffffff !important;
    border-radius: 12px !important;
    overflow: hidden !important; /* Prevents inner divs from bleeding past corners */
}

/* Inner wrappers: Added matching border-radius for clean alignment */
[data-testid="stChatInput"] > div,
[data-testid="stChatInput"] > div > div {
    background: #000000 !important;
    border: none !important;
    box-shadow: none !important;
    border-radius: 11px !important; /* Slightly smaller to fit snugly inside the 12px outer border */
}

/* Focus state: Keeps the single border clean on click */
[data-testid="stChatInput"]:focus-within {
    border-color: #ffffff !important;
}
[data-testid="stChatInput"]:focus-within > div,
[data-testid="stChatInput"]:focus-within > div > div {
    border: none !important;
    box-shadow: none !important;
}

/* Text area styling */
[data-testid="stChatInput"] textarea {
    color: #ffffff !important;
    background: #000000 !important;
    caret-color: #ffffff !important;
}
[data-testid="stChatInput"] textarea::placeholder {
    color: rgba(255,255,255,0.35) !important;
}

/* Send button styling */
[data-testid="stChatInput"] button {
    background: #846cf8 !important;
    border-radius: 8px !important;
    color: #ffffff !important;
}

/* ── PROFILE DROPDOWN CARD ── */
.profile-card {
    background: #000000;
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
    width: 38px; height: 38px;
    border-radius: 50%;
    background: #846cf8;
    display: flex; align-items: center; justify-content: center;
    font-size: 13px; font-weight: 600; color: #fff;
}
.profile-name { font-size: 13px; font-weight: 600; color: #ffffff; }
.profile-sub { font-size: 11px; color: #ffffff; opacity: 0.6; margin-top: 2px; }
.profile-body { padding: 12px 16px; }
.profile-row {
    display: flex; justify-content: space-between; align-items: center;
    padding: 6px 0; border-bottom: 1px solid rgba(255,255,255,0.05);
}
.profile-key { font-size: 11px; color: #ffffff; opacity: 0.5; font-weight: 500; }
.profile-val { font-size: 11px; color: #ffffff; font-family: 'JetBrains Mono', monospace; }

/* ── EXPANDERS & MISC ── */
[data-testid="stExpander"],
[data-testid="stExpander"] > div,
[data-testid="stExpander"] details,
[data-testid="stExpander"] details > div,
[data-testid="stExpander"] details summary {
    background: #000000 !important;
    border: 1px solid rgba(132,108,248,0.15) !important;
    border-radius: 8px !important;
    margin-bottom: 8px !important;
}
[data-testid="stExpander"] summary { color: #ffffff !important; }
[data-testid="stExpander"] * { background: #000000 !important; }

/* Metrics */
[data-testid="stMetric"] { color: #ffffff !important; }
[data-testid="stMetricValue"] { color: #846cf8 !important; }
[data-testid="stMetricLabel"] { color: #ffffff !important; }

/* Caption / small text */
.stMarkdown small, .stMarkdown .small, [data-testid="stCaptionContainer"] p {
    color: #ffffff !important; opacity: 0.6 !important;
}

/* ── JSON VIEWER CONTAINER & FIXES ── */
/* Base layout card */
[data-testid="stJson"] {
    background: #000000 !important;
    border-radius: 8px !important;
    border: 1px solid rgba(132,108,248,0.15) !important;
}

/* Base containers, trees, and code blocks inside the JSON frame */
[data-testid="stJson"] div,
[data-testid="stJson"] pre,
[data-testid="stJson"] code {
    background: #000000 !important;
    color: #ffffff !important;
}

/* Explicit node item handling: keys, strings, formatting brackets */
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

/* Fix for the interactive header/accordion wrapper */
/* Forces the object row header block ("Product2 (3 Objects)") to stay pitch black */
[data-testid="stJson"] [role="button"],
[data-testid="stJson"] [role="button"] *,
[data-testid="stJson"] summary,
[data-testid="stJson"] summary * {
    background-color: #000000 !important;
    color: #ffffff !important;
}

/* Clean hover state behavior on interactive nodes */
[data-testid="stJson"] [role="button"]:hover,
[data-testid="stJson"] summary:hover {
    background-color: #111111 !important;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# BACKEND IMPORTS
# ─────────────────────────────────────────────────────────────────────────────
from agents.cpq_agent import CPQAgent
from schema import schema_loader
import state.running_json as rj


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def check_sf_login():
    try:
        result = subprocess.run(
            "sf org display --target-org cpqOrg --json",
            shell=True, capture_output=True, text=True
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            if "result" in data:
                res = data["result"]
                return {
                    "username": res.get("username"),
                    "instanceUrl": res.get("instanceUrl"),
                    "accessToken": res.get("accessToken"),
                    "orgId": res.get("orgId") or res.get("id"),
                }
        return None
    except Exception:
        return None


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


# ─────────────────────────────────────────────────────────────────────────────
# SF CONNECTION CHECK
# ─────────────────────────────────────────────────────────────────────────────
if "sf_connected" not in st.session_state:
    env_keys = ["SF_USERNAME", "SF_INSTANCE_URL", "SF_ACCESS_TOKEN", "SF_ORG_ID"]
    if all(os.getenv(k) for k in env_keys):
        valid, _ = validate_sf_session(os.getenv("SF_INSTANCE_URL"), os.getenv("SF_ACCESS_TOKEN"))
        if valid:
            for k in env_keys:
                st.session_state[f"sf_{k.lower().replace('sf_', '')}"] = os.getenv(k)
            st.session_state.sf_username = os.getenv("SF_USERNAME")
            st.session_state.sf_instance_url = os.getenv("SF_INSTANCE_URL")
            st.session_state.sf_access_token = os.getenv("SF_ACCESS_TOKEN")
            st.session_state.sf_org_id = os.getenv("SF_ORG_ID")
            st.session_state.sf_connected = True
        else:
            cli_res = check_sf_login()
            if cli_res:
                save_sf_credentials(cli_res["username"], cli_res["instanceUrl"], cli_res["accessToken"], cli_res["orgId"])
                st.session_state.sf_username = cli_res["username"]
                st.session_state.sf_instance_url = cli_res["instanceUrl"]
                st.session_state.sf_access_token = cli_res["accessToken"]
                st.session_state.sf_org_id = cli_res["orgId"]
                st.session_state.sf_connected = True
            else:
                st.session_state.sf_connected = False
    else:
        cli_res = check_sf_login()
        if cli_res:
            save_sf_credentials(cli_res["username"], cli_res["instanceUrl"], cli_res["accessToken"], cli_res["orgId"])
            st.session_state.sf_username = cli_res["username"]
            st.session_state.sf_instance_url = cli_res["instanceUrl"]
            st.session_state.sf_access_token = cli_res["accessToken"]
            st.session_state.sf_org_id = cli_res["orgId"]
            st.session_state.sf_connected = True
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

        if st.button("Connect to Salesforce", use_container_width=True):
            with st.spinner("Opening Salesforce login — authenticate in the browser tab…"):
                proc = subprocess.run(
                    "sf org login web --alias cpqOrg",
                    shell=True, capture_output=True, text=True
                )
                if proc.returncode == 0:
                    cli_res = check_sf_login()
                    if cli_res:
                        valid, msg = validate_sf_session(cli_res["instanceUrl"], cli_res["accessToken"])
                        if valid:
                            save_sf_credentials(cli_res["username"], cli_res["instanceUrl"], cli_res["accessToken"], cli_res["orgId"])
                            st.session_state.sf_username = cli_res["username"]
                            st.session_state.sf_instance_url = cli_res["instanceUrl"]
                            st.session_state.sf_access_token = cli_res["accessToken"]
                            st.session_state.sf_org_id = cli_res["orgId"]
                            st.session_state.sf_connected = True
                            st.success("Connected!")
                            st.rerun()
                        else:
                            st.error(f"Validation failed: {msg}")
                    else:
                        st.error("Could not retrieve session after login.")
                else:
                    st.error(f"Login failed: {proc.stderr}")
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

# ── TOP NAV ──────────────────────────────────────────────────────────────────
nav_left, nav_right = st.columns([6, 1])
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

with nav_right:
    st.markdown("<div style='padding-top:8px'>", unsafe_allow_html=True)
    if st.button(f"👤  {short_user}", help="Account & settings", use_container_width=True):
        st.session_state.profile_open = not st.session_state.profile_open
    st.markdown("</div>", unsafe_allow_html=True)


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
                <span class="profile-val">{sf_org_id or "—"}</span>
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
        if st.button("↺  Reset Session", use_container_width=True):
            st.session_state.agent.reset()
            rj.clear_state()
            sync_from_backend()
            st.session_state.chat_history = [{"role": "assistant", "content": "Session cleared. Ready for a fresh start!"}]
            st.session_state.selected_record = None
            st.session_state.profile_open = False
            st.toast("Session reset.")
            st.rerun()
    with pc2:
        if st.button("⏻  Disconnect", use_container_width=True):
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
# STABLE COLUMNS LAYOUT
# ═════════════════════════════════════════════════════════════════════════════
col_left, col_right = st.columns([1, 1], gap="medium")


# ─────────────────────────────────────────────────────────────────────────────
# LEFT PANEL — Collapsible JSON Viewer & Interactivity Block Chart Diagram
# ─────────────────────────────────────────────────────────────────────────────
with col_left:
    st.markdown('<div class="panel-label">Interactive Data & Architecture State</div>', unsafe_allow_html=True)

    running_data = st.session_state.running_json
    has_data = any(records for records in running_data.values())

    if not has_data:
        st.markdown("""
        <div class="tree-empty">
            No active CPQ structures in stack context.<br>
            Use the chat assistant to spin up objects or load existing definitions.
        </div>
        """, unsafe_allow_html=True)
    else:
        # ── Collapsible JSON Schema Tree (Block Diagram removed) ──
        st.markdown("<p style='font-size:13px; font-weight:600; color:#846cf8; letter-spacing:0.8px; text-transform:uppercase; margin-bottom:8px;'>DATA STRUCTURAL ARCHITECTURE ALLOCATION</p>", unsafe_allow_html=True)

        chart_dataset = {key: len(val) for key, val in running_data.items() if len(val) > 0}

        if chart_dataset:
            col_metric1, col_metric2 = st.columns(2)
            with col_metric1:
                st.metric(label="Active Objects Tracked", value=len(chart_dataset))
            with col_metric2:
                st.metric(label="Total Individual Nodes Generated", value=sum(chart_dataset.values()))
        else:
            st.caption("Awaiting initial context creation map metrics to frame structural architecture details.")

        for obj_name, records in running_data.items():
            if not records:
                continue

            with st.expander(f"📦 {obj_name} ({len(records)} Records)", expanded=True):
                for rec in records:
                    rec_uuid = rec.get("uuid", "")
                    rec_name = rec.get("Name", f"Record {rec_uuid[:6]}")
                    is_deployed = bool(rec.get("Id"))
                    label_prefix = "🟢 Deployed" if is_deployed else "⚪ Draft"
                    st.markdown(f"**{rec_name}** · {label_prefix}")
                    st.json(rec)


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
    if user_input := st.chat_input("Ask me to construct models or provision validation rules..."):
        st.session_state.chat_history.append({"role": "user", "content": user_input})

        with st.spinner("Analyzing operational directives..."):
            try:
                response_payload = st.session_state.agent.chat(user_input)
                st.session_state.chat_history.append({"role": "assistant", "content": response_payload})
                sync_from_backend()
            except Exception as ex:
                err_msg = f"An analytical runtime error occurred processing the pipeline query:\n```\n{traceback.format_exc()}\n```"
                st.session_state.chat_history.append({"role": "assistant", "content": err_msg})

        st.rerun()