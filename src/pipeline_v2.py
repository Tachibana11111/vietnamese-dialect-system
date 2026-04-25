import requests, json, time, re, os
from bs4 import BeautifulSoup
import trafilatura
from google import genai

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
client = genai.Client(api_key=GEMINI_API_KEY)
OUTPUT_PATH = "/content/vietnamese-dialect-system/data/processed/dialect_words.json"
HEADERS = {"User-Agent": "Mozilla/5.0 (research-bot; dialect-preservation-project)"}

SOURCES = {
    "nghengu_tudien": {
        "urls": [
            "https://nghengu.vn/tu-dien-tieng-nghe/",
            "https://nghengu.vn/tieng-nghe-cua-toi/tu-dien-tieng-nghe-tinh-961.html",
            "https://nghengu.vn/tieng-nghe-cua-toi/top-100-tu-tieng-nghe-an-ha-tinh-hay-nhat-728.html",
        ],
        "province_hint": "Nghệ An",
        "region_group": "Nghệ Tĩnh",
        "verified_by": "cong_dong_online",
        "confidence": 0.7,
    },
    "xomaonguyen_blog": {
        "urls": ["http://xomaonguyen.blogspot.com/2014/09/tu-ien-tieng-nghe-tinh-tu-en-zvan-van.html"],
        "province_hint": "Nghệ An",
        "region_group": "Nghệ Tĩnh",
        "verified_by": "cong_dong_online",
        "confidence": 0.65,
    },
    "baonghean": {
        "urls": ["https://baonghean.vn/van-hoa", "https://baonghean.vn/xa-hoi"],
        "province_hint": "Nghệ An",
        "region_group": "Nghệ Tĩnh",
        "verified_by": "cong_dong_online",
        "confidence": 0.7,
    },
    "baohatinh": {
        "urls": ["https://baohatinh.vn/van-hoa-giai-tri/"],
        "province_hint": "Hà Tĩnh",
        "region_group": "Nghệ Tĩnh",
        "verified_by": "cong_dong_online",
        "confidence": 0.7,
    },
    "baothuathienhue": {
        "urls": ["https://baothuathienhue.vn/van-hoa-nghe-thuat"],
        "province_hint": "Thừa Thiên Huế",
        "region_group": "Bình Trị Thiên",
        "verified_by": "cong_dong_online",
        "confidence": 0.7,
    },
    "nguyentienhai_hue": {
        "urls": [
            "https://nguyentienhai.blogspot.com/2011/01/tieu-tu-ien-phuong-ngu-hue.html",
        ],
        "province_hint": "Th\u1eeba Thi\u00ean Hu\u1ebf",
        "region_group": "B\u00ecnh Tr\u1ecb Thi\u00ean",
        "verified_by": "cong_dong_online",
        "confidence": 0.75,
    },
    "nguyentienhai_quangbinh": {
        "urls": [
            "https://nguyentienhai.blogspot.com/2011/01/tieu-tu-dien-phuong-ngu-quang-binh.html",
        ],
        "province_hint": "Qu\u1ea3ng B\u00ecnh",
        "region_group": "B\u00ecnh Tr\u1ecb Thi\u00ean",
        "verified_by": "cong_dong_online",
        "confidence": 0.75,
    },
    "vannghequangtri": {
        "urls": [
            "https://vannghequangtri.blogspot.com/2024/09/tu-ien-phuong-ngu-quang-tri-vo-cong.html",
            "https://nghengu.vn/chuyen-nguoi-nghe-ke/tieng-quang-tri-2027.html",
        ],
        "province_hint": "Qu\u1ea3ng Tr\u1ecb",
        "region_group": "B\u00ecnh Tr\u1ecb Thi\u00ean",
        "verified_by": "cong_dong_online",
        "confidence": 0.75,
    },
    "spiderum_hue": {
        "urls": [
            "https://spiderum.com/bai-dang/Huong-dan-tu-hoc-tieng-Nghe-Tinh-tu-A-Zor-Nhap-mon-phuong-ngu-mien-Trung-love-kn2",
        ],
        "province_hint": "Th\u1eeba Thi\u00ean Hu\u1ebf",
        "region_group": "B\u00ecnh Tr\u1ecb Thi\u00ean",
        "verified_by": "cong_dong_online",
        "confidence": 0.7,
    },
    "nghengu_hatinh": {
        "urls": [
            "https://nghengu.vn/tieng-nghe-cua-toi/tu-dien-tieng-ha-tinh-995.html",
            "http://humansofhatinh.blogspot.com/2016/01/phuong-ngu-ky-anh-tu-ien-tieng-nghe-tinh.html",
        ],
        "province_hint": "H\u00e0 T\u0129nh",
        "region_group": "Ngh\u1ec7 T\u0129nh",
        "verified_by": "cong_dong_online",
        "confidence": 0.7,
    },
    "wikipedia_thanhhoa": {
        "urls": [
            "https://vi.wikipedia.org/wiki/Ph%C6%B0%C6%A1ng_ng%E1%BB%AF_Thanh_H%C3%B3a",
            "https://spiderum.com/bai-dang/MI-DI-MO-MA-VIEN-THANH-HOA-17EIvue9Wauh",
            "http://tuancongthuphong.blogspot.com/2013/10/tho-am-tho-ngu-thanh-hoa.html",
        ],
        "province_hint": "Thanh H\u00f3a",
        "region_group": "Thanh H\u00f3a",
        "verified_by": "cong_dong_online",
        "confidence": 0.7,
    },
    "quangbinh_fix": {
        "urls": [
            "http://alomartnew.blogspot.com/2013/12/tim-hieu-ve-tieng-ia-phuong-ha-tinh.html",
        ],
        "province_hint": "Qu\u1ea3ng B\u00ecnh",
        "region_group": "B\u00ecnh Tr\u1ecb Thi\u00ean",
        "verified_by": "cong_dong_online",
        "confidence": 0.7,
    },
}

