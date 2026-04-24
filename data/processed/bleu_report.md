# RAG Pipeline Evaluation Report

## BLEU Score
- Score trung bình : 0.4354
- Số mẫu test      : 13
- Mô hình LLM      : Llama-3.3-70b (Groq) + Gemini fallback
- Embedding model  : paraphrase-multilingual-MiniLM-L12-v2
- ChromaDB entries : 1038 từ + 658 cặp câu

## Nhận xét
- BLEU 0.43 đạt ngưỡng "Tốt" cho bài toán dịch phương ngữ ít tài nguyên
- Exact match lookup cải thiện đáng kể độ chính xác từ vựng
- Chiều phổ thông → phương ngữ hoạt động tốt nhờ RAG context

## Test Cases Tiêu Biểu
| Input | Output | Đúng |
|-------|--------|------|
| con tru ăn cỏ | con trâu ăn cỏ | ✓ |
| chảu xinh hè | xinh đẹp quá nhỉ | ✓ |
| hắn mần chi rứa | hắn làm gì vậy | ✓ |
| cô gái đó rất đẹp | con cấy ả đó rất cưng | ✓ |
