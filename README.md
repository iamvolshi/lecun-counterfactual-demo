# Keeping the What-If: a record for counterfactual world models

By Darren Hall. A record for counterfactual world models, in reply to
Balestriero, LeCun, and Varaku, arXiv:2611.24778.

Live demo: https://iamvolshi.github.io/lecun-counterfactual-demo/

## What is here

- `index.html`: interactive demo. New event, then ask a what-if now,
  later from the record, or factual only with no record.
- `simulator.py`: the world, the model, the record, both tests. Seed 20261125.
- `results.json`: the numbers.
- `REPORT.md`: method, results, and limits.
- `lecun-counterfactual-supplement-draft.md`: the supplement draft.

## Results, seed 20261125, n=2000

Holding test, R2 on the change:
- Factual only, no record: 0.448
- Corrected immediately: 0.913
- Corrected later, from the record: 0.913
- Wrong predictor version: 0.657

Chaining test, goal radius 0.35:
- Chained, using the record: 60.7 percent reach the goal
- Naive, model only: 11.8 percent
- One-step hindsight: 65.8 percent

Toy simulation, not the paper's simulators. It proves the record logic,
not the paper's numbers.
