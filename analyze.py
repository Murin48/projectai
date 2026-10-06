import hashlib
import json
import os
import re
import time
from google import genai
from google.genai import types
from config import MODEL, REQUEST_DELAY, LAW_FILE, BASE_DIR  # config โหลด .env ให้ด้วย
from privacy import redact

client = genai.Client()  # อ่านคีย์จากตัวแปร GEMINI_API_KEY

BASE_SYSTEM = """คุณคือทนายความผู้เชี่ยวชาญด้านกฎหมายคุ้มครองผู้บริโภคและกฎหมายอสังหาริมทรัพย์ในประเทศไทย หน้าที่ของคุณคือวิเคราะห์ข้อความหรือรูปภาพสัญญาเช่าหอพัก/คอนโด เพื่อตรวจสอบข้อสัญญาที่ไม่เป็นธรรม ขัดต่อกฎหมาย หรือฝ่าฝืนประกาศ สคบ.
วิเคราะห์ข้อสัญญาที่ได้รับ แล้วตอบเป็น JSON เท่านั้น ตามรูปแบบนี้:
{
  "summary": "สรุปข้อนี้ด้วยภาษาง่าย ๆ 1-2 ประโยค",
  "risk": "low | medium | high",
  "issues": ["จุดที่ควรระวังหรืออาจไม่เป็นธรรม"],
  "law_ref": ["กฎหมายหรือมาตราที่เกี่ยวข้อง ถ้าไม่แน่ใจให้ใส่ []"],
  "suggestion": "สิ่งที่ผู้เช่าควรถามหรือขอแก้"
}
กฎสำคัญ:
- ห้ามอ้างมาตราที่ไม่แน่ใจ ถ้าข้อมูลไม่พอให้บอกว่าไม่แน่ใจ
- อ้างอิงเฉพาะกฎหมายและตัวเลขที่ปรากฏใน "ข้อมูลกฎหมายอ้างอิง" ด้านล่างเท่านั้น ห้ามอ้างเลขมาตรา ชื่อประกาศ ปี พ.ศ. จำนวนเดือน หรือจำนวนวัน จากความจำของตัวเอง
- ถ้าประเด็นใดไม่มีในข้อมูลอ้างอิง ให้ปล่อย law_ref เป็น [] และแนะนำให้ตรวจกับ สคบ. สายด่วน 1166
- ใน issues ให้ระบุเสมอว่าข้อสังเกตทางกฎหมายใช้ได้กับที่พักประเภทใด (หอพักจดทะเบียน หรืออพาร์ตเมนต์/ห้องเช่าทั่วไป) เพราะสัญญาไม่ได้บอกประเภทที่พัก
- ประเด็นที่ต้องตรวจเป็นพิเศษ: เงินประกัน การคืนเงินประกัน ค่าปรับ/ค่าเสียหาย
  การเพิ่มค่าเช่า ค่าน้ำค่าไฟ การเข้าห้องโดยไม่แจ้ง การยกเลิกสัญญา"""


def build_system() -> str:
    system = BASE_SYSTEM
    if LAW_FILE.exists():
        law = LAW_FILE.read_text(encoding="utf-8").strip()
        if law:
            system += "\n\n## ข้อมูลกฎหมายอ้างอิง\n" + law
            print(f"📚 โหลดไฟล์กฎหมายแล้ว: {LAW_FILE} ({len(law)} ตัวอักษร)")
        else:
            print(f"⚠️  ไฟล์กฎหมายว่างเปล่า: {LAW_FILE}")
    else:
        print(f"⚠️  ไม่พบไฟล์กฎหมาย: {LAW_FILE}")
    return system


SYSTEM = build_system()
FALLBACK = {
    "summary": "วิเคราะห์ข้อนี้ไม่สำเร็จ (เซิร์ฟเวอร์ไม่ตอบหรือโควตาเต็ม)",
    "risk": "unknown",
    "issues": [],
    "law_ref": [],
    "suggestion": "รันใหม่อีกครั้ง หรืออ่านข้อนี้ด้วยตัวเอง",
}

