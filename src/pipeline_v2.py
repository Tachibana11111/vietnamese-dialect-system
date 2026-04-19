
import requests, json, time, re, os
from bs4 import BeautifulSoup
import trafilatura
from google import genai
from google.colab import userdata

# ============================================================
# CONFIG
# ============================================================
GEMINI_API_KEY = userdata.get("GEMINI_API_KEY")
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
        "urls": [
            "http://xomaonguyen.blogspot.com/2014/09/tu-ien-tieng-nghe-tinh-tu-en-zvan-van.html",
        ],
        "province_hint": "Nghệ An",
        "region_group": "Nghệ Tĩnh",
        "verified_by": "cong_dong_online",
        "confidence": 0.65,
    },
    "baonghean": {
        "urls": [
            "https://baonghean.vn/van-hoa",
            "https://baonghean.vn/xa-hoi",
        ],
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
}

EXTRACT_PROMPT_V2 = """Bạn là chuyên gia ngôn ngữ học phương ngữ Việt Nam Bắc Trung Bộ.

Từ đoạn văn bản dưới đây, hãy trích xuất các từ phương ngữ theo tiêu chí NGHIÊM NGẶT:

TIÊU CHÍ CHẤP NHẬN:
- Từ phương ngữ phải KHÁC RÕ RÀNG với từ phổ thông (không chỉ khác thanh điệu nhẹ)
- Phải là TỪ ĐƠN hoặc TỪ GHÉP ngắn (tối đa 3 âm tiết)
- Phải thuộc vùng Bắc Trung Bộ: Thanh Hóa, Nghệ An, Hà Tĩnh, Quảng Bình, Quảng Trị, Huế

TIÊU CHÍ LOẠI BỎ:
- Từ phổ thông bình thường
- Câu dài hơn 3 âm tiết
- Từ mà word == standard_form
- Từ không rõ nghĩa

Với mỗi từ hợp lệ, trả về JSON với đúng các trường sau:
{{
  "word": "từ phương ngữ (viết thường)",
  "standard_form": "từ phổ thông tương đương",
  "meaning": "giải thích nghĩa cụ thể, ít nhất 10 ký tự",
  "word_type": "từ_vựng hoặc ngữ_âm hoặc thành_ngữ",
  "example_sentence": "câu ví dụ bằng phương ngữ nếu có, nếu không thì để chuỗi rỗng",
  "standard_sentence": "câu ví dụ dịch sang phổ thông nếu có, nếu không thì để chuỗi rỗng"
}}

Quy tắc word_type:
- từ_vựng: nghĩa khác hoàn toàn (tru=trâu, mô=đâu)
- ngữ_âm: biến âm theo vùng (ngá=ngứa, trấy=trái)
- thành_ngữ: cụm cố định 2-3 âm tiết

Nếu không tìm thấy từ nào, trả về [].
CHỈ trả về JSON array, không giải thích, không markdown.

VĂN BẢN:
{text}"""

# ============================================================
# FUNCTIONS
# ============================================================
def crawl_url(url: str) -> str:
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            text = trafilatura.extract(downloaded, include_links=False)
            if text and len(text) > 100:
                return text
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        return soup.get_text(separator="\n", strip=True)
    except Exception as e:
        print(f"  Lỗi crawl {url}: {e}")
        return ""


def extract_words_v2(text: str, max_chars: int = 3000) -> list:
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
    print("  Hết quota hôm nay — dừng lại, chạy tiếp ngày mai")
    return []


def deduplicate(entries: list) -> tuple[list, int]:
    seen = {}
    for entry in entries:
        key = entry["word"].strip().lower()
        if key not in seen or entry["confidence"] > seen[key]["confidence"]:
            seen[key] = entry
    return list(seen.values()), len(entries) - len(seen)


def validate_entry(entry: dict) -> tuple[bool, list[str]]:
    REQUIRED = [
        "word", "standard_form", "province", "region_group", "word_type",
        "meaning", "source", "verified_by", "confidence", "needs_verification"
    ]
    PROVINCES     = ["Thanh Hóa", "Nghệ An", "Hà Tĩnh", "Quảng Bình", "Quảng Trị", "Thừa Thiên Huế"]
    REGION_GROUPS = ["Thanh Hóa", "Nghệ Tĩnh", "Bình Trị Thiên"]
    WORD_TYPES    = ["từ_vựng", "ngữ_âm", "thành_ngữ"]
    VERIFIED_BY   = ["sach_hoc_thuat", "luan_van", "cong_dong_online", "da_nguon"]

    errors = []
    for field in REQUIRED:
        if field not in entry or entry[field] in [None, ""]:
            errors.append(f"Thiếu: {field}")
    if errors:
        return False, errors
    if entry["province"] not in PROVINCES:
        errors.append(f"province không hợp lệ: {entry['province']}")
    if entry["region_group"] not in REGION_GROUPS:
        errors.append(f"region_group không hợp lệ")
    if entry["word_type"] not in WORD_TYPES:
        errors.append(f"word_type không hợp lệ: {entry['word_type']}")
    if entry["verified_by"] not in VERIFIED_BY:
        errors.append(f"verified_by không hợp lệ")
    if not (0.0 <= float(entry["confidence"]) <= 1.0):
        errors.append("confidence phải 0.0–1.0")
    if not isinstance(entry["needs_verification"], bool):
        errors.append("needs_verification phải True/False")
    return len(errors) == 0, errors


