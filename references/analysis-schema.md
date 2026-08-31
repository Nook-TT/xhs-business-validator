# Analysis JSON schema

Create a UTF-8 JSON object with these fields before running `score.py`:

```json
{
  "idea": "business idea",
  "summary": "two or three evidence-backed sentences",
  "confidence": "high|medium|low",
  "sample": {
    "queries": ["query"],
    "notes_collected": 0,
    "notes_relevant": 0,
    "comments_reviewed": 0,
    "requests_made": 0,
    "estimated_cost_usd": 0.0,
    "limitations": ["limitation"]
  },
  "dimensions": {
    "demand_strength": {"score": 0, "rationale": "", "evidence": [{"note_id": "", "text": ""}]},
    "payment_intent": {"score": 0, "rationale": "", "evidence": []},
    "pain_clarity": {"score": 0, "rationale": "", "evidence": []},
    "differentiation_space": {"score": 0, "rationale": "", "evidence": []},
    "product_feasibility": {"score": 0, "rationale": "", "evidence": []},
    "acquisition_and_compliance": {"score": 0, "rationale": "", "evidence": []}
  },
  "supporting_signals": [{"title": "", "detail": "", "note_id": ""}],
  "opposing_signals": [{"title": "", "detail": "", "note_id": ""}],
  "positioning": {"recommendation": "", "target_user": "", "wedge": ""},
  "experiment": {
    "duration": "",
    "steps": [""],
    "pass_thresholds": [""],
    "stop_thresholds": [""]
  }
}
```

`score.py` adds `weighted_raw_score`, `final_score`, `verdict`, and `scored_at`. Keep quotes short and avoid personal identifiers. A note ID provides auditability without reproducing an entire post.

