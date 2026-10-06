import html

RISK_META = {
    "high": ("red", "เสี่ยงสูง", "🔴"),
    "medium": ("yellow", "ควรระวัง", "🟡"),
    "low": ("green", "เป็นธรรม", "🟢"),
    "unknown": ("gray", "วิเคราะห์ไม่สำเร็จ", "⚪"),
}
ORDER = ["high", "medium", "unknown", "low"]
CAP_MONTHS = 3  # ค่าเช่าล่วงหน้า + เงินประกัน ไม่เกิน 3 เดือน (ดู laws/law_context.md ส่วน A)


def esc(text) -> str:
    """escape ข้อความทุกอย่างจากโมเดล/ผู้ใช้ก่อนใส่ใน HTML และตัดบรรทัดว่าง (กัน markdown ตีความผิด)"""
    lines = [html.escape(str(l)) for l in str(text or "").splitlines() if l.strip()]
    return "<br>".join(lines)


def risk_of(r: dict) -> str:
    return r.get("risk") if r.get("risk") in RISK_META else "unknown"


def stats_html(results: list[dict]) -> str:
    counts = {k: 0 for k in RISK_META}
    for r in results:
        counts[risk_of(r)] += 1
    boxes = [("gray", f"{len(results)}", "ข้อทั้งหมด")]
    boxes += [("red", f"{counts['high']}", "🔴 เสี่ยงสูง"), ("yellow", f"{counts['medium']}", "🟡 ควรระวัง"), ("green", f"{counts['low']}", "🟢 เป็นธรรม")]
    if counts["unknown"]:
        boxes.append(("gray", f"{counts['unknown']}", "⚪ วิเคราะห์ไม่สำเร็จ"))
    return '<div class="lc-stats">' + "".join(
        f'<div class="lc-stat {c}"><div class="n">{n}</div><div class="t">{t}</div></div>' for c, n, t in boxes
    ) + "</div>"


def card_html(r: dict) -> str:
    risk = risk_of(r)
    cls, label, dot = RISK_META[risk]
    clause = str(r.get("clause", ""))
    first = next((l.strip() for l in clause.splitlines() if l.strip()), "")
    title = esc(first[:70] + ("..." if len(first) > 70 else ""))
    parts = [f'<details class="lc-res {cls}"' + (" open" if risk == "high" else "") + ">",
             f'<summary><span>{dot}</span><span class="ttl">{title}</span><span class="pill">{label}</span></summary>',
             '<div class="body">']
    if r.get("summary"):
        parts.append(f"<div>{esc(r['summary'])}</div>")
    issues = r.get("issues") or []
    if issues:
        parts.append('<div class="sub">ประเด็นที่ควรระวัง</div><ul>' + "".join(f"<li>{esc(i)}</li>" for i in issues) + "</ul>")
    if r.get("suggestion"):
        parts.append(f'<div class="sub">ข้อแนะนำ</div><div>{esc(r["suggestion"])}</div>')
    refs = r.get("law_ref") or []
    if refs:
        parts.append(f'<div class="ref">อ้างอิง: {esc(" / ".join(map(str, refs)))}</div>')
    if clause:
        parts.append(f'<details class="orig"><summary>ดูข้อความต้นฉบับ</summary><div class="origtxt">{esc(clause)}</div></details>')
    parts.append("</div></details>")
    return "".join(parts)


def sort_results(results: list[dict], by_risk: bool) -> list[dict]:
    if not by_risk:
        return list(results)
    return sorted(results, key=lambda r: ORDER.index(risk_of(r)))


def calc_difference(rent, deposit, advance, e_rate, e_units, e_official, w_rate, w_units, w_official, months):
    e_diff = max(0.0, (e_rate - e_official) * e_units)
    w_diff = max(0.0, (w_rate - w_official) * w_units)
    cap = CAP_MONTHS * rent
    collected = deposit + advance
    over = max(0.0, collected - cap)
    yearly_util = (e_diff + w_diff) * months
    return {
        "e_diff": e_diff, "w_diff": w_diff, "cap": cap, "collected": collected,
        "over": over, "yearly_util": yearly_util, "total": yearly_util + over,
    }


def money(x: float) -> str:
    return f"{x:,.2f}"


def calc_html(c: dict, months: int, e_official, w_official) -> str:
    over_cls = "bad" if c["over"] > 0 else "ok"
    over_txt = f"+{money(c['over'])} บาท (เกินเพดาน)" if c["over"] > 0 else "ไม่เกินเพดาน"
    big_cls = "" if c["total"] > 0 else " ok"
    return (
        '<div class="lc-calc"><h4>📊 ผลสรุปยอดเงินที่ถูกเก็บเกินจริง</h4>'
        f'<div class="lc-row"><span>ส่วนต่างค่าไฟต่อเดือน (ฐานที่ใส่ {e_official:g} บ./หน่วย):</span><span class="v {"bad" if c["e_diff"] > 0 else "ok"}">+{money(c["e_diff"])} บาท/เดือน</span></div>'
        f'<div class="lc-row"><span>ส่วนต่างค่าน้ำต่อเดือน (ฐานที่ใส่ {w_official:g} บ./หน่วย):</span><span class="v {"bad" if c["w_diff"] > 0 else "ok"}">+{money(c["w_diff"])} บาท/เดือน</span></div>'
        f'<div class="lc-row"><span>เงินประกัน + ค่าเช่าล่วงหน้า (รวม {money(c["collected"])} บาท) เทียบเพดาน {money(c["cap"])} บาท ({CAP_MONTHS} เดือน):</span><span class="v {over_cls}">{over_txt}</span></div>'
        f'<div class="lc-total"><b>รวมยอดเสียเปรียบ (น้ำ-ไฟ {months} เดือน + ส่วนเกินเงินประกัน):</b><span class="big{big_cls}">{money(c["total"])} บาท</span></div>'
        '<div class="lc-tip">💡 ส่วนที่เก็บเกินอาจขอคืนได้ หรือร้องเรียนต่อ สคบ. สายด่วน 1166 ควรเก็บบิลและสัญญาไว้เป็นหลักฐาน '
        'เพดานเงินประกันใช้เมื่อเข้าข่ายประกาศ (ผู้ให้เช่า 3 หน่วยขึ้นไป ไม่ใช่หอพักจดทะเบียน)</div></div>'
    )
