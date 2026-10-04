import streamlit as st
from extract import split_clauses
from analyze import analyze_clauses
from config import DISCLAIMER
from overview import summarize_contract
from vision import load_contract
 
st.set_page_config(page_title="LeaseCheck", page_icon="🏠")
st.title("LeaseCheck 🏠")
st.caption("ผู้ช่วยอ่านสัญญาเช่าหอพัก")
st.info("ก่อนอัปโหลด ควรปิดชื่อ ที่อยู่ และข้อมูลส่วนตัวในสัญญา ระบบปิดให้เฉพาะเลขบัตร เบอร์โทร และอีเมล")
 
ICON = {"low": "🟢", "medium": "🟡", "high": "🔴", "unknown": "⚪"}
ORDER = ["high", "medium", "unknown", "low"]
 
f = st.file_uploader(
    "อัปโหลดสัญญา (PDF หรือรูปถ่าย เรียงไฟล์ตามหน้า)",
    type=["pdf", "png", "jpg", "jpeg"],
    accept_multiple_files=True,
)
 
if f and st.button("ตรวจสัญญา", type="primary"):
    try:
        with st.spinner("กำลังอ่านไฟล์..."):
            text = load_contract(f)
    except Exception as e:
        st.error(f"อ่านไฟล์ไม่สำเร็จ: {e}")
        st.stop()
    clauses = split_clauses(text)
 
    if not clauses:
        st.error("อ่านข้อความจากไฟล์ไม่ได้ (อาจเป็นไฟล์สแกน) ลองไฟล์ PDF ที่เลือกข้อความได้")
        st.stop()
 
    bar = st.progress(0.0, text=f"กำลังวิเคราะห์ {len(clauses)} ข้อ...")
 
    def on_progress(done, total):
        bar.progress(done / total if total else 1.0, text=f"วิเคราะห์แล้ว {done}/{total} ข้อ")
 
    analysed = analyze_clauses(clauses, progress=on_progress)
    bar.empty()
    with st.spinner("กำลังสรุปภาพรวมสัญญา..."):
        st.session_state["overview"] = summarize_contract(clauses)
 
results = st.session_state.get("results")
 
if results:
    ov = st.session_state.get("overview")
    if ov:
        st.subheader("📋 สรุปภาพรวม")
        a, b = st.columns(2)
        a.metric("ค่าเช่า", ov["rent"])
        b.metric("ระยะเวลา", ov["duration"])
        st.write(f"**เงินประกัน:** {ov['deposit']}")
        st.write(f"**สาธารณูปโภค:** {ov['utilities']}")
        st.write(f"**ค่าปรับ/ยกเลิก:** {ov['penalty']}")
        if ov["missing"]:
            st.warning("**สัญญาไม่ได้พูดถึง:** " + " • ".join(ov["missing"]))

    high = sum(1 for r in results if r.get("risk") == "high")
    med = sum(1 for r in results if r.get("risk") == "medium")
    c1, c2, c3 = st.columns(3)
    c1.metric("ทั้งหมด", f"{len(results)} ข้อ")
    c2.metric("🔴 เสี่ยงสูง", high)
    c3.metric("🟡 ควรระวัง", med)
    
    failed = sum(1 for r in results if r.get("risk") == "unknown")
    if failed:
        st.error(f"วิเคราะห์ไม่สำเร็จ {failed} ข้อ (เซิร์ฟเวอร์ล่มหรือโควตาเต็ม) กดตรวจใหม่อีกครั้ง")
 
    def sort_key(x):
        return ORDER.index(x["risk"]) if x.get("risk") in ORDER else 1
 
    for r in sorted(results, key=sort_key):
        with st.expander(f"{ICON.get(r.get('risk'), '⚪')} {r['clause'][:50]}..."):
            st.write(r.get("summary", ""))
            for i in r.get("issues", []):
                st.warning(i)
            if r.get("suggestion"):
                st.info(r["suggestion"])
            if r.get("law_ref"):
                st.caption("อ้างอิง: " + ", ".join(r["law_ref"]))
 
st.divider()
st.caption(DISCLAIMER)