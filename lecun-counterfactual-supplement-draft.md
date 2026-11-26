# Keeping the What-If: A Record for Counterfactual World Models

Darren Hall
November 26, 2026

## Abstract

This note is built around its findings. A record that holds the observed outcome lets an agent ask a what-if later, and the gain is measured in percent. One event: 82.6% improvement. Mean across 2000 events: 65.9% improvement. Chaining across two steps: 408% improvement in goals reached. From WILD to MATURE trust: 264% improvement. A retest measures slow after fast's authority collapses: slow holds at 0.696 while fast cannot answer. The rest of this note explains the record that produced those numbers, and the limits that still apply to them.

A world model trained only on what did happen cannot answer what would have happened under a different action, whatever its data or capacity. Balestriero, LeCun, and Varaku solve the one-step version of that problem [1]. This note does not correct their paper. It asks a separate question: what does an agent need in order to ask that what-if later, after the step is over, for hindsight planning, debugging, and audit? The proposal here is a record as one way to hold the observed outcome for later use, not the only way, and not a way the paper itself needs.

## 1. What the paper shows

World models work in a world they cannot fully observe. A hidden disturbance, like a current pushing a boat, can change the outcome of an action. The question that follows is simple to ask and hard to answer: what would have happened under a different action, under the same disturbance? The answer separates a bad decision from bad luck.

The paper proves that a world model trained only on factual transitions cannot answer that question on its own, whatever its data or capacity [1]. A model that predicts what happens on average cannot tell you what would have happened this once, under this disturbance.

Their fix is one subtraction. The counterfactual outcome is the observed outcome plus the model prediction under the alternative action minus the model prediction under the factual action. It needs no counterfactual data, no extra parameters, and no retraining. On four rendered simulators it lifts counterfactual R2 from 38-46 percent to 86-96 percent with the same world models. In hindsight planning it finds the action that would have reached the goal in 35-69 percent of events, against 14-23 percent for an oracle planner that knows the simulator but not the outcome. The error bound is O(h^2) in the transition duration [1].

The paper is honest about its limits, and that honesty is what makes the next question visible. The work is in simulation only, it covers one transition at a time, and it fails at discontinuities, at coordinate folds, and where a disturbance scales the command itself [1].

## 2. Findings

This note centralizes around these findings. All gains are in percent. Demo and code: https://github.com/iamvolshi/lecun-counterfactual-demo, live at https://iamvolshi.github.io/lecun-counterfactual-demo/.

The test world is a toy boat, 2D, seed 20261125, n=2000 events. True dynamics: z' = z + a * s(z) + d, s = 1 + 0.4 sin(x) + 0.3 cos(y). Model mu(z, a) = z + a. Disturbance d is a hidden current. This is a toy simulation, not the paper's rendered simulators, not a JEPA, not a learned encoder.

Event 14. Start (1.41, 0.12). True what-if outcome (1.06, 1.77). Without the record, factual prediction (1.53, 0.82), misses by 1.07 units. With the record, corrected prediction (1.11, 1.59), misses by 0.19 units. Gain: 82.6% improvement.

Across all 2000 events, mean miss: factual 0.94 units, corrected 0.32 units. Gain: 65.9% improvement. Median miss: 0.88 down to 0.24. Gain: 72.7% improvement.

Holding test: ask the what-if later, from the record, versus immediately. Corrected R2 on the change: factual only 0.448, corrected immediately 0.913, corrected later from the record 0.913. The later answer is identical to the immediate answer. The record held what was needed, with no loss.

Trust levels, same 2000 events, run again as if every entry were at that level. Holding R2: WILD 0.241, CANDIDATE 0.716, MATURE fast 0.877, MATURE slow 0.698, REVOKED 0.516, REVOKED gated: cannot-answer, no wrong answer. Gain from WILD to MATURE fast: 264% improvement. Those numbers are measured immediately, right after the event. A retest measures them again after fast's authority collapses. The predictor version advances from v1 to v2, which revokes fast's single-visit entries. The world returns to baseline and slow holds the record for 600 more ticks. Measured after that: MATURE slow 0.696, MATURE fast cannot-answer, MATURE fast forced under v2 0.516. Slow sits 34.9% above forced fast. Fast loses 0.361 R2 points to the collapse, 41.2% of its immediate number. That loss is the scar, measured after the return to baseline. The limit: slow's number rests on the record holding the stored predictor version. Forced through the live v2 predictor, slow drops to 0.333.

Chaining test: two steps, goal at step 2. Naive plan reaches the goal 12 percent of the time. Chained plan, with the record, reaches it 61 percent of the time. Gain: 408% improvement. One-step hindsight reaches it 66 percent of the time, so chaining does not beat one-step. Slow chain, MATURE, reaches it 23.8 percent of the time. Measured immediately, slow is worse for hindsight on a specific event, because it replaces the actual disturbance with the regional mean. That ranking holds only for the immediate measurement. After fast's authority collapses, slow is the one still standing: 0.696 against fast's cannot-answer. Fast is for this event, slow is for the domain.

## 3. What the paper does not try to do

The paper solves one transition. It does not try to solve how an agent holds the outcome after the transition ends, or how it reuses that outcome later. That is a separate problem, not a flaw in the paper.

An agent that lives in a chain of transitions may still want to ask, later, what would have happened at step one. That later question is hindsight planning, debugging, and audit, not planning step two. Step two has its own what-if, about step two, and it does not need step one's outcome to compute it. The formula needs the observed outcome at the moment the what-if is asked. If the outcome is gone by then, the subtraction cannot be done.

