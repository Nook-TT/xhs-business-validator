#!/usr/bin/env python3
"""Render scored analysis JSON as a self-contained HTML report."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any

DIMENSION_LABELS = {
    "demand_strength": "需求强度", "payment_intent": "付费意向", "pain_clarity": "痛点清晰度",
    "differentiation_space": "差异化空间", "product_feasibility": "产品可行性",
    "acquisition_and_compliance": "获客与合规",
}


def esc(value: Any) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def evidence(items: list[dict[str, Any]]) -> str:
    if not items:
        return '<p class="small">未提供可引用证据</p>'
    return "".join(f'<div class="evidence">{esc(i.get("text"))}<div class="small">Note ID: {esc(i.get("note_id"))}</div></div>' for i in items)


def cards(items: list[dict[str, Any]]) -> str:
    return "".join(f'<div class="card"><b>{esc(i.get("title"))}</b><p>{esc(i.get("detail"))}</p><div class="small">Note ID: {esc(i.get("note_id"))}</div></div>' for i in items) or '<div class="card">无</div>'


def list_html(items: list[Any]) -> str:
    return '<ul class="fact-list">' + "".join(f"<li>{esc(item)}</li>" for item in items) + "</ul>"


def section_head(index: str, title: str) -> str:
    return f'<div class="section-head"><span class="section-index">{esc(index)}</span><h2>{esc(title)}</h2></div>'


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("analysis", type=Path)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--template", type=Path, default=Path(__file__).resolve().parent.parent / "assets" / "report-template.html")
    args = p.parse_args()
    data = json.loads(args.analysis.read_text(encoding="utf-8-sig"))
    if "final_score" not in data:
        raise SystemExit("analysis has no final_score; run score.py first")
    sample = data.get("sample") or {}
    rows = []
    for key, label in DIMENSION_LABELS.items():
        item = (data.get("dimensions") or {}).get(key) or {}
        rows.append(f'<tr><td>{label}</td><td>{esc(item.get("score"))}</td><td>{esc(item.get("rationale"))}{evidence(item.get("evidence") or [])}</td></tr>')
    positioning = data.get("positioning") or {}
    experiment = data.get("experiment") or {}
    body = f'''
<section class="hero"><span class="eyebrow">XIAOHONGSHU MARKET SIGNALS</span><div class="score-row"><div class="score">{esc(data["final_score"])} <small>/ 100</small></div><span class="tag">置信度 {esc(data.get("confidence"))}</span></div><h1>{esc(data.get("idea"))}</h1><p class="lead verdict">{esc(data.get("verdict"))}</p><p class="lead">{esc(data.get("summary"))}</p></section>
<section class="grid"><div class="card metric-card"><div class="metric">{esc(sample.get("notes_collected", 0))}</div><div class="label">采集笔记</div></div><div class="card metric-card"><div class="metric">{esc(sample.get("notes_relevant", 0))}</div><div class="label">相关笔记</div></div><div class="card metric-card"><div class="metric">{esc(sample.get("comments_reviewed", 0))}</div><div class="label">审阅评论</div></div><div class="card metric-card"><div class="metric">${esc(sample.get("estimated_cost_usd", 0))}</div><div class="label">估算 API 费用</div></div></section>
<section class="section">{section_head("01", "市场判断")}<div class="table-wrap"><table><tr><th>维度</th><th>分数</th><th>依据与证据</th></tr>{''.join(rows)}</table></div></section>
<section class="section">{section_head("02", "支持信号")}<div class="signal-grid">{cards(data.get("supporting_signals") or [])}</div></section>
<section class="section">{section_head("03", "反对信号与风险")}<div class="signal-grid">{cards(data.get("opposing_signals") or [])}</div></section>
<section class="section">{section_head("04", "建议定位")}<div class="card"><p><b>目标用户：</b>{esc(positioning.get("target_user"))}</p><p><b>切入口：</b>{esc(positioning.get("wedge"))}</p><p><b>建议：</b>{esc(positioning.get("recommendation"))}</p></div></section>
<section class="section">{section_head("05", "低成本验证实验")}<div class="card"><p><span class="tag">周期 {esc(experiment.get("duration"))}</span></p><h3>执行步骤</h3>{list_html(experiment.get("steps") or [])}<h3>通过标准</h3>{list_html(experiment.get("pass_thresholds") or [])}<h3>停止标准</h3>{list_html(experiment.get("stop_thresholds") or [])}</div></section>
<section class="section">{section_head("06", "样本边界")}<div class="card"><p><b>查询：</b>{esc('、'.join(sample.get("queries") or []))}</p>{list_html(sample.get("limitations") or [])}</div></section>
<footer class="footer"><strong>数据说明：</strong>成功请求 {esc(sample.get("requests_made", 0))} 次。小红书公开内容反映平台用户信号，不等同于总体市场统计或投资保证。</footer>
'''
    template = args.template.read_text(encoding="utf-8")
    output = template.replace("{{TITLE}}", esc(f'{data.get("idea", "市场验证")}｜小红书市场验证报告')).replace("{{BODY}}", body)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(output, encoding="utf-8")
    print(json.dumps({"report": str(args.output.resolve()), "score": data["final_score"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

