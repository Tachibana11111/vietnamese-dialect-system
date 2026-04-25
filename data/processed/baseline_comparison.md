# Baseline Comparison Report

## Methodology
- Test set: 30 câu từ test.json (đã lock, không có trong ChromaDB)
- Baseline: Groq Llama-3.3-70b gọi trực tiếp, không có RAG context
- RAG: Groq + ChromaDB retrieve (1038 từ + 658 cặp câu)
- Metric: BLEU score với smoothing method1

## Kết quả
| Phương pháp | BLEU Score |
|-------------|-----------|
| Baseline (no RAG) | 0.3106 |
| RAG Pipeline | 0.4903 |
| Cải thiện | +0.1796 (+57.8%) |

## Phân tích
- Baseline 0.31 không thấp vì Llama-3.3-70b đã biết một số từ phổ biến
- RAG cải thiện 57.8% trên nền model mạnh — chứng minh knowledge base có giá trị thực
- Kết quả xác nhận kiến trúc RAG phù hợp cho bài toán low-resource dialect

## Lưu ý về data leakage
- Test đầu tiên dùng dialect_pairs.json (đã nhúng vào ChromaDB) → BLEU 0.94 — không hợp lệ
- Test này dùng test.json chưa nhúng vào ChromaDB → BLEU 0.49 — kết quả đúng methodology
- Sự khác biệt này chứng minh tầm quan trọng của việc tách tập test trước khi build DB

## Kết luận
RAG pipeline cải thiện 57.8% so với baseline trên tập test sạch.
Đây là bằng chứng định lượng cho đóng góp kỹ thuật của hệ thống.
