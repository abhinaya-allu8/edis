"""
EDIS — Frontend
Enterprise Document Intelligence System
"""

import streamlit as st
import requests
from typing import Optional

BACKEND_URL = "http://localhost:8000"

st.set_page_config(
    page_title="EDIS — Document Intelligence",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:ital,wght@0,300;0,400;0,500;1,300&family=Outfit:wght@300;400;500;600&display=swap');
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}
html,body,[data-testid="stAppViewContainer"]{background:#060b18!important;color:#e2e8f0!important;font-family:'Outfit',sans-serif!important;}
[data-testid="stAppViewContainer"]{background:radial-gradient(ellipse at 20% 0%,rgba(0,212,255,0.07) 0%,transparent 50%),radial-gradient(ellipse at 80% 100%,rgba(99,60,255,0.06) 0%,transparent 50%),#060b18!important;}
[data-testid="stSidebar"]{background:#080d1c!important;border-right:1px solid rgba(0,212,255,0.1)!important;}
#MainMenu,footer,header{visibility:hidden!important;}
[data-testid="stDecoration"]{display:none!important;}
h1,h2,h3,h4{font-family:'Syne',sans-serif!important;}
[data-testid="stTabs"] button{font-family:'Outfit',sans-serif!important;font-size:0.85rem!important;font-weight:500!important;color:#64748b!important;border-radius:0!important;border-bottom:2px solid transparent!important;padding:0.6rem 1.2rem!important;transition:all 0.2s!important;}
[data-testid="stTabs"] button[aria-selected="true"]{color:#00d4ff!important;border-bottom:2px solid #00d4ff!important;background:transparent!important;}
[data-testid="stTextArea"] textarea{background:#0d1526!important;border:1px solid rgba(0,212,255,0.15)!important;border-radius:10px!important;color:#e2e8f0!important;font-family:'Outfit',sans-serif!important;font-size:0.95rem!important;resize:none!important;}
[data-testid="stTextInput"] input{background:#0d1526!important;border:1px solid rgba(0,212,255,0.15)!important;border-radius:8px!important;color:#e2e8f0!important;font-family:'DM Mono',monospace!important;font-size:0.8rem!important;}
[data-testid="stSelectbox"]>div>div{background:#0d1526!important;border:1px solid rgba(0,212,255,0.15)!important;border-radius:8px!important;color:#e2e8f0!important;}
[data-testid="stButton"]>button[kind="primary"]{background:linear-gradient(135deg,#00d4ff 0%,#0099cc 100%)!important;border:none!important;border-radius:10px!important;color:#060b18!important;font-family:'Syne',sans-serif!important;font-size:0.9rem!important;font-weight:700!important;letter-spacing:0.05em!important;transition:all 0.2s!important;text-transform:uppercase!important;}
[data-testid="stButton"]>button[kind="primary"]:hover{box-shadow:0 0 24px rgba(0,212,255,0.4)!important;transform:translateY(-1px)!important;}
[data-testid="stButton"]>button[kind="secondary"]{background:transparent!important;border:1px solid rgba(255,80,80,0.3)!important;border-radius:8px!important;color:#ff5050!important;font-size:0.8rem!important;transition:all 0.2s!important;}
[data-testid="stFileUploader"]{background:#0d1526!important;border:1px dashed rgba(0,212,255,0.2)!important;border-radius:12px!important;}
[data-testid="stCheckbox"] label{color:#64748b!important;font-size:0.82rem!important;}
::-webkit-scrollbar{width:4px;height:4px;}
::-webkit-scrollbar-thumb{background:rgba(0,212,255,0.2);border-radius:4px;}
.edis-logo{font-family:'Syne',sans-serif;font-size:1.6rem;font-weight:800;background:linear-gradient(135deg,#00d4ff,#7c6fff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}
.edis-tagline{font-family:'DM Mono',monospace;font-size:0.68rem;color:#334155;letter-spacing:0.12em;text-transform:uppercase;margin-top:2px;}
.status-dot{display:inline-block;width:7px;height:7px;border-radius:50%;margin-right:8px;animation:pulse 2s infinite;}
.status-dot.green{background:#22c55e;box-shadow:0 0 6px #22c55e;}
.status-dot.red{background:#ef4444;box-shadow:0 0 6px #ef4444;animation:none;}
@keyframes pulse{0%,100%{opacity:1;}50%{opacity:0.4;}}
.section-label{font-family:'DM Mono',monospace;font-size:0.65rem;letter-spacing:0.15em;text-transform:uppercase;color:#334155;margin-bottom:0.75rem;}
.answer-box{background:linear-gradient(135deg,#0d1a2e,#0a1525);border:1px solid rgba(0,212,255,0.15);border-radius:14px;padding:1.75rem;margin:1rem 0;position:relative;overflow:hidden;}
.answer-box::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,#00d4ff,#7c6fff,transparent);}
.answer-label{font-family:'DM Mono',monospace;font-size:0.62rem;letter-spacing:0.2em;text-transform:uppercase;color:#00d4ff;margin-bottom:0.75rem;opacity:0.7;}
.stat-card{background:#0d1526;border:1px solid rgba(0,212,255,0.08);border-radius:12px;padding:1.2rem;}
.stat-label{font-family:'DM Mono',monospace;font-size:0.62rem;letter-spacing:0.15em;text-transform:uppercase;color:#334155;margin-bottom:0.5rem;}
.stat-value{font-family:'Syne',sans-serif;font-size:1.8rem;font-weight:700;color:#00d4ff;line-height:1;}
.stat-sub{font-family:'DM Mono',monospace;font-size:0.68rem;color:#334155;margin-top:0.3rem;}
.citation-item{background:#0a1120;border:1px solid rgba(124,111,255,0.15);border-left:3px solid rgba(124,111,255,0.5);border-radius:8px;padding:0.9rem 1.1rem;margin-bottom:0.5rem;}
.citation-header{font-family:'DM Mono',monospace;font-size:0.72rem;color:#7c6fff;margin-bottom:0.4rem;display:flex;justify-content:space-between;}
.citation-score{background:rgba(124,111,255,0.12);padding:1px 8px;border-radius:20px;font-size:0.65rem;}
.citation-preview{font-family:'Outfit',sans-serif;font-size:0.8rem;color:#475569;line-height:1.5;}
.ingest-result{background:#0a1120;border:1px solid rgba(34,197,94,0.2);border-left:3px solid #22c55e;border-radius:8px;padding:0.8rem 1.1rem;margin-bottom:0.5rem;}
.ingest-fail{border-left-color:#ef4444!important;border-color:rgba(239,68,68,0.2)!important;}
.ingest-filename{font-family:'DM Mono',monospace;font-size:0.75rem;color:#22c55e;margin-bottom:0.2rem;}
.ingest-fail .ingest-filename{color:#ef4444;}
.ingest-meta{font-family:'Outfit',sans-serif;font-size:0.78rem;color:#475569;}
.main-title{font-family:'Syne',sans-serif;font-size:1.9rem;font-weight:800;letter-spacing:-0.03em;background:linear-gradient(135deg,#ffffff 0%,#94a3b8 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;line-height:1;}
.main-sub{font-family:'DM Mono',monospace;font-size:0.68rem;letter-spacing:0.15em;text-transform:uppercase;color:#334155;margin-top:0.5rem;margin-bottom:1.5rem;}
.config-row{display:flex;align-items:center;gap:0.5rem;margin-bottom:0.35rem;}
.config-key{font-family:'DM Mono',monospace;font-size:0.65rem;color:#475569;}
.config-val{font-family:'DM Mono',monospace;font-size:0.65rem;color:#00d4ff;background:rgba(0,212,255,0.06);padding:1px 7px;border-radius:4px;}
.ragas-row{display:flex;align-items:center;gap:0.75rem;margin-bottom:0.6rem;}
.ragas-lbl{font-family:'DM Mono',monospace;font-size:0.68rem;color:#64748b;width:140px;flex-shrink:0;}
.ragas-bg{flex:1;height:4px;background:rgba(255,255,255,0.06);border-radius:4px;overflow:hidden;}
.ragas-fill{height:100%;border-radius:4px;}
.ragas-num{font-family:'Syne',sans-serif;font-size:0.8rem;font-weight:700;width:36px;text-align:right;}
</style>
""", unsafe_allow_html=True)


def check_backend():
    try:
        r = requests.get(f"{BACKEND_URL}/health", timeout=4)
        return r.status_code == 200
    except:
        return False

def get_collection_info():
    try:
        r = requests.get(f"{BACKEND_URL}/collection/info", timeout=4)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return None

def ingest_file(file):
    r = requests.post(f"{BACKEND_URL}/ingest", files={"file": (file.name, file.getvalue(), file.type)}, timeout=300)
    return r.json()

def ingest_url(url):
    r = requests.post(f"{BACKEND_URL}/ingest/url", json={"url": url}, timeout=300)
    return r.json()

def query_backend(query, source_filter, doc_type_filter, skip_evaluation):
    r = requests.post(f"{BACKEND_URL}/query", json={"query": query, "source_filter": source_filter or None, "doc_type_filter": doc_type_filter or None, "skip_evaluation": skip_evaluation}, timeout=300)
    return r.json()

def wipe_collection():
    r = requests.delete(f"{BACKEND_URL}/collection", timeout=30)
    return r.json()

def ragas_bar(label, score):
    if score is None:
        return ""
    pct = int(score * 100)
    color = "#22c55e" if pct >= 80 else "#f59e0b" if pct >= 60 else "#ef4444"
    return f'<div class="ragas-row"><span class="ragas-lbl">{label}</span><div class="ragas-bg"><div class="ragas-fill" style="width:{pct}%;background:linear-gradient(90deg,{color},#00d4ff);"></div></div><span class="ragas-num" style="color:{color}">{score:.2f}</span></div>'


with st.sidebar:
    st.markdown('<div class="edis-logo">⬡ EDIS</div>', unsafe_allow_html=True)
    st.markdown('<div class="edis-tagline">Enterprise Document Intelligence</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    backend_ok = check_backend()
    if backend_ok:
        st.markdown('<div><span class="status-dot green"></span><span style="font-family:monospace;font-size:0.72rem;color:#22c55e;">System online</span></div>', unsafe_allow_html=True)
        col_info = get_collection_info()
        if col_info:
            st.markdown(f'<div style="font-family:monospace;font-size:0.65rem;color:#334155;margin-left:15px;">{col_info.get("total_vectors",0)} vectors indexed</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div><span class="status-dot red"></span><span style="font-family:monospace;font-size:0.72rem;color:#ef4444;">Backend offline</span></div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-label">Configuration</div>', unsafe_allow_html=True)
    from dotenv import dotenv_values
    try:
        env = dotenv_values("/Users/abhi/desktop/projects/edis/.env")
    except:
        env = {}
    provider = env.get("LLM_PROVIDER", "ollama")
    model = env.get("OPENAI_MODEL","gpt-4o-mini") if provider=="openai" else env.get("ANTHROPIC_MODEL","claude") if provider=="anthropic" else env.get("OLLAMA_MODEL","llama3.2")
    for k, v in [("LLM",provider),("Model",model),("Embed",env.get("EMBEDDING_PROVIDER","ollama")),("Chunk",env.get("CHUNKING_STRATEGY","semantic")),("Size",env.get("CHUNK_SIZE","512")),("Top-K",env.get("TOP_K","10"))]:
        st.markdown(f'<div class="config-row"><span class="config-key">{k}</span><span class="config-val">{v}</span></div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("⚠ Wipe Collection", use_container_width=True, type="secondary"):
        result = wipe_collection()
        if result.get("status") == "wiped":
            st.success("Wiped.")
            st.rerun()


st.markdown('<div class="main-title">Document Intelligence</div>', unsafe_allow_html=True)
st.markdown('<div class="main-sub">Multi-Agent RAG · Semantic Retrieval · RAGAS Evaluation</div>', unsafe_allow_html=True)

tab_query, tab_ingest = st.tabs(["Query", "Ingest"])

with tab_query:
    col_main, col_filters = st.columns([3, 1], gap="large")
    with col_main:
        st.markdown('<div class="section-label">Ask anything about your documents</div>', unsafe_allow_html=True)
        query_input = st.text_area("", placeholder="e.g. How is attention usually designed for in HCI?", height=120, label_visibility="collapsed")
    with col_filters:
        st.markdown('<div class="section-label">Filters</div>', unsafe_allow_html=True)
        source_filter = st.text_input("Source", placeholder="filename.pdf", label_visibility="collapsed")
        doc_type_filter = st.selectbox("Type", options=["","pdf","docx","csv","txt","url"], format_func=lambda x: "All types" if x=="" else x, label_visibility="collapsed")
        skip_eval = st.checkbox("Skip RAGAS eval", value=True)

    if st.button("⬡  Run Query", use_container_width=True, type="primary"):
        if not query_input.strip():
            st.warning("Enter a query first.")
        elif not backend_ok:
            st.error("Backend is offline.")
        else:
            with st.spinner("Retrieving → Reranking → Synthesizing..."):
                try:
                    result = query_backend(query_input, source_filter, doc_type_filter, skip_eval)
                    answer = result.get("answer", "No answer returned.")
                    citations = result.get("citations", [])
                    r_stats = result.get("retrieval_stats", {})
                    s_stats = result.get("synthesis_stats", {})
                    eval_data = result.get("evaluation") or {}

                    st.markdown('<div class="answer-box"><div class="answer-label">⬡ Response</div></div>', unsafe_allow_html=True)
                    st.markdown(f"**{answer}**")

                    st.markdown("<br>", unsafe_allow_html=True)
                    c1, c2, c3, c4 = st.columns(4)
                    with c1:
                        st.markdown(f'<div class="stat-card"><div class="stat-label">Retrieved</div><div class="stat-value">{r_stats.get("total_retrieved",0)}</div><div class="stat-sub">chunks from Qdrant</div></div>', unsafe_allow_html=True)
                    with c2:
                        st.markdown(f'<div class="stat-card"><div class="stat-label">Reranked</div><div class="stat-value">{r_stats.get("total_reranked",0)}</div><div class="stat-sub">cross-encoder pass</div></div>', unsafe_allow_html=True)
                    with c3:
                        latency = round((r_stats.get("duration_seconds") or 0)+(s_stats.get("duration_seconds") or 0),1)
                        st.markdown(f'<div class="stat-card"><div class="stat-label">Latency</div><div class="stat-value" style="font-size:1.4rem">{latency}s</div><div class="stat-sub">{s_stats.get("model_used","")}</div></div>', unsafe_allow_html=True)
                    with c4:
                        if eval_data.get("status")=="success":
                            faith=eval_data.get("faithfulness",0)
                            col="#22c55e" if faith>=0.8 else "#f59e0b" if faith>=0.6 else "#ef4444"
                            st.markdown(f'<div class="stat-card"><div class="stat-label">Faithfulness</div><div class="stat-value" style="color:{col}">{faith:.2f}</div><div class="stat-sub">RAGAS score</div></div>', unsafe_allow_html=True)
                        else:
                            st.markdown('<div class="stat-card"><div class="stat-label">RAGAS Eval</div><div class="stat-value" style="font-size:1rem;color:#334155">—</div><div class="stat-sub">skipped</div></div>', unsafe_allow_html=True)

                    if eval_data.get("status")=="success":
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.markdown('<div class="section-label">RAGAS Evaluation</div>', unsafe_allow_html=True)
                        st.markdown(ragas_bar("Faithfulness",eval_data.get("faithfulness"))+ragas_bar("Answer Relevancy",eval_data.get("answer_relevancy"))+ragas_bar("Context Precision",eval_data.get("context_precision")), unsafe_allow_html=True)

                    if citations:
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.markdown('<div class="section-label">Source Citations</div>', unsafe_allow_html=True)
                        for c in citations:
                            fname = c["source"].split("/")[-1]
                            st.markdown(f'<div class="citation-item"><div class="citation-header"><span>[Context {c["index"]}] {fname} · page {c["page_num"]}</span><span class="citation-score">score {c["score"]}</span></div><div class="citation-preview">{c["text_preview"]}…</div></div>', unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"Request failed: {e}")


with tab_ingest:
    st.markdown('<div class="section-label">Index documents into the knowledge base</div>', unsafe_allow_html=True)
    sub1, sub2 = st.tabs(["Upload Files", "Web URL"])
    with sub1:
        uploaded = st.file_uploader("", type=["pdf","docx","doc","csv","tsv","txt","md"], accept_multiple_files=True, label_visibility="collapsed")
        if st.button("⬡  Ingest Files", use_container_width=True, type="primary"):
            if not uploaded:
                st.warning("Select at least one file.")
            else:
                for file in uploaded:
                    with st.spinner(f"Processing {file.name}..."):
                        try:
                            result = ingest_file(file)
                            if result.get("status")=="indexed":
                                st.markdown(f'<div class="ingest-result"><div class="ingest-filename">✓ {file.name}</div><div class="ingest-meta">{result["total_chunks"]} chunks · {result["chunk_strategy"]} chunking · {result["duration_seconds"]}s</div></div>', unsafe_allow_html=True)
                            else:
                                st.markdown(f'<div class="ingest-result ingest-fail"><div class="ingest-filename">✗ {file.name}</div><div class="ingest-meta">{result.get("error","Unknown error")}</div></div>', unsafe_allow_html=True)
                        except Exception as e:
                            st.error(f"{file.name}: {e}")
    with sub2:
        url_input = st.text_input("", placeholder="https://example.com/report", label_visibility="collapsed")
        if st.button("⬡  Ingest URL", use_container_width=True, type="primary"):
            if not url_input.strip():
                st.warning("Enter a URL.")
            else:
                with st.spinner(f"Fetching {url_input}..."):
                    try:
                        result = ingest_url(url_input)
                        if result.get("status")=="indexed":
                            st.markdown(f'<div class="ingest-result"><div class="ingest-filename">✓ {url_input}</div><div class="ingest-meta">{result["total_chunks"]} chunks · {result["duration_seconds"]}s</div></div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div class="ingest-result ingest-fail"><div class="ingest-filename">✗ Failed</div><div class="ingest-meta">{result.get("error","Unknown error")}</div></div>', unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"Error: {e}")
