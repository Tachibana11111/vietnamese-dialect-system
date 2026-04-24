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
    "Ban la chuyen gia dich thuat phuong ngu Bac Trung Bo Viet Nam.\n"
    "NGUYEN TAC:\n"
    "- Uu tien TU DIEN duoc cung cap hon kien thuc cua ban\n"
    "- Neu cau dau vao la PHUONG NGU -> dich sang pho thong\n"
    "- Neu cau dau vao la PHO THONG -> dich sang phuong ngu vung {province}\n\n"
    "TU DIEN:\n{words_context}\n\n"
    "CAU MAU:\n{pairs_context}\n\n"
    "CAU CAN DICH: {query}\n\n"
    '{"translation": "ban dich", "dialect_words": ["tu: nghia (tinh)"], "province_hint": "tinh", "confidence": 0.0}'
)

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
    try:
        raw = re.sub(r"```json|```", "", raw).strip()
        result = json.loads(raw)
        result["retrieved_words"] = ctx["words"]
        result["retrieved_pairs"] = ctx["pairs"]
        return result
    except:
        return {"translation": raw, "error": "parse JSON that bai"}

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