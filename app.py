
import streamlit as st
import sys, os, json, re
import chromadb
from sentence_transformers import SentenceTransformer

# ============================================================
# CONFIG
# ============================================================
CHROMA_PATH = "./chroma_db"
sys.path.append("./src")

st.set_page_config(
    page_title="Hệ thống Phương ngữ Bắc Trung Bộ",
    page_icon="🗣️",
    layout="wide"
)

PROVINCES = [
    "Nghệ An", "Hà Tĩnh", "Thanh Hóa",
    "Quảng Bình", "Quảng Trị", "Thừa Thiên Huế"
]

PROVINCE_INFO = {
    "Nghệ An":        {"group": "Nghệ Tĩnh",       "color": "#1D9E75"},
    "Hà Tĩnh":        {"group": "Nghệ Tĩnh",       "color": "#1D9E75"},
    "Thanh Hóa":      {"group": "Thanh Hóa",       "color": "#534AB7"},
    "Quảng Bình":     {"group": "Bình Trị Thiên",  "color": "#D85A30"},
    "Quảng Trị":      {"group": "Bình Trị Thiên",  "color": "#D85A30"},
    "Thừa Thiên Huế": {"group": "Bình Trị Thiên",  "color": "#D85A30"},
}

# ============================================================
# INIT RAG (cache để không load lại mỗi lần)
# ============================================================
@st.cache_resource
def load_rag():
    from rag_engine import init_rag, translate, lookup, retrieve_context
    init_rag()
    return translate, lookup, retrieve_context

@st.cache_resource
def load_classifier():
    try:
        import torch
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        MODEL_NAME = "vinai/phobert-base"
        tokenizer  = AutoTokenizer.from_pretrained(MODEL_NAME)
        model      = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=3)
        ckpt_path  = "./data/classifier_best.pt"
        if os.path.exists(ckpt_path):
            model.load_state_dict(torch.load(ckpt_path, map_location="cpu"))
            model.eval()
            return tokenizer, model
    except:
        pass
    return None, None

GROUP_NAMES = {0: "Thanh Hóa", 1: "Nghệ Tĩnh", 2: "Bình Trị Thiên"}

def predict_region(text, tokenizer, model):
    import torch
    enc = tokenizer(text, return_tensors="pt", max_length=128,
                    padding="max_length", truncation=True)
    with torch.no_grad():
        out   = model(**enc)
        probs = torch.softmax(out.logits, dim=1)[0].tolist()
        pred  = int(torch.argmax(out.logits, dim=1))
    return GROUP_NAMES[pred], probs

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.title("⚙️ Cài đặt")
    province = st.selectbox("Tỉnh dịch sang:", PROVINCES, index=0)
    st.divider()
    st.markdown("**Thông tin tỉnh:**")
    info = PROVINCE_INFO[province]
    st.markdown(f"- Nhóm: **{info['group']}**")
    st.divider()
    st.markdown("**Về hệ thống:**")
    st.markdown("- 1038 từ phương ngữ")
    st.markdown("- 658 cặp câu song ngữ")
    st.markdown("- RAG + PhoBERT")
    st.markdown("- 6 tỉnh Bắc Trung Bộ")

# ============================================================
# MAIN UI
# ============================================================
st.title("🗣️ Hệ thống Phương ngữ Bắc Trung Bộ")
st.markdown("*Dịch thuật hai chiều · Phân loại vùng miền · Tra cứu từ điển*")
st.divider()

# Load models
with st.spinner("Đang khởi tạo hệ thống..."):
    translate_fn, lookup_fn, retrieve_fn = load_rag()
    tokenizer, clf_model = load_classifier()

# Tabs
tab1, tab2, tab3 = st.tabs(["🔄 Dịch thuật", "🔍 Tra cứu từ", "📊 Phân loại vùng miền"])

