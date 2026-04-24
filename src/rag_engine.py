import json, re, os
import chromadb
from sentence_transformers import SentenceTransformer

CHROMA_PATH = "/content/vietnamese-dialect-system/data/chromadb"

_words_col = None
_pairs_col = None
_embedder  = None

def init_rag():
    global _words_col, _pairs_col, _embedder
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    _words_col = client.get_collection("dialect_words")
    _pairs_col = client.get_collection("dialect_pairs")
    _embedder  = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    print(f"RAG ready: {_words_col.count()} words, {_pairs_col.count()} pairs")

def retrieve_context(query, k_words=7, k_pairs=4):
    emb      = _embedder.encode([query]).tolist()
    word_res = _words_col.query(query_embeddings=emb, n_results=k_words)
    pair_res = _pairs_col.query(query_embeddings=emb, n_results=k_pairs)
    words_ctx = []
    for m, d in zip(word_res["metadatas"][0], word_res["distances"][0]):
        words_ctx.append({
            "word":          m["word"],
            "standard_form": m["standard_form"],
            "province":      m["province"],
            "score":         round(1 - d, 3)
        })
    pairs_ctx = []
    for m, d in zip(pair_res["metadatas"][0], pair_res["distances"][0]):
        pairs_ctx.append({
            "dialect":  m["dialect_sentence"],
            "standard": m["standard_sentence"],
            "province": m["province"],
            "score":    round(1 - d, 3)
        })
    return {"words": words_ctx, "pairs": pairs_ctx}

def _format_context(context):
    w_lines = []
    for w in context["words"]:
        w_lines.append(
            "- " + w["word"] + " = " + w["standard_form"]
            + " (tinh: " + w["province"] + ", score: " + str(w["score"]) + ")"
        )
    p_lines = []
    for p in context["pairs"]:
        p_lines.append(
            "- " + p["dialect"] + " -> " + p["standard"]
            + " (" + p["province"] + ")"
        )
    return "\n".join(w_lines), "\n".join(p_lines)

RAG_PROMPT = (
    "You are a dialect translation expert for North Central Vietnam.\n"
    "STRICT RULES:\n"
    "1. You MUST return ONLY a JSON object, no explanation, no extra text\n"
    "2. Use the dictionary below as primary source\n"
    "3. If input is dialect -> translate to standard Vietnamese\n"
    "4. If input is standard Vietnamese -> translate to dialect of {province}\n\n"
    "DICTIONARY:\n{words_context}\n\n"
    "EXAMPLE SENTENCES:\n{pairs_context}\n\n"
    "INPUT: {query}\n\n"
    "Return ONLY this JSON, nothing else:\n"
    '{{"translation":"...","dialect_words":["word:meaning(province)"],"province_hint":"...","confidence":0.0}}'
)

def extract_json(text):
    try:
        clean = re.sub(r"```json|```", "", text).strip()
        return json.loads(clean)
    except:
        pass
    match = re.search(r'\{[^{}]*"translation"[^{}]*}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except:
            pass
    result = {}
    t = re.search(r'"translation"\s*:\s*"([^"]+)"', text)
    p = re.search(r'"province_hint"\s*:\s*"([^"]+)"', text)
    c = re.search(r'"confidence"\s*:\s*([0-9.]+)', text)
    if t: result["translation"]    = t.group(1)
    if p: result["province_hint"]  = p.group(1)
    if c: result["confidence"]     = float(c.group(1))
    result["dialect_words"] = []
    return result if result else {"translation": text, "error": "extract failed"}

def translate(query, province="Nghe An"):
    from pipeline_v2 import call_llm
    ctx = retrieve_context(query)
    w_str, p_str = _format_context(ctx)
    prompt = RAG_PROMPT.format(
        province=province,
        words_context=w_str or "Khong tim thay",
        pairs_context=p_str or "Khong tim thay",
        query=query
    )
    raw = call_llm(prompt)
    if not raw:
        return {"error": "LLM khong phan hoi"}
    result = extract_json(raw)
    result["retrieved_words"] = ctx["words"]
    result["retrieved_pairs"] = ctx["pairs"]
    return result

def lookup(word):
    emb = _embedder.encode([word]).tolist()
    res = _words_col.query(query_embeddings=emb, n_results=5)
    results = []
    for m, d in zip(res["metadatas"][0], res["distances"][0]):
        results.append({
            "word":          m["word"],
            "standard_form": m["standard_form"],
            "province":      m["province"],
            "score":         round(1 - d, 3)
        })
    return {"query": word, "results": results}