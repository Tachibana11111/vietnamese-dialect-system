# Data Report — Phase 2 Complete

## Dataset Summary
- Từ vựng   : 1038 từ (6 tỉnh)
- Cặp câu   : 658 cặp (6 tỉnh)
- ChromaDB  : 2 collections production-ready

## Phân bố từ vựng theo tỉnh
| Tỉnh | Số từ |
|------|-------|
| Nghệ An | 351 |
| Quảng Bình | 238 |
| Quảng Trị | 236 |
| Hà Tĩnh | 87 |
| Thừa Thiên Huế | 86 |
| Thanh Hóa | 40 |

## Phân bố cặp câu theo tỉnh
| Tỉnh | Số cặp |
|------|--------|
| Nghệ An | 329 |
| Quảng Bình | 117 |
| Quảng Trị | 63 |
| Hà Tĩnh | 57 |
| Thừa Thiên Huế | 56 |
| Thanh Hóa | 36 |

## ChromaDB
- Model embedding : paraphrase-multilingual-MiniLM-L12-v2
- Words collection: 1038 entries
- Pairs collection: 658 entries
- Retrieve test   : PASS (5/5 queries)

## Ghi chú
- 572/1038 từ còn needs_verification=True (nguồn online đơn lẻ)
- Mất cân bằng Thanh Hóa (40 từ) — xử lý bằng class weighting khi train PhoBERT
- Tập test đã lock tại data/processed/test.json
