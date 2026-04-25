# PhoBERT Classifier Report

## Kết quả
- Val Accuracy  : 0.750
- Test Accuracy : 0.733
- Số nhóm       : 3 (Thanh Hóa / Nghệ Tĩnh / Bình Trị Thiên)
- Model         : vinai/phobert-base
- Epochs        : 10
- Best epoch    : 8

## Nhận xét
- Đạt target ≥60% trong checklist
- Thanh Hóa ít data (52 samples) nên F1 thấp hơn 2 nhóm còn lại
- Class weighting đã giúp cân bằng một phần

## Cách giải thích với hội đồng
- 70% accuracy với chỉ 1159 samples là kết quả tốt
- Baseline random = 33% → model tốt hơn baseline 2x
- Hạn chế chính: Thanh Hóa thiếu data
