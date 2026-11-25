"""
LeCun counterfactual demo, Section 4 tests.

Toy world, stated plainly so the numbers mean what they say.
- 2D boat, state z = (x, y), action a = thrust, disturbance d = current.
- True dynamics: z' = z + a * s(z) + d, s(z) = 1 + 0.15*sin(x) + 0.10*cos(y)
  s is unknown to the model, so the model is imperfect, as in the paper.
- Model mu(z, a) = z + a. It predicts the average outcome, no disturbance,
  no s. That is the factual-only predictor.
- Counterfactual correction, from the paper [1]:
  z_cf = z_obs + mu(z, a') - mu(z, a)
- Record: append-only entries, one per transition, holding
  z, a, mu(z,a), encoder/predictor version, observed z', residual.
  Alternative prediction mu(z, a') is NOT stored, it is computed at
  query time from the stored z and stored predictor version.

Tests, exactly as in the supplement Section 4:
1. Holding test: ask the one-step what-if later, from the record,
   vs immediately. Compare corrected R2 later vs immediately,
   and vs factual-only R2 (no record, outcome gone).
   Sub-test: predictor version changes after the event. Using the
   stored version keeps R2. Using the new version by mistake drops it.
2. Chaining test: two steps, goal at step 2. Ask what a1' would have
   made the goal reachable, chaining the correction back through
   step 1. Measure true success: does the a1' chosen by the
   chained estimate actually reach the goal in the true dynamics?
   Compare with a naive planner that ignores disturbances (mu only).

Limits, stated in REPORT.md too:
- This is a toy simulation, not LeCun's rendered simulators, not a JEPA,
  not a learned encoder. The model here is hand-written mu = z + a.
- It proves the record logic and the chaining logic, not the paper's
  numbers. The paper's R2 86-96% is theirs, not reproduced here.
"""
import json, math, random, hashlib

SEED = 20261125
random.seed(SEED)

def s_of(z):
    x, y = z
    return 1.0 + 0.40 * math.sin(x) + 0.30 * math.cos(y)

def true_step(z, a, d):
    s = s_of(z)
    return (z[0] + a[0] * s + d[0], z[1] + a[1] * s + d[1])

def mu(z, a, version="v1"):
    # v1: mu = z + a. v2: a slightly different predictor, after an update.
    if version == "v1":
        return (z[0] + a[0], z[1] + a[1])
    if version == "v2":
        return (z[0] + a[0] * 0.5, z[1] + a[1] * 0.5)
    raise ValueError(version)

def r2(true_vals, pred_vals):
    # R2 per coordinate, averaged. true_vals/pred_vals are lists of (x,y).
    out = []
    for coord in (0, 1):
        t = [v[coord] for v in true_vals]
        p = [v[coord] for v in pred_vals]
        mean = sum(t) / len(t)
        ss_tot = sum((v - mean) ** 2 for v in t)
        ss_res = sum((tv - pv) ** 2 for tv, pv in zip(t, p))
        out.append(1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0)
    return sum(out) / len(out)

class Record:
    """Append-only, hash-chained. A revision is a new entry, old stays."""
    def __init__(self):
        self.entries = []
        self.prev_hash = "genesis"
    def append(self, entry):
        body = json.dumps(entry, sort_keys=True)
        h = hashlib.sha256((self.prev_hash + body).encode()).hexdigest()
        self.entries.append({"entry": entry, "hash": h, "prev": self.prev_hash})
        self.prev_hash = h
        return h

def rand_vec(scale=1.0):
    return (random.uniform(-scale, scale), random.uniform(-scale, scale))

def run_holding(n=2000):
    # R2 is computed on the change, z_cf - z, not on absolute position.
    # Otherwise the starting position z, which every predictor knows,
    # inflates R2 and hides the disturbance effect.
    rec = Record()
    true_cf, pred_fact, pred_corr_now, pred_corr_later, pred_corr_wrongver = [], [], [], [], []
    for _ in range(n):
        z = rand_vec(2.0)
        a = rand_vec(1.0)
        ap = rand_vec(1.0)
        d = (random.gauss(0, 0.7), random.gauss(0, 0.7))
        z_obs = true_step(z, a, d)
        z_cf_true = true_step(z, ap, d)
        # record at act time, predictor v1
        rec.append({"z": z, "a": a, "mu": mu(z, a, "v1"), "version": "v1",
                    "z_obs": z_obs, "residual": (z_obs[0]-mu(z, a, "v1")[0],
                                                 z_obs[1]-mu(z, a, "v1")[1])})
        # immediate correction
        m = mu(z, a, "v1"); mp = mu(z, ap, "v1")
        corr_now = (z_obs[0] + mp[0] - m[0], z_obs[1] + mp[1] - m[1])
        # later, from the record, same stored z and stored version v1
        e = rec.entries[-1]["entry"]
        m2 = mu(e["z"], e["a"], e["version"]); mp2 = mu(e["z"], ap, e["version"])
        corr_later = (e["z_obs"][0] + mp2[0] - m2[0], e["z_obs"][1] + mp2[1] - m2[1])
        # wrong version: use v2 by mistake at query time
        m3 = mu(e["z"], e["a"], "v2"); mp3 = mu(e["z"], ap, "v2")
        corr_wrong = (e["z_obs"][0] + mp3[0] - m3[0], e["z_obs"][1] + mp3[1] - m3[1])
        true_cf.append((z_cf_true[0]-z[0], z_cf_true[1]-z[1]))
        pred_fact.append((mp[0]-z[0], mp[1]-z[1]))
        pred_corr_now.append((corr_now[0]-z[0], corr_now[1]-z[1]))
        pred_corr_later.append((corr_later[0]-z[0], corr_later[1]-z[1]))
        pred_corr_wrongver.append((corr_wrong[0]-z[0], corr_wrong[1]-z[1]))
    return {
        "n": n,
        "note": "R2 on the change z_cf - z, not absolute position",
        "factual_only_R2": r2(true_cf, pred_fact),
        "corrected_immediate_R2": r2(true_cf, pred_corr_now),
        "corrected_later_from_record_R2": r2(true_cf, pred_corr_later),
        "corrected_wrong_predictor_version_R2": r2(true_cf, pred_corr_wrongver),
        "record_entries": len(rec.entries),
    }