EXTRACT_PROMPT_V2 = (
    "Bạn là chuyên gia ngôn ngữ học phương ngữ Việt Nam Bắc Trung Bộ.\n\n"
    "Từ đoạn văn bản dưới đây, hãy trích xuất các từ phương ngữ theo tiêu chí NGHIÊM NGẶT:\n\n"
    "TIÊU CHÍ CHẤP NHẬN:\n"
    "- Từ phương ngữ phải KHÁC RÕ RÀNG với từ phổ thông\n"
    "- Phải là TỪ ĐƠN hoặc TỪ GHÉP ngắn (tối đa 3 âm tiết)\n"
    "- Phải thuộc vùng Bắc Trung Bộ: Thanh Hóa, Nghệ An, Hà Tĩnh, Quảng Bình, Quảng Trị, Huế\n\n"
    "TIÊU CHÍ LOẠI Bỏ:\n"
    "- Từ phổ thông bình thường\n"
    "- Câu dài hơn 3 âm tiết\n"
    "- Từ mà word == standard_form\n"
    "- Từ không rõ nghĩa\n\n"
    "Với mỗi từ hợp lệ, trả về JSON với đúng các trường sau:\n"
    '{{"word": "từ phương ngữ (viết thường)", '
    '"standard_form": "từ phổ thông", '
    '"meaning": "giải thích nghĩa ít nhất 10 ký tự", '
    '"word_type": "từ_vựng hoặc ngữ_âm hoặc thành_ngữ", '
    '"example_sentence": "câu ví dụ nếu có, nếu không để chuỗi rỗng", '
    '"standard_sentence": "bản dịch nếu có, nếu không để chuỗi rỗng"}}\n\n'
    "Quy tắc word_type:\n"
    "- từ_vựng: nghĩa khác hoàn toàn (tru=trâu, mô=đâu)\n"
    "- ngữ_âm: biến âm theo vùng (ngá=ngứa, trấy=trái)\n"
    "- thành_ngữ: cụm cố định 2-3 âm tiết\n\n"
    "Nếu không tìm thấy từ nào, trả về [].\n"
    "CHỂ trả về JSON array, không giải thích, không markdown.\n\n"
    "VĂN BẢN:\n{text}"
)

def crawl_url(url):
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            text = trafilatura.extract(downloaded, include_links=False)
            if text and len(text) > 100:
                return text
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.encoding = "utf-8"
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        return soup.get_text(separator="\n", strip=True)
    except Exception as e:
        print(f"  Lỗi crawl {url}: {e}")
        return ""

