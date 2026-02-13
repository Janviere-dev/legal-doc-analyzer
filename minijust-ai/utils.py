import json
import os
import re
import uuid
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

try:
    import fitz as pymupdf  # Common import name for PyMuPDF
except ModuleNotFoundError:
    try:
        import pymupdf  # Fallback module name
    except ModuleNotFoundError as e:
        raise ModuleNotFoundError(
            "PyMuPDF is required for PDF ingestion. Install it with: pip install PyMuPDF"
        ) from e

from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pymilvus import MilvusClient



load_dotenv()

# NOTE: This is an example schema (not used directly by code). Keep it here as a reference
# for what “rich metadata” means for legal traceability.
legal_schema = {
    "document_identity": "RP/GEN 00003/2019",
    "doc_type": "Case Law",  # Essential for filtering
    "legal_category": "Criminal Law",
    "primary_article": "Article 91",  # The 'Hero' article of this chunk
    "other_citations": ["Art 335", "Law 062/2024"],
    "court_level": "High Court",
    "language": "English",
    "issued_date": 20241226,  # Store as Integer for faster sorting
    "gazette_ref": "Special Bis",
    "gazette_date": 20231031,
    "page_number": 12,  # Vital for PDFs
}


SUPPORTED_LANGS = ("rw", "en", "fr")
DOC_TYPES = ("Legislation", "Case Law", "Other")


@dataclass(frozen=True)
class ColumnText:
    column_index: int
    bbox: Tuple[float, float, float, float]  # (x0, y0, x1, y1)
    text: str


def _new_int64_id() -> int:
    """
    Milvus default primary key type (for `create_collection(dimension=...)`) is INT64.
    Generate a positive int64 id to match that schema.
    """
    return uuid.uuid4().int % (2**63 - 1)


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"[ \t]+", " ", re.sub(r"\n{3,}", "\n\n", text)).strip()


def _guess_language(text: str) -> str:
    """
    Lightweight language guesser for Amategeko’s common languages (rw/en/fr).
    This is intentionally simple (no extra deps) and works well enough for
    column-level language tagging in tri-lingual gazettes.
    """
    t = " " + re.sub(r"[^A-Za-zÀ-ÿ’'\s]", " ", text.lower()) + " "
    if len(t.strip()) < 40:
        return "en"

    # High-signal Kinyarwanda function words
    rw_hits = sum(t.count(w) for w in [" na ", " mu ", " ku ", " kandi ", " cyangwa ", " ingingo ", " itegeko "])
    fr_hits = sum(t.count(w) for w in [" le ", " la ", " les ", " des ", " du ", " de ", " et ", " article "])
    en_hits = sum(t.count(w) for w in [" the ", " and ", " of ", " to ", " in ", " article "])

    scores = {"rw": rw_hits, "fr": fr_hits, "en": en_hits}
    return max(scores, key=scores.get)  # type: ignore[arg-type]


def detect_columns(page: pymupdf.Page, max_columns: int = 3) -> List[pymupdf.Rect]:
    """
    Detect likely columns using x-gaps between text blocks.

    Returns a list of column rectangles spanning full page height, left-to-right.
    Falls back to 1 column when no clear gaps are detected.
    """
    layout = page.get_text("dict")
    page_w = float(layout.get("width", page.rect.width))
    page_h = float(layout.get("height", page.rect.height))

    blocks = layout.get("blocks", [])
    x_ranges: List[Tuple[float, float]] = []
    for b in blocks:
        bbox = b.get("bbox")
        if not bbox or b.get("type") != 0:
            continue
        x0, y0, x1, y1 = map(float, bbox)
        # Ignore tiny artifacts
        if (x1 - x0) < page_w * 0.05 or (y1 - y0) < page_h * 0.02:
            continue
        x_ranges.append((x0, x1))

    if len(x_ranges) < 8:
        return [pymupdf.Rect(0, 0, page_w, page_h)]

    # Build a set of candidate vertical "gaps" from sorted x0 values.
    x0s = sorted(x0 for x0, _ in x_ranges)
    gaps: List[Tuple[float, float]] = []
    for a, b in zip(x0s, x0s[1:]):
        if (b - a) > page_w * 0.12:
            gaps.append((a, b))

    if not gaps:
        return [pymupdf.Rect(0, 0, page_w, page_h)]

    # Use midpoints of largest gaps as split points.
    gaps.sort(key=lambda g: g[1] - g[0], reverse=True)
    split_points = sorted([(g[0] + g[1]) / 2.0 for g in gaps[: max_columns - 1]])
    # Add boundaries
    boundaries = [0.0] + split_points + [page_w]
    rects = [pymupdf.Rect(boundaries[i], 0, boundaries[i + 1], page_h) for i in range(len(boundaries) - 1)]

    # Drop very narrow columns (noise)
    rects = [r for r in rects if r.width > page_w * 0.18]
    return rects or [pymupdf.Rect(0, 0, page_w, page_h)]


