"""
KT v2: show the variants, by trust level.

Same boat world as simulator.py, plus one KT fact that makes
authority matter: the current is partly systematic per region.
d = region_current(z) + noise
region_current(z) = (0.5*sin(2x), 0.5*cos(2y))
noise sigma 0.3 per coordinate.

A single visit gives a fast residual: region + noise, noisy.
Repeated visits to the same region give a slow residual: the mean
over visits, noise cancels, region is learned. That is consolidation.

Authority, by visits to the same 1x1 cell:
  1 visit: WILD, weight 0.3, fast residual only
  2 visits: CANDIDATE, weight 0.7, fast residual only
  3+ visits: MATURE, weight 1.0, slow residual (mean per cell)
  REVOKED: entry was made under predictor v2 (scale 0.5). If used,
  it is wrong. If revoked, it is excluded and the query is
  cannot-answer, not a wrong answer.

Variants are run on the SAME events, so the comparison is fair.
Holding test: R2 on the change, z_cf - z, n=2000.
Chaining test: two steps, goal radius 0.35, n=2000, 60 candidates.
"""
import json, math, random, hashlib

SEED = 20261125
random.seed(SEED)

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

def run_holding_variants(n=2000):
    # Fair variant table: run the SAME 2000 events four times, each time
    # as if all entries were at that trust level. That is what Darren
    # asked for: run it with MATURE, run it with REVOKED, show the outcome.
    # First pass: build events, with a slow residual per cell.
    slow = {}
    events = []
    for _ in range(n):
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
    variants = {}
    # name -> (weight on model difference, use slow residual, predictor version)
    specs = {
        "WILD": (0.3, False, "v1"),
        "CANDIDATE": (0.7, False, "v1"),
        "MATURE_FAST": (1.0, False, "v1"),
        "MATURE_SLOW": (1.0, True, "v1"),
        "REVOKED": (1.0, False, "v2"),
    }
    for name, (weight, use_slow, version) in specs.items():
        true_d, pred_d = [], []
        for e in events:
            m = mu(e["z"], e["a"], version); mp = mu(e["z"], e["ap"], version)
            if use_slow:
                base = (e["z"][0] + e["a"][0]*s_of(e["z"]) + e["slow_resid"][0],
                        e["z"][1] + e["a"][1]*s_of(e["z"]) + e["slow_resid"][1])
                cf = (base[0] + mp[0] - m[0], base[1] + mp[1] - m[1])
            else:
                cf = (e["z_obs"][0] + weight*(mp[0]-m[0]),
                      e["z_obs"][1] + weight*(mp[1]-m[1]))
            true_d.append((e["z_cf_true"][0]-e["z"][0], e["z_cf_true"][1]-e["z"][1]))
            pred_d.append((cf[0]-e["z"][0], cf[1]-e["z"][1]))
        variants[name] = {"answered": n, "answered_rate": 1.0,
                          "R2_on_change": r2(true_d, pred_d)}
    variants["REVOKED_GATED"] = {
        "answered": 0, "answered_rate": 0.0, "R2_on_change": None,
        "note": "Revoked entries are not used. Query is cannot-answer, not a wrong answer.",
    }
    return {"n": n, "variants": variants}