def review_and_save(raw_entries: list, output_path: str) -> list:
    print(f"Tổng raw entries: {len(raw_entries)}")

    # Lọc rỗng
    filtered = []
    for e in raw_entries:
        if (len(e.get("word","")) >= 1
                and len(e.get("standard_form","")) >= 1
                and len(e.get("meaning","")) >= 3
                and e.get("word","").lower() != e.get("standard_form","").lower()):
            filtered.append(e)
    print(f"Sau lọc: {len(filtered)} ({len(raw_entries)-len(filtered)} bị loại)")

    # Deduplicate
    deduped, n_dupes = deduplicate(filtered)
    print(f"Sau deduplicate: {len(deduped)} ({n_dupes} trùng)")

    # Điền optional fields
    for e in deduped:
        e.setdefault("example_sentence", "")
        e.setdefault("standard_sentence", "")
        e.setdefault("source_page", "")
        e.setdefault("word_type", "từ_vựng")

    # Validate
    valid, invalid = [], []
    for e in deduped:
        ok, errs = validate_entry(e)
        if ok:
            valid.append(e)
        else:
            invalid.append({"entry": e, "errors": errs})

    # Load existing data nếu có
    existing = []
    if os.path.exists(output_path):
        with open(output_path, encoding="utf-8") as f:
            existing = json.load(f)

    # Gộp với existing, deduplicate lại
    combined, n_dup2 = deduplicate(existing + valid)
    print(f"Validate passed: {len(valid)} | Failed: {len(invalid)}")
    print(f"Gộp với existing ({len(existing)}) → tổng: {len(combined)}")

    # Phân bố tỉnh
    province_count = {}
    has_example = 0
    for e in combined:
        p = e.get("province", "unknown")
        province_count[p] = province_count.get(p, 0) + 1
        if e.get("example_sentence"):
            has_example += 1
    print("\nPhân bố theo tỉnh:")
    for p, count in sorted(province_count.items(), key=lambda x: -x[1]):
        bar = "█" * (count // 5 + 1)
        print(f"  {p:<22} {count:>3}  {bar}")
    print(f"\nCó câu ví dụ: {has_example}/{len(combined)}")
    print(f"Cần xác minh: {sum(1 for e in combined if e.get('needs_verification'))}/{len(combined)}")

    # Lưu
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(combined, f, ensure_ascii=False, indent=2)
    print(f"\nĐã lưu {len(combined)} từ → {output_path}")
    return combined


def run_pipeline_v2(sources: dict, delay: float = 3.0) -> list:
    raw_entries = []
    for source_name, config in sources.items():
        print(f"\n{\'=\'*50}")
        print(f"Nguồn: {source_name}")
        print(f"{\'=\'*50}")
        for url in config["urls"]:
            print(f"\n  Crawling: {url}")
            text = crawl_url(url)
            if not text:
                print("  Không lấy được nội dung, bỏ qua")
                continue
            print(f"  Lấy được {len(text)} ký tự")
            chunks = [text[i:i+3000] for i in range(0, min(len(text), 9000), 3000)]
            for i, chunk in enumerate(chunks):
                print(f"  Chunk {i+1}/{len(chunks)}...")
                words = extract_words_v2(chunk)
                if words is None:
                    return raw_entries  # hết quota, dừng hẳn
                for w in words:
                    if not w.get("word") or not w.get("standard_form"):
                        continue
                    w["province"]          = config["province_hint"]
                    w["region_group"]      = config["region_group"]
                    w["source"]            = url
                    w["source_page"]       = ""
                    w["verified_by"]       = config["verified_by"]
                    w["confidence"]        = config["confidence"]
                    w["needs_verification"] = config["confidence"] < 0.8
                    raw_entries.append(w)
                print(f"    → {len(words)} từ")
                time.sleep(delay)
    return raw_entries