def detect_columns_and_reconstruct(page):
    """
    Backward-compatible helper: extracts 1–3 columns of text, left-to-right.
    Returns a dict keyed by language codes when we can infer them (rw/en/fr),
    otherwise returns content in generic left-to-right order.
    """
    rects = detect_columns(page, max_columns=3)
    cols: List[ColumnText] = []
    for idx, rect in enumerate(rects):
        column_text = _normalize_whitespace(page.get_text("text", clip=rect))
        cols.append(ColumnText(column_index=idx, bbox=(rect.x0, rect.y0, rect.x1, rect.y1), text=column_text))

    # Infer language per column and return keyed result (best-effort).
    inferred: Dict[str, str] = {}
    used = set()
    for c in cols:
        lang = _guess_language(c.text)
        if lang in used:
            # If language duplicates, keep deterministic unique keys by falling back to order.
            lang = f"{lang}_{c.column_index}"
        used.add(lang)
        inferred[lang] = c.text

    # If we got exactly rw/en/fr at least once, normalize to those keys.
    normalized: Dict[str, str] = {"rw": "", "en": "", "fr": ""}
    for key, val in inferred.items():
        if key in normalized:
            normalized[key] = val
    if any(normalized.values()):
        return normalized

    # Otherwise return left-to-right buckets.
    return {f"col_{c.column_index}": c.text for c in cols}

def split_into_articles(text, language="en"):
    """
    Split a legal text into articles while keeping the article headers.
    Case-insensitive to handle PDF noise (ARTICLE, Article, article).
    """
    patterns = {
        "en": r"(Article\s+\d+)",
        "rw": r"(Ingingo\s+ya\s+\d+)",
        "fr": r"(Article\s+premier|Article\s+\d+)",
    }

    regex = patterns.get(language, patterns["en"])

    # Split text but keep the "Article X" headers (case-insensitive)
    parts = re.split(regex, text, flags=re.IGNORECASE)
    articles = []

    for i in range(1, len(parts), 2):
        header = parts[i]
        body = parts[i + 1] if i + 1 < len(parts) else ""
        articles.append({"header": header.strip(), "content": body.strip()})

    return articles


def _split_legal_units(text: str, doc_type: str, language: str) -> List[Dict[str, str]]:
    """
    Returns a list of logical “units” before chunking.
    For Legislation, we split into articles (when detectable).
    For Case Law/Other, we treat the whole text as one unit (chunker will handle).
    """
    cleaned = _normalize_whitespace(text)
    if not cleaned:
        return []

    if doc_type == "Legislation" and language in SUPPORTED_LANGS:
        articles = split_into_articles(cleaned, language=language)
        if articles:
            enriched: List[Dict[str, str]] = []
            for a in articles:
                header = a.get("header", "")
                content = a.get("content", "")
                if not content:
                    continue
                # Extract article number, e.g. from:
                # - Article 14
                # - ARTICLE 14
                # - Ingingo ya 14
                m = re.search(r"(?:[Aa]rticle\\s+|[Ii]ngingo\\s+ya\\s+)(\\d+)", header)
                article_number = m.group(1) if m else ""
                enriched.append(
                    {
                        "header": header,
                        "content": content,
                        "article_number": article_number,
                    }
                )
            if enriched:
                return enriched

    return [{"header": "", "content": cleaned, "article_number": ""}]


