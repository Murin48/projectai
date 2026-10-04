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

BASE_SYSTEM = """คุณคือทนายความผู้เชี่ยวชาญด้านกฎหมายคุ้มครองผู้บริโภคและกฎหมายอสังหาริมทรัพย์ในประเทศไทย หน้าที่ของคุณคือวิเคราะห์ข้อความหรือรูปภาพสัญญาเช่าหอพัก/คอนโด เพื่อตรวจสอบข้อสัญญาที่ไม่เป็นธรรม ขัดต่อกฎหมาย หรือฝ่าฝืนประกาศ สคบ.  จัดรูปแบบคำตอบที่ได้รับ แล้วตอบเป็น JSON เท่านั้น ตามรูปแบบนี้:
{
  "summary": "สรุปข้อนี้ด้วยภาษาง่าย ๆ 1-2 ประโยค",
  "risk": "low | medium | high",
  "issues": ["จุดที่ควรระวังหรืออาจไม่เป็นธรรม"],
  "law_ref": ["กฎหมายหรือมาตราที่เกี่ยวข้อง ถ้าไม่แน่ใจให้ใส่ []"],
  "suggestion": "สิ่งที่ผู้เช่าควรถามหรือขอแก้"
}
กฎสำคัญ:
- ประเมินเฉพาะข้อความที่เขียนไว้ในข้อนั้น ห้ามสมมติข้อเท็จจริงที่ไม่ได้เขียน
- เรื่องที่สัญญาไม่ได้พูดถึง ไม่นับเป็นความเสี่ยงของข้อนี้ (มีส่วนสรุปภาพรวมแยกไว้แล้ว)
- ถ้าข้อสัญญาสอดคล้องกับกฎหมายอ้างอิง หรือให้ประโยชน์ผู้เช่ามากกว่ากฎหมาย ให้ risk เป็น low
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

# กำหนดโมเดลสำรองสำหรับสลับใช้งาน
FALLBACK_MODELS = [m.strip() for m in os.getenv("GEMINI_FALLBACKS", "gemini-3.5-flash,gemini-2.5-flash-lite,gemini-flash-latest").split(",") if m.strip()]
MODELS = [MODEL] + [m for m in FALLBACK_MODELS if m != MODEL]


CLAUSES_PER_REQUEST = int(os.getenv("CLAUSES_PER_REQUEST", "8"))
CACHE_FILE = BASE_DIR / ".cache" / "analysis.json"
SYSTEM_HASH = hashlib.sha256(SYSTEM.encode("utf-8")).hexdigest()[:16]

BATCH_NOTE = """รูปแบบการทำงานแบบหลายข้อ: ข้อมูลที่ได้รับเป็น JSON array ของ {"no": เลขลำดับ, "clause": ข้อความข้อสัญญา}
ให้วิเคราะห์ทุกข้อ แล้วตอบเป็น JSON array เท่านั้น แต่ละรายการมีฟิลด์ "no" (ใช้เลขเดิม) ตามด้วย summary, risk, issues, law_ref, suggestion ตามรูปแบบข้างต้น ให้ครบทุกข้อตามลำดับเดิม"""
BATCH_SYSTEM = SYSTEM + "\n\n" + BATCH_NOTE

_exhausted: set[str] = set()  # โมเดลที่โควตาหมดหรือใช้ไม่ได้ในรอบนี้


class QuotaExhausted(Exception):
    pass


def _retry_delay(msg: str) -> int:
    m = re.search(r"retry in ([\d.]+)s", msg) or re.search(r"retryDelay['\"]?:\s*['\"](\d+)s", msg)
    return min(int(float(m.group(1))) + 2, 90) if m else 30


def _call(system: str, contents: str, retries: int = 6):
    config = types.GenerateContentConfig(
        system_instruction=system,
        response_mime_type="application/json",
    )
    for attempt in range(retries):
        live = [m for m in MODELS if m not in _exhausted]
        if not live:
            raise QuotaExhausted(
                "⛔ โควตาของทุกโมเดลหมดแล้ว (รายวัน) ให้รอให้โควตารีเซ็ต หรือใช้ API key ของโปรเจกต์อื่น/เปิดบิลลิ่ง "
                "ผลที่วิเคราะห์เสร็จแล้วถูกเก็บไว้ รันใหม่ภายหลังจะไม่เสียโควตากับข้อเดิม"
            )
        model = live[attempt % len(live)]
        try:
            resp = client.models.generate_content(
                model=model,
                contents=contents,
                config=config
            )
            
            text = (getattr(resp, "text", "") or "").replace("```json", "").replace("```", "").strip()
            
            start_idx = text.find("{")
            end_idx = text.rfind("}")
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                text = text[start_idx:end_idx + 1]
                
            data = json.loads(text)
            time.sleep(REQUEST_DELAY)  # กันชนโควตาต่อนาที
            return data
        except json.JSONDecodeError:
            print(f"⚠️  {model} ตอบกลับมาไม่ใช่ JSON ลองใหม่...")
        except Exception as e:
            code = getattr(e, "code", None)
            msg = str(e)
            print(f"⚠️  {model} ผิดพลาด (รหัส {code}): {msg[:600]}")
            low = msg.lower()
            if code == 429:
                if "perday" in low or "per day" in low or "limit: 0" in low or "quotavalue': '0'" in low:
                    print(f"⛔ {model} โควตารายวันหมด หรือไม่มีโควตาฟรี ข้ามไปใช้โมเดลอื่น")
                    _exhausted.add(model)
                    continue
                wait = _retry_delay(msg)
                print(f"⏳ ชนโควตาต่อนาที รอ {wait} วินาที...")
                time.sleep(wait)
                continue
            if code == 404:
                print(f"⛔ ใช้โมเดล {model} ไม่ได้ ข้ามไป")
                _exhausted.add(model)
                continue
            if code is not None and code < 500:
                continue
        time.sleep(5 * (attempt + 1))
    raise RuntimeError("เรียก API ไม่สำเร็จหลายครั้งติดต่อกัน")


def _key(clause: str, ctx: str = "") -> str:
    return hashlib.sha256((SYSTEM_HASH + ctx + clause).encode("utf-8")).hexdigest()


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


def analyze_clauses(clauses: list[str], progress=None) -> list[dict]:
    cache = _load_cache()
    ctx = hashlib.sha256("\n".join(clauses).encode("utf-8")).hexdigest()[:16]
    results: list = [None] * len(clauses)
    todo = []
    for i, c in enumerate(clauses):
        hit = cache.get(_key(c, ctx))            
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
            data = _call(BATCH_SYSTEM, json.dumps(payload, ensure_ascii=False))
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
                cache[_key(clauses[n], ctx)] = item
        _save_cache(cache)
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