def extract_words_v2(text, max_chars=3000):
    text = text[:max_chars]
    models = ["gemini-2.5-flash-lite", "gemini-2.0-flash-lite", "gemini-2.0-flash"]
    for model in models:
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=EXTRACT_PROMPT_V2.format(text=text)
                )
                raw = response.text.strip()
                raw = re.sub(r"```json|```", "", raw).strip()
                return json.loads(raw)
            except Exception as e:
                err = str(e)
                if "429" in err:
                    if attempt < 2:
                        wait = (attempt + 1) * 15
                        print(f"  Rate limit {model}, chờ {wait}s...")
                        time.sleep(wait)
                    else:
                        print(f"  Hết quota {model}, thử model khác...")
                        break
                else:
                    print(f"  Lỗi: {e}")
                    return []
    print("  Hết quota hôm nay — dừng lại")
    return None

def deduplicate(entries):
    seen = {}
    for entry in entries:
        key = entry["word"].strip().lower()
        if key not in seen or entry["confidence"] > seen[key]["confidence"]:
            seen[key] = entry
    return list(seen.values()), len(entries) - len(seen)

def validate_entry(entry):
    REQUIRED = ["word","standard_form","province","region_group","word_type",
                "meaning","source","verified_by","confidence","needs_verification"]
    PROVINCES = ["Thanh Hóa","Nghệ An","Hà Tĩnh","Quảng Bình","Quảng Trị","Thừa Thiên Huế"]
    REGION_GROUPS = ["Thanh Hóa","Nghệ Tĩnh","Bình Trị Thiên"]
    WORD_TYPES = ["từ_vựng","ngữ_âm","thành_ngữ"]
    VERIFIED_BY = ["sach_hoc_thuat","luan_van","cong_dong_online","da_nguon"]
    errors = []
    for field in REQUIRED:
        if field not in entry or entry[field] in [None, ""]:
            errors.append(f"Thiếu: {field}")
    if errors: return False, errors
    if entry["province"] not in PROVINCES: errors.append("province không hợp lệ")
    if entry["region_group"] not in REGION_GROUPS: errors.append("region_group không hợp lệ")
    if entry["word_type"] not in WORD_TYPES: errors.append("word_type không hợp lệ")
    if entry["verified_by"] not in VERIFIED_BY: errors.append("verified_by không hợp lệ")
    if not (0.0 <= float(entry["confidence"]) <= 1.0): errors.append("confidence không hợp lệ")
    if not isinstance(entry["needs_verification"], bool): errors.append("needs_verification phải bool")
    return len(errors) == 0, errors

def review_and_save(raw_entries, output_path=OUTPUT_PATH):
    print(f"Tổng raw: {len(raw_entries)}")
    filtered = [e for e in raw_entries
                if len(e.get("word","")) >= 1
                and len(e.get("standard_form","")) >= 1
                and len(e.get("meaning","")) >= 3
                and e.get("word","").lower() != e.get("standard_form","").lower()]
    print(f"Sau lọc: {len(filtered)} ({len(raw_entries)-len(filtered)} loại)")
    deduped, n = deduplicate(filtered)
    print(f"Sau deduplicate: {len(deduped)} ({n} trùng)")
    for e in deduped:
        e.setdefault("example_sentence", "")
        e.setdefault("standard_sentence", "")
        e.setdefault("source_page", "")
        e.setdefault("word_type", "từ_vựng")
    valid = [e for e in deduped if validate_entry(e)[0]]
    print(f"Validate passed: {len(valid)}")
    existing = []
    if os.path.exists(output_path):
        with open(output_path, encoding="utf-8") as f:
            existing = json.load(f)
    combined, _ = deduplicate(existing + valid)
    province_count = {}
    for e in combined:
        p = e.get("province","unknown")
        province_count[p] = province_count.get(p, 0) + 1
    print(f"Tổng sau gộp với existing: {len(combined)}")
    print("Phân bố tỉnh:")
    for p, c in sorted(province_count.items(), key=lambda x: -x[1]):
        print(f"  {p:<22} {c:>3}  {'█'*(c//5+1)}")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(combined, f, ensure_ascii=False, indent=2)
    print(f"\nĐã lưu {len(combined)} từ → {output_path}")
    return combined

