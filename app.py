import streamlit as st
import requests
import json
import time
import base64
from datetime import datetime
import os

# ─── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="GitMind — AI GitHub Agent",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;600;700&family=Space+Grotesk:wght@300;400;500;600;700&display=swap');

:root {
    --bg: #0a0e1a;
    --surface: #111827;
    --surface2: #1a2235;
    --border: #1e2d45;
    --accent: #00d4aa;
    --accent2: #7c3aed;
    --danger: #ef4444;
    --text: #e2e8f0;
    --muted: #64748b;
    --success: #10b981;
    --warning: #f59e0b;
}

html, body, [class*="css"] {
    font-family: 'Space Grotesk', sans-serif;
    background-color: var(--bg) !important;
    color: var(--text) !important;
}
.stApp { background: var(--bg) !important; }

section[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border);
}
section[data-testid="stSidebar"] * { color: var(--text) !important; }

.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div {
    background: var(--surface2) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    border-radius: 8px !important;
    font-family: 'Space Grotesk', sans-serif !important;
}

.stButton > button {
    background: linear-gradient(135deg, var(--accent2), #4f46e5) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 600 !important;
    padding: 0.6rem 1.5rem !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 20px rgba(124, 58, 237, 0.4) !important;
}

.hero {
    background: linear-gradient(135deg, #0f172a 0%, #1a1f35 50%, #0f1a2e 100%);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 2rem 2.5rem;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
}
.hero::before {
    content: '';
    position: absolute; top: -50%; right: -10%;
    width: 400px; height: 400px;
    background: radial-gradient(circle, rgba(0,212,170,0.08) 0%, transparent 70%);
    pointer-events: none;
}
.hero::after {
    content: '';
    position: absolute; bottom: -30%; left: 10%;
    width: 300px; height: 300px;
    background: radial-gradient(circle, rgba(124,58,237,0.08) 0%, transparent 70%);
    pointer-events: none;
}
.hero h1 {
    font-size: 2.4rem; font-weight: 700; margin: 0;
    background: linear-gradient(135deg, #00d4aa, #7c3aed);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.hero p { color: var(--muted); font-size: 1rem; margin: 0.5rem 0 0; }

.card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 0.75rem;
    transition: border-color 0.2s;
}
.card:hover { border-color: var(--accent); }
.card-title {
    font-size: 0.85rem; color: var(--muted);
    text-transform: uppercase; letter-spacing: 0.08em;
    margin-bottom: 0.5rem; font-family: 'JetBrains Mono', monospace;
}
.card-value { font-size: 1.6rem; font-weight: 700; color: var(--accent); }

.response-box {
    background: var(--surface2);
    border: 1px solid var(--accent); border-left: 4px solid var(--accent);
    border-radius: 8px; padding: 1rem 1.25rem;
    font-family: 'JetBrains Mono', monospace; font-size: 0.88rem;
    line-height: 1.7; margin-top: 1rem;
}
.error-box {
    background: rgba(239,68,68,0.1);
    border: 1px solid var(--danger); border-left: 4px solid var(--danger);
    border-radius: 8px; padding: 1rem 1.25rem; margin-top: 1rem;
}

/* ── Upload mode toggle ── */
.mode-toggle {
    display: flex;
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 4px;
    gap: 4px;
    margin-bottom: 1rem;
}

/* ── Drag-drop zone ── */
.drop-zone {
    border: 2px dashed var(--border);
    border-radius: 12px;
    padding: 2.5rem 1.5rem;
    text-align: center;
    background: var(--surface2);
    transition: all 0.25s ease;
    cursor: pointer;
    position: relative;
}
.drop-zone:hover, .drop-zone.dragover {
    border-color: var(--accent);
    background: rgba(0, 212, 170, 0.05);
}
.drop-zone .drop-icon { font-size: 2.8rem; margin-bottom: 0.5rem; }
.drop-zone .drop-title {
    font-size: 1rem; font-weight: 600; color: var(--text); margin-bottom: 0.3rem;
}
.drop-zone .drop-sub { font-size: 0.82rem; color: var(--muted); }

/* ── File preview chip ── */
.file-chip {
    display: inline-flex; align-items: center; gap: 8px;
    background: rgba(0,212,170,0.1);
    border: 1px solid rgba(0,212,170,0.3);
    border-radius: 8px; padding: 6px 12px;
    font-size: 0.85rem; font-family: 'JetBrains Mono', monospace;
    margin-top: 0.75rem; color: var(--accent);
}
.file-chip .chip-icon { font-size: 1.1rem; }

/* ── Supported formats badge row ── */
.format-badges {
    display: flex; flex-wrap: wrap; gap: 6px; margin-top: 0.75rem;
}
.fmt-badge {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 6px; padding: 2px 8px;
    font-size: 0.72rem; font-family: 'JetBrains Mono', monospace;
    color: var(--muted);
}

/* ── Upload progress ── */
.upload-progress {
    background: var(--surface2); border: 1px solid var(--border);
    border-radius: 10px; padding: 1rem 1.25rem; margin-top: 0.75rem;
}

.repo-card {
    background: var(--surface2); border: 1px solid var(--border);
    border-radius: 10px; padding: 1rem; margin-bottom: 0.6rem;
    display: flex; justify-content: space-between; align-items: center;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 8px; background: var(--surface) !important;
    padding: 4px; border-radius: 10px; border: 1px solid var(--border);
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important; border-radius: 8px !important;
    color: var(--muted) !important; font-weight: 500 !important;
}
.stTabs [aria-selected="true"] {
    background: var(--surface2) !important; color: var(--accent) !important;
}
.stTabs [data-baseweb="tab-panel"] { background: transparent !important; padding-top: 1.5rem; }

.chat-msg-user {
    background: rgba(124,58,237,0.15); border: 1px solid rgba(124,58,237,0.3);
    border-radius: 12px 12px 4px 12px; padding: 0.75rem 1rem;
    margin-bottom: 0.5rem; text-align: right;
}
.chat-msg-agent {
    background: var(--surface2); border: 1px solid var(--border);
    border-radius: 12px 12px 12px 4px; padding: 0.75rem 1rem;
    margin-bottom: 0.5rem; font-family: 'JetBrains Mono', monospace; font-size: 0.88rem;
}

.badge { display: inline-block; padding: 2px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
.badge-success { background: rgba(16,185,129,0.2); color: var(--success); }
.badge-danger { background: rgba(239,68,68,0.2); color: var(--danger); }
.badge-info { background: rgba(0,212,170,0.2); color: var(--accent); }
.badge-warning { background: rgba(245,158,11,0.2); color: var(--warning); }

/* Streamlit file uploader custom style */
[data-testid="stFileUploader"] {
    background: var(--surface2) !important;
    border: 2px dashed var(--border) !important;
    border-radius: 12px !important;
    padding: 1rem !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: var(--accent) !important;
}
[data-testid="stFileUploader"] label { color: var(--muted) !important; }

#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ─── Session State ─────────────────────────────────────────────────────────────
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "repos_cache" not in st.session_state:
    st.session_state.repos_cache = []
if "last_response" not in st.session_state:
    st.session_state.last_response = None
if "upload_mode" not in st.session_state:
    st.session_state.upload_mode = "text"  # "text" or "file"

API_BASE = os.environ.get("GITMIND_API", "http://localhost:8000")

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 1rem 0 1.5rem;">
        <div style="font-size:2.5rem;">🧠</div>
        <div style="font-size:1.2rem; font-weight:700; color:#00d4aa;">GitMind</div>
        <div style="font-size:0.75rem; color:#64748b;">AI GitHub Agent · Powered by Ollama</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 🔑 Credentials")
    st.markdown("**🦙 Ollama Model**")
    ollama_model = st.selectbox(
        "Select model",
        ["llama3", "llama3.1", "mistral", "gemma2", "phi3", "codellama", "llama2"],
        index=0, key="ollama_model_select", label_visibility="collapsed"
    )
    st.markdown('<div class="badge badge-info">✓ Ollama — no API key needed</div>', unsafe_allow_html=True)
    st.markdown("")
    github_token = st.text_input("GitHub Token", type="password", placeholder="ghp_...", key="github_token_input")
    if github_token:
        st.markdown('<div class="badge badge-success">✓ GitHub token set</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="badge badge-danger">⚠ GitHub token needed</div>', unsafe_allow_html=True)

    st.divider()
    st.markdown("### 🟢 Ollama Status")
    if st.button("Check Ollama", use_container_width=True, key="check_ollama"):
        try:
            r = requests.get(f"{API_BASE}/ollama/status", timeout=5)
            if r.status_code == 200:
                d = r.json()
                st.success(f"✅ Ollama running · {d.get('model', ollama_model)}")
            else:
                st.error("❌ Ollama not reachable via backend")
        except Exception:
            st.error("❌ Backend not running on port 8000")

    st.divider()
    st.markdown("### ⚡ Quick Commands")
    quick_cmds = ["List all my repos", "Create a new public repo", "Analyze my latest repo",
                  "Draft a PR description", "Add a README file", "Generate README for my repo"]
    for cmd in quick_cmds:
        if st.button(cmd, use_container_width=True, key=f"quick_{cmd}"):
            st.session_state["prefill_command"] = cmd

    st.divider()
    st.markdown("""
    <div style="color:#64748b; font-size:0.75rem;">
    Powered by <b>Ollama</b> (local LLM) + GitHub API<br>
    No API keys · Fully private · Runs on your machine
    </div>
    """, unsafe_allow_html=True)

# ─── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <h1>🧠 GitMind</h1>
    <p>Voice &amp; text-powered AI agent for GitHub — powered by Ollama (local LLM, free &amp; private) · create, manage, and understand your code with natural language</p>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🤖 Agent", "🎤 Voice", "📦 Repos", "✨ Insights", "📋 PR Drafter", "📝 README Gen"
])

def base_payload(**kwargs):
    return {"github_token": github_token, "ollama_model": ollama_model, **kwargs}

# ─── Tab 1: Agent ─────────────────────────────────────────────────────────────
with tab1:
    st.markdown("### Natural Language GitHub Agent")
    st.caption("Just tell GitMind what you want — Ollama figures out the rest.")

    prefill = st.session_state.pop("prefill_command", "")
    instruction = st.text_area(
        "What do you want to do?", value=prefill,
        placeholder='e.g. "Create a private repo called my-portfolio" or "List all my repos"',
        height=100, key="agent_instruction"
    )
    col1, col2 = st.columns([2, 1])
    with col1:
        run_btn = st.button("🚀 Execute", use_container_width=True)
    with col2:
        clear_btn = st.button("🗑 Clear History", use_container_width=True)

    if clear_btn:
        st.session_state.chat_history = []
        st.rerun()

    if run_btn and instruction:
        if not github_token:
            st.error("⚠️ Please enter your GitHub token in the sidebar.")
        else:
            with st.spinner("🧠 GitMind (Ollama) is thinking..."):
                try:
                    resp = requests.post(f"{API_BASE}/agent", json=base_payload(instruction=instruction), timeout=60)
                    data = resp.json()
                    if resp.status_code == 200:
                        st.session_state.chat_history.append({
                            "user": instruction, "agent": data,
                            "time": datetime.now().strftime("%H:%M:%S")
                        })
                        st.session_state.last_response = data
                    else:
                        st.markdown(f'<div class="error-box">❌ {data.get("detail", "Unknown error")}</div>', unsafe_allow_html=True)
                except requests.exceptions.ConnectionError:
                    st.error("❌ Cannot connect to backend. Is FastAPI running on port 8000?")
                except Exception as e:
                    st.error(f"❌ {str(e)}")

    if st.session_state.chat_history:
        st.markdown("---")
        st.markdown("### 💬 Conversation")
        for entry in reversed(st.session_state.chat_history):
            st.markdown(f'<div class="chat-msg-user">👤 {entry["user"]} <small style="color:#64748b"> {entry["time"]}</small></div>', unsafe_allow_html=True)
            details = entry["agent"].get("details", {})
            msg = details.get("message", "")
            action = entry["agent"].get("action", "")
            if action == "list_repos" and "repos" in details:
                st.markdown(f'<div class="chat-msg-agent">🤖 {msg}</div>', unsafe_allow_html=True)
                for r in details["repos"][:10]:
                    visibility = "🔒" if r.get("private") else "🌐"
                    st.markdown(f"""<div class="repo-card">
                        <span>{visibility} <b>{r['name']}</b> <small style="color:#64748b">({r.get('language','—')})</small></span>
                        <span style="color:#64748b; font-size:0.8rem">⭐ {r['stars']} · {r['updated']}</span>
                    </div>""", unsafe_allow_html=True)
            elif action == "generate_readme" and "readme" in details:
                st.markdown(f'<div class="chat-msg-agent">🤖 {details.get("message","")}</div>', unsafe_allow_html=True)
                if details.get("url"):
                    st.markdown(f'🔗 [View README on GitHub]({details["url"]})')
                with st.expander("👁 Preview Generated README"):
                    st.markdown(details["readme"])
                st.download_button("💾 Download README.md", details["readme"],
                                   file_name="README.md", mime="text/markdown",
                                   key=f"dl_readme_{entry['time']}")
            elif action == "insight" and "summary" in details:
                st.markdown(f'<div class="chat-msg-agent">🤖 <b>Repo Insight: {details.get("repo","")}</b><br><br>{details["summary"]}</div>', unsafe_allow_html=True)
            elif action == "pr_draft" and "pr_draft" in details:
                st.markdown(f'<div class="chat-msg-agent">🤖 PR Draft Generated ✅<br><br>{details["pr_draft"]}</div>', unsafe_allow_html=True)
            else:
                display = msg or json.dumps(details, indent=2)
                st.markdown(f'<div class="chat-msg-agent">🤖 {display}</div>', unsafe_allow_html=True)

# ─── Tab 2: Voice ─────────────────────────────────────────────────────────────
with tab2:
    st.markdown("### 🎤 Voice Commands")
    st.caption("Record your voice — GitMind transcribes and executes via Ollama (local).")
    st.markdown("""
    <div class="card">
        <div class="card-title">How Voice Works</div>
        <div style="color:#94a3b8; font-size:0.9rem; line-height:1.7;">
        1. Click <b>Start Recording</b> to capture your voice<br>
        2. Speak your GitHub command naturally<br>
        3. Click <b>Stop</b> — audio is saved locally<br>
        4. Upload it below — Ollama transcribes and executes<br>
        <span style="color:#64748b; font-size:0.82rem;">Note: local Whisper/speech model required for transcription</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    voice_html = """
    <div style="font-family: 'Space Grotesk', sans-serif;">
        <div id="status" style="color:#64748b; font-size:0.85rem; margin-bottom:1rem;">Ready to record</div>
        <div style="display:flex; gap:12px; margin-bottom:1rem;">
            <button id="startBtn" onclick="startRecording()" style="background:linear-gradient(135deg,#00d4aa,#0891b2);color:white;border:none;border-radius:8px;padding:10px 20px;font-size:14px;cursor:pointer;font-weight:600;">🎙 Start Recording</button>
            <button id="stopBtn" onclick="stopRecording()" disabled style="background:linear-gradient(135deg,#ef4444,#dc2626);color:white;border:none;border-radius:8px;padding:10px 20px;font-size:14px;cursor:pointer;font-weight:600;opacity:0.5;">⏹ Stop Recording</button>
        </div>
        <div id="transcript" style="background:#111827;border:1px solid #1e2d45;border-radius:8px;padding:12px;font-size:0.9rem;color:#94a3b8;min-height:60px;font-family:'JetBrains Mono',monospace;">Transcript will appear here...</div>
        <audio id="audioPlayback" controls style="margin-top:12px;width:100%;display:none;"></audio>
    </div>
    <script>
    let mediaRecorder, audioChunks = [];
    async function startRecording() {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];
        mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
        mediaRecorder.start();
        document.getElementById('status').innerHTML = '<span style="color:#00d4aa">● Recording...</span>';
        document.getElementById('startBtn').disabled = true;
        document.getElementById('stopBtn').disabled = false;
        document.getElementById('stopBtn').style.opacity = '1';
    }
    function stopRecording() {
        mediaRecorder.stop();
        mediaRecorder.stream.getTracks().forEach(t => t.stop());
        document.getElementById('status').textContent = 'Processing...';
        document.getElementById('startBtn').disabled = false;
        document.getElementById('stopBtn').disabled = true;
        mediaRecorder.onstop = () => {
            const blob = new Blob(audioChunks, { type: 'audio/webm' });
            const url = URL.createObjectURL(blob);
            document.getElementById('audioPlayback').src = url;
            document.getElementById('audioPlayback').style.display = 'block';
            document.getElementById('transcript').textContent = '✅ Audio recorded! Download and upload below.';
            document.getElementById('status').textContent = 'Recording complete.';
            const a = document.createElement('a');
            a.href = url; a.download = 'voice_command.webm';
            a.textContent = '💾 Download Audio';
            a.style = 'color:#00d4aa;display:block;margin-top:8px;font-size:0.85rem;';
            document.getElementById('transcript').appendChild(a);
        };
    }
    </script>
    """
    st.components.v1.html(voice_html, height=280)
    st.markdown("**Upload audio for transcription:**")
    audio_file = st.file_uploader("Upload recorded audio (.webm / .mp3 / .wav)", type=["webm", "mp3", "wav", "m4a"])
    if audio_file:
        if st.button("🔊 Transcribe Audio"):
            with st.spinner("Transcribing via backend..."):
                try:
                    resp = requests.post(
                        f"{API_BASE}/voice/transcribe",
                        files={"audio": (audio_file.name, audio_file.read(), audio_file.type)},
                        data={"ollama_model": ollama_model}, timeout=60
                    )
                    if resp.status_code == 200:
                        transcript = resp.json().get("transcript", "")
                        st.session_state["voice_transcript"] = transcript
                        st.success(f"📝 Transcript: **{transcript}**")
                    else:
                        st.error(resp.json().get("detail", "Transcription failed"))
                except Exception as e:
                    st.error(str(e))
    if "voice_transcript" in st.session_state and st.session_state["voice_transcript"]:
        st.markdown(f"**Detected command:** `{st.session_state['voice_transcript']}`")
        if st.button("▶ Execute Voice Command"):
            with st.spinner("Executing..."):
                try:
                    resp = requests.post(f"{API_BASE}/agent", json=base_payload(instruction=st.session_state["voice_transcript"]), timeout=60)
                    data = resp.json()
                    if resp.status_code == 200:
                        st.markdown(f'<div class="response-box">✅ {json.dumps(data.get("details", {}), indent=2)}</div>', unsafe_allow_html=True)
                    else:
                        st.error(data.get("detail"))
                except Exception as e:
                    st.error(str(e))

# ─── Tab 3: Repos ─────────────────────────────────────────────────────────────
with tab3:
    st.markdown("### 📦 Repository Manager")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("#### ➕ Create Repo")
        new_name = st.text_input("Repo name", placeholder="my-awesome-project")
        new_desc = st.text_input("Description", placeholder="What does this repo do?")
        new_private = st.checkbox("Private repo")
        if st.button("Create Repository", key="create_repo_btn"):
            if not github_token:
                st.error("GitHub token required")
            elif not new_name:
                st.error("Repo name required")
            else:
                with st.spinner("Creating..."):
                    try:
                        resp = requests.post(f"{API_BASE}/repos/create", json={
                            "github_token": github_token, "repo_name": new_name,
                            "description": new_desc, "private": new_private
                        }, timeout=15)
                        d = resp.json()
                        if resp.status_code == 200:
                            st.success(f"✅ Created [{d['repo']}]({d['url']})")
                        else:
                            st.error(d.get("detail"))
                    except Exception as e:
                        st.error(str(e))

    with col_b:
        st.markdown("#### 🗑 Delete Repo")
        del_name = st.text_input("Repo name to delete", placeholder="old-repo")
        st.warning("⚠️ This is permanent and cannot be undone.")
        if st.button("Delete Repository", key="del_repo_btn"):
            if not github_token or not del_name:
                st.error("Token and repo name required")
            else:
                with st.spinner("Deleting..."):
                    try:
                        resp = requests.post(f"{API_BASE}/repos/delete", json={
                            "github_token": github_token, "repo_name": del_name
                        }, timeout=15)
                        d = resp.json()
                        if resp.status_code == 200:
                            st.success(f"🗑 Deleted: {del_name}")
                        else:
                            st.error(d.get("detail"))
                    except Exception as e:
                        st.error(str(e))

    st.divider()
    st.markdown("#### 📋 All Repositories")
    if st.button("🔄 Fetch All Repos"):
        if not github_token:
            st.error("GitHub token required")
        else:
            with st.spinner("Fetching repos..."):
                try:
                    resp = requests.post(f"{API_BASE}/repos/list", json={"github_token": github_token, "repo_name": ""}, timeout=20)
                    if resp.status_code == 200:
                        st.session_state.repos_cache = resp.json().get("repos", [])
                    else:
                        st.error(resp.json().get("detail"))
                except Exception as e:
                    st.error(str(e))

    if st.session_state.repos_cache:
        st.caption(f"Showing {len(st.session_state.repos_cache)} repos")
        for r in st.session_state.repos_cache:
            vis = "🔒" if r.get("private") else "🌐"
            lang = r.get("language") or "—"
            rc1, rc2 = st.columns([5, 2])
            with rc1:
                st.markdown(f"""<div class="repo-card">
                    <div>
                        <span style="font-weight:600;">{vis} {r['name']}</span>
                        <span style="color:#64748b;font-size:0.8rem;margin-left:8px;">{lang}</span><br>
                        <a href="{r['url']}" style="color:#00d4aa;font-size:0.8rem;">{r['url']}</a>
                    </div>
                    <div style="text-align:right;">
                        <div>⭐ {r['stars']}</div>
                        <div style="color:#64748b;font-size:0.75rem;">{r['updated']}</div>
                    </div>
                </div>""", unsafe_allow_html=True)
            with rc2:
                if st.button(f"📝 Gen README", key=f"readme_quick_{r['name']}", use_container_width=True):
                    if not github_token:
                        st.error("GitHub token required in sidebar")
                    else:
                        with st.spinner(f"🧠 Generating README for {r['name']}..."):
                            try:
                                resp = requests.post(f"{API_BASE}/readme/generate", json={
                                    "github_token": github_token, "repo_name": r["name"],
                                    "ollama_model": ollama_model, "extra_context": "", "push_to_repo": True
                                }, timeout=120)
                                d = resp.json()
                                if resp.status_code == 200:
                                    st.session_state["generated_readme"] = d
                                    st.session_state["generated_readme"]["message"] = f"README pushed to **{r['name']}**!"
                                    st.success(f"✅ README generated & pushed to [{r['name']}]({d.get('url','')})")
                                    with st.expander(f"👁 Preview README for {r['name']}", expanded=False):
                                        st.markdown(d.get("readme", ""))
                                else:
                                    st.error(d.get("detail"))
                            except Exception as e:
                                st.error(str(e))

    # ══════════════════════════════════════════════════════════════
    # ── ADD / UPDATE FILE SECTION (with mode toggle) ──────────────
    # ══════════════════════════════════════════════════════════════
    st.divider()
    st.markdown("#### 📄 Add / Update File")

    # ── Mode toggle ──
    mode_col1, mode_col2 = st.columns(2)
    with mode_col1:
        if st.button(
            "✏️ Text / Code Editor",
            use_container_width=True,
            key="mode_text_btn",
            type="primary" if st.session_state.upload_mode == "text" else "secondary"
        ):
            st.session_state.upload_mode = "text"
            st.rerun()
    with mode_col2:
        if st.button(
            "📁 Upload File (Drag & Drop)",
            use_container_width=True,
            key="mode_file_btn",
            type="primary" if st.session_state.upload_mode == "file" else "secondary"
        ):
            st.session_state.upload_mode = "file"
            st.rerun()

    # ── Active mode indicator ──
    if st.session_state.upload_mode == "text":
        st.markdown('<div class="badge badge-info" style="margin-bottom:1rem;">✏️ Mode: Text / Code</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="badge badge-warning" style="margin-bottom:1rem;">📁 Mode: Binary / Any File Upload</div>', unsafe_allow_html=True)

    # ────────────────────────────────────────────────────────────
    # MODE A: Text / Code editor (original behaviour)
    # ────────────────────────────────────────────────────────────
    if st.session_state.upload_mode == "text":
        file_repo    = st.text_input("Target repo name", placeholder="my-awesome-project", key="file_repo_text")
        file_path    = st.text_input("File path in repo", placeholder="src/main.py  or  data/notes.txt", key="file_path_text")
        file_content = st.text_area("File content", height=220, placeholder="# Paste your code or text here", key="file_content_text")
        file_commit  = st.text_input("Commit message (leave blank for AI-generated)", placeholder="Add feature X", key="file_commit_text")

        if st.button("📤 Push Text File", key="push_text_btn"):
            if not github_token or not file_repo or not file_path or not file_content:
                st.error("All fields required (except commit message)")
            else:
                with st.spinner("Pushing..."):
                    try:
                        resp = requests.post(f"{API_BASE}/files/add", json={
                            "github_token": github_token,
                            "repo_name": file_repo,
                            "file_path": file_path,
                            "content": file_content,
                            "commit_message": file_commit,
                            "ollama_model": ollama_model
                        }, timeout=60)
                        d = resp.json()
                        if resp.status_code == 200:
                            st.success(f"✅ {d.get('action','Done').capitalize()}: `{file_path}` — Commit: *{d.get('commit','')}*")
                        else:
                            st.error(d.get("detail"))
                    except Exception as e:
                        st.error(str(e))

    # ────────────────────────────────────────────────────────────
    # MODE B: Drag & Drop — any file (images, datasets, binaries)
    # ────────────────────────────────────────────────────────────
    else:
        st.markdown("""
        <div class="card" style="margin-bottom:1rem;">
            <div class="card-title">Supported file types</div>
            <div class="format-badges">
                <span class="fmt-badge">🖼 PNG</span>
                <span class="fmt-badge">🖼 JPG/JPEG</span>
                <span class="fmt-badge">🖼 GIF</span>
                <span class="fmt-badge">🖼 SVG</span>
                <span class="fmt-badge">🖼 WEBP</span>
                <span class="fmt-badge">📊 CSV</span>
                <span class="fmt-badge">📊 XLSX</span>
                <span class="fmt-badge">📊 JSON</span>
                <span class="fmt-badge">📊 Parquet</span>
                <span class="fmt-badge">📄 PDF</span>
                <span class="fmt-badge">🗜 ZIP</span>
                <span class="fmt-badge">📝 TXT</span>
                <span class="fmt-badge">🐍 .py</span>
                <span class="fmt-badge">⚙️ Any</span>
            </div>
            <div style="color:#64748b; font-size:0.8rem; margin-top:0.75rem;">
            Max file size: <b>100 MB</b> (GitHub API limit)
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Target repo + path row
        up_col1, up_col2 = st.columns(2)
        with up_col1:
            upload_repo = st.text_input(
                "Target repo name",
                placeholder="my-awesome-project",
                key="upload_repo"
            )
        with up_col2:
            upload_dest_path = st.text_input(
                "Destination path in repo",
                placeholder="assets/logo.png  or  data/train.csv",
                key="upload_dest_path",
                help="The path where the file will appear in your GitHub repo. Include folders if needed."
            )

        upload_commit = st.text_input(
            "Commit message (leave blank for AI-generated)",
            placeholder="Add dataset / Add image",
            key="upload_commit"
        )

        # ── Drag & drop uploader ──
        st.markdown("""
        <div style="color:#94a3b8; font-size:0.85rem; margin-bottom:0.5rem;">
            📂 <b>Drag files here</b> or click to browse — images, CSVs, datasets, any binary
        </div>
        """, unsafe_allow_html=True)

        uploaded_file = st.file_uploader(
            "Drop your file here",
            type=None,          # accept ALL file types
            accept_multiple_files=False,
            key="binary_uploader",
            label_visibility="collapsed",
            help="Drag and drop any file — image, dataset, PDF, zip, etc."
        )

        # ── File preview after upload ──
        if uploaded_file is not None:
            file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
            file_ext = uploaded_file.name.split(".")[-1].lower() if "." in uploaded_file.name else "bin"

            # Choose icon based on type
            ext_icons = {
                "png": "🖼", "jpg": "🖼", "jpeg": "🖼", "gif": "🖼", "svg": "🖼", "webp": "🖼",
                "csv": "📊", "xlsx": "📊", "xls": "📊", "parquet": "📊", "json": "📋",
                "pdf": "📄", "zip": "🗜", "gz": "🗜", "tar": "🗜",
                "py": "🐍", "js": "🟨", "ts": "🟦", "txt": "📝", "md": "📝",
            }
            icon = ext_icons.get(file_ext, "📎")

            st.markdown(f"""
            <div class="file-chip">
                <span class="chip-icon">{icon}</span>
                <span><b>{uploaded_file.name}</b></span>
                <span style="color:#64748b;">·</span>
                <span style="color:#64748b;">{file_size_mb:.2f} MB</span>
                <span style="color:#64748b;">·</span>
                <span style="color:#64748b;">{uploaded_file.type or 'binary'}</span>
            </div>
            """, unsafe_allow_html=True)

            # Preview for images
            if file_ext in ("png", "jpg", "jpeg", "gif", "webp"):
                with st.expander("👁 Image Preview", expanded=True):
                    st.image(uploaded_file, use_container_width=True)

            # Preview for CSV
            elif file_ext == "csv":
                try:
                    import pandas as pd
                    df = pd.read_csv(uploaded_file)
                    uploaded_file.seek(0)   # reset buffer after read
                    with st.expander(f"👁 CSV Preview — {len(df)} rows × {len(df.columns)} cols", expanded=True):
                        st.dataframe(df.head(20), use_container_width=True)
                except Exception:
                    pass

            # Preview for JSON
            elif file_ext == "json":
                try:
                    raw_json = json.loads(uploaded_file.getvalue().decode("utf-8"))
                    uploaded_file.seek(0)
                    with st.expander("👁 JSON Preview", expanded=False):
                        st.json(raw_json)
                except Exception:
                    pass

            # Preview for text / code
            elif file_ext in ("txt", "md", "py", "js", "ts", "html", "css", "yaml", "yml", "toml", "sh"):
                try:
                    text_content = uploaded_file.getvalue().decode("utf-8", errors="replace")
                    uploaded_file.seek(0)
                    with st.expander("👁 Text Preview", expanded=False):
                        st.code(text_content[:3000] + ("\n... (truncated)" if len(text_content) > 3000 else ""), language=file_ext)
                except Exception:
                    pass

            st.markdown("")

            # Auto-fill destination path from filename if empty
            if not upload_dest_path:
                st.info(f"💡 Tip: Set **Destination path** above to where this file should go in the repo (e.g. `assets/{uploaded_file.name}` or `data/{uploaded_file.name}`)")

            # ── Push button ──
            if st.button("🚀 Push File to GitHub", key="push_binary_btn", use_container_width=True):
                if not github_token:
                    st.error("⚠️ GitHub token required in sidebar.")
                elif not upload_repo:
                    st.error("⚠️ Target repo name required.")
                elif not upload_dest_path:
                    st.error("⚠️ Destination path required (e.g. `assets/logo.png`).")
                elif file_size_mb > 100:
                    st.error(f"❌ File too large ({file_size_mb:.1f} MB). GitHub API limit is 100 MB.")
                else:
                    with st.spinner(f"📤 Uploading `{uploaded_file.name}` ({file_size_mb:.2f} MB) to `{upload_repo}/{upload_dest_path}`..."):
                        try:
                            uploaded_file.seek(0)
                            resp = requests.post(
                                f"{API_BASE}/files/upload",
                                files={"file": (uploaded_file.name, uploaded_file, uploaded_file.type or "application/octet-stream")},
                                data={
                                    "github_token": github_token,
                                    "repo_name": upload_repo,
                                    "file_path": upload_dest_path,
                                    "commit_message": upload_commit,
                                    "ollama_model": ollama_model,
                                },
                                timeout=120
                            )
                            d = resp.json()
                            if resp.status_code == 200:
                                action_word = d.get("action", "pushed").capitalize()
                                st.success(
                                    f"✅ **{action_word}** `{upload_dest_path}` to `{upload_repo}`\n\n"
                                    f"📝 Commit: *{d.get('commit', '')}*"
                                )
                                if d.get("url"):
                                    st.markdown(f"🔗 [View file on GitHub]({d['url']})")
                                st.markdown(f"""
                                <div class="upload-progress">
                                    <div style="display:flex;justify-content:space-between;align-items:center;">
                                        <span style="color:#10b981;font-weight:600;">✅ Upload complete</span>
                                        <span style="color:#64748b;font-size:0.8rem;">{file_size_mb:.2f} MB · {d.get('action','created')}</span>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                            else:
                                st.error(f"❌ {d.get('detail', 'Upload failed')}")
                        except requests.exceptions.ConnectionError:
                            st.error("❌ Cannot connect to backend. Is FastAPI running on port 8000?")
                        except Exception as e:
                            st.error(f"❌ {str(e)}")
        else:
            # Empty state placeholder
            st.markdown("""
            <div class="drop-zone">
                <div class="drop-icon">📂</div>
                <div class="drop-title">Drag &amp; drop any file here</div>
                <div class="drop-sub">or click to browse your computer</div>
                <div class="drop-sub" style="margin-top:0.5rem; font-size:0.75rem;">
                    Images · CSVs · Datasets · PDFs · ZIPs · Any binary
                </div>
            </div>
            """, unsafe_allow_html=True)

# ─── Tab 4: Insights ──────────────────────────────────────────────────────────
with tab4:
    st.markdown("### ✨ AI Repo Insights")
    st.caption("Ollama analyzes your repo's commit history and gives you actionable insights.")
    insight_repo = st.text_input("Repo name to analyze", placeholder="my-portfolio", key="insight_repo")
    if st.button("🔍 Analyze Repo", key="analyze_btn"):
        if not github_token or not insight_repo:
            st.error("GitHub token and repo name required")
        else:
            with st.spinner("Ollama is analyzing your repo..."):
                try:
                    resp = requests.post(f"{API_BASE}/repos/insight", json={
                        "github_token": github_token, "repo_name": insight_repo, "ollama_model": ollama_model
                    }, timeout=120)
                    d = resp.json()
                    if resp.status_code == 200:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.markdown(f'<div class="card"><div class="card-title">⭐ Stars</div><div class="card-value">{d.get("stars",0)}</div></div>', unsafe_allow_html=True)
                        with col2:
                            st.markdown(f'<div class="card"><div class="card-title">🍴 Forks</div><div class="card-value">{d.get("forks",0)}</div></div>', unsafe_allow_html=True)
                        with col3:
                            st.markdown(f'<div class="card"><div class="card-title">🐛 Open Issues</div><div class="card-value">{d.get("open_issues",0)}</div></div>', unsafe_allow_html=True)
                        st.markdown("#### 🧠 AI Analysis")
                        st.markdown(f'<div class="response-box">{d.get("summary","No summary available")}</div>', unsafe_allow_html=True)
                    else:
                        st.error(d.get("detail"))
                except Exception as e:
                    st.error(str(e))

# ─── Tab 5: PR Drafter ────────────────────────────────────────────────────────
with tab5:
    st.markdown("### 📋 AI Pull Request Drafter")
    st.caption("Describe your changes in plain English — Ollama writes a professional PR.")
    pr_repo = st.text_input("Repository name", placeholder="my-project", key="pr_repo")
    pr_desc = st.text_area("Describe what you changed", height=150,
        placeholder="I added a login system with JWT auth, fixed the password reset bug...", key="pr_desc")
    if st.button("✍️ Generate PR Draft", key="pr_btn"):
        if not pr_repo or not pr_desc:
            st.error("Repo name and description required")
        else:
            with st.spinner("Ollama is writing your PR..."):
                try:
                    resp = requests.post(f"{API_BASE}/pr/draft", json={
                        "github_token": github_token or "dummy",
                        "repo_name": pr_repo, "description": pr_desc, "ollama_model": ollama_model
                    }, timeout=60)
                    d = resp.json()
                    if resp.status_code == 200:
                        pr_text = d.get("pr_draft", "")
                        st.markdown("#### 📋 Your PR Draft")
                        st.markdown(f'<div class="response-box">{pr_text}</div>', unsafe_allow_html=True)
                        st.download_button("💾 Download PR", pr_text, file_name="pr_draft.md", mime="text/markdown")
                    else:
                        st.error(d.get("detail"))
                except Exception as e:
                    st.error(str(e))

# ─── Tab 6: README Generator ──────────────────────────────────────────────────
with tab6:
    st.markdown("### 📝 AI README Generator")
    st.caption("Ollama reads your repo's files, commits, and structure — then writes a professional README.")

    col_info, col_preview = st.columns([1, 1])
    with col_info:
        st.markdown("""
        <div class="card">
            <div class="card-title">How it works</div>
            <div style="color:#94a3b8; font-size:0.88rem; line-height:1.8;">
            🔍 <b>Scans</b> your full file tree<br>
            📦 <b>Reads</b> dependency files (package.json, requirements.txt, etc.)<br>
            📜 <b>Analyzes</b> recent commit history<br>
            🦙 <b>Ollama</b> infers what the project does (local, free, private)<br>
            📝 <b>Writes</b> a world-class README with badges, usage, structure<br>
            🚀 <b>Pushes</b> directly to your repo (optional)
            </div>
        </div>
        """, unsafe_allow_html=True)
        readme_repo = st.text_input("Repository name", placeholder="my-awesome-project", key="readme_repo")
        extra_context = st.text_area("Extra context for Ollama (optional)",
            placeholder="e.g. 'This is a REST API for a food delivery app using FastAPI and PostgreSQL.'",
            height=100, key="readme_context")
        push_readme = st.checkbox("Push README.md directly to repo", value=True, key="push_readme")
        if push_readme:
            st.markdown('<div class="badge badge-info">📤 Will auto-commit README.md to repo</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="badge badge-info">📋 Preview only — won\'t push to GitHub</div>', unsafe_allow_html=True)
        st.markdown("")
        gen_btn = st.button("🧠 Generate README", use_container_width=True, key="gen_readme_btn")

    with col_preview:
        if "generated_readme" in st.session_state and st.session_state["generated_readme"]:
            r = st.session_state["generated_readme"]
            st.markdown(f"""<div class="card">
                <div class="card-title">Generation Result</div>
                <div style="color:#10b981;font-size:0.9rem;">✅ {r.get('message','README generated!')}</div>
                {'<div style="margin-top:8px;"><a href="' + r.get("url","") + '" style="color:#00d4aa;font-size:0.85rem;">🔗 View on GitHub →</a></div>' if r.get("url") else ''}
            </div>""", unsafe_allow_html=True)
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                st.markdown(f'<div class="card"><div class="card-title">Language</div><div style="color:#e2e8f0;font-weight:600;">{r.get("language","—")}</div></div>', unsafe_allow_html=True)
            with col_d2:
                st.markdown(f'<div class="card"><div class="card-title">Files Scanned</div><div style="color:#e2e8f0;font-weight:600;">{r.get("file_count","—")}</div></div>', unsafe_allow_html=True)
        else:
            st.markdown("""<div style="height:200px;display:flex;align-items:center;justify-content:center;
                border:1px dashed #1e2d45;border-radius:12px;color:#334155;font-size:0.9rem;">
                Preview will appear here after generation
            </div>""", unsafe_allow_html=True)

    if gen_btn:
        if not github_token:
            st.error("⚠️ GitHub token required in the sidebar.")
        elif not readme_repo:
            st.error("⚠️ Enter a repository name.")
        else:
            progress_bar = st.progress(0, text="🔍 Scanning repository structure...")
            try:
                import time as _time
                _time.sleep(0.4)
                progress_bar.progress(25, text="📜 Reading commits and dependency files...")
                _time.sleep(0.3)
                progress_bar.progress(50, text="🦙 Ollama is writing your README...")
                resp = requests.post(f"{API_BASE}/readme/generate", json={
                    "github_token": github_token, "repo_name": readme_repo,
                    "ollama_model": ollama_model, "extra_context": extra_context,
                    "push_to_repo": push_readme
                }, timeout=120)
                progress_bar.progress(90, text="📝 Finalizing...")
                _time.sleep(0.2)
                d = resp.json()
                if resp.status_code == 200:
                    progress_bar.progress(100, text="✅ Done!")
                    pushed = d.get("pushed", False)
                    d["message"] = f"README pushed to **{readme_repo}**!" if pushed else "README generated (not pushed)."
                    st.session_state["generated_readme"] = d
                    st.rerun()
                else:
                    progress_bar.empty()
                    st.error(f"❌ {d.get('detail','Generation failed')}")
            except requests.exceptions.ConnectionError:
                progress_bar.empty()
                st.error("❌ Cannot connect to backend. Is FastAPI running on port 8000?")
            except Exception as e:
                progress_bar.empty()
                st.error(f"❌ {str(e)}")

    if "generated_readme" in st.session_state and st.session_state.get("generated_readme", {}).get("readme"):
        readme_text = st.session_state["generated_readme"]["readme"]
        st.divider()
        view_col, raw_col = st.columns([3, 1])
        with view_col:
            st.markdown("#### 📄 Generated README")
        with raw_col:
            st.download_button("💾 Download README.md", readme_text,
                               file_name="README.md", mime="text/markdown", use_container_width=True)
        with st.expander("👁 Rendered Preview", expanded=True):
            st.markdown(readme_text)
        with st.expander("🔤 Raw Markdown"):
            st.code(readme_text, language="markdown")
        if st.button("🔄 Regenerate with different context", key="regen_readme"):
            del st.session_state["generated_readme"]
            st.rerun()

st.markdown("""
<div style="text-align:center;color:#334155;font-size:0.75rem;padding:2rem 0 1rem;font-family:'JetBrains Mono',monospace;">
    GitMind v2.0 · Powered by Ollama (local LLM, free &amp; private) · GitHub API · By [Neha Geete]
</div>
""", unsafe_allow_html=True)