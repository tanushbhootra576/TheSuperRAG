"""
app.py -- Streamlit interface for TheSuperRAG (v2).

Updated to use the new DocumentStore + RAGGraph architecture.
Shows: confidence badge, source citations, self-heal logs.
"""
import streamlit as st
from ingest import DocumentStore
from graph import RAGGraph

st.set_page_config(
    page_title="TheSuperRAG",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom Styling ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    .stApp { background-color: #0f172a; color: #f8fafc; font-family: 'Inter', sans-serif; }
    h1, h2, h3 { color: #38bdf8 !important; font-weight: 700 !important; }
    .stChatMessage {
        background-color: #1e293b !important;
        border-radius: 12px; padding: 1rem;
        margin-bottom: 1rem;
        border: 1px solid #334155;
    }
    .stChatInput input {
        border-radius: 20px !important;
        border: 1px solid #38bdf8 !important;
        background-color: #0f172a !important;
        color: white !important;
    }
    .confidence-badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 600;
        margin-top: 8px;
    }
    .source-block {
        background: #0f172a;
        border-left: 3px solid #38bdf8;
        padding: 8px 12px;
        border-radius: 4px;
        margin-top: 8px;
        font-size: 13px;
        color: #94a3b8;
    }
</style>
""", unsafe_allow_html=True)

st.title("🤖 TheSuperRAG v2")
st.markdown("*Self-Healing · Hybrid Search · Re-Ranked · Citations · Confidence Scores*")


# ── System Initialisation ──────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def get_rag_system():
    with st.spinner("Initialising -- loading models and indexing documents... 🧠"):
        doc_store = DocumentStore(folder_path="DATA", collection_name="super_rag")
        return RAGGraph(doc_store=doc_store), doc_store


if "rag_system" not in st.session_state:
    try:
        rag, store = get_rag_system()
        st.session_state.rag_system = rag
        st.session_state.doc_store = store
        st.session_state.initialized = True
    except Exception as e:
        st.error(f"Initialisation failed: {e}")
        st.session_state.initialized = False

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🤖 TheSuperRAG v2")
    st.caption("Self-Healing Engine")

    if st.session_state.get("initialized"):
        store = st.session_state.doc_store
        docs = store.get_indexed_files()

        st.success(f"✅ Active -- {len(docs)} document(s) indexed")
        st.markdown("**📁 Indexed Documents:**")
        for d in docs:
            st.markdown(f"&nbsp;&nbsp;* {d}")

        if not docs:
            st.warning("No PDFs found. Add PDFs to the DATA/ folder.")

    else:
        st.error("System not initialised.")

    st.divider()
    st.markdown("**📊 Session Metrics**")
    heal_count = st.session_state.get("heal_count", 0)
    query_count = st.session_state.get("query_count", 0)
    col1, col2 = st.columns(2)
    col1.metric("Queries", query_count)
    col2.metric("Self-Heals", heal_count)

    hybrid_on = (
        st.session_state.doc_store.hybrid_enabled
        if st.session_state.get("doc_store")
        else False
    )
    st.divider()
    st.markdown(f"**🔍 Search Mode:** {'Hybrid (Dense + BM25)' if hybrid_on else 'Dense Only'}")
    st.markdown("**🔄 Re-ranking:** Cross-Encoder [OK]")


# ── Chat History ───────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Hello! I am **TheSuperRAG v2** -- powered by hybrid search, "
                "cross-encoder re-ranking, and self-healing query rewriting. "
                "I'll cite my sources and show you a confidence score for every answer. Ask away!"
            ),
            "confidence": None,
            "docs": [],
        }
    ]

if "heal_count" not in st.session_state:
    st.session_state.heal_count = 0
if "query_count" not in st.session_state:
    st.session_state.query_count = 0

# Render existing messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

        # Confidence badge
        conf = msg.get("confidence")
        if conf and conf.get("score"):
            score = conf["score"]
            emoji = conf.get("emoji", "⚪")
            label = conf.get("label", "")
            color = {"High": "#10b981", "Medium": "#f59e0b", "Low": "#ef4444"}.get(label, "#6b7280")
            st.markdown(
                f'<span class="confidence-badge" style="background:{color}22;color:{color};border:1px solid {color}44">'
                f'{emoji} {label} Confidence ({score}/10)</span>',
                unsafe_allow_html=True,
            )

        # Source citations
        docs = msg.get("docs", [])
        if docs:
            with st.expander(f"📄 {len(docs)} Source(s) cited"):
                for d in docs:
                    st.markdown(
                        f'<div class="source-block">'
                        f'<strong>{d["file"]}</strong> -- Page {d["page"]}<br/>'
                        f'<em>{d["snippet"]}</em>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )


# ── Chat Input ─────────────────────────────────────────────────────────────────
if prompt := st.chat_input("Ask about your policies, regulations, or documentation..."):
    if not st.session_state.get("initialized"):
        st.error("System not ready. Check the DATA/ folder and restart.")
        st.stop()

    st.session_state.query_count += 1
    history_payload = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages[1:]
    ]

    st.session_state.messages.append({
        "role": "user", "content": prompt, "confidence": None, "docs": []
    })
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_container = st.empty()

        with st.status("Thinking & Validating...", expanded=True) as status:
            app_wf = st.session_state.rag_system.app
            inputs = {
                "chat_history": history_payload,
                "user_query": prompt,
                "current_search_query": prompt,
                "retrieved_context": "",
                "retrieved_docs": [],
                "generation": "",
                "confidence": {},
                "loop_count": 0,
                "logs": [],
                "selected_documents": [],
            }

            final_generation = ""
            final_docs = []
            final_confidence = {}
            current_query = prompt

            for output in app_wf.stream(inputs):
                for key, value in output.items():
                    if key == "smart_router":
                        st.write("🧠 **Contextualising query with conversation history...**")
                    elif key == "retrieve":
                        final_docs = value.get("retrieved_docs", [])
                        final_confidence = value.get("confidence", {})
                        st.write(f"🔍 **Hybrid search + re-ranking for:** `{current_query}`")
                    elif key == "generate":
                        st.write("🤖 **Drafting answer with citations...**")
                        final_generation = value.get("generation", "")
                    elif key == "rewrite_query":
                        current_query = value.get("current_search_query", current_query)
                        st.session_state.heal_count += 1
                        st.write(f"[!]️ **Self-Heal Triggered -> Rewrote query to:** `{current_query}`")

            status.update(label="Analysis complete!", state="complete", expanded=False)

        if "information missing" in final_generation.lower():
            final_generation = (
                "I apologise -- after exhaustive self-healing operations, "
                "no verifiable answer could be found in the available documents."
            )

        response_container.markdown(final_generation)

        # Confidence badge
        if final_confidence.get("score"):
            score = final_confidence["score"]
            emoji = final_confidence.get("emoji", "⚪")
            label = final_confidence.get("label", "")
            color = {"High": "#10b981", "Medium": "#f59e0b", "Low": "#ef4444"}.get(label, "#6b7280")
            st.markdown(
                f'<span class="confidence-badge" style="background:{color}22;color:{color};border:1px solid {color}44">'
                f'{emoji} {label} Confidence ({score}/10)</span>',
                unsafe_allow_html=True,
            )

        # Source citations
        if final_docs:
            with st.expander(f"📄 {len(final_docs)} Source(s) cited"):
                for d in final_docs:
                    st.markdown(
                        f'<div class="source-block">'
                        f'<strong>{d["file"]}</strong> -- Page {d["page"]}<br/>'
                        f'<em>{d["snippet"]}</em>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

        st.session_state.messages.append({
            "role": "assistant",
            "content": final_generation,
            "confidence": final_confidence,
            "docs": final_docs,
        })