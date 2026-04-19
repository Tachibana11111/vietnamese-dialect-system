
import json

REQUIRED_FIELDS_STRICT = [
    "word", "standard_form", "province", "region_group", "word_type",
    "meaning", "source", "verified_by", "confidence", "needs_verification"
]
PROVINCES     = ["Thanh Hóa", "Nghệ An", "Hà Tĩnh", "Quảng Bình", "Quảng Trị", "Thừa Thiên Huế"]
REGION_GROUPS = ["Thanh Hóa", "Nghệ Tĩnh", "Bình Trị Thiên"]
WORD_TYPES    = ["từ_vựng", "ngữ_âm", "thành_ngữ"]
VERIFIED_BY   = ["sach_hoc_thuat", "luan_van", "cong_dong_online", "da_nguon"]

def validate_entry(entry: dict) -> tuple[bool, list[str]]:
    errors = []
    for field in REQUIRED_FIELDS_STRICT:
        if field not in entry or entry[field] in [None, ""]:
            errors.append(f"Thiếu hoặc rỗng: '{field}'")
    if errors:
        return False, errors
    if entry["province"] not in PROVINCES:
        errors.append(f"province không hợp lệ: '{entry['province']}'")
    if entry["region_group"] not in REGION_GROUPS:
        errors.append(f"region_group không hợp lệ: '{entry['region_group']}'")
    if entry["word_type"] not in WORD_TYPES:
        errors.append(f"word_type không hợp lệ: '{entry['word_type']}'")
    if entry["verified_by"] not in VERIFIED_BY:
        errors.append(f"verified_by không hợp lệ: '{entry['verified_by']}'")
    if not (0.0 <= float(entry["confidence"]) <= 1.0):
        errors.append(f"confidence phải từ 0.0 đến 1.0")
    if not isinstance(entry["needs_verification"], bool):
        errors.append(f"needs_verification phải là True/False")
    return len(errors) == 0, errors
