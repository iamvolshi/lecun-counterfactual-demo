# Keeping the What-If: demo and proof

Date: November 25, 2026
Seed: 20261125
Code: simulator.py and simulator_kt.py in this folder
Live demo: https://iamvolshi.github.io/lecun-counterfactual-demo/
Repo: https://github.com/iamvolshi/lecun-counterfactual-demo

## What was proven

Both tests from Section 4 of the supplement, `lecun-counterfactual-supplement-draft.md`.

### 1. Holding test

Ask the one-step what-if later, from the record, vs immediately.

Toy world: 2D boat, z' = z + a * s(z) + d, s = 1 + 0.4 sin(x) + 0.3 cos(y).
Model mu(z, a) = z + a. Disturbance d is a hidden current, sigma 0.7 per coordinate.
R2 is on the change, z_cf - z, not on absolute position, so the starting
position does not inflate it. n = 2000 events.

- Factual only, no record, outcome gone: R2 0.448
- Corrected immediately: R2 0.913
- Corrected later, from the record: R2 0.913
- Corrected with the wrong predictor version (v2, scale 0.5, by mistake): R2 0.657

The later answer is identical to the immediate answer. The record held
what was needed, with no loss. The wrong-version run shows why the
reliance layer matters: using the wrong stored version changes the
answer, and the record lets you see which version was used.

This mirrors the paper's pattern, it does not reproduce their numbers.
Their R2 was 38-46 percent factual, 86-96 percent corrected, on four
rendered simulators. Ours is 44.8 percent factual, 91.3 percent corrected,
on this toy.

### 2. Chaining test

Two steps, goal at step 2. Ask what action at step 1 would have made
the goal reachable, chaining the correction back through step 1.
n = 2000 events, goal radius 0.35, 60 candidate actions searched.

- Chained, using the record: 60.7 percent reach the goal
- Naive, mu only, disturbances ignored: 11.8 percent
- One-step hindsight, for comparison: 65.8 percent

Chaining works, and it beats naive by a lot. It does not beat one-step,
and it does not compound in the good direction. It degrades a little
against one-step, 60.7 vs 65.8, as the draft expected. The record is
still useful for one-step what-ifs asked later and for audit, but
chaining is not a free win.

## What this does not prove

- This is a toy simulation, not LeCun's rendered simulators, not a JEPA,
  not a learned encoder. The model here is hand-written mu = z + a.
- It proves the record logic and the chaining logic, not the paper's
  numbers, and not that a real world model would behave the same way.
- The disturbance here is Gaussian, the dynamics are smooth, there are
  no discontinuities, coordinate folds, or command-scaling disturbances,
  all of which the paper lists as failures.
- The version-change sub-test uses a deliberately worse v2 predictor.
  A better v2 would improve the answer, not degrade it. The point is
  attribution, not that old is always better.

## The gain, in distance, not R2

One typical event, event 14, seed 20261125. Start (1.41, 0.12).
True what-if outcome (1.06, 1.77).
- Factual, no record: (1.53, 0.82), misses by 1.07 units.
- Corrected, with record: (1.11, 1.59), misses by 0.19 units.
- Gain: 82.6 percent closer.

Across all 2000 events:
- Mean miss: factual 0.94 units, corrected 0.32 units, gain 65.9 percent closer.
- Median miss: factual 0.88 units, corrected 0.24 units, gain 72.7 percent closer.

Chaining, out of 100 tries:
- Naive: 12 percent reach the goal.
- Chained with record: 61 percent reach the goal. Gain: 49 percentage points, 408 percent more goals reached.
- One-step: 66 percent reach the goal. Chaining does not beat one-step.

## KT v2: run it by trust level

Same 2000 events, run again as if every entry were at that level.
Code: simulator_kt.py, numbers: results_kt.json. The current is
partly systematic per region, d = region_current(z) + noise, sigma 0.3,
so a slow residual (mean per cell) learns the region and a fast
residual keeps this event's actual disturbance.

Holding test, R2 on the change, n=2000 each:
- WILD, weight 0.3: 0.241
- CANDIDATE, weight 0.7: 0.716
- MATURE fast, weight 1.0: 0.877
- MATURE slow, mean per cell: 0.698
- REVOKED, predictor v2 by mistake: 0.516
- REVOKED gated: cannot-answer, no wrong answer

Chaining test, n=2000, goal radius 0.35:
- Fast chain: 61.8 percent reach the goal
- Slow chain, MATURE: 23.8 percent
- Naive, mu only: 12.6 percent
- One-step hindsight: 66.0 percent

Slow is worse for this specific event, and that is the honest KT
split. Slow replaces the actual disturbance for this event with the
regional mean, so it loses the exact residual the hindsight question
needs. Fast is for this event, slow is for the domain, for new events
in a known region. Do not claim slow beats fast on hindsight. It does
not here, and the numbers show it.

## Files

- simulator.py: the world, the model, the record, both tests, seed fixed
- results.json: the numbers above, machine-readable
- simulator_kt.py: KT v2, authority variants, fast vs slow
- results_kt.json: the KT variant numbers, machine-readable
- index.html in the repo: interactive demo, with Run as WILD /
  CANDIDATE / MATURE / REVOKED buttons
