import json
import os
import re
from typing import List, Dict, Any

import streamlit as st
from dotenv import load_dotenv
from groq import Groq

from utils import _get_embeddings, _get_milvus_client


load_dotenv()

st.set_page_config(
    page_title="Chat",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Sidebar: branding + document attachments
with st.sidebar:
    try:
        st.logo("assets/minijust.png", icon_image="assets/minijust.png", size="large")
    except Exception:
        st.title("MINIJUST")

    footer = """
    <style>
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: transparent;
        color: gray;
        text-align: center;
        padding: 10px;
        font-size: 12px;
    }
    </style>
    <div class="footer">
        <p>© 2026 MINIJUST AI | A Year of Remarkable Change</p>
    </div>
    """
    st.markdown(footer, unsafe_allow_html=True)


# Session state for chat
if "chat_history" not in st.session_state:
    st.session_state.chat_history: List[Dict[str, Any]] = []
if "selected_docs" not in st.session_state:
    st.session_state.selected_docs: List[str] = []


def get_available_documents(data_folder: str = "data") -> List[str]:
    if not os.path.exists(data_folder):
        os.makedirs(data_folder)
    return sorted([f for f in os.listdir(data_folder) if os.path.isfile(os.path.join(data_folder, f))])


def build_filter_expression(selected_docs: List[str]) -> str:
    if not selected_docs:
        return ""
    quoted = [f'"{d}"' for d in selected_docs]
    return f"source_file in [{', '.join(quoted)}]"


def _extract_article_numbers(question: str) -> List[str]:
    """
    Best-effort extraction of article numbers from the question.
    Supports patterns like:
    - Article 14
    - article 14
    - Ingingo ya 14
    """
    nums = set()
    # English / French style: “Article 14”
    for m in re.findall(r"[Aa]rticle\s+(\d+)", question):
        nums.add(m)
    # Kinyarwanda style: “Ingingo ya 14”
    for m in re.findall(r"[Ii]ngingo\s+ya\s+(\d+)", question):
        nums.add(m)
    return sorted(nums)


def search_context(question: str, selected_docs: List[str], top_k: int = 5) -> List[Dict[str, Any]]:
    embeddings = _get_embeddings()
    query_vec = embeddings.embed_query(question)

    client = _get_milvus_client()
    collection_name = "legal_docs"
    if not client.has_collection(collection_name):
        raise RuntimeError("No Milvus collection found. Please ingest documents on the Upload page.")

    filter_expr = build_filter_expression(selected_docs)

    # 1) Semantic search for general relevant context
    results = client.search(
        collection_name=collection_name,
        data=[query_vec],
        limit=top_k,
        output_fields=["text", "source_file", "page", "unit_header", "metadata_json"],
        filter=filter_expr or None,
        search_params={"metric_type": "COSINE", "params": {"nprobe": 10}},
    )

    hits = results[0] if results else []
    contexts: List[Dict[str, Any]] = []
    for hit in hits:
        meta_raw = hit.get("metadata_json") or "{}"
        try:
            meta = json.loads(meta_raw)
        except Exception:
            meta = {}
        contexts.append(
            {
                "text": hit.get("text", ""),
                "source_file": hit.get("source_file", "unknown"),
                "page": hit.get("page", None),
                "unit_header": hit.get("unit_header", ""),
                "metadata": meta,
                "score": hit.get("score", hit.get("distance")),
            }
        )

    # 2) If the question clearly refers to a specific article number,
    #    pull *all* chunks for that article (per document) so the lawyer
    #    can see the full text, not just partial snippets.
    article_numbers = _extract_article_numbers(question)
    if article_numbers:
        try:
            for art_num in article_numbers:
                def _run_article_query(filter_clause: str) -> List[Dict[str, Any]]:
                    rows_local = client.query(
                        collection_name=collection_name,
                        filter=filter_clause,
                        output_fields=["text", "source_file", "page", "unit_header", "metadata_json", "article_number"],
                        limit=200,
                    )
                    return rows_local or []

                # Prefer precise article_number field, which we populate at ingestion time.
                expr_parts = []
                if filter_expr:
                    expr_parts.append(f"({filter_expr})")
                expr_parts.append(f'article_number == "{art_num}"')
                expr = " and ".join(expr_parts) if len(expr_parts) > 1 else expr_parts[0]
                rows = _run_article_query(expr)

                # Backward-compatible fallback for already-indexed docs (before article_number existed)
                if not rows:
                    expr_parts_fallback = []
                    if filter_expr:
                        expr_parts_fallback.append(f"({filter_expr})")
                    expr_parts_fallback.append(
                        f'(unit_header == "Article {art_num}" or unit_header == "Ingingo ya {art_num}" or unit_header == "ARTICLE {art_num}")'
                    )
                    expr_fb = (
                        " and ".join(expr_parts_fallback)
                        if len(expr_parts_fallback) > 1
                        else expr_parts_fallback[0]
                    )
                    rows = _run_article_query(expr_fb)

                if not rows:
                    continue

                # Group by (source_file, unit_header) and concatenate all chunks
                grouped: Dict[str, List[Dict[str, Any]]] = {}
                for r in rows:
                    key = f"{r.get('source_file','unknown')}|{r.get('unit_header','')}"
                    grouped.setdefault(key, []).append(r)

                for key, chunks in grouped.items():
                    chunks_sorted = sorted(chunks, key=lambda x: x.get("page", 0) or 0)
                    full_text = "\n\n".join(c.get("text", "") for c in chunks_sorted if c.get("text"))
                    first = chunks_sorted[0]
                    meta_raw = first.get("metadata_json") or "{}"
                    try:
                        meta = json.loads(meta_raw)
                    except Exception:
                        meta = {}

                    # Avoid duplicating if the same (file, header) is already in contexts
                    if any(
                        c.get("source_file") == first.get("source_file")
                        and c.get("unit_header") == first.get("unit_header")
                        for c in contexts
                    ):
                        continue

                    contexts.insert(
                        0,
                        {
                            "text": full_text,
                            "source_file": first.get("source_file", "unknown"),
                            "page": first.get("page", None),
                            "unit_header": first.get("unit_header", ""),
                            "metadata": meta,
                            "score": 1.0,  # highest priority
                        },
                    )
        except Exception:
            # If article-aware fallback fails for any reason, we still
            # return the normal semantic contexts so the chat keeps working.
            pass

    return contexts


def generate_answer(question: str, contexts: List[Dict[str, Any]]) -> str:
    context_blocks = []
    for idx, ctx in enumerate(contexts, start=1):
        page_info = f"(page {ctx['page']})" if ctx.get("page") else ""
        header = ctx.get("unit_header", "") or ""
        header_line = f" — {header}" if header else ""
        context_blocks.append(f"[{idx}] {ctx['source_file']}{header_line} {page_info}\n{ctx['text']}")
    context_str = "\n\n".join(context_blocks) if context_blocks else "No supporting passages found."

    system_prompt = (
        "You are MINIJUST's legal research assistant. Provide concise, factual answers "
        "grounded in the retrieved context. Cite the supporting snippet numbers when relevant. "
        "If the context is missing, say you cannot find that information."
    )

    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    completion = client.chat.completions.create(
        model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        temperature=0.2,
        max_tokens=512,
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"Question: {question}\n\nContext:\n{context_str}",
            },
        ],
    )
    return completion.choices[0].message.content.strip()