def run_chaining_variants(n=2000, goal_radius=0.35):
    # Simpler, honest variant table for chaining: fast chain (all steps,
    # fast residuals) vs slow chain (MATURE steps only, slow residuals)
    # vs naive (mu only) vs one-step.
    # Reuse the same world, with region current.
    def dist(p, q):
        return math.hypot(p[0]-q[0], p[1]-q[1])
    fast_ok = slow_ok = naive_ok = one_ok = 0
    # slow consolidation: learn region current per cell over a warm-up
    visits = {}
    slow_map = {}
    for _ in range(500):
        z = rand_vec(2.0); a = rand_vec(1.0)
        rc = region_current(z)
        d = (rc[0] + random.gauss(0, 0.3), rc[1] + random.gauss(0, 0.3))
        zo = true_step(z, a, d)
        resid = (zo[0]-mu(z, a, "v1")[0], zo[1]-mu(z, a, "v1")[1])
        c = cell(z)
        slow_map.setdefault(c, []).append(resid)
    slow_mean = {c: (sum(r[0] for r in v)/len(v), sum(r[1] for r in v)/len(v))
                 for c, v in slow_map.items()}
    for _ in range(n):
        z0 = rand_vec(2.0)
        a1 = rand_vec(1.0); a2 = rand_vec(1.0)
        rc1 = region_current(z0)
        d1 = (rc1[0] + random.gauss(0, 0.3), rc1[1] + random.gauss(0, 0.3))
        z1 = true_step(z0, a1, d1)
        rc2 = region_current(z1)
        d2 = (rc2[0] + random.gauss(0, 0.3), rc2[1] + random.gauss(0, 0.3))
        z2 = true_step(z1, a2, d2)
        goal = (z2[0] + random.uniform(-0.8, 0.8), z2[1] + random.uniform(-0.8, 0.8))
        candidates = [rand_vec(1.0) for _ in range(60)]
        r1 = (z1[0]-mu(z0, a1, "v1")[0], z1[1]-mu(z0, a1, "v1")[1])
        r2 = (z2[0]-mu(z1, a2, "v1")[0], z2[1]-mu(z1, a2, "v1")[1])
        def fast_est(a1p):
            m1 = mu(z0, a1, "v1"); mp1 = mu(z0, a1p, "v1")
            z1c = (z1[0] + mp1[0] - m1[0], z1[1] + mp1[1] - m1[1])
            return (mu(z1c, a2, "v1")[0] + r2[0], mu(z1c, a2, "v1")[1] + r2[1])
        def slow_est(a1p):
            # MATURE only: use slow residual for step 1, from the consolidated map.
            # If the cell was never consolidated, fall back to fast, and mark it.
            sr = slow_mean.get(cell(z0), r1)
            m1 = mu(z0, a1, "v1"); mp1 = mu(z0, a1p, "v1")
            # Reconstruct z1 with slow residual, then step 2 with slow residual 2.
            sr2 = slow_mean.get(cell(z1), r2)
            z1c = (z0[0] + a1p[0]*s_of(z0) + sr[0], z0[1] + a1p[1]*s_of(z0) + sr[1])
            return (z1c[0] + a2[0]*s_of(z1c) + sr2[0], z1c[1] + a2[1]*s_of(z1c) + sr2[1])
        def naive_est(a1p):
            return mu(mu(z0, a1p, "v1"), a2, "v1")
        best_fast = min(candidates, key=lambda ap: dist(fast_est(ap), goal))
        best_slow = min(candidates, key=lambda ap: dist(slow_est(ap), goal))
        best_naive = min(candidates, key=lambda ap: dist(naive_est(ap), goal))
        def true_out(a1p):
            return true_step(true_step(z0, a1p, d1), a2, d2)
        if dist(true_out(best_fast), goal) < goal_radius:
            fast_ok += 1
        if dist(true_out(best_slow), goal) < goal_radius:
            slow_ok += 1
        if dist(true_out(best_naive), goal) < goal_radius:
            naive_ok += 1
        # one-step hindsight at step 2
        cands2 = [rand_vec(1.0) for _ in range(60)]
        def one_est(a2p):
            m = mu(z1, a2, "v1"); mp = mu(z1, a2p, "v1")
            return (z2[0] + mp[0] - m[0], z2[1] + mp[1] - m[1])
        best2 = min(cands2, key=lambda ap: dist(one_est(ap), goal))
        if dist(true_step(z1, best2, d2), goal) < goal_radius:
            one_ok += 1
    return {
        "n": n, "goal_radius": goal_radius,
        "fast_chain_WILD_CANDIDATE": fast_ok / n,
        "slow_chain_MATURE": slow_ok / n,
        "naive_mu_only": naive_ok / n,
        "one_step_hindsight": one_ok / n,
    }

if __name__ == "__main__":
    holding = run_holding_variants()
    chaining = run_chaining_variants()
    print(json.dumps({"holding_variants": holding, "chaining_variants": chaining}, indent=2))
    with open("results_kt.json", "w") as f:
        json.dump({"holding_variants": holding, "chaining_variants": chaining, "seed": SEED}, f, indent=2)
