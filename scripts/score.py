#!/usr/bin/env python3
"""Validate analysis evidence and calculate a reproducible market score."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

WEIGHTS = {
    "demand_strength": 0.25,
    "payment_intent": 0.20,
    "pain_clarity": 0.15,
    "differentiation_space": 0.15,
    "product_feasibility": 0.15,
    "acquisition_and_compliance": 0.10,
}
MULTIPLIERS = {"high": 1.0, "medium": 0.95, "low": 0.85}


def verdict(score: int) -> str:
    if score >= 80:
        return "市场机会较强，值得扩大验证"
    if score >= 60:
        return "有潜力，建议进行小范围付费验证"
    if score >= 40:
        return "证据不足或风险较高，需要补充验证"
    return "当前定位市场信号较弱"


def validate(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if data.get("confidence") not in MULTIPLIERS:
        errors.append("confidence must be high, medium, or low")
    dimensions = data.get("dimensions") or {}
    for name in WEIGHTS:
        item = dimensions.get(name)
        if not isinstance(item, dict):
            errors.append(f"missing dimension: {name}")
            continue
        score = item.get("score")
        if not isinstance(score, (int, float)) or not 0 <= score <= 100:
            errors.append(f"{name}.score must be 0..100")
        evidence = item.get("evidence") or []
        valid_evidence = [e for e in evidence if isinstance(e, dict) and e.get("note_id") and e.get("text")]
        if score and score > 40 and not valid_evidence:
            errors.append(f"{name}: scores above 40 require evidence with note_id and text")
    return errors


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("analysis", type=Path)
    args = p.parse_args()
    data = json.loads(args.analysis.read_text(encoding="utf-8-sig"))
    errors = validate(data)
    if errors:
        raise SystemExit("Invalid analysis:\n- " + "\n- ".join(errors))
    raw = sum(float(data["dimensions"][name]["score"]) * weight for name, weight in WEIGHTS.items())
    final = round(raw * MULTIPLIERS[data["confidence"]])
    data["weighted_raw_score"] = round(raw, 1)
    data["final_score"] = final
    data["verdict"] = verdict(final)
    data["score_weights"] = WEIGHTS
    data["confidence_multiplier"] = MULTIPLIERS[data["confidence"]]
    data["scored_at"] = datetime.now(timezone.utc).isoformat()
    args.analysis.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"final_score": final, "verdict": data["verdict"], "analysis": str(args.analysis.resolve())}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