def run_chaining(n=2000, goal_radius=0.35):
    # Two steps. Goal G is placed near where step 2 would land, so the
    # hindsight question is non-trivial.
    rec = Record()
    chain_success = 0
    naive_success = 0
    one_step_success = 0
    total = 0
    for _ in range(n):
        z0 = rand_vec(2.0)
        a1 = rand_vec(1.0); a2 = rand_vec(1.0)
        d1 = (random.gauss(0, 0.7), random.gauss(0, 0.7))
        d2 = (random.gauss(0, 0.7), random.gauss(0, 0.7))
        z1 = true_step(z0, a1, d1)
        z2 = true_step(z1, a2, d2)
        rec.append({"z": z0, "a": a1, "mu": mu(z0, a1, "v1"), "version": "v1", "z_obs": z1,
                    "residual": (z1[0]-mu(z0, a1, "v1")[0], z1[1]-mu(z0, a1, "v1")[1])})
        rec.append({"z": z1, "a": a2, "mu": mu(z1, a2, "v1"), "version": "v1", "z_obs": z2,
                    "residual": (z2[0]-mu(z1, a2, "v1")[0], z2[1]-mu(z1, a2, "v1")[1])})
        # Goal: a point offset from z2, reachable by a different a1 in principle.
        goal = (z2[0] + random.uniform(-0.8, 0.8), z2[1] + random.uniform(-0.8, 0.8))
        # Search a1' candidates, score by chained estimate, pick best.
        candidates = [rand_vec(1.0) for _ in range(60)]
        def chained_estimate(a1p):
            # step 1 correction from record
            m1 = mu(z0, a1, "v1"); mp1 = mu(z0, a1p, "v1")
            z1_cf = (z1[0] + mp1[0] - m1[0], z1[1] + mp1[1] - m1[1])
            # step 2: model from z1_cf, plus recorded residual 2
            m2 = mu(z1, a2, "v1")
            r2v = (z2[0]-m2[0], z2[1]-m2[1])
            z2_est = (mu(z1_cf, a2, "v1")[0] + r2v[0], mu(z1_cf, a2, "v1")[1] + r2v[1])
            return z2_est
        def naive_estimate(a1p):
            # ignore disturbances entirely, mu only, chained
            z1n = mu(z0, a1p, "v1")
            return mu(z1n, a2, "v1")
        def dist(p, q):
            return math.hypot(p[0]-q[0], p[1]-q[1])
        best_chain = min(candidates, key=lambda ap: dist(chained_estimate(ap), goal))
        best_naive = min(candidates, key=lambda ap: dist(naive_estimate(ap), goal))
        # True outcome of the chosen a1', same disturbances d1, d2
        z1_true = true_step(z0, best_chain, d1)
        z2_true = true_step(z1_true, a2, d2)
        z1_true_n = true_step(z0, best_naive, d1)
        z2_true_n = true_step(z1_true_n, a2, d2)
        total += 1
        if dist(z2_true, goal) < goal_radius:
            chain_success += 1
        if dist(z2_true_n, goal) < goal_radius:
            naive_success += 1
        # One-step hindsight reference: what a2' would have reached the goal
        # from z1, using the one-step correction. That is the paper's own
        # hindsight planning, for comparison, not a chain.
        cands2 = [rand_vec(1.0) for _ in range(60)]
        def one_step_est(a2p):
            m = mu(z1, a2, "v1"); mp = mu(z1, a2p, "v1")
            return (z2[0] + mp[0] - m[0], z2[1] + mp[1] - m[1])
        best2 = min(cands2, key=lambda ap: dist(one_step_est(ap), goal))
        z2_one = true_step(z1, best2, d2)
        if dist(z2_one, goal) < goal_radius:
            one_step_success += 1
    return {
        "n": total,
        "goal_radius": goal_radius,
        "chained_record_success_rate": chain_success / total,
        "naive_mu_only_success_rate": naive_success / total,
        "one_step_hindsight_success_rate": one_step_success / total,
        "record_entries": len(rec.entries),
    }

if __name__ == "__main__":
    holding = run_holding()
    chaining = run_chaining()
    print(json.dumps({"holding": holding, "chaining": chaining}, indent=2))
    with open("results.json", "w") as f:
        json.dump({"holding": holding, "chaining": chaining, "seed": SEED}, f, indent=2)