# โมเดลสำรองที่ลองสลับใช้เมื่อโมเดลหลักล่ม ตั้งได้ใน .env เช่น GEMINI_FALLBACKS=gemini-3.5-flash,gemini-3.5-flash-lite
FALLBACK_MODELS = [m.strip() for m in os.getenv("GEMINI_FALLBACKS", "gemini-3.5-flash,gemini-3.5-flash-lite").split(",") if m.strip()]
MODELS = [MODEL] + [m for m in FALLBACK_MODELS if m != MODEL]


CLAUSES_PER_REQUEST = int(os.getenv("CLAUSES_PER_REQUEST", "8"))
CACHE_FILE = BASE_DIR / ".cache" / "analysis.json"
SYSTEM_HASH = hashlib.sha256(SYSTEM.encode("utf-8")).hexdigest()[:16]

BATCH_NOTE = """รูปแบบการทำงานแบบหลายข้อ: ข้อมูลที่ได้รับเป็น JSON array ของ {"no": เลขลำดับ, "clause": ข้อความข้อสัญญา}
ตอบให้กระชับ: summary 1 ประโยค, issues ไม่เกิน 3 ข้อ ข้อละไม่เกิน 2 ประโยค, suggestion ไม่เกิน 3 ประโยค
ให้วิเคราะห์ทุกข้อ แล้วตอบเป็น JSON array เท่านั้น แต่ละรายการมีฟิลด์ "no" (ใช้เลขเดิม) ตามด้วย summary, risk, issues, law_ref, suggestion ตามรูปแบบข้างต้น ให้ครบทุกข้อตามลำดับเดิม"""
BATCH_SYSTEM = SYSTEM + "\n\n" + BATCH_NOTE

QUOTA_FILE = BASE_DIR / ".cache" / "quota.json"


def _load_quota() -> dict:
    """โมเดลที่โควตาหมดและเวลาที่คาดว่าจะรีเซ็ต (จำข้ามการรัน จะได้ไม่เสียคำขอลองโมเดลที่เต็มซ้ำ)"""
    try:
        d = json.loads(QUOTA_FILE.read_text(encoding="utf-8"))
        now = time.time()
        return {m: t for m, t in d.items() if t > now}
    except Exception:
        return {}


_exhausted_until: dict = _load_quota()
_exhausted: set[str] = set(_exhausted_until)  # โมเดลที่ข้ามในรอบนี้


def _mark_exhausted(model: str, seconds=None) -> None:
    _exhausted.add(model)
    secs = seconds if seconds and seconds > 0 else 6 * 3600
    _exhausted_until[model] = time.time() + min(secs, 24 * 3600)
    try:
        QUOTA_FILE.parent.mkdir(exist_ok=True)
        QUOTA_FILE.write_text(json.dumps(_exhausted_until), encoding="utf-8")
    except Exception:
        pass


def _hours_left() -> float:
    ts = [t for m, t in _exhausted_until.items() if m in MODELS]
    return max(0.0, (min(ts) - time.time()) / 3600) if ts else 0.0


if _exhausted:
    left = ", ".join(f"{m} (อีก ~{(t - time.time()) / 3600:.1f} ชม.)" for m, t in _exhausted_until.items() if m in MODELS)
    if left:
        print(f"⏭️  ข้ามโมเดลที่โควตาหมดไปแล้ว: {left}")


class QuotaExhausted(Exception):
    pass


def _retry_seconds(msg: str):
    """อ่านเวลารอที่ Google แจ้ง เช่น 'retry in 7h59m12.6s' หรือ 'retry in 38s' คืนค่าเป็นวินาที (ไม่พบคืน None)"""
    m = re.search(r"retry in ((?:\d+h)?(?:\d+m)?[\d.]*s?)", msg)
    if not m or not m.group(1):
        m = re.search(r"retryDelay['\"]?:\s*['\"]([\dhms.]+)['\"]", msg)
        if not m:
            return None
    t = m.group(1)
    h = re.search(r"(\d+)h", t)
    mi = re.search(r"(\d+)m", t)
    sec = re.search(r"([\d.]+)s", t)
    total = (int(h.group(1)) * 3600 if h else 0) + (int(mi.group(1)) * 60 if mi else 0) + (float(sec.group(1)) if sec else 0)
    return int(total) if total else None