def run_pipeline_v2(sources=SOURCES, delay=3.0):
    raw_entries = []
    for source_name, config in sources.items():
        print(f"\n== Nguồn: {source_name} ==")
        for url in config["urls"]:
            print(f"  Crawling: {url}")
            text = crawl_url(url)
            if not text:
                print("  Không lấy được nội dung")
                continue
            print(f"  {len(text)} ký tự")
            chunks = [text[i:i+3000] for i in range(0, min(len(text),9000), 3000)]
            for i, chunk in enumerate(chunks):
                print(f"  Chunk {i+1}/{len(chunks)}...")
                words = extract_words_v2(chunk)
                if words is None:
                    print("  Dừng pipeline — hết quota")
                    return raw_entries
                for w in words:
                    if not w.get("word") or not w.get("standard_form"): continue
                    w["province"]           = config["province_hint"]
                    w["region_group"]       = config["region_group"]
                    w["source"]             = url
                    w["source_page"]        = ""
                    w["verified_by"]        = config["verified_by"]
                    w["confidence"]         = config["confidence"]
                    w["needs_verification"] = config["confidence"] < 0.8
                    raw_entries.append(w)
                print(f"    → {len(words)} từ")
                time.sleep(delay)
    return raw_entries

# ============================================================
# PAIRS PIPELINE — Thu thập cặp câu song ngữ
# ============================================================
PAIRS_PROMPT = (
    "Bạn là chuyên gia ngôn ngữ học phương ngữ Việt Nam Bắc Trung Bộ.\n\n"
    "Từ đoạn văn bản dưới đây, hãy trích xuất TẤT CẢ các CẶP CÂU song ngữ:\n"
    "- Câu bằng phương ngữ địa phương\n"
    "- Câu dịch sang tiếng phổ thông tương đương\n\n"
    "TIÊU CHÍ CHẤP NHẬN:\n"
    "- Phải là câu hoàn chỉnh (có chủ ngữ + vị ngữ)\n"
    "- Câu phương ngữ phải chứa ít nhất 1 từ địa phương rõ ràng\n"
    "- Cặp câu phải tương đương về nghĩa\n\n"
    "TIÊU CHÍ LOẠI BỎ:\n"
    "- Câu quá ngắn (dưới 3 từ)\n"
    "- Câu phổ thông thuần túy không có từ phương ngữ\n\n"
    'Trả về JSON array, mỗi phần tử:\n'
    '{{"dialect_sentence": "câu phương ngữ", '
    '"standard_sentence": "câu phổ thông", '
    '"province": "tỉnh: Thanh Hóa/Nghệ An/Hà Tĩnh/Quảng Bình/Quảng Trị/Thừa Thiên Huế"}}\n\n'
    "Nếu không có cặp câu nào, trả về [].\n"
    "CHỈ trả về JSON array, không giải thích, không markdown.\n\n"
    "VĂN BẢN:\n{text}"
)

PAIRS_OUTPUT = "/content/vietnamese-dialect-system/data/processed/dialect_pairs.json"

VALID_PROVINCES = [
    "Thanh Hóa", "Nghệ An", "Hà Tĩnh",
    "Quảng Bình", "Quảng Trị", "Thừa Thiên Huế"
]

def extract_pairs(text, max_chars=3000):
    text = text[:max_chars]
    models = ["gemini-2.5-flash-lite", "gemini-2.0-flash-lite", "gemini-2.0-flash"]
    for model in models:
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=PAIRS_PROMPT.format(text=text)
                )
                raw = response.text.strip()
                raw = re.sub(r"```json|```", "", raw).strip()
                return json.loads(raw)
            except Exception as e:
                err = str(e)
                if "429" in err:
                    if attempt < 2:
                        wait = (attempt + 1) * 15
                        print(f"  Rate limit {model}, chờ {wait}s...")
                        time.sleep(wait)
                    else:
                        print(f"  Hết quota {model}, thử model khác...")
                        break
                else:
                    print(f"  Lỗi: {e}")
                    return []
    print("  Hết quota hôm nay — dừng lại")
    return None


