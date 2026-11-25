# Keeping the What-If: A Record for Counterfactual World Models

Darren Hall
November 25, 2026

## Abstract

A world model trained only on what did happen cannot answer what would have happened under a different action, no matter how much data or capacity it has. Balestriero, LeCun, and Varaku solve the one-step version of that problem [1]. This note does not correct their paper. It asks a separate question: what does an agent need in order to ask that what-if later, after the step is over, for hindsight planning, debugging, and audit? The what-if for one transition is asked about that transition, not about the next one. A record does not change that. The proposal here is a record as one way to hold the observed outcome for later use, not the only way, and not a way the paper itself needs. Stacking that fix across steps is an open question, not a proven result, and this note states the test that would settle it.

## 1. What the paper shows

World models work in a world they cannot fully observe. A hidden disturbance, like a current pushing a boat, can change the outcome of an action. The question that follows is simple to ask and hard to answer: what would have happened under a different action, under the same disturbance? The answer separates a bad decision from bad luck.

The paper proves that a world model trained only on factual transitions cannot answer that question on its own, whatever its data or capacity [1]. A model that predicts what happens on average cannot tell you what would have happened this once, under this disturbance.

Their fix is one subtraction. The counterfactual outcome is the observed outcome plus the model prediction under the alternative action minus the model prediction under the factual action. It needs no counterfactual data, no extra parameters, and no retraining. On four rendered simulators it lifts counterfactual R2 from 38-46 percent to 86-96 percent with the same world models. In hindsight planning it finds the action that would have reached the goal in 35-69 percent of events, against 14-23 percent for an oracle planner that knows the simulator but not the outcome. The error bound is O(h^2) in the transition duration [1].

The paper is honest about its limits, and that honesty is what makes the next question visible. The work is in simulation only, it covers one transition at a time, and it fails at discontinuities, at coordinate folds, and where a disturbance scales the command itself [1].

## 2. What the paper does not try to do

The paper solves one transition. That is its job, and it does it. It does not try to solve how an agent holds the outcome after the transition ends, or how it reuses that outcome later. That is a separate problem, not a flaw in the paper.

An agent that lives in a chain of transitions may still want to ask, later, what would have happened at step one. That later question is hindsight planning, debugging, and audit, not planning step two. Step two has its own what-if, about step two, and it does not need step one's outcome to compute it. The formula needs the observed outcome at the moment the what-if is asked. If the outcome is gone by then, the subtraction cannot be done. Holding it is storage and provenance work. The paper does not do that work, because that was not its question.

A carpenter knows the move. Roll a big fender washer along a wonky wall and it transfers the wall's shape onto the wood without ever measuring the wall itself. The paper does the same thing with a model. It never measures the current. It transfers the gap. The question here is how that transferred gap is kept, so it can be used again later.

## 3. The record, stated as a proposal

The proposal is a record kept in knowledge time: the what, when, and why of machine justification [2]. This is a proposal, not a built system. Reference [2] is a candidate law in a reconstructed model, and reference [3] is a design proposal with no implementation and no test yet. This note does not hide that. It proposes the record, it does not claim the record is proven.

A record entry for one transition holds, in plain terms:

- the representation the system started from, z_t, and the action it took, a_t
- the factual prediction it made, mu(z_t, a_t), and the encoder and predictor version it relied on
- the observed outcome, z_{t+1}
- the residual, z_{t+1} minus mu(z_t, a_t), which is the proxy for the disturbance