# งบ "การคิด" ของโมเดล ยิ่งน้อยยิ่งเร็ว (0 = ปิด) ตั้งใน .env ด้วย GEMINI_THINKING_BUDGET หรือใส่ default เพื่อใช้ค่าของ Google
THINKING_BUDGET = os.getenv("GEMINI_THINKING_BUDGET", "0").strip()
_thinking_enabled = THINKING_BUDGET not in ("", "default")


def _make_config(system: str):
    kwargs = dict(system_instruction=system, response_mime_type="application/json")
    if _thinking_enabled:
        try:
            kwargs["thinking_config"] = types.ThinkingConfig(thinking_budget=int(THINKING_BUDGET))
        except Exception:
            pass
    return types.GenerateContentConfig(**kwargs)


def _call(system: str, contents: str, retries: int = 6):
    global _thinking_enabled
    for attempt in range(retries):
        live = [m for m in MODELS if m not in _exhausted]
        if not live:
            raise QuotaExhausted(
                f"⛔ โควตาของทุกโมเดลหมดแล้ว (รายวัน) โมเดลที่เร็วที่สุดน่าจะกลับมาใช้ได้อีก ~{_hours_left():.1f} ชั่วโมง "
                "หรือใช้ API key ของโปรเจกต์อื่น/เปิดบิลลิ่ง ผลที่วิเคราะห์เสร็จแล้วถูกเก็บไว้ รันใหม่ภายหลังจะไม่เสียโควตากับข้อเดิม"
            )
        model = live[attempt % len(live)]
        try:
            t0 = time.time()
            resp = client.models.generate_content(model=model, contents=contents, config=_make_config(system))
            text = (resp.text or "").replace("```json", "").replace("```", "").strip()
            data = json.loads(text)
            print(f"⏱️  {model} ตอบใน {time.time() - t0:.1f} วินาที")
            return data
        except json.JSONDecodeError:
            print(f"⚠️  {model} ตอบกลับมาไม่ใช่ JSON ลองใหม่...")
        except Exception as e:
            code = getattr(e, "code", None)
            msg = str(e)
            print(f"⚠️  {model} ผิดพลาด (รหัส {code}): {msg[:600]}")
            low = msg.lower()
            if code == 400 and "thinking" in low and _thinking_enabled:
                print("ℹ️  โมเดลนี้ไม่รับการตั้งค่า thinking ปิดการตั้งค่านี้แล้วลองใหม่")
                _thinking_enabled = False
                continue
            if code == 429:
                hint = _retry_seconds(msg)
                if "perday" in low or "per day" in low or "limit: 0" in low or "quotavalue': '0'" in low or (hint is not None and hint > 120):
                    print(f"⛔ {model} โควตารายวันหมด หรือไม่มีโควตาฟรี (Google แจ้งให้รอ {hint or '?'} วินาที) ข้ามไปใช้โมเดลอื่น")
                    _mark_exhausted(model, hint)
                    continue
                wait = min((hint or 30) + 2, 90)
                print(f"⏳ ชนโควตาต่อนาที รอ {wait} วินาที...")
                time.sleep(wait)
                continue
            if code == 404:
                print(f"⛔ ใช้โมเดล {model} ไม่ได้ ข้ามไป")
                _mark_exhausted(model, 86400)
                continue
            if code is not None and code < 500:
                continue
        time.sleep(5 * (attempt + 1))
    raise RuntimeError("เรียก API ไม่สำเร็จหลายครั้งติดต่อกัน")


def _key(clause: str, housing: str = "unknown") -> str:
    return hashlib.sha256((SYSTEM_HASH + housing + clause).encode("utf-8")).hexdigest()


def _load_cache() -> dict:
    try:
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_cache(cache: dict) -> None:
    CACHE_FILE.parent.mkdir(exist_ok=True)
    CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")


def _valid(item) -> bool:
    return isinstance(item, dict) and item.get("risk") in ("low", "medium", "high") and "summary" in item


