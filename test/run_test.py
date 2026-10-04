import json
import sys
from pathlib import Path
 
sys.path.insert(0, str(Path(__file__).parent.parent))
from analyze import analyze_clause
 
cases = json.loads((Path(__file__).parent / "sample_clauses.json").read_text(encoding="utf-8"))
ok = 0
for c in cases:
    r = analyze_clause(c["clause"])
    passed = r["risk"] == c["expect_risk"]
    ok += passed
    print(("✅" if passed else "❌"), c["clause"][:40], "→", r["risk"], f"(คาดหวัง {c['expect_risk']})")
print(f"\nผ่าน {ok}/{len(cases)}")