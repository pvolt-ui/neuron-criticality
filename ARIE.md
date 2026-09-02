# Project in four lines

**Question** — Which neurons are the chokepoints from each sense (smell, touch, vision)
to the motor-command neurons, are any shared across senses, and does the fly need them?

**Approach** — Rank them by synapse-weighted betweenness in FlyWire; then try to break
the ranking three ways: degree-preserving null, a selection-bias control on that null,
and deleting the neuron outright. Replicate the whole thing in the male CNS.

**Progress** — Done, all four pathways. Bottlenecks are real, anatomically sensible, and
conserved (9/12/13 of the top 25 cell types replicate in a second brain) — but redundant:
deleting any one lengthens routes ~0.5% and disconnects nothing. Six neurons of 200 are
shared across two senses, none across three. Two self-corrections caught along the way
(the first "visual" pathway was ocellar; the null was over-counting until controlled).

**Deliverable** — Ranked + validated bottleneck lists per pathway, cross-modal overlap,
cross-dataset replication, `RESULTS.md`, reproducible scripts, 5-slide talk + backups.