def _get_embeddings() -> HuggingFaceEmbeddings:
    model_name = os.getenv(
        "EMBEDDING_MODEL",
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    )
    return HuggingFaceEmbeddings(model_name=model_name)


def _get_milvus_client() -> MilvusClient:
    # Milvus Lite expects a local file ending with `.db`, or a server URI
    # such as http(s)://..., tcp://..., unix://...
    uri = os.getenv("MILVUS_URI", "./milvus_data.db")
    token = os.getenv("MILVUS_TOKEN")
    if token:
        return MilvusClient(uri=uri, token=token)
    return MilvusClient(uri=uri)


def _ensure_collection(client: MilvusClient, collection_name: str, dim: int) -> None:
    if client.has_collection(collection_name):
        return

    # Use a simple collection with dynamic fields.
    # Milvus will store all extra fields (text, doc_type, language, etc.) as dynamic fields.
    client.create_collection(
        collection_name=collection_name,
        dimension=dim,
        metric_type="COSINE",
        primary_field_name="id",
        vector_field_name="embedding",
        enable_dynamic_field=True,
    )


def process_and_store_document(
    file_path: str,
    source_file_name: str,
    *,
    doc_type: str = "Legislation",
    extra_metadata: Optional[Dict[str, str]] = None,
    collection_name: str = "legal_docs",
    chunk_size: int = 1200,
    chunk_overlap: int = 180,
) -> int:
    """
    Ingestion pipeline (one-time per PDF):
    - Parse PDF → words/blocks with coordinates per page (via PyMuPDF)
    - Detect columns
    - Reconstruct reading order per column
    - Detect language per column
    - Split into legal units (articles for legislation when possible)
    - Chunk
    - Embed
    - Store in Milvus with rich metadata
    """
    if doc_type not in DOC_TYPES:
        doc_type = "Other"

    extra_metadata = extra_metadata or {}
    embeddings = _get_embeddings()
    client = _get_milvus_client()

    # Infer embedding dimension once.
    test_vec = embeddings.embed_query("dimension probe")
    _ensure_collection(client, collection_name, dim=len(test_vec))

    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    doc = pymupdf.open(file_path)
    rows = []

    for page_idx in range(doc.page_count):
        page = doc.load_page(page_idx)
        rects = detect_columns(page, max_columns=3)

        for col_idx, rect in enumerate(rects):
            col_text = _normalize_whitespace(page.get_text("text", clip=rect))
            if not col_text:
                continue

            lang = _guess_language(col_text)
            units = _split_legal_units(col_text, doc_type=doc_type, language=lang if lang in SUPPORTED_LANGS else "en")

            for unit in units:
                unit_header = unit.get("header", "")[:256]
                article_number = unit.get("article_number", "")
                unit_text = unit.get("content", "")
                if not unit_text:
                    continue

                chunks = splitter.split_text(unit_text)
                for chunk in chunks:
                    chunk = chunk.strip()
                    if not chunk:
                        continue

                    meta = {
                        "source": "amategeko.gov.rw",
                        "source_file": source_file_name,
                        "doc_type": doc_type,
                        "language": lang,
                        "page": page_idx + 1,
                        "column": col_idx,
                        "column_bbox": [rect.x0, rect.y0, rect.x1, rect.y1],
                        "unit_header": unit_header,
                        "article_number": article_number,
                        **extra_metadata,
                    }

                    rows.append(
                        {
                            "id": _new_int64_id(),
                            "embedding": embeddings.embed_query(chunk),
                            "text": chunk,
                            "source_file": source_file_name,
                            "doc_type": doc_type,
                            "language": lang,
                            "page": page_idx + 1,
                            "column": col_idx,
                            "unit_header": unit_header,
                            "article_number": article_number,
                            "metadata_json": json.dumps(meta, ensure_ascii=False),
                        }
                    )

    if rows:
        client.insert(collection_name=collection_name, data=rows)

    return len(rows)


def delete_document_from_store(source_file_name: str, *, collection_name: str = "legal_docs") -> None:
    client = _get_milvus_client()
    if not client.has_collection(collection_name):
        return
    expr = f'source_file == "{source_file_name}"'
    client.delete(collection_name=collection_name, filter=expr)































































































































































































































































