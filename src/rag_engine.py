import json, re, os
import chromadb
from sentence_transformers import SentenceTransformer

CHROMA_PATH = "/content/vietnamese-dialect-system/data/chromadb"

_chroma_client = None
_words_col     = None
_pairs_col     = None
_embedder      = None

def init_rag():
    global _chroma_client, _words_col, _pairs_col, _embedder
    _chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    _words_col     = _chroma_client.get_collection("dialect_words")
    _pairs_col     = _chroma_client.get_collection("dialect_pairs")
    _embedder      = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    print(f"RAG ready: {_words_col.count()} words, {_pairs_col.count()} pairs")

RAG_PROMPT_V2 = (
    "Bạn là chuyên gia dịch thuật phương ngữ Bắc Trung Bộ Việt Nam.\n"
    "NGUYÊN TẮc QUAN TRỌNG:\n"
    "- Phải ưu tiên TỪ ĐIỂN được cung cấp hơn kiến thức của bạn\n"
    "- Nếu từ điển nói chảu = xinh/đẹp thì PHẢI dịch theo từ điển\n"
    "- Nếu câu đầu vào là PHƯƠNG NGỮ → dịch sang phổ thông\n"
    "- Nếu câu đầu vào là PHỔ THÔNG → dịch sang phương ngữ vùng {province}\n\n"
    "TỪ ĐIỂN BẮt BUỘC DÙNG:\n{words_context}\n\n"
    "CÂU MẪu THAM KHẢO:\n{pairs_context}\n\n"
    "VÍ DỤ CÁCH DỊCH ĐÚNG:\n"
    "- con tru ăn cỏ → translation: con trâu ăn cỏ, dialect_words: [tru: trâu (Nghệ An)]\n"
    "- chảu xinh hè → translation: đẹp quá nhỉ, dialect_words: [chảu: đẹp/xinh (Quảng Trị)]\n\n"
    "CÂU CẦN DỊCH: \"{query}\"\n\n"
    'Trả lời ĐÚNG format JSON sau, KHÔNG giải thích thêm:\n'
    '{"translation": "bản dịch", "dialect_words": ["từ: nghĩa (tỉnh)"], "province_hint": "tỉnh", "confidence": 0.0}'
)

def retrieve_context(query, k_words=7, k_pairs=4):
    query_emb = _embedder.encode([query]).tolist()
    word_res  = _words_col.query(query_embeddings=query_emb, n_results=k_words)
    pair_res  = _pairs_col.query(query_embeddings=query_emb, n_results=k_pairs)
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
    words_str = ""
    for w in context["words"]:
        words_str += f"- '{w[chr(39)+chr(119)+chr(111)+chr(114)+chr(100)+chr(39)]}' = '{w[chr(39)+chr(115)+chr(116)+chr(97)+chr(110)+chr(100)+chr(97)+chr(114)+chr(100)+chr(95)+chr(102)+chr(111)+chr(114)+chr(109)+chr(39)]}' (tỉnh: {w[chr(39)+chr(112)+chr(114)+chr(111)+chr(118)+chr(105)+chr(110)+chr(99)+chr(101)+chr(39)]}, score: {w[chr(39)+chr(115)+chr(99)+chr(111)+chr(114)+chr(101)+chr(39)]})\n"
    pairs_str = ""
    for p in context["pairs"]:
        pairs_str += f"- '{p[chr(39)+chr(100)+chr(105)+chr(97)+chr(108)+chr(101)+chr(99)+chr(116)+chr(39)]}' → '{p[chr(39)+chr(115)+chr(116)+chr(97)+chr(110)+chr(100)+chr(97)+chr(114)+chr(100)+chr(39)]}' ({p[chr(39)+chr(112)+chr(114)+chr(111)+chr(118)+chr(105)+chr(110)+chr(99)+chr(101)+chr(39)]})\n"
    return words_str.strip(), pairs_str.strip()

def translate(query: str, province: str = "Nghệ An") -> dict:
    from pipeline_v2 import call_llm
    context = retrieve_context(query)
    words_str, pairs_str = _format_context(context)
    prompt = RAG_PROMPT_V2.format(
        province=province,
        words_context=words_str or "Không tìm thấy",
        pairs_context=pairs_str or "Không tìm thấy",
        query=query
    )
    raw = call_llm(prompt)
    if not raw:
        return {"error": "LLM không phản hồi"}
    try:
        import re
        raw    = re.sub(r"```json|```", "", raw).strip()
        result = json.loads(raw)
        result["retrieved_words"] = context["words"]
        result["retrieved_pairs"] = context["pairs"]
        return result
    except:
        return {"translation": raw, "error": "parse JSON thất bại"}

def lookup(word: str) -> dict:
    query_emb = _embedder.encode([word]).tolist()
    res = _words_col.query(query_embeddings=query_emb, n_results=5)
    results = []
    for meta, dist in zip(res["metadatas"][0], res["distances"][0]):
        results.append({
            "word":          meta["word"],
            "standard_form": meta["standard_form"],
            "province":      meta["province"],
            "score":         round(1 - dist, 3)
        })
    return {"query": word, "results": results}