The alternative prediction, mu(z_t, a'), is not stored at act time. It is computed at query time, using the stored z_t and the stored predictor version, when a what-if is asked. Mixing act time and query time would hide which prediction was made when.

That mapping is the whole point of this section. Belief, in this note, means what the system relied on: the encoder and predictor version, and the prediction it made. The disturbance itself is not stored. What is stored is the residual, which is the difference that stands in for the disturbance for that transition, not as a measured current.

This is not a replay buffer under another name. A replay buffer stores transitions for training, and it is sampled, overwritten, and reused without keeping what was relied on or why. This record is kept for justification, not for training. It keeps the reliance and its authority with the outcome, it does not overwrite old entries, and it does not reuse a stale representation blindly: the encoder version is recorded, so an old z_t is not mistaken for a current one if the encoder changes.

Knowledge time [2] is what ties reliance to time here. K time tracks the authority of what the system relied on as that authority changes. When the predictor version changes, old entries keep their old authority and new entries get the new authority, so a residual from an old predictor is not read as if it came from the new one. That is the link between K time and the transition: authority over the predictor, tracked over time, not a second clock on the transition duration h.

For this use, every transition gets an outcome entry, because any step may be asked what-if later. That is different from the reliance layer in [2] and [3], where a new entry is made only when what the system relies on changes. The two layers are separate. The outcome layer is dense, one entry per transition. The reliance layer is sparse, one entry per change.

Trust, in this note, means one thing only: tamper evidence. The record is append-only. A revision is a new entry, and the earlier entry stays on the record with its own time and authority [3]. Under the proposal in [3], entries would be hash-chained, so a change to an old entry would be detectable. That does not make the content true. It makes a change visible. A record can be wrong and still be tamper-evident, and this note does not claim otherwise. If the recorded z or predictor version is wrong, the residual is wrong and the counterfactual is wrong. Tamper evidence does not fix that. What it does fix is attribution: the wrongness is traceable to a specific predictor version, encoder version, and residual, instead of being hidden in an overwritten log.

## 4. Stacking is an open question

With a record, the one-step fix can be tried across a chain. That does not mean it works across a chain. That is the question to test, not a result to claim.

Take the boat. Step one ends with an observed outcome. Step two starts from that outcome, which already carries the effect of step one's disturbance on the state. The residual from step one is not carried into step two as a separate thing. It belongs to step one. Step two has its own disturbance and its own residual, and its own O(h^2) error. What the record carries forward is not the residual, it is the outcome and the reliance behind it, so step one's what-if can still be asked later.

That distinction gives two separate tests, and they must not be mixed. First, the holding test: ask step one's what-if later, using the recorded outcome, and measure whether counterfactual R2 is the same as when it was asked immediately. That tests whether the record preserves accuracy over time. It does not test whether the record improves the model. If accuracy falls, the record failed to hold what was needed. If it holds, the record did its job, and no more.

Second, the chaining test: ask what action at step one would have made the goal at step two reachable. That is a harder, backward question, not the one-step question in [1]. It requires chaining a counterfactual from step two back through step one, and errors add across steps unless something offsets them. A naive chain should be expected to degrade, not to improve. Stacking cannot be assumed. It has to be tested in the counterfactual setting itself, because the logic alone gives no reason to expect a growing advantage.

If the chaining test degrades, the record is still useful for one-step what-ifs asked later and for audit, but not for planning across steps. Either result is informative, and this note does not prejudge it.

## 5. Scope

This note does not claim the record fixes the paper's limits. It does not make a simulated result real, it does not fix discontinuities or coordinate folds, and it does not answer what happens when a disturbance scales the command. It does not prove stacking. It does not prove that a record is necessary. The paper needs an observed outcome in memory at the moment of use. A record is one way to hold it over time.

The claim here is narrower. Where the paper has a formula that needs an observed outcome and a rule that covers one step, a record of the kind proposed in [2] and [3] is one way to hold that outcome for later use, with its reliance and its residual written down where they can be checked. Whether that holding lets the step stack into a plan is a test, not a conclusion.

## References

[1] Balestriero, R., LeCun, Y., Varaku, K. Counterfactual World Models: JEPAs That Reason About What If. arXiv:2611.24778, November 18, 2026. https://arxiv.org/abs/2611.24778

[2] Hall, D. The Tritemporal Field Law: K Time, A Third Clock for Memory. alphaXiv v1.8, October 6, 2026. https://www.alphaxiv.org/abs/2611.tritemporal-field-law-memory Zenodo v1.9, November 22, 2026, DOI 10.5281/zenodo.24450290. https://zenodo.org/records/24450290

[3] Hall, D. A Record for Persistent Latent State: Knowledge Time and the Latent Lattice. alphaXiv, November 19, 2026. https://www.alphaxiv.org/abs/2611.persistent-latent-state-knowledge-time Zenodo, DOI 10.5281/zenodo.24375625. https://zenodo.org/records/24375625
