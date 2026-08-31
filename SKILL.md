---
name: xhs-business-validator
description: Validate a business idea with public Xiaohongshu notes and comments, then produce an evidence-backed market score and HTML report. Use when a user asks for 小红书调研、市场验证、需求验证、竞品洞察或验证一个商业想法. Do not use for general business advice that does not require Xiaohongshu evidence.
metadata:
  short-description: 用小红书公开内容验证商业想法
---

# Xiaohongshu Business Validator

Turn a business idea into a bounded Xiaohongshu research run, an auditable score, and a self-contained HTML report. The skill is portable: code and rules live here; credentials and outputs live in the user's current workspace.

At runtime, resolve `<skill-root>` to the directory containing this `SKILL.md`. Resolve every bundled script, reference, and asset relative to `<skill-root>`, never relative to the user's workspace. Use an available Python 3 interpreter (`python3`, `python`, or the host application's bundled Python runtime).

## Before collection

1. Work from the user's current workspace. Never write runtime credentials or outputs into this skill directory.
2. Read `TIKHUB_TOKEN` from the workspace `.env`. If missing, ask the user for it, write it locally, and ensure `.env` is ignored by Git. Never echo the full token.
3. Default to `standard` mode unless the user explicitly asks for a quick or deep study:

| Mode | Search requests | Comment requests | Default cap |
|---|---:|---:|---:|
| `quick` | 2 | 3 | USD 0.05 |
| `standard` | 4 | 5 | USD 0.10 |
| `deep` | 6 | 10 | USD 0.20 |

These caps assume USD 0.01 per successful Xiaohongshu request. If current pricing or the planned call count exceeds the cap, tell the user before spending more. Failed calls do not authorize retries without a bounded stopping condition.

## Plan the search

Translate the idea into 2–6 discriminating queries that cover direct demand, buyer pain-language, substitutes or named competitors, and location terms for a local business.

Avoid broad terms that attract unrelated audiences. For local ideas, keep national category demand separate from local availability and local purchase intent. Before ranking engagement, exclude irrelevant results and record why they were excluded.

## Collect

Read [references/tikhub-api.md](references/tikhub-api.md) when calling or troubleshooting TikHub. Run:

```text
<python3> <skill-root>/scripts/collect.py --idea "<idea>" --mode standard --workspace "<workspace>" --keywords "<q1>" "<q2>" "<q3>" "<q4>"
```

The script reads the workspace `.env`, applies the request cap, respects a one-second delay, reuses the 24-hour workspace cache, normalizes results, and redacts secrets from saved errors. It writes a run folder under `data/xhs-validator/` and prints its path.

If the API returns 401, stop and ask for a new token. If it returns 402, explain whether the endpoint rejects free credit or the paid balance is insufficient; do not claim all visible credit is usable. Never show raw response headers.

## Analyze and score

Read [references/scoring-rubric.md](references/scoring-rubric.md). Use the normalized notes and comments to create `<run>/analysis.json` following [references/analysis-schema.md](references/analysis-schema.md).

Separate attention, pain, intent, adoption, and competition. Do not treat high engagement as purchase intent. Quote or paraphrase evidence with a note ID. Mark sponsored-looking content and generic creator replies as lower confidence. State sample limitations and avoid generalizing Xiaohongshu users to the entire market.

Run the deterministic score calculator:

```text
<python3> <skill-root>/scripts/score.py <run>/analysis.json
```

The calculator validates evidence counts, applies fixed weights, and writes the final score back to the file. Do not manually override it. If evidence is sparse, lower `confidence` rather than inventing certainty.

## Report

Generate the self-contained report in the workspace:

```text
<python3> <skill-root>/scripts/render_report.py <run>/analysis.json --output <workspace>/reports/<safe-name>.html
```

The final response should lead with the score and decision, then give the strongest supporting and opposing evidence, a narrow positioning recommendation, and a low-cost validation experiment with pass/fail thresholds. Link the report. Mention the request count and estimated API spend.

## Security and distribution invariants

- Never store `.env`, tokens, raw authorization headers, user research data, caches, or generated reports inside the skill folder or distribution archive.
- Sanitize error bodies before saving or displaying them.
- The optional external LLM path is intentionally omitted: analyze with the active agent unless the user explicitly requests another model or service.
- Keep runtime dependencies to the Python standard library so the skill remains portable.
- Codex may use `agents/openai.yaml`; WorkBuddy may ignore it. No core behavior depends on that file.

