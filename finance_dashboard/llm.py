from __future__ import annotations

import os
from typing import Dict, List, Optional


def generate_explanation(summary: Dict, user_question: Optional[str] = None) -> str:
    """Return an explanation string for performance vs plan using the OpenAI API.

    The `summary` dict should contain:
      - period (str)
      - total_plan (float)
      - total_actual (float)
      - total_variance (float)
      - total_variance_pct (float)
      - top_positive_contributors: list[(metric, variance)]
      - top_negative_contributors: list[(metric, variance)]
    """
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY".lower())
    if not api_key:
        return (
            "OpenAI API key is not configured. Set OPENAI_API_KEY in your environment to enable the chat agent."
        )

    try:
        from openai import OpenAI  # type: ignore
    except Exception:  # pragma: no cover - optional dependency
        return "OpenAI Python SDK is not installed. Add 'openai' to requirements and reinstall."

    client = OpenAI(api_key=api_key)

    period = summary.get("period")
    total_plan = summary.get("total_plan")
    total_actual = summary.get("total_actual")
    total_variance = summary.get("total_variance")
    total_variance_pct = summary.get("total_variance_pct")
    top_pos = summary.get("top_positive_contributors", [])
    top_neg = summary.get("top_negative_contributors", [])

    pos_lines = [f"- {m}: +{v:,.0f}" for m, v in top_pos]
    neg_lines = [f"- {m}: {v:,.0f}" for m, v in top_neg]

    base_context = f"""
You are a finance performance analyst. Explain monthly performance vs plan clearly, concisely, and with actionable insights. Focus on drivers, not fluff. If variance percent is extreme due to a small base, point that out. Keep the tone professional.

Period: {period}
Total Plan: {total_plan:,.0f}
Total Actual: {total_actual:,.0f}
Variance: {total_variance:,.0f} ({total_variance_pct:.1f}%)

Top positive drivers (Actual > Plan):
{chr(10).join(pos_lines) if pos_lines else "(none)"}

Top negative drivers (Actual < Plan):
{chr(10).join(neg_lines) if neg_lines else "(none)"}
""".strip()

    user_msg = user_question or "Explain the main reasons for the variance and any risks/opportunities."

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a senior FP&A partner. Respond with 4-7 bullet points."},
            {"role": "user", "content": base_context},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.2,
    )

    content = response.choices[0].message.content if response and response.choices else ""
    return content.strip() if content else "(No response)"

