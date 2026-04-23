# Data Collection Report
Generated: Phase 1 — Tuần 2

## Tổng quan
- Tổng số từ: 1038
- Train/Val/Test: 836/101/101

## Phân bố theo tỉnh
- Nghệ An: 351 từ (182 có câu ví dụ)
- Quảng Bình: 238 từ (55 có câu ví dụ)
- Quảng Trị: 236 từ (209 có câu ví dụ)
- Hà Tĩnh: 87 từ (50 có câu ví dụ)
- Thừa Thiên Huế: 86 từ (49 có câu ví dụ)
- Thanh Hóa: 40 từ (40 có câu ví dụ)

## Nguồn dữ liệu
- nghengu.vn (từ điển tiếng Nghệ)
- xomaonguyen.blogspot.com (từ điển văn vần)
- nguyentienhai.blogspot.com (từ điển Huế, Quảng Bình)
- vannghequangtri.blogspot.com (từ điển Quảng Trị)
- humansofhatinh.blogspot.com (phương ngữ Hà Tĩnh)
- vi.wikipedia.org (phương ngữ Thanh Hóa)
- m0nst3rbee.blogspot.com (từ điển Quảng Bình)
- baohatinh.vn, baothuathienhue.vn (báo địa phương)

## Quy trình xác minh
- Tầng 1: Nguồn học thuật (sách, luận văn) — confidence 0.9
- Tầng 2: Blog/trang chuyên về phương ngữ — confidence 0.75
- Tầng 3: Cộng đồng online — confidence 0.7
- Từ cần xác minh thêm: 1038

## Ghi chú
- Tập test đã được tách riêng và KHÔNG được dùng để train
- Mất cân bằng Thanh Hóa (40 từ) do thiếu nguồn online — xử lý bằng class weighting khi train
