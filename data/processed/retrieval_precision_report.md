# Retrieval Precision@K Report

## Tổng quan
- Test cases: 50
- Nguồn: test.json (đã lock, không có trong training)

## Kết quả
| K | Precision@K |
|---|-------------|
| 1 | 0.4200 |
| 3 | 0.5000 |
| 5 | 0.6000 |
| 10| 0.6200 |

## Phân tích
- P@5 = 0.6000 có nghĩa là 60.0% trường hợp,
  từ đúng xuất hiện trong top-5 retrieved docs
- Đây là retrieval accuracy độc lập với LLM
- Kết hợp với BLEU 0.4903 cho thấy cả retrieve và generate đều hoạt động

## Phân bố theo tỉnh (P@5)
- Hà Tĩnh: 1.0000 (n=1)
- Nghệ An: 0.4000 (n=15)
- Quảng Bình: 0.6000 (n=5)
- Quảng Trị: 0.6190 (n=21)
- Thanh Hóa: 1.0000 (n=4)
- Thừa Thiên Huế: 0.7500 (n=4)
