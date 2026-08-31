# Scoring rubric

Score six dimensions from 0 to 100. Every dimension requires at least one evidence item with a note ID; otherwise its score may not exceed 40.

| Dimension | Weight | What raises the score |
|---|---:|---|
| `demand_strength` | 25% | repeated first-person pain, concrete use cases, urgency |
| `payment_intent` | 20% | price questions, purchase requests, actual payment or repeat buying |
| `pain_clarity` | 15% | specific, repeated and costly problems rather than generic interest |
| `differentiation_space` | 15% | unmet needs, complaints about substitutes, credible narrow wedge |
| `product_feasibility` | 15% | a testable solution with manageable delivery and quality risks |
| `acquisition_and_compliance` | 10% | reachable buyers and manageable trust, privacy, safety or policy risks |

For `acquisition_and_compliance`, 100 means low risk and clear acquisition; 0 means severe unresolved risk.

The weighted raw score is reduced by confidence:

- `high`: multiplier 1.00; multiple queries, relevant comments, both positive and opposing evidence.
- `medium`: multiplier 0.95; useful evidence but limited intent, geography, or comment depth.
- `low`: multiplier 0.85; sparse, highly promotional, poorly matched, or mostly engagement-only evidence.

Interpretation:

- 80–100: strong opportunity worth a larger validation.
- 60–79: promising; run a narrow paid experiment.
- 40–59: uncertain; collect missing evidence before building.
- 0–39: weak or high-risk under the tested positioning.

Do not add engagement points directly to the business score. Engagement ranks which content to inspect; it does not prove demand or willingness to pay.

