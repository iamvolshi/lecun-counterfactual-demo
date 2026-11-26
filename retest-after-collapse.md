# Retest: slow vs fast, measured after the collapse

## The change

The published KT result measured MATURE fast and MATURE slow at the
same instant, right after the event: fast 0.877, slow 0.698. The
published note says slow is worse than fast for hindsight on a
specific event.

Darren's point: slow was measured too early. Slow cannot be measured
until after the authority collapses on fast. The measurement comes
after the return to baseline. That is when the scar is deepest.
Slow keeps the record another ~600 ticks, and the measurement is
taken after that window.

## Design (in the simulation's own terms)

Same world, same seed (20261125), same 2000 events as
`simulator_kt.py`. Nothing else changed.

- **Collapse:** the predictor version advances v1 to v2. The fast
  path's authority collapses: its entries were single visits
  recorded under v1, and a superseded predictor version is the
  sim's own revocation mechanism (REVOKED in `simulator_kt.py`:
  if used it is wrong, if revoked it is excluded and the query is
  cannot-answer). Fast after the collapse: cannot-answer.
- **Slow survives:** the slow entries are cell means. The mean
  washes out the predictor dependence and converges to the region
  current, a property of the world, not of the predictor version.
- **Return to baseline and the hold:** the world keeps running
  under the same baseline regime (region current + noise sigma
  0.3). Slow holds the record for 600 more ticks; each visit feeds
  its residual into the cell means (16 cells, 2600 visits total).
  Fast records nothing new.
- **Measurement:** the same hindsight question on the original
  2000 events, asked after the window. Slow answers from the
  consolidated record under its stored version v1 (the record
  holds the version it was recorded under; `simulator.py`'s
  holding test shows using the stored version keeps R2).

## Numbers (actual run, `retest_after_collapse.py`)

| | Immediate (published) | After collapse + 600-tick hold |
|---|---|---|
| MATURE fast | 0.877 | cannot-answer (revoked) |
| MATURE fast, forced under v2 | | 0.516 |
| MATURE slow | 0.698 | 0.696 |

- Immediate numbers reproduced exactly (fast 0.8769, slow 0.6979).
- The scar: fast loses 0.361 R2 points to the collapse, 41.2% of
  its immediate R2. Fast forced to answer anyway scores 0.516,
  the same number as REVOKED in the original run.
- Slow after the hold: 0.696, down 0.3% from 0.698. The hold does
  not make slow better on a specific event. Consolidation cannot
  remove the event's own noise, and that noise is the dominant
  error in slow's answer. What the hold does is keep slow alive.
- After the collapse, slow is 34.9% above forced fast (0.696
  against 0.516).

## Verdict

Measured after the collapse, slow no longer looks worse than
fast. Fast cannot answer at all, and if forced to answer it
scores below slow. The published claim, slow is worse than fast
for hindsight on a specific event, holds only for the immediate
measurement. The ranking flips once fast's authority collapses.

## Limit, stated plainly

Slow's post-collapse value rests on the record holding the stored
version. If the query is forced through the live v2 predictor
instead, slow drops to 0.333, 52.1% below its stored-version
number and below forced fast. The record preserving the version
is doing real work here, not just slow.

## Files

- `retest_after_collapse.py`: the retest script.
- `results_kt_retest_after_collapse.json`: the numbers above.
- Nothing published was touched: `results_kt.json`,
  `results.json`, `REPORT.md`, and the supplement draft are
  unchanged.
