
import json
from typing import Union

PROVINCES = ["Thanh Hóa", "Nghệ An", "Hà Tĩnh", "Quảng Bình", "Quảng Trị", "Thừa Thiên Huế"]
REGION_GROUPS = ["Thanh Hóa", "Nghệ Tĩnh", "Bình Trị Thiên"]
WORD_TYPES = ["từ_vựng", "ngữ_âm", "thành_ngữ"]
VERIFIED_BY = ["sach_hoc_thuat", "luan_van", "cong_dong_online", "da_nguon"]

REQUIRED_FIELDS = [
    "word", "standard_form", "province", "region_group", "word_type",
    "meaning", "example_sentence", "standard_sentence",
    "source", "verified_by", "confidence", "needs_verification"
]

def validate_entry(entry: dict) -> tuple[bool, list[str]]:
    errors = []

    # Kiểm tra trường bắt buộc
    for field in REQUIRED_FIELDS:
        if field not in entry or entry[field] in [None, "", []]:
            errors.append(f"Thiếu hoặc rỗng: '{field}'")

    if errors:
        return False, errors

    # Kiểm tra giá trị hợp lệ
    if entry["province"] not in PROVINCES:
        errors.append(f"province không hợp lệ: '{entry['province']}'")

    if entry["region_group"] not in REGION_GROUPS:
        errors.append(f"region_group không hợp lệ: '{entry['region_group']}'")

    if entry["word_type"] not in WORD_TYPES:
        errors.append(f"word_type không hợp lệ: '{entry['word_type']}'")

    if entry["verified_by"] not in VERIFIED_BY:
        errors.append(f"verified_by không hợp lệ: '{entry['verified_by']}'")

    if not (0.0 <= float(entry["confidence"]) <= 1.0):
        errors.append(f"confidence phải từ 0.0 đến 1.0: '{entry['confidence']}'")

    if not isinstance(entry["needs_verification"], bool):
        errors.append(f"needs_verification phải là True/False")

    return len(errors) == 0, errors


def validate_dataset(filepath: str) -> dict:
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    total = len(data)
    passed = 0
    failed = 0
    needs_check = 0
    province_count = {}
    errors_log = []

    for i, entry in enumerate(data):
        ok, errs = validate_entry(entry)
        if ok:
            passed += 1
        else:
            failed += 1
            errors_log.append({"index": i, "word": entry.get("word","?"), "errors": errs})

        if entry.get("needs_verification"):
            needs_check += 1

        p = entry.get("province", "unknown")
        province_count[p] = province_count.get(p, 0) + 1

    print("=" * 45)
    print("DATA VALIDATION REPORT")
    print("=" * 45)
    print(f"Tổng số từ     : {total}")
    print(f"Passed         : {passed} ({100*passed//total if total else 0}%)")
    print(f"Failed         : {failed}")
    print(f"Cần xác minh   : {needs_check}")
    print()
    print("Phân bố theo tỉnh:")
    for p, count in sorted(province_count.items(), key=lambda x: -x[1]):
        bar = "█" * (count // 2) or "▏"
        print(f"  {p:<20} {count:>3}  {bar}")

    if errors_log:
        print()
        print("Lỗi cần fix:")
        for e in errors_log[:5]:  # hiện tối đa 5 lỗi
            print(f"  [{e['index']}] '{e['word']}': {', '.join(e['errors'])}")
        if len(errors_log) > 5:
            print(f"  ... và {len(errors_log)-5} lỗi khác")

    print("=" * 45)
    return {"total": total, "passed": passed, "failed": failed, "needs_verification": needs_check}