def save_pairs(pairs, output_path=PAIRS_OUTPUT):
    seen = set()
    unique = []
    for p in pairs:
        key = p["dialect_sentence"].strip().lower()
        if key not in seen:
            seen.add(key)
            unique.append(p)
    existing = []
    if os.path.exists(output_path):
        with open(output_path, encoding="utf-8") as f:
            existing = json.load(f)
    existing_keys = {e["dialect_sentence"].strip().lower() for e in existing}
    new_pairs = [p for p in unique if p["dialect_sentence"].strip().lower() not in existing_keys]
    combined = existing + new_pairs
    print(f"New: {len(new_pairs)} | Existing: {len(existing)} | Total: {len(combined)}")
    prov_count = {}
    for p in combined:
        pv = p.get("province", "unknown")
        prov_count[pv] = prov_count.get(pv, 0) + 1
    print("Phân bố tỉnh:")
    for pv, c in sorted(prov_count.items(), key=lambda x: -x[1]):
        print(f"  {pv:<22} {c:>3}  {chr(9608)*(c//5+1)}")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(combined, f, ensure_ascii=False, indent=2)
    print(f"Đã lưu {len(combined)} cặp câu → {output_path}")
    return combined


def run_pairs_pipeline(sources, delay=4.0):
    all_pairs = []
    for source_name, config in sources.items():
        print(f"\n== Nguồn: {source_name} ==")
        for url in config["urls"]:
            print(f"  Crawling: {url}")
            text = crawl_url(url)
            if not text:
                print("  Không lấy được nội dung")
                continue
            print(f"  {len(text)} ký tự")
            chunks = [text[i:i+3000] for i in range(0, min(len(text), 9000), 3000)]
            for i, chunk in enumerate(chunks):
                print(f"  Chunk {i+1}/{len(chunks)}...")
                pairs = extract_pairs(chunk)
                if pairs is None:
                    print("  Dừng — hết quota")
                    return all_pairs
                for p in pairs:
                    if (p.get("dialect_sentence") and
                            p.get("standard_sentence") and
                            p["dialect_sentence"] != p["standard_sentence"]):
                        p["source"] = url
                        if p.get("province") not in VALID_PROVINCES:
                            p["province"] = config["province_hint"]
                        all_pairs.append(p)
                print(f"    → {len(pairs)} cặp câu")
                time.sleep(delay)
    return all_pairs


# ============================================================
# UNIFIED LLM CALLER — Groq primary, Gemini fallback
# ============================================================
from groq import Groq

def get_groq_client():
    import os
    key = os.environ.get("GROQ_API_KEY", "")
    if key:
        try:
            return Groq(api_key=key)
        except:
            pass
    return None

_groq_client = get_groq_client()

def call_llm(prompt: str) -> str:
    global _groq_client
    # Tầng 1: Groq
    if _groq_client:
        try:
            response = _groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.1
            )
            return response.choices[0].message.content
        except Exception as e:
            if "429" in str(e) or "rate" in str(e).lower():
                print("  Groq rate limit, thử Gemini...")
            else:
                print(f"  Groq lỗi: {e}")
    # Tầng 2: Gemini fallback
    for model in ["gemini-2.5-flash-lite", "gemini-2.0-flash-lite", "gemini-2.0-flash"]:
        for attempt in range(2):
            try:
                response = client.models.generate_content(model=model, contents=prompt)
                return response.text
            except Exception as e:
                if "429" in str(e):
                    if attempt < 1:
                        print(f"  Gemini {model} rate limit, chờ 15s...")
                        time.sleep(15)
                    else:
                        break
                else:
                    break
    print("  Hết quota tất cả — dừng")
    return None


def extract_words_v2(text, max_chars=3000):
    text = text[:max_chars]
    raw = call_llm(EXTRACT_PROMPT_V2.format(text=text))
    if raw is None: return None
    try:
        raw = re.sub(r"```json|```", "", raw).strip()
        return json.loads(raw)
    except: return []

def extract_pairs(text, max_chars=3000):
    text = text[:max_chars]
    raw = call_llm(PAIRS_PROMPT.format(text=text))
    if raw is None: return None
    try:
        raw = re.sub(r"```json|```", "", raw).strip()
        return json.loads(raw)
    except: return []