HOUSING_NOTES = {
    "unknown": "ผู้ใช้ไม่ทราบประเภทที่พัก ให้ระบุเงื่อนไขสั้น ๆ ว่าข้อสังเกตทางกฎหมายใช้ได้เมื่อที่พักเป็นประเภทใด (อพาร์ตเมนต์/ห้องเช่าตามส่วน A หรือหอพักจดทะเบียนตามส่วน B) อย่าเขียนซ้ำยาว",
    "apartment": "ผู้ใช้ระบุว่าเป็นอพาร์ตเมนต์หรือห้องเช่าทั่วไป (ไม่ใช่หอพักจดทะเบียน) ให้ใช้ส่วน A เป็นหลัก และบอกเงื่อนไขสั้น ๆ ว่าใช้ได้เมื่อผู้ให้เช่ามีที่พักให้เช่าตั้งแต่ 3 หน่วยขึ้นไป",
    "dorm": "ผู้ใช้ระบุว่าเป็นหอพักที่จดทะเบียนตามกฎหมายหอพัก ให้ใช้ส่วน B เป็นหลัก ประกาศส่วน A ไม่ใช้บังคับโดยตรงกับหอพักจดทะเบียน ให้ใช้เป็นเกณฑ์เปรียบเทียบเท่านั้น และบอกผู้ใช้ตรงๆ ว่าเพดานของหอพักจดทะเบียนยังไม่ได้ตรวจสอบ",
}


def analyze_clauses(clauses: list[str], progress=None, housing: str = "unknown") -> list[dict]:
    """วิเคราะห์ทั้งฉบับโดยส่งหลายข้อต่อคำขอ (ประหยัดโควตา) และจำผลที่ทำเสร็จแล้วไว้ในโฟลเดอร์ .cache"""
    batch_system = BATCH_SYSTEM + "\n\n## ประเภทที่พักที่ผู้ใช้ระบุ\n" + HOUSING_NOTES.get(housing, HOUSING_NOTES["unknown"])
    cache = _load_cache()
    results: list = [None] * len(clauses)
    todo = []
    for i, c in enumerate(clauses):
        hit = cache.get(_key(c, housing))
        if hit:
            results[i] = hit
        else:
            todo.append(i)
    if len(todo) < len(clauses):
        print(f"♻️  ใช้ผลที่เคยวิเคราะห์แล้ว {len(clauses) - len(todo)} ข้อ ไม่เสียโควตา")

    for start in range(0, len(todo), CLAUSES_PER_REQUEST):
        idxs = todo[start:start + CLAUSES_PER_REQUEST]
        payload = [{"no": n + 1, "clause": redact(clauses[n])} for n in idxs]
        print(f"กำลังวิเคราะห์ข้อ {idxs[0] + 1}-{idxs[-1] + 1} จาก {len(clauses)} ...")
        try:
            data = _call(batch_system, json.dumps(payload, ensure_ascii=False))
        except QuotaExhausted as e:
            print(e)
            break
        except Exception as e:
            print(f"⚠️  ชุดข้อ {idxs[0] + 1}-{idxs[-1] + 1} วิเคราะห์ไม่สำเร็จ: {e}")
            continue
        by_no = {}
        for item in data if isinstance(data, list) else []:
            try:
                by_no[int(item["no"])] = item
            except Exception:
                pass
        for n in idxs:
            item = by_no.get(n + 1)
            if _valid(item):
                item = {k: v for k, v in item.items() if k != "no"}
                results[n] = item
                cache[_key(clauses[n], housing)] = item
        _save_cache(cache)
        if start + CLAUSES_PER_REQUEST < len(todo):
            time.sleep(REQUEST_DELAY)  # เว้นช่วงระหว่างชุด กันชนโควตาต่อนาที
        if progress:
            progress(min(start + CLAUSES_PER_REQUEST, len(todo)), len(todo))

    return [r if r is not None else dict(FALLBACK) for r in results]


def analyze_clause(clause: str) -> dict:
    """วิเคราะห์ทีละข้อ (ใช้ในชุดทดสอบ)"""
    try:
        data = _call(SYSTEM, redact(clause))
        return data if _valid(data) else dict(FALLBACK)
    except Exception as e:
        print(e)
        return dict(FALLBACK)


if __name__ == "__main__":
    demo = "ข้อ 5 ผู้เช่าไม่มีสิทธิ์ขอคืนเงินประกันในทุกกรณี หากย้ายออกก่อนครบสัญญา"
    print(json.dumps(analyze_clause(demo), ensure_ascii=False, indent=2))
