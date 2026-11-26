"""
Retest: slow-vs-fast trust measurement, measured AFTER the collapse.

Darren's spec: slow was measured right away, at the same instant as
fast. Slow cannot be measured until after the authority collapses on
fast. The measurement comes after the return to baseline. That is
when the scar is deepest. Slow keeps the record another ~600 ticks,
and the measurement is taken after that window.

Design, in the simulation's own terms (world functions copied
unchanged from simulator_kt.py; seed 20261125, n=2000, same events):

Phase A - immediate (reproduction): the same 2000 events as
run_holding_variants, fast and slow measured immediately.
Expect MATURE_FAST 0.877, MATURE_SLOW 0.698.

Phase B - collapse: the predictor version advances v1 -> v2.
The fast path's authority collapses: its entries were single
visits recorded under v1, and a superseded predictor version is
the sim's own revocation mechanism (simulator_kt.py REVOKED:
entry made under a superseded predictor, if used it is wrong,
if revoked it is excluded and the query is cannot-answer).
Fast after the collapse: cannot-answer. The slow entries survive:
their content is the cell mean, which washes out the predictor
dependence and converges to the region current, a property of the
world, not of the predictor version.

Phase C - return to baseline + slow holds the record ~600 ticks:
the world keeps running under the same baseline regime (region
current + noise sigma 0.3). 600 more visits (ticks) feed their
residuals into the cell means. Slow keeps consolidating. Fast
records nothing new; its authority is dead.

Phase D - measurement after the window: the same hindsight
question on the original 2000 events, asked from the record:
- SLOW (primary): consolidated cell mean after the 600 ticks,
  model-difference term under the stored version v1. The record
  holds the version it was recorded under, and simulator.py's
  holding test shows using the stored version keeps R2.
- SLOW under live v2 (reference): same, difference term under v2.
- FAST: cannot-answer (revoked).
- FAST forced under v2 (reference): what collapsed authority
  costs if you use it anyway. Wrong-version R2.

The scar: the R2 fast loses to the collapse, measured after the
return to baseline: immediate fast R2 minus forced fast R2.
"""
import json, math, random

SEED = 20261125
N = 2000
HOLD_TICKS = 600

def s_of(z):
    x, y = z
    return 1.0 + 0.40 * math.sin(x) + 0.30 * math.cos(y)

def region_current(z):
    return (0.5 * math.sin(2*z[0]), 0.5 * math.cos(2*z[1]))

def true_step(z, a, d):
    s = s_of(z)
    return (z[0] + a[0] * s + d[0], z[1] + a[1] * s + d[1])

def mu(z, a, version="v1"):
    if version == "v1":
        return (z[0] + a[0], z[1] + a[1])
    if version == "v2":
        return (z[0] + a[0] * 0.5, z[1] + a[1] * 0.5)
    raise ValueError(version)

def r2(true_vals, pred_vals):
    out = []
    for coord in (0, 1):
        t = [v[coord] for v in true_vals]
        p = [v[coord] for v in pred_vals]
        mean = sum(t) / len(t)
        ss_tot = sum((v - mean) ** 2 for v in t)
        ss_res = sum((tv - pv) ** 2 for tv, pv in zip(t, p))
        out.append(1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0)
    return sum(out) / len(out)

def rand_vec(scale=1.0):
    return (random.uniform(-scale, scale), random.uniform(-scale, scale))

def cell(z):
    return (math.floor(z[0]), math.floor(z[1]))

