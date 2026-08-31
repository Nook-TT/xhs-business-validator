#!/usr/bin/env python3
"""Collect and normalize public Xiaohongshu evidence with bounded TikHub spend."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BASE = "https://api.tikhub.io/api/v1/xiaohongshu/app_v2"
MODES = {
    "quick": {"search": 2, "comments": 3, "cap": 0.05},
    "standard": {"search": 4, "comments": 5, "cap": 0.10},
    "deep": {"search": 6, "comments": 10, "cap": 0.20},
}
PRICE_ESTIMATE = 0.01
SECRET_KEYS = ("authorization", "token", "secret", "api_key", "apikey")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--idea", required=True)
    p.add_argument("--mode", choices=MODES, default="standard")
    p.add_argument("--keywords", nargs="+", required=True)
    p.add_argument("--workspace", type=Path, default=Path.cwd())
    p.add_argument("--max-cost", type=float, default=None)
    return p.parse_args()


def read_dotenv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: "[REDACTED]" if any(s in k.lower() for s in SECRET_KEYS) else redact(v) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v) for v in value]
    if isinstance(value, str):
        value = re.sub(r"(?i)bearer\s+[A-Za-z0-9+/_=.-]+", "Bearer [REDACTED]", value)
        value = re.sub(r'(?i)(authorization|token|api[_-]?key)(["\s:=]+)[^",\s}]+', r"\1\2[REDACTED]", value)
    return value


def number(value: Any) -> int:
    if value is None:
        return 0
    text = str(value).strip().replace(",", "")
    match = re.search(r"([0-9]+(?:\.[0-9]+)?)", text)
    if not match:
        return 0
    result = float(match.group(1))
    if "万" in text:
        result *= 10000
    return int(result)


def safe_name(text: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "-", text).strip(" .-")
    return (cleaned[:48] or "idea").replace(" ", "-")


def bigrams(text: str) -> set[str]:
    compact = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "", text.lower())
    grams = {compact[i:i + 2] for i in range(max(0, len(compact) - 1))}
    grams.update(re.findall(r"[a-z0-9]{2,}", compact))
    return grams


class Client:
    def __init__(self, token: str, cache_dir: Path, max_requests: int):
        self.token = token
        self.cache_dir = cache_dir
        self.max_requests = max_requests
        self.requests_made = 0
        self.cache_hits = 0
        cache_dir.mkdir(parents=True, exist_ok=True)

    def get(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        canonical = endpoint + "?" + urllib.parse.urlencode(sorted((k, str(v)) for k, v in params.items()))
        key = hashlib.sha256(canonical.encode()).hexdigest()
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists() and time.time() - cache_file.stat().st_mtime < 86400:
            self.cache_hits += 1
            return json.loads(cache_file.read_text(encoding="utf-8"))
        if self.requests_made >= self.max_requests:
            raise RuntimeError(f"Request cap reached ({self.max_requests}); stopping before extra spend.")
        url = f"{BASE}/{endpoint}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={
            "Authorization": f"Bearer {self.token}",
            "User-Agent": "Mozilla/5.0 (Codex xhs-business-validator)",
            "Accept": "application/json",
        })
        self.requests_made += 1
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            try:
                detail = redact(json.loads(body))
                message = detail.get("detail", {}).get("message_zh") or detail.get("detail", {}).get("message") or str(detail)
            except json.JSONDecodeError:
                message = str(redact(body))[:600]
            raise RuntimeError(f"TikHub HTTP {exc.code}: {message}") from None
        safe_payload = redact(payload)
        cache_file.write_text(json.dumps(safe_payload, ensure_ascii=False), encoding="utf-8")
        time.sleep(1)
        return safe_payload


def normalize_note(item: dict[str, Any], query: str, idea_grams: set[str]) -> dict[str, Any] | None:
    note = item.get("note") or {}
    note_id = note.get("id")
    if not note_id:
        return None
    title = note.get("title") or ""
    desc = note.get("desc") or ""
    likes, collects = number(note.get("liked_count")), number(note.get("collected_count"))
    shares, comments = number(note.get("shared_count")), number(note.get("comments_count"))
    engagement = likes + 2 * collects + 3 * shares + 3 * comments
    content_grams = bigrams(f"{title} {desc}")
    overlap = len(content_grams & idea_grams)
    relevance = min(1.0, overlap / max(2, min(8, len(idea_grams))))
    return {
        "id": str(note_id), "query": query, "title": title, "description": desc,
        "author": (note.get("user") or {}).get("nickname") or "",
        "timestamp": note.get("timestamp") or note.get("time"),
        "likes": likes, "collects": collects, "shares": shares, "comments_count": comments,
        "engagement_score": engagement, "lexical_relevance": round(relevance, 3),
        "review_priority": round((0.25 + relevance) * math.log1p(engagement), 4),
    }


def main() -> int:
    args = parse_args()
    config = MODES[args.mode]
    keywords = list(dict.fromkeys(k.strip() for k in args.keywords if k.strip()))[:config["search"]]
    if not keywords:
        raise SystemExit("At least one non-empty keyword is required.")
    planned = len(keywords) + config["comments"]
    cap = config["cap"] if args.max_cost is None else args.max_cost
    if planned * PRICE_ESTIMATE > cap + 1e-9:
        raise SystemExit(f"Planned estimated cost ${planned * PRICE_ESTIMATE:.2f} exceeds cap ${cap:.2f}.")
    env = read_dotenv(args.workspace / ".env")
    token = env.get("TIKHUB_TOKEN") or os.environ.get("TIKHUB_TOKEN", "")
    if not token:
        raise SystemExit("TIKHUB_TOKEN is missing from workspace .env or environment.")
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = args.workspace / "data" / "xhs-validator" / f"{safe_name(args.idea)}-{stamp}"
    run_dir.mkdir(parents=True, exist_ok=False)
    client = Client(token, args.workspace / "data" / "xhs-validator" / ".cache", planned)
    idea_grams = bigrams(args.idea + " " + " ".join(keywords))
    notes_by_id: dict[str, dict[str, Any]] = {}
    try:
        for query in keywords:
            payload = client.get("search_notes", {
                "keyword": query, "page": 1, "sort_type": "general", "note_type": "不限",
                "time_filter": "不限", "ai_mode": 0,
            })
            for item in (((payload.get("data") or {}).get("data") or {}).get("items") or []):
                note = normalize_note(item, query, idea_grams)
                if note and (note["id"] not in notes_by_id or note["review_priority"] > notes_by_id[note["id"]]["review_priority"]):
                    notes_by_id[note["id"]] = note
        ranked = sorted(notes_by_id.values(), key=lambda n: n["review_priority"], reverse=True)
        comment_targets = ranked[:config["comments"]]
        comments: list[dict[str, Any]] = []
        for note in comment_targets:
            payload = client.get("get_note_comments", {
                "note_id": note["id"], "cursor": "", "index": 0,
                "pageArea": "UNFOLDED", "sort_strategy": "like_count",
            })
            rows = (((payload.get("data") or {}).get("data") or {}).get("comments") or [])
            for row in rows:
                comments.append({
                    "note_id": note["id"], "comment_id": str(row.get("id") or ""),
                    "content": row.get("content") or "", "likes": number(row.get("like_count")),
                    "sub_comment_count": number(row.get("sub_comment_count")), "is_sub_comment": False,
                })
                for sub in row.get("sub_comments") or []:
                    if sub.get("content"):
                        comments.append({
                            "note_id": note["id"], "comment_id": str(sub.get("id") or ""),
                            "content": sub.get("content") or "", "likes": number(sub.get("like_count")),
                            "sub_comment_count": 0, "is_sub_comment": True,
                        })
    except Exception as exc:
        (run_dir / "error.json").write_text(json.dumps({"error": str(redact(str(exc)))}, ensure_ascii=False), encoding="utf-8")
        print(str(redact(str(exc))), file=sys.stderr)
        return 2
    output = {
        "meta": {
            "idea": args.idea, "mode": args.mode, "queries": keywords,
            "collected_at": datetime.now(timezone.utc).isoformat(),
            "requests_made": client.requests_made, "cache_hits": client.cache_hits,
            "estimated_cost_usd": round(client.requests_made * PRICE_ESTIMATE, 2),
            "pricing_is_estimate": True,
        },
        "notes": ranked,
        "comments": sorted(comments, key=lambda c: c["likes"], reverse=True),
    }
    (run_dir / "evidence.json").write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"run_dir": str(run_dir.resolve()), **output["meta"], "notes": len(ranked), "comments": len(comments)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

