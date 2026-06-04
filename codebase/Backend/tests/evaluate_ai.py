import json
import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app


CASES_PATH = Path(__file__).with_name("eval_cases.json")


def main() -> None:
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    session_id = "eval-session"
    passed = 0
    rows = []

    with TestClient(app) as client:
        for index, case in enumerate(cases, start=1):
            response = client.post(
                "/api/chat",
                json={"message": case["message"], "session_id": session_id, "user_context": {}},
            )
            data = response.json()
            ok = (
                response.status_code == 200
                and data["intent"] == case["expected_intent"]
                and data["action"] == case["expected_action"]
            )
            passed += int(ok)
            rows.append(
                {
                    "case": index,
                    "ok": ok,
                    "message": case["message"],
                    "expected": f"{case['expected_intent']} / {case['expected_action']}",
                    "actual": f"{data.get('intent')} / {data.get('action')}",
                }
            )

    for row in rows:
        status = "PASS" if row["ok"] else "FAIL"
        print(f"{status} #{row['case']}: {row['message']}")
        if not row["ok"]:
            print(f"  expected: {row['expected']}")
            print(f"  actual:   {row['actual']}")

    print(f"\nScore: {passed}/{len(cases)} = {passed / len(cases):.0%}")


if __name__ == "__main__":
    main()