def main():
    random.seed(SEED)

    # Phase A: build the same 2000 events as run_holding_variants,
    # same draw order, so the immediate numbers reproduce exactly.
    slow = {}
    events = []
    for _ in range(N):
        z = rand_vec(2.0)
        a = rand_vec(1.0); ap = rand_vec(1.0)
        rc = region_current(z)
        d = (rc[0] + random.gauss(0, 0.3), rc[1] + random.gauss(0, 0.3))
        z_obs = true_step(z, a, d)
        z_cf_true = true_step(z, ap, d)
        c = cell(z)
        resid = (z_obs[0]-mu(z, a, "v1")[0], z_obs[1]-mu(z, a, "v1")[1])
        slow.setdefault(c, []).append(resid)
        slow_resid = (sum(r[0] for r in slow[c])/len(slow[c]),
                      sum(r[1] for r in slow[c])/len(slow[c]))
        events.append({"z": z, "a": a, "ap": ap, "z_obs": z_obs,
                       "z_cf_true": z_cf_true, "resid": resid,
                       "slow_resid": slow_resid, "cell": c})

    def measure(use_slow, version, slow_map=None):
        true_d, pred_d = [], []
        for e in events:
            m = mu(e["z"], e["a"], version); mp = mu(e["z"], e["ap"], version)
            if use_slow:
                sr = slow_map[e["cell"]] if slow_map is not None else e["slow_resid"]
                base = (e["z"][0] + e["a"][0]*s_of(e["z"]) + sr[0],
                        e["z"][1] + e["a"][1]*s_of(e["z"]) + sr[1])
                cf = (base[0] + mp[0] - m[0], base[1] + mp[1] - m[1])
            else:
                cf = (e["z_obs"][0] + (mp[0]-m[0]),
                      e["z_obs"][1] + (mp[1]-m[1]))
            true_d.append((e["z_cf_true"][0]-e["z"][0], e["z_cf_true"][1]-e["z"][1]))
            pred_d.append((cf[0]-e["z"][0], cf[1]-e["z"][1]))
        return r2(true_d, pred_d)

    # Phase A measurement: immediate, as published.
    fast_immediate = measure(False, "v1")
    slow_immediate = measure(True, "v1")

    # Phase B: collapse. Predictor v1 -> v2. Fast entries revoked.
    # (No code change needed: revocation is the measurement rule below.)

    # Phase C: return to baseline + slow holds the record HOLD_TICKS
    # more ticks. Each tick is a visit: its residual joins the cell mean.
    for _ in range(HOLD_TICKS):
        z = rand_vec(2.0)
        a = rand_vec(1.0)
        rc = region_current(z)
        d = (rc[0] + random.gauss(0, 0.3), rc[1] + random.gauss(0, 0.3))
        z_obs = true_step(z, a, d)
        resid = (z_obs[0]-mu(z, a, "v1")[0], z_obs[1]-mu(z, a, "v1")[1])
        slow.setdefault(cell(z), []).append(resid)

    slow_mean_final = {c: (sum(r[0] for r in v)/len(v),
                           sum(r[1] for r in v)/len(v))
                       for c, v in slow.items()}
    visits_per_cell = {f"{c}": len(v) for c, v in slow.items()}

    # Phase D: measurement after the window, on the original events.
    slow_after_v1 = measure(True, "v1", slow_mean_final)
    slow_after_v2 = measure(True, "v2", slow_mean_final)
    fast_forced_v2 = measure(False, "v2")
    fast_forced_v1 = measure(False, "v1")  # sanity: equals immediate

    scar = fast_immediate - fast_forced_v2

    result = {
        "design": {
            "seed": SEED,
            "n_events": N,
            "hold_ticks": HOLD_TICKS,
            "collapse": "predictor version v1 -> v2; fast (single-visit) entries revoked, slow (consolidated cell-mean) entries kept",
            "measurement": "hindsight R2 on the change, same 2000 events, asked after the collapse, return to baseline, and 600-tick hold",
            "scar_definition": "immediate fast R2 minus forced fast R2 under v2 (what collapsed authority costs)",
        },
        "immediate_reproduction": {
            "MATURE_FAST": fast_immediate,
            "MATURE_SLOW": slow_immediate,
        },
        "after_collapse_baseline_and_hold": {
            "MATURE_SLOW_stored_v1": slow_after_v1,
            "MATURE_SLOW_live_v2_reference": slow_after_v2,
            "MATURE_FAST": None,
            "MATURE_FAST_note": "cannot-answer: fast entries revoked at the collapse, no fast record kept during the hold",
            "MATURE_FAST_forced_v2_reference": fast_forced_v2,
            "MATURE_FAST_forced_v1_sanity": fast_forced_v1,
        },
        "scar": {
            "fast_R2_lost_to_collapse": scar,
            "fast_immediate_R2": fast_immediate,
            "fast_forced_after_collapse_R2": fast_forced_v2,
        },
        "consolidation": {
            "cells": len(slow_mean_final),
            "visits_per_cell_after_hold": visits_per_cell,
            "total_visits": sum(len(v) for v in slow.values()),
        },
    }
    print(json.dumps(result, indent=2))
    with open("results_kt_retest_after_collapse.json", "w") as f:
        json.dump(result, f, indent=2)

if __name__ == "__main__":
    main()