st.title("Chat with Indexed Documents")
st.caption("Attach one or more indexed documents, ask a question, and search around them.")

available_docs = get_available_documents()
if not available_docs:
    st.warning("No documents found. Please upload and index files on the Upload page.")
else:
    st.info(
        "Tip: If a document was indexed before we added article-level metadata, re-upload it once on the Upload page "
        "to enable reliable full-article retrieval (e.g., 'Article 14')."
    )

# Show prior messages
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        sources = message.get("sources") or []
        if sources:
            with st.expander("Sources"):
                for s in sources:
                    page_info = f" (page {s['page']})" if s.get("page") else ""
                    header = s.get("unit_header") or ""
                    header_info = f" — {header}" if header else ""
                    full_text = s.get("text", "")
                    snippet_len = 400
                    snippet = full_text[:snippet_len]
                    st.markdown(
                        f"- `{s['source_file']}`{header_info}{page_info}: "
                        f"{snippet}{'…' if len(full_text) > len(snippet) else ''}"
                    )
                    if header and len(full_text) > snippet_len:
                        with st.expander(f"View full text for {header}"):
                            st.write(full_text)

# Chat input area
with st.form("chat_form", clear_on_submit=True):
    st.subheader("Attach documents to search")
    selected = st.multiselect(
        "Indexed documents",
        options=available_docs,
        default=st.session_state.selected_docs,
        help="Only chunks from these files will be searched. Leave empty to search all indexed content.",
    )
    question = st.text_area("Your question", placeholder="Ask about a specific article or case...", height=120)
    top_k = st.slider("Results to retrieve", min_value=3, max_value=10, value=5, step=1)
    submitted = st.form_submit_button("Ask")

if submitted and question:
    st.session_state.selected_docs = selected
    with st.spinner("Retrieving context and querying Groq..."):
        try:
            contexts = search_context(question, selected, top_k=top_k)
            answer = generate_answer(question, contexts)
            st.session_state.chat_history.append({"role": "user", "content": question})
            st.session_state.chat_history.append({"role": "assistant", "content": answer, "sources": contexts})
            st.rerun()
        except Exception as e:
            st.error(f"Could not complete the request: {str(e)}")
