#!/usr/bin/env python
"""
scipy port of DrugowitschLab/ConnectomeInfluenceCalculator v0.3.

The original requires petsc4py + slepc4py, which have no binary wheels for this
platform. PETSc/SLEPc are used for exactly two things -- the largest real
eigenvalue and a sparse linear solve -- both of which scipy.sparse does. This
reproduces the algorithm step for step:

    W[post, pre] = c_ij / N_i        (input-normalized, accumulated)
    silence      -> zero those columns
    rescale      -> W *= 0.99/lambda_max   if lambda_max > 0.99
    shift        -> W -= I
    solve        -> (W - I) x = -s
    influence    -> |Re(x)|

Validated against a dense exact solve on the authors' toy fixture.
"""
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla


def build_W(pre, post, weight, ids=None):
    """Sparse W with rows=postsynaptic, cols=presynaptic. Duplicate edges sum."""
    if ids is None:
        ids = np.unique(np.concatenate([np.asarray(post), np.asarray(pre)]))
    index = {nid: i for i, nid in enumerate(ids)}
    n = len(ids)
    r = np.fromiter((index[i] for i in post), dtype=np.int64, count=len(post))
    c = np.fromiter((index[i] for i in pre), dtype=np.int64, count=len(pre))
    W = sp.coo_matrix((np.asarray(weight, dtype=float), (r, c)), shape=(n, n)).tocsr()
    W.sum_duplicates()
    return W, index, ids


def largest_real_eigenvalue(W):
    """Largest real eigenvalue, matching SLEPc EPS LARGEST_REAL."""
    n = W.shape[0]
    if n < 3:
        return float(np.max(np.linalg.eigvals(W.toarray()).real))
    try:
        v = spla.eigs(W, k=1, which="LR", return_eigenvectors=False,
                      maxiter=10000, tol=1e-10)
        return float(np.real(v[0]))
    except Exception:
        return float(np.max(np.linalg.eigvals(W.toarray()).real))


def influence(W, seed_idx, silenced_idx=(), dense=False):
    """Steady-state influence of the seed set on every neuron."""
    n = W.shape[0]
    s = np.zeros(n)
    s[list(seed_idx)] = 1.0

    A = W.tolil(copy=True)
    silenced = np.setdiff1d(np.asarray(list(silenced_idx), dtype=np.int64),
                            np.asarray(list(seed_idx), dtype=np.int64))
    if silenced.size:
        A[:, silenced] = 0.0          # silenced cells emit nothing
    A = A.tocsr()

    lam = largest_real_eigenvalue(A)
    if lam > 0.99:
        A = A * (0.99 / lam)
    A = A - sp.identity(n, format="csr")

    if dense:
        x = np.linalg.solve(A.toarray(), -s)
    else:
        x = spla.spsolve(A.tocsc(), -s)
    return np.abs(np.real(x))


def adjusted(r, c=24.0):
    """Paper's 'adjusted influence': log(r) + c, floored at 0."""
    with np.errstate(divide="ignore"):
        a = np.log(r) + c
    return np.where(np.isfinite(a), np.maximum(a, 0.0), 0.0)


if __name__ == "__main__":
    import sqlite3
    import pandas as pd
    import sys

    db = sys.argv[1] if len(sys.argv) > 1 else (
        "cic/DrugowitschLab-ConnectomeInfluenceCalculator-e31fe5b/"
        "tests/toy_network_example.sqlite")
    con = sqlite3.connect(db)
    meta = pd.read_sql_query("SELECT * FROM meta", con)
    el = pd.read_sql_query("SELECT * FROM edgelist_simple WHERE count >= 5", con)
    con.close()

    W, index, ids = build_W(el["pre"], el["post"], el["norm"])
    print(f"toy network: {W.shape[0]} neurons, {W.nnz} edges")

    seed = [index[i] for i in meta.loc[meta.seed_01 == "olfactory", "root_id"] if i in index]
    sil = [index[i] for i in meta.loc[meta.super_class.isin(["sensory", "ascending_sensory"]),
                                      "root_id"] if i in index]
    print(f"seed: {len(seed)}   silenced: {len(sil)}")

    r_sparse = influence(W, seed, sil, dense=False)
    r_dense = influence(W, seed, sil, dense=True)
    err = np.max(np.abs(r_sparse - r_dense))
    print(f"max |sparse - dense exact| = {err:.3e}   -> {'MATCH' if err < 1e-9 else 'MISMATCH'}")

    out = pd.DataFrame({"id": ids, "influence": r_sparse, "adjusted": adjusted(r_sparse)})
    out["is_seed"] = out["id"].isin([ids[i] for i in seed])
    print(out.sort_values("influence", ascending=False).to_string(index=False))