# ============================================================
# TAB 1: DỊCH THUẬT
# ============================================================
with tab1:
    st.subheader("Dịch thuật hai chiều")
    col1, col2 = st.columns(2)

    with col1:
        query = st.text_area(
            "Nhập câu cần dịch:",
            placeholder="VD: con tru ăn cỏ ngoài đồng\nhoặc: con trâu ăn cỏ ngoài đồng",
            height=120
        )
        btn_translate = st.button("🔄 Dịch", type="primary", use_container_width=True)

    with col2:
        if btn_translate and query.strip():
            with st.spinner("Đang dịch..."):
                result = translate_fn(query.strip(), province)

            st.success("Kết quả dịch:")
            st.markdown(f"### {result.get('translation', 'Không dịch được')}")

            if result.get("dialect_words"):
                st.markdown("**Từ phương ngữ nhận diện:**")
                for w in result["dialect_words"]:
                    st.markdown(f"- `{w}`")

            conf = result.get("confidence", 0)
            st.progress(float(conf) if conf else 0)
            st.caption(f"Độ tin cậy: {conf}")

            # Classifier
            if tokenizer and clf_model:
                region, probs = predict_region(query, tokenizer, clf_model)
                st.divider()
                st.markdown("**Vùng miền dự đoán:**")
                st.info(f"🗺️ {region}")
                cols = st.columns(3)
                for i, (name, prob) in enumerate(zip(GROUP_NAMES.values(), probs)):
                    cols[i].metric(name, f"{prob:.1%}")

        elif btn_translate:
            st.warning("Vui lòng nhập câu cần dịch")

    # Retrieved context
    if btn_translate and query.strip():
        with st.expander("📚 Context từ ChromaDB"):
            ctx = retrieve_fn(query.strip())
            st.markdown("**Từ vựng liên quan:**")
            for w in ctx["words"][:5]:
                st.markdown(f"- `{w['word']}` → `{w['standard_form']}` ({w['province']}) score={w['score']}")
            st.markdown("**Cặp câu tương tự:**")
            for p in ctx["pairs"][:3]:
                st.markdown(f"- *{p['dialect']}* → *{p['standard']}*")

# ============================================================
# TAB 2: TRA CỨU TỪ
# ============================================================
with tab2:
    st.subheader("Tra cứu từ phương ngữ")
    word_query = st.text_input("Nhập từ cần tra:", placeholder="VD: tru, răng, mô, chảu...")
    btn_lookup = st.button("🔍 Tra cứu", type="primary")

    if btn_lookup and word_query.strip():
        with st.spinner("Đang tra cứu..."):
            result = lookup_fn(word_query.strip())

        st.markdown(f"**Kết quả cho:** `{word_query}`")
        for r in result["results"]:
            color = PROVINCE_INFO.get(r["province"], {}).get("color", "#888")
            with st.container():
                col1, col2, col3 = st.columns([2, 3, 1])
                col1.markdown(f"**{r['word']}** → *{r['standard_form']}*")
                col2.markdown(f"📍 {r['province']}")
                col3.markdown(f"score: `{r['score']}`")
            st.divider()

# ============================================================
# TAB 3: PHÂN LOẠI VÙNG MIỀN
# ============================================================
with tab3:
    st.subheader("Phân loại vùng miền")
    if tokenizer and clf_model:
        region_input = st.text_area(
            "Nhập câu phương ngữ:",
            placeholder="VD: răng mi không đi học rứa",
            height=100
        )
        btn_classify = st.button("📊 Phân loại", type="primary")

        if btn_classify and region_input.strip():
            with st.spinner("Đang phân tích..."):
                region, probs = predict_region(region_input.strip(), tokenizer, clf_model)

            st.success(f"Vùng miền dự đoán: **{region}**")
            st.divider()
            st.markdown("**Xác suất từng nhóm:**")
            for name, prob in zip(GROUP_NAMES.values(), probs):
                st.progress(prob, text=f"{name}: {prob:.1%}")
    else:
        st.warning("Model classifier chưa được load. Cần file classifier_best.pt từ Google Drive.")
        st.info("Chạy Phase 4 để train model trước.")