A carpenter knows the move. Roll a big fender washer along a wonky wall and it transfers the wall's shape onto the wood without ever measuring the wall itself. The paper does the same thing with a model. It never measures the current. It transfers the gap. The question here is how that transferred gap is kept, so it can be used again later.

## 4. The record, stated as a proposal

The proposal is a record kept in knowledge time: the what, when, and why of machine justification [2]. This is a proposal, not a built system. Reference [2] is a candidate law in a reconstructed model, and reference [3] is a design proposal with no implementation and no test yet. This note proposes the record, it does not claim the record is proven.

A record entry for one transition holds, in plain terms:

- the representation the system started from, z_t, and the action it took, a_t
- the factual prediction it made, mu(z_t, a_t), and the encoder and predictor version it relied on
- the observed outcome, z_{t+1}
- the residual, z_{t+1} minus mu(z_t, a_t), which is the proxy for the disturbance

The alternative prediction, mu(z_t, a'), is not stored at act time. It is computed at query time, using the stored z_t and the stored predictor version, when a what-if is asked. Mixing act time and query time would hide which prediction was made when.

Belief, in this note, means what the system relied on: the encoder and predictor version, and the prediction it made. The disturbance itself is not stored. What is stored is the residual, the difference that stands in for the disturbance for that transition.

This is not a replay buffer under another name. A replay buffer stores transitions for training, and it is sampled, overwritten, and reused without keeping what was relied on or why. This record is kept for justification, not for training. It keeps the reliance and its authority with the outcome, it does not overwrite old entries, and it does not reuse a stale representation blindly: the encoder version is recorded, so an old z_t is not mistaken for a current one if the encoder changes.

Knowledge time [2] is what ties reliance to time here. K time tracks the authority of what the system relied on as that authority changes. When the predictor version changes, old entries keep their old authority and new entries get the new authority, so a residual from an old predictor is not read as if it came from the new one. That is the link between K time and the transition: authority over the predictor, tracked over time, not a second clock on the transition duration h.

For this use, every transition gets an outcome entry, because any step may be asked what-if later. That is different from the reliance layer in [2] and [3], where a new entry is made only when what the system relies on changes. The two layers are separate. The outcome layer is dense, one entry per transition. The reliance layer is sparse, one entry per change.

Trust, in this note, means one thing only: tamper evidence. The record is append-only. A revision is a new entry, and the earlier entry stays on the record with its own time and authority [3]. Under the proposal in [3], entries would be hash-chained, so a change to an old entry would be detectable. That does not make the content true. A record can be wrong and still be tamper-evident. If the recorded z or predictor version is wrong, the residual is wrong and the counterfactual is wrong. What tamper evidence does fix is attribution: the wrongness is traceable to a specific predictor version, encoder version, and residual, instead of being hidden in an overwritten log.

## 5. Stacking, measured

With a record, the one-step fix can be tried across a chain. Measured in Section 2, it works, but it does not beat one-step: 61 percent against 66 percent. Stacking does not compound in the good direction in this toy.

Take the boat. Step one ends with an observed outcome. Step two starts from that outcome, which already carries the effect of step one's disturbance on the state. The residual from step one is not carried into step two as a separate thing. It belongs to step one. Step two has its own disturbance and its own residual, and its own O(h^2) error. What the record carries forward is not the residual, it is the outcome and the reliance behind it, so step one's what-if can still be asked later.

The two tests must not be mixed. First, the holding test: ask step one's what-if later, using the recorded outcome, and measure whether counterfactual R2 is the same as when it was asked immediately. If accuracy falls, the record failed to hold what was needed. If it holds, the record did its job, and no more.

Second, the chaining test: ask what action at step one would have made the goal at step two reachable. That is a harder, backward question, not the one-step question in [1]. It requires chaining a counterfactual from step two back through step one, and errors add across steps unless something offsets them.

The record is still useful for one-step what-ifs asked later and for audit, and for chaining over naive, but not for planning across steps better than one-step.

## 6. Scope

This note does not claim the record fixes the paper's limits. It does not make a simulated result real, it does not fix discontinuities or coordinate folds, and it does not answer what happens when a disturbance scales the command. It does not prove stacking. It does not prove that a record is necessary. The paper needs an observed outcome in memory at the moment of use. A record is one way to hold it over time. The findings in Section 2 are from a toy simulation, not from the paper's simulators, not from a JEPA, and not from a learned encoder.

The claim here is narrower, and it is the findings. Where the paper has a formula that needs an observed outcome and a rule that covers one step, a record of the kind proposed in [2] and [3] holds that outcome for later use, with its reliance and its residual written down where they can be checked. The gain from holding it is measured in percent in Section 2.

## References

[1] Balestriero, R., LeCun, Y., Varaku, K. Counterfactual World Models: JEPAs That Reason About What If. arXiv:2611.24778, November 18, 2026. https://arxiv.org/abs/2611.24778

[2] Hall, D. The Tritemporal Field Law: K Time, A Third Clock for Memory. alphaXiv v1.8, October 6, 2026. https://www.alphaxiv.org/abs/2611.tritemporal-field-law-memory Zenodo v1.9, November 22, 2026, DOI 10.5281/zenodo.24450290. https://zenodo.org/records/24450290

[3] Hall, D. A Record for Persistent Latent State: Knowledge Time and the Latent Lattice. alphaXiv, November 19, 2026. https://www.alphaxiv.org/abs/2611.persistent-latent-state-knowledge-time Zenodo, DOI 10.5281/zenodo.24375625. https://zenodo.org/records/24375625
