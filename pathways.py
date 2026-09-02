"""
pathways.py -- single source of truth for which neurons are the *sources* of
each sensory pathway.

Why this exists: the original "visual" pathway used `class == "visual"`
(photoreceptors) as sources. Only 146 of 11,426 photoreceptors can reach a
descending neuron within the hop window, and 142 of those are OCELLAR
photoreceptors -- so that pathway was the ocellar reflex pathway, not compound-
eye vision. It is now named `ocellar`, and `visual` is rebuilt with the
lamina/medulla columnar input neurons the project spec asked for.

Downstream scripts must not re-derive sources from `class`; they read the
`is_source` column that build_pathway_subgraphs.py / prepare_mcns.py write into
subgraph_nodes_<modality>.csv, via source_mask() below (which falls back to the
old `class == modality` rule for node files written before this column existed).
"""
import pandas as pd

MODALITIES = ["olfactory", "mechanosensory", "visual", "ocellar"]
DESCENDING_CLASSES = {"descending", "motor"}

# Curated optic-lobe families (Codex visual_neuron_types.csv, Matsliah et al.
# 2024) that constitute the lamina and medulla columnar input stages.
VISUAL_INPUT_FAMILIES = {"Lamina Monopolar", "Transmedullary", "Medulla Intrinsic"}

SOURCE_DEFINITION = {
    "olfactory":      "classification class == olfactory (ORNs)",
    "mechanosensory": "classification class == mechanosensory (JO + other mechanosensory afferents)",
    "visual":         "visual_neuron_types family in {Lamina Monopolar, Transmedullary, Medulla Intrinsic}",
    "ocellar":        "classification class == visual AND sub_class == ocellar (ocellar photoreceptors)",
}


def fafb_source_ids(modality, classification, visual_types=None):
    """Root IDs of the sensory sources for a modality, FAFB v783 tables."""
    c = classification
    if modality in ("olfactory", "mechanosensory"):
        return set(c.loc[c["class"] == modality, "root_id"])
    if modality == "ocellar":
        return set(c.loc[(c["class"] == "visual") & (c["sub_class"] == "ocellar"), "root_id"])
    if modality == "visual":
        if visual_types is None:
            raise ValueError("visual sources need the visual_neuron_types table")
        return set(visual_types.loc[visual_types["family"].isin(VISUAL_INPUT_FAMILIES), "root_id"])
    raise ValueError(modality)


def source_mask(nodes_df, modality):
    """Boolean mask over a subgraph_nodes_<modality>.csv frame selecting sources."""
    if "is_source" in nodes_df.columns:
        return nodes_df["is_source"].astype(bool)
    # legacy node files (pre-`is_source`): class == modality, with the old
    # photoreceptor rule for ocellar
    if modality == "ocellar":
        return nodes_df["class"] == "visual"
    return nodes_df["class"] == modality


def source_ids(nodes_df, modality):
    return nodes_df.loc[source_mask(nodes_df, modality), "root_id"]


# --- MCNS (Janelia male CNS v0.9) ---------------------------------------------
# MCNS annotates no ocellar photoreceptors, so the "ocellar" pathway cannot be
# built there. Its `class == visual` neurons are compound-eye R1-R8; that
# pathway is kept under the honest name "photoreceptor" (it is NOT the FAFB
# ocellar pathway and the two must not be compared as replications).
MCNS_MODALITIES = ["olfactory", "mechanosensory", "visual", "photoreceptor"]
MCNS_SOURCE_DEFINITION = {
    "olfactory":      "Class == olfactory",
    "mechanosensory": "Class in mechanosensory{,_tactile,_proprioceptive,_tbc}",
    "visual":         "Primary Cell Type matches L[1-5] | Tm* | TmY* | Mi*  (lamina/medulla columnar inputs)",
    "photoreceptor":  "Class == visual (compound-eye R1-R8; MCNS has no ocellar PRs)",
}
_MCNS_VISUAL_RE = r"(L[1-5]|Tm\d+[a-z]*|TmY\d+[a-z]*|Mi\d+[a-z]*)"


def mcns_source_ids(modality, ann):
    """ann: mcns annotations frame with root_id, class (mapped), primary_type."""
    if modality in ("olfactory", "mechanosensory"):
        return set(ann.loc[ann["class"] == modality, "root_id"])
    if modality == "photoreceptor":
        return set(ann.loc[ann["class"] == "visual", "root_id"])
    if modality == "visual":
        pt = ann["primary_type"].fillna("").astype(str)
        return set(ann.loc[pt.str.fullmatch(_MCNS_VISUAL_RE), "root_id"])
    if modality == "ocellar":
        raise ValueError("MCNS has no ocellar photoreceptor annotations")
    raise ValueError(modality)
