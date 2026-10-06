import io
import streamlit as st

from extract import read_pdf, split_clauses
from analyze import analyze_clauses
from config import DISCLAIMER
from ui_style import CSS
from ui_content import SAMPLES, HOUSING_OPTIONS, PROHIBITIONS, RIGHTS, DORM_NOTES
from ui_logic import esc, stats_html, card_html, sort_results, calc_difference, calc_html

st.set_page_config(page_title="LeaseCheck", page_icon="🛡️", layout="wide")
st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)

st.markdown(
    '<div class="lc-header"><span class="lc-logo">🛡️ LeaseCheck</span><span class="lc-badge">สคบ. 2568</span></div>',
    unsafe_allow_html=True,
)

tab_check, tab_calc, tab_rules = st.tabs(["🔍 ตรวจสอบสัญญา", "🧮 คำนวณส่วนต่าง", "📖 เกณฑ์ สคบ."])


def use_sample(key: str) -> None:
    st.session_state["contract_text"] = SAMPLES[key]["text"]
    st.session_state["results"] = None


# =====================================================================
# แท็บ 1: ตรวจสอบสัญญา
# =====================================================================
with tab_check:
    st.markdown(
        '<div class="lc-hero"><h1>ระบบตรวจสอบสัญญาเช่าหอพักอัตโนมัติ</h1>'
        "<p>วิเคราะห์สัญญาเช่าเทียบกับเกณฑ์ สคบ. จำแนกข้อสัญญาตามสี 3 ระดับ เพื่อช่วยให้ผู้เช่าเข้าใจสิทธิของตัวเอง</p>"
        '<span class="lc-chip red">🔴 สีแดง: เข้าข่ายต้องห้าม / เสี่ยงสูง</span>'
        '<span class="lc-chip yellow">🟡 สีเหลือง: ข้อควรระวัง</span>'
        '<span class="lc-chip green">🟢 สีเขียว: เป็นธรรม / สอดคล้องเกณฑ์</span></div>',
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        st.subheader("1. เลือกสัญญาเช่าเพื่อตรวจสอบ")
        pdf = st.file_uploader("คลิกหรือลากไฟล์ PDF สัญญาเช่ามาวางที่นี่ (รองรับ .pdf ที่เลือกข้อความได้)", type="pdf")
        st.markdown('<div class="lc-or">— หรือทดลองด้วยสัญญาจำลอง 3 รูปแบบ (สมมติขึ้นเพื่อทดสอบ) —</div>', unsafe_allow_html=True)

        cols = st.columns(3)
        for col, (key, s) in zip(cols, SAMPLES.items()):
            with col:
                st.markdown(
                    f'<div class="lc-sample {s["cls"]}"><b>{s["emoji"]} {esc(s["title"])}</b><div>{esc(s["desc"])}</div></div>',
                    unsafe_allow_html=True,
                )
                st.button("ใช้ตัวอย่างนี้", key=f"sample_{key}", on_click=use_sample, args=(key,))

        st.text_area("ข้อความสัญญาเช่า:", key="contract_text", height=220,
                     placeholder="หรือพิมพ์ / วางข้อความสัญญาเช่าลงในช่องนี้...")
        housing_label = st.radio("ประเภทที่พัก (ถ้าทราบ ช่วยให้ผลตรงขึ้น)", list(HOUSING_OPTIONS), horizontal=True)
        st.caption("ถ้ามีทั้งไฟล์ PDF และข้อความ ระบบจะใช้ไฟล์ PDF ระบบปิดเลขบัตร เบอร์โทร อีเมลให้ก่อนส่งวิเคราะห์ "
                   "แต่ควรลบชื่อและที่อยู่เองด้วย เพราะระดับฟรีของ Gemini อาจนำข้อมูลไปปรับปรุงผลิตภัณฑ์ของ Google")

        run = st.button("⚡ เริ่มตรวจสอบสัญญาตามเกณฑ์ สคบ.", type="primary")

    if run:
        text = ""
        if pdf is not None:
            try:
                text = read_pdf(io.BytesIO(pdf.getvalue()))
            except Exception as e:
                st.error(f"เปิดไฟล์ PDF ไม่ได้: {e}")
        else:
            text = st.session_state.get("contract_text", "")

        if not text.strip():
            st.warning("ยังไม่มีสัญญาให้ตรวจ อัปโหลดไฟล์ PDF หรือวางข้อความสัญญาก่อน (ไฟล์สแกนที่เป็นรูปภาพยังอ่านไม่ได้)")
        else:
            clauses = split_clauses(text)
            if not clauses:
                st.error("อ่านข้อความจากสัญญาไม่ได้")
            else:
                with st.spinner(f"กำลังวิเคราะห์ {len(clauses)} ข้อ..."):
                    analysed = analyze_clauses(clauses, housing=HOUSING_OPTIONS[housing_label])
                st.session_state["results"] = [dict(r, clause=c) for r, c in zip(analysed, clauses)]

    results = st.session_state.get("results")
    if results:
        st.markdown("### ผลการตรวจสอบ")
        st.markdown(stats_html(results), unsafe_allow_html=True)
        failed = sum(1 for r in results if r.get("risk") not in ("low", "medium", "high"))
        if failed:
            st.error(f"วิเคราะห์ไม่สำเร็จ {failed} ข้อ (เซิร์ฟเวอร์ล่มหรือโควตาเต็ม) กดตรวจอีกครั้ง ข้อที่สำเร็จแล้วไม่เสียโควตาซ้ำ")
        by_risk = st.checkbox("เรียงข้อที่เสี่ยงสูงไว้บนสุด", value=True)
        st.markdown("".join(card_html(r) for r in sort_results(results, by_risk)), unsafe_allow_html=True)
        st.markdown('<div class="lc-help"><div><b>📞 ถูกเอาเปรียบ? ปรึกษา สคบ.</b><div>สายด่วนร้องเรียนผู้บริโภค ให้คำปรึกษาและรับเรื่องร้องเรียนฟรี</div></div>'
                    '<a class="lc-call" href="tel:1166">โทร 1166</a></div>', unsafe_allow_html=True)

# =====================================================================
# แท็บ 2: เครื่องคำนวณ
# =====================================================================
with tab_calc:
    with st.container(border=True):
        st.subheader("🧮 เครื่องคำนวณส่วนต่างค่าน้ำ-ค่าไฟ และเงินประกัน")
        st.caption("เปรียบเทียบอัตราที่หอพักเรียกเก็บจริง กับอัตราทางการ ใส่อัตราทางการตามบิลของการไฟฟ้าและการประปา "
                   "(ค่าตั้งต้นมาจากแบบร่าง อัตราจริงเปลี่ยนได้ ควรตรวจกับบิลปัจจุบัน)")

        c1, c2, c3 = st.columns(3)
        rent = c1.number_input("ค่าเช่าห้องพัก (บาท/เดือน)", min_value=0.0, value=4500.0, step=100.0)
        deposit = c2.number_input("เงินประกันความเสียหายที่จ่าย (บาท)", min_value=0.0, value=9000.0, step=100.0)
        advance = c3.number_input("ค่าเช่าล่วงหน้าที่จ่าย (บาท)", min_value=0.0, value=0.0, step=100.0)

        a1, a2, a3, a4 = st.columns(4)
        e_rate = a1.number_input("ค่าไฟที่หอพักคิด (บาท/หน่วย)", min_value=0.0, value=8.0, step=0.5)
        e_units = a2.number_input("หน่วยไฟที่ใช้ต่อเดือน", min_value=0.0, value=150.0, step=10.0)
        w_rate = a3.number_input("ค่าน้ำที่หอพักคิด (บาท/หน่วย)", min_value=0.0, value=20.0, step=0.5)
        w_units = a4.number_input("หน่วยน้ำที่ใช้ต่อเดือน", min_value=0.0, value=6.0, step=1.0)

        b1, b2, b3 = st.columns(3)
        e_official = b1.number_input("อัตราค่าไฟทางการ (บาท/หน่วย)", min_value=0.0, value=4.20, step=0.1)
        w_official = b2.number_input("อัตราค่าน้ำทางการ (บาท/หน่วย)", min_value=0.0, value=12.50, step=0.5)
        months = b3.number_input("ระยะสัญญา (เดือน)", min_value=1, value=12, step=1)

        res = calc_difference(rent, deposit, advance, e_rate, e_units, e_official, w_rate, w_units, w_official, int(months))
        st.markdown(calc_html(res, int(months), e_official, w_official), unsafe_allow_html=True)

# =====================================================================
# แท็บ 3: เกณฑ์ สคบ.
# =====================================================================
with tab_rules:
    st.markdown('<div class="lc-help"><div><b>📞 ถูกหอพักเอาเปรียบ? ปรึกษา สคบ.</b><div>สายด่วนร้องเรียนผู้บริโภค ให้คำปรึกษาและรับเรื่องร้องเรียนฟรี</div></div>'
                '<a class="lc-call" href="tel:1166">โทร 1166</a></div>', unsafe_allow_html=True)

    with st.container(border=True):
        st.subheader("🚫 10 ข้อห้ามของผู้ให้เช่า ตามประกาศคณะกรรมการว่าด้วยสัญญา พ.ศ. 2568")
        st.markdown(
            '<div class="lc-note">ขอบเขต: ใช้กับผู้ให้เช่าที่มีที่พักให้เช่าตั้งแต่ 3 หน่วยขึ้นไป (เช่น อพาร์ตเมนต์ ห้องเช่า) '
            "ไม่รวมหอพักที่จดทะเบียนตามกฎหมายหอพักและโรงแรม ข้อสัญญาที่ฝ่าฝืนถือว่าไม่มีผลบังคับ "
            "ผู้ประกอบธุรกิจที่ฝ่าฝืนมีโทษจำคุกไม่เกิน 1 ปี ปรับไม่เกิน 200,000 บาท หรือทั้งจำทั้งปรับ ตาม พ.ร.บ.คุ้มครองผู้บริโภค</div>",
            unsafe_allow_html=True,
        )
        st.markdown("".join(
            f'<div class="lc-rule"><span class="tag ban">ข้อห้าม</span><div><b>{i}. {esc(t)}</b>' + (f"<div>{esc(d)}</div>" if d else "") + "</div></div>"
            for i, (t, d) in enumerate(PROHIBITIONS, 1)
        ), unsafe_allow_html=True)

        st.subheader("✅ สิทธิของผู้เช่า")
        st.markdown("".join(
            f'<div class="lc-rule"><span class="tag right">สิทธิผู้เช่า</span><div><b>{i}. {esc(t)}</b><div>{esc(d)}</div></div></div>'
            for i, (t, d) in enumerate(RIGHTS, 1)
        ), unsafe_allow_html=True)

    with st.container(border=True):
        st.subheader("🏫 กรณีหอพักที่จดทะเบียนตาม พ.ร.บ.หอพัก พ.ศ. 2558")
        st.markdown("".join(f'<div class="lc-rule"><span class="tag right">หอพัก</span><div>{esc(n)}</div></div>' for n in DORM_NOTES),
                    unsafe_allow_html=True)
        st.markdown(
            '<div class="lc-note">ที่มา: ประกาศ พ.ศ. 2568 สรุปจากสำนักกฎหมายและสื่อ (แหล่งรอง) ยังไม่ได้เทียบกับตัวประกาศในราชกิจจานุเบกษา '
            "แบบสัญญาหอพักตรวจจากราชกิจจานุเบกษา 9 ก.ย. 2559 ก่อนใช้จริงควรตรวจกับเว็บ สคบ. หรือโทร 1166</div>",
            unsafe_allow_html=True,
        )

st.markdown(f'<div class="lc-foot">{esc(DISCLAIMER)}</div>', unsafe_allow_html=True)
