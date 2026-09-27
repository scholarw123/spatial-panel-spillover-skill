# -*- coding: utf-8 -*-
"""Generic, configuration-driven v0.2–v0.4 extensions (no research data included).

Research protocol, not a causal-identification engine. Demonstration calculations use
balanced panels and one common time-invariant W. Baseline estimator uses concentrated
Gaussian likelihood with two-way demeaning; impact SE use numeric Hessian / delta method.
"""
from __future__ import annotations
import argparse
import json
import math
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar
from scipy.stats import norm
from statsmodels.tools.numdiff import approx_hess3
SEED=20260401

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))


def build_distance_matrix(units: Sequence[str], coordinates: Dict[str, Tuple[float, float]]) -> np.ndarray:
    n = len(units)
    D = np.zeros((n, n), dtype=float)
    for i, pi in enumerate(units):
        for j, pj in enumerate(units):
            if i != j:
                D[i, j] = haversine_km(*coordinates[pi], *coordinates[pj])
    return D


def row_standardize(A: np.ndarray) -> np.ndarray:
    A = np.asarray(A, dtype=float).copy()
    np.fill_diagonal(A, 0.0)
    rs = A.sum(axis=1)
    W = np.zeros_like(A)
    nz = rs > 0
    W[nz] = A[nz] / rs[nz, None]
    return W


def spectral_standardize(A: np.ndarray) -> np.ndarray:
    A = np.asarray(A, dtype=float).copy()
    np.fill_diagonal(A, 0.0)
    sr = float(np.max(np.abs(np.linalg.eigvals(A)))) if np.any(A) else 0.0
    return A / sr if sr > 0 else A


def symmetric_standardize(A: np.ndarray) -> np.ndarray:
    A = np.asarray(A, dtype=float).copy()
    np.fill_diagonal(A, 0.0)
    d = A.sum(axis=1)
    inv = np.zeros_like(d)
    positive = d > 0
    inv[positive] = 1 / np.sqrt(d[positive])
    return inv[:, None] * A * inv[None, :]


def global_standardize(A: np.ndarray, target_sum: Optional[float] = None) -> np.ndarray:
    A = np.asarray(A, dtype=float).copy()
    np.fill_diagonal(A, 0.0)
    if target_sum is None:
        target_sum = A.shape[0]
    total = A.sum()
    return A * (target_sum / total) if total > 0 else A


def inverse_distance_A(D: np.ndarray, alpha: float = 1.0, cutoff_km: Optional[float] = None) -> np.ndarray:
    A = np.zeros_like(D, dtype=float)
    mask = D > 0
    if cutoff_km is not None:
        mask &= D <= cutoff_km
    A[mask] = D[mask] ** (-float(alpha))
    return A


def knn_A(D: np.ndarray, k: int = 4, symmetrize: str = "union") -> np.ndarray:
    """K-nearest-neighbour binary adjacency based on distance.

    symmetrize='union' means i-j is an edge if either i selects j or j selects i.
    This gives a symmetric graph and is the default for the spatial-panel runner.
    """
    n = D.shape[0]
    if not 1 <= k < n: raise ValueError("k must be between 1 and n-1")
    A = np.zeros((n, n), dtype=float)
    for i in range(n):
        row = D[i].copy()
        row[i] = np.inf
        js = np.argsort(row)[:k]
        A[i, js] = 1.0
    if symmetrize == "union":
        A = ((A + A.T) > 0).astype(float)
    elif symmetrize == "intersection":
        A = ((A > 0) & (A.T > 0)).astype(float)
    elif symmetrize != "none":
        raise ValueError("symmetrize must be union/intersection/none")
    return A


def distance_band_A(D: np.ndarray, cutoff_km: float, weighted: bool = True, alpha: float = 1.0) -> np.ndarray:
    mask = (D > 0) & (D <= cutoff_km)
    A = np.zeros_like(D, dtype=float)
    if weighted:
        A[mask] = D[mask] ** (-float(alpha))
    else:
        A[mask] = 1.0
    return A


def distance_ring_A(D: np.ndarray, lower_km: float, upper_km: float, weighted: bool = True) -> np.ndarray:
    mask = (D > lower_km) & (D <= upper_km)
    A = np.zeros_like(D, dtype=float)
    A[mask] = 1.0 / D[mask] if weighted else 1.0
    return A


def economic_anchor(panel: pd.DataFrame, column: str, id_col: str, labels: Sequence[str]) -> np.ndarray:
    """Time-invariant economic anchor: period mean by spatial unit.

    Using a period mean keeps W common across t. A time-varying economic W_t would
    require a different estimator and should not be silently passed to this runner.
    """
    m = panel.groupby(id_col, observed=False)[column].mean()
    return m.reindex(labels).to_numpy(float)


def economic_A(
    anchor: np.ndarray,
    method: str = "gaussian",
    bandwidth: Optional[float] = None,
    epsilon: Optional[float] = None,
) -> Tuple[np.ndarray, Dict[str, float]]:
    diff = np.abs(anchor[:, None] - anchor[None, :])
    np.fill_diagonal(diff, np.inf)
    vals = diff[np.isfinite(diff)]

    if method == "gaussian":
        if bandwidth is None:
            positive_vals = vals[vals > 0]
            bandwidth = float(np.median(positive_vals)) if positive_vals.size else 1.0
        if bandwidth <= 0: raise ValueError("Economic Gaussian bandwidth must be > 0")
        A = np.exp(-0.5 * (diff / bandwidth) ** 2)
        np.fill_diagonal(A, 0.0)
        return A, {"bandwidth": float(bandwidth)}

    if method == "inverse":
        if epsilon is None:
            # A documented stabilizer is essential because 1/|g_i-g_j| can explode.
            positive_vals = vals[vals > 0]
            epsilon = float(np.quantile(positive_vals, 0.05)) if positive_vals.size else 1.0
        if epsilon <= 0: raise ValueError("Economic inverse epsilon must be > 0")
        A = np.zeros_like(diff)
        finite = np.isfinite(diff)
        A[finite] = 1.0 / (diff[finite] + epsilon)
        np.fill_diagonal(A, 0.0)
        return A, {"epsilon": float(epsilon)}

    raise ValueError("economic method must be gaussian or inverse")


def geo_economic_nested_A(A_geo: np.ndarray, A_econ: np.ndarray) -> np.ndarray:
    """Multiplicative nesting: geography and economic similarity must both be strong."""
    A = np.asarray(A_geo, float) * np.asarray(A_econ, float)
    np.fill_diagonal(A, 0.0)
    return A


def contiguity_A_from_geometries(geometries: Sequence, mode: str = "queen", tol: float = 1e-12) -> np.ndarray:
    """Build Queen/Rook adjacency from polygon geometries.

    Queen: boundaries intersect at a point or a segment.
    Rook:  boundaries share a segment with positive length.
    """
    n = len(geometries)
    A = np.zeros((n, n), dtype=float)
    for i in range(n):
        bi = geometries[i].boundary
        for j in range(i + 1, n):
            inter = bi.intersection(geometries[j].boundary)
            if mode == "queen":
                linked = not inter.is_empty
            elif mode == "rook":
                linked = (not inter.is_empty) and float(getattr(inter, "length", 0.0)) > tol
            else:
                raise ValueError("mode must be queen or rook")
            if linked:
                A[i, j] = A[j, i] = 1.0
    return A


def contiguity_A_from_boundary_file(
    boundary_path: str,
    id_col: str,
    mode: str = "queen",
    unit_order: Sequence[str] = (),
) -> np.ndarray:
    try:
        import geopandas as gpd
    except Exception as exc:
        raise RuntimeError("Queen/Rook from a boundary file requires geopandas.") from exc

    gdf = gpd.read_file(boundary_path)
    if id_col not in gdf.columns:
        raise ValueError(f"Boundary id column not found: {id_col}")
    gdf[id_col] = gdf[id_col].astype(str)
    if gdf[id_col].duplicated().any(): raise ValueError("Duplicate boundary ids")
    if set(gdf[id_col]) != set(unit_order): raise ValueError("Boundary ids must match panel ids exactly")
    gdf = gdf.set_index(id_col).reindex(list(unit_order))
    if gdf.geometry.isna().any():
        missing = gdf.index[gdf.geometry.isna()].tolist()
        raise ValueError(f"Boundary file cannot match these units: {missing}")
    return contiguity_A_from_geometries(gdf.geometry.to_list(), mode=mode)


def diagnose_W(A: np.ndarray, W: Optional[np.ndarray] = None, labels: Optional[Sequence[str]] = None) -> Dict[str, object]:
    A = np.asarray(A, float)
    if labels is None: labels = [f"U{i+1}" for i in range(A.shape[0])]
    binary = (A > 0).astype(int)
    np.fill_diagonal(binary, 0)
    counts = binary.sum(axis=1)
    G = nx.from_numpy_array(binary, create_using=nx.Graph)
    components = list(nx.connected_components(G))
    isolate_idx = np.where(counts == 0)[0].tolist()
    positive = A[A > 0]
    out: Dict[str, object] = {
        "min_neighbors": int(counts.min()),
        "mean_neighbors": float(counts.mean()),
        "max_neighbors": int(counts.max()),
        "isolates": len(isolate_idx),
        "isolated_units": [labels[i] for i in isolate_idx],
        "components": len(components),
        "largest_component": max((len(c) for c in components), default=0),
        "density": float(binary.sum() / (len(labels) * (len(labels) - 1))),
        "asymmetry_share": float(np.count_nonzero(binary != binary.T) / binary.size),
        "raw_row_sum_min": float(A.sum(axis=1).min()),
        "raw_row_sum_max": float(A.sum(axis=1).max()),
        "raw_weight_min_positive": float(positive.min()) if positive.size else 0.0,
        "raw_weight_max": float(positive.max()) if positive.size else 0.0,
    }
    if W is not None and np.any(W):
        out["W_spectral_radius"] = float(np.max(np.abs(np.linalg.eigvals(W))))
    return out


def moran_i(x: np.ndarray, W: np.ndarray) -> float:
    x = np.asarray(x, float)
    z = x - x.mean()
    s0 = W.sum()
    if s0 <= 0 or z @ z == 0: return float("nan")
    return float(len(x) / s0 * (z @ W @ z) / (z @ z))


def bivariate_moran_i(x: np.ndarray, y: np.ndarray, W: np.ndarray) -> float:
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    if W.sum() <= 0 or x.std() <= 0 or y.std() <= 0: return float("nan")
    zx = (x - x.mean()) / x.std(ddof=0)
    zy = (y - y.mean()) / y.std(ddof=0)
    return float(zx @ W @ zy / float(W.sum()))


def permutation_global_moran(x: np.ndarray, W: np.ndarray, permutations: int = 999, seed: int = SEED) -> Tuple[float, float]:
    rng = np.random.default_rng(seed)
    observed = moran_i(x, W)
    sims = np.array([moran_i(rng.permutation(x), W) for _ in range(permutations)])
    p = (1 + np.sum(sims >= observed)) / (permutations + 1) if observed >= 0 else (1 + np.sum(sims <= observed)) / (permutations + 1)
    return observed, float(p)


def permutation_bivariate_moran(x: np.ndarray, y: np.ndarray, W: np.ndarray, permutations: int = 999, seed: int = SEED) -> Tuple[float, float]:
    rng = np.random.default_rng(seed)
    observed = bivariate_moran_i(x, y, W)
    sims = np.array([bivariate_moran_i(x, rng.permutation(y), W) for _ in range(permutations)])
    p = (1 + np.sum(sims >= observed)) / (permutations + 1) if observed >= 0 else (1 + np.sum(sims <= observed)) / (permutations + 1)
    return observed, float(p)


def local_moran(
    x: np.ndarray,
    W: np.ndarray,
    permutations: int = 999,
    seed: int = SEED,
    alpha: float = 0.05,
) -> pd.DataFrame:
    """Conditional-randomization Local Moran table.

    For each focal unit i, z_i is held fixed and values of the other n-1 units
    are randomly reassigned to i's weights. The pseudo p-value uses |I_i|.
    """
    x = np.asarray(x, float)
    if x.std(ddof=0) <= 0: raise ValueError("Local Moran requires nonconstant x")
    z = (x - x.mean()) / x.std(ddof=0)
    lag_z = W @ z
    local_i = z * lag_z
    rng = np.random.default_rng(seed)
    pvals = np.ones(len(x), dtype=float)

    for i in range(len(x)):
        others = np.delete(z, i)
        weights = np.delete(W[i], i)
        sims = np.empty(permutations, dtype=float)
        for b in range(permutations):
            sims[b] = z[i] * float(weights @ rng.permutation(others))
        pvals[i] = (1 + np.sum(np.abs(sims) >= abs(local_i[i]))) / (permutations + 1)

    clusters: List[str] = []
    for i in range(len(x)):
        if pvals[i] >= alpha:
            clusters.append("NS")
        elif z[i] >= 0 and lag_z[i] >= 0:
            clusters.append("HH")
        elif z[i] < 0 and lag_z[i] < 0:
            clusters.append("LL")
        elif z[i] < 0 and lag_z[i] >= 0:
            clusters.append("LH")
        else:
            clusters.append("HL")

    return pd.DataFrame({
        "z": z,
        "lag_z": lag_z,
        "local_I": local_i,
        "p_perm": pvals,
        "cluster": clusters,
    })


@dataclass
class PanelEngine:
    panel: pd.DataFrame
    y: str
    xvars: Tuple[str, ...]
    id_col: str
    time_col: str
    labels: Tuple[str, ...]

    def __post_init__(self) -> None:
        self.years = sorted(self.panel[self.time_col].unique())
        self.N = len(self.labels)
        self.T = len(self.years)
        self.n = self.N * self.T
        if self.n != len(self.panel): raise ValueError("Expected balanced T x N panel")
        if self.panel[[self.y, *self.xvars]].isna().any().any(): raise ValueError("Missing estimator values")
        self.Y = self.panel[self.y].to_numpy(float)
        self.X = self.panel[list(self.xvars)].to_numpy(float)
        self.Yd = self.tw_demean(self.Y)
        self.Xd = self.tw_demean(self.X)

    def tw_demean(self, v: np.ndarray) -> np.ndarray:
        a = np.asarray(v, float)
        was_1d = a.ndim == 1
        if was_1d:
            a = a[:, None]
        cube = a.reshape(self.T, self.N, -1)
        out = cube - cube.mean(axis=0, keepdims=True) - cube.mean(axis=1, keepdims=True) + cube.mean(axis=(0, 1), keepdims=True)
        out = out.reshape(self.n, -1)
        return out[:, 0] if was_1d else out

    def spatial_lag(self, v: np.ndarray, W: np.ndarray) -> np.ndarray:
        a = np.asarray(v, float)
        was_1d = a.ndim == 1
        if was_1d:
            a = a[:, None]
        cube = a.reshape(self.T, self.N, -1)
        out = np.empty_like(cube)
        for t in range(self.T):
            out[t] = W @ cube[t]
        out = out.reshape(self.n, -1)
        return out[:, 0] if was_1d else out

    @staticmethod
    def admissible_rho_bounds(W: np.ndarray, pad: float = 1e-4) -> Tuple[float, float]:
        """Eigenvalue-derived admissible interval for rho.

        For real eigenvalues, rho must lie between reciprocal extreme
        eigenvalues so I-rho W remains nonsingular. If W has material complex
        eigenvalues, use a conservative spectral-radius fallback.
        """
        eig = np.linalg.eigvals(W)
        if np.max(np.abs(eig.imag)) > 1e-8:
            sr = float(np.max(np.abs(eig)))
            return (-0.98 / sr, 0.98 / sr)
        er = eig.real
        pos = er[er > 1e-10]
        neg = er[er < -1e-10]
        upper = 1.0 / pos.max() if pos.size else 10.0
        lower = 1.0 / neg.min() if neg.size else -10.0
        return float(lower + pad), float(upper - pad)

    def concentrated_ll(self, rho: float, sse: float, W: np.ndarray) -> float:
        sign, ld = np.linalg.slogdet(np.eye(self.N) - rho * W)
        if sign <= 0 or sse <= 0:
            return -np.inf
        return float(self.T * ld - self.n / 2 * (np.log(2 * np.pi) + 1 + np.log(sse / self.n)))

    def fit_sdm(self, W: np.ndarray, covariance: bool = True) -> Dict[str, object]:
        if W.shape != (self.N, self.N) or not np.any(W): raise ValueError("W must be nonzero and NxN")
        WYd = self.tw_demean(self.spatial_lag(self.Y, W))
        WXd = self.tw_demean(self.spatial_lag(self.X, W))
        Z = np.column_stack([self.Xd, WXd])

        def given(rho: float):
            ys = self.Yd - rho * WYd
            delta = np.linalg.lstsq(Z, ys, rcond=None)[0]
            err = ys - Z @ delta
            sse = float(err @ err)
            return self.concentrated_ll(rho, sse, W), delta, sse

        lo, hi = self.admissible_rho_bounds(W)
        opt = minimize_scalar(lambda r: -given(r)[0], bounds=(lo, hi), method="bounded", options={"xatol": 1e-10})
        if not opt.success: raise RuntimeError("rho optimization failed")
        rho = float(opt.x)
        ll, delta, sse = given(rho)
        sigma2 = sse / self.n
        result: Dict[str, object] = {
            "rho": rho,
            "rho_lower": lo,
            "rho_upper": hi,
            "delta": delta,
            "sse": sse,
            "ll": ll,
            "sigma2": sigma2,
        }

        if not covariance:
            return result

        params = np.r_[rho, delta, np.log(sigma2)]

        def loglik_full(p: np.ndarray) -> float:
            r = float(p[0])
            d = p[1:-1]
            s2 = float(np.exp(p[-1]))
            sign, ld = np.linalg.slogdet(np.eye(self.N) - r * W)
            if sign <= 0 or s2 <= 0:
                return -1e100
            err = self.Yd - r * WYd - Z @ d
            return float(self.T * ld - self.n / 2 * np.log(2 * np.pi * s2) - (err @ err) / (2 * s2))

        H = approx_hess3(params, loglik_full, epsilon=5e-4)
        result["params"] = params
        result["V"] = np.linalg.pinv(-H)
        return result

    def data_impacts(self, W: np.ndarray, fit: Dict[str, object]) -> Dict[str, float]:
        rho = float(fit["rho"])
        delta = np.asarray(fit["delta"])
        beta = float(delta[0])
        theta = float(delta[len(self.xvars)])

        def impact_vector(p: np.ndarray) -> np.ndarray:
            r, b, th = map(float, p)
            S = np.linalg.inv(np.eye(self.N) - r * W)
            M = S @ (b * np.eye(self.N) + th * W)
            direct = float(np.trace(M) / self.N)
            total = float(M.sum() / self.N)
            return np.array([direct, total - direct, total])

        p0 = np.array([rho, beta, theta])
        imp = impact_vector(p0)
        out = {"direct": float(imp[0]), "indirect": float(imp[1]), "total": float(imp[2])}

        if "V" not in fit:
            return out

        V = np.asarray(fit["V"])
        # parameter order: rho, beta[0:k], theta[0:k], log(sigma2)
        theta_data_idx = 1 + len(self.xvars)
        Vsub = V[np.ix_([0, 1, theta_data_idx], [0, 1, theta_data_idx])]
        J = np.zeros((3, 3))
        for j in range(3):
            h = 1e-6 * max(1.0, abs(p0[j]))
            pp, pm = p0.copy(), p0.copy()
            pp[j] += h
            pm[j] -= h
            J[:, j] = (impact_vector(pp) - impact_vector(pm)) / (2 * h)
        Vimp = J @ Vsub @ J.T
        se = np.sqrt(np.maximum(np.diag(Vimp), 0))
        pvals = 2 * norm.sf(np.abs(imp / se))
        out.update({
            "se_direct": float(se[0]), "p_direct": float(pvals[0]),
            "se_indirect": float(se[1]), "p_indirect": float(pvals[1]),
            "se_total": float(se[2]), "p_total": float(pvals[2]),
        })
        return out


def decay_A(D: np.ndarray, family: str, param: float) -> np.ndarray:
    A = np.zeros_like(D, dtype=float)
    mask = D > 0
    if param <= 0: raise ValueError("Decay parameter must be positive")
    if family == "power":
        A[mask] = D[mask] ** (-float(param))
    elif family == "exponential":
        A[mask] = np.exp(-D[mask] / float(param))
    else:
        raise ValueError("family must be power or exponential")
    return A


def distance_claim_guard(diag: Dict[str, object], fit: Dict[str, object], label: str) -> List[str]:
    warnings: List[str] = []
    if int(diag["isolates"]) > 0:
        warnings.append(f"{label}: contains isolates; do not use it to claim a spillover boundary.")
    if int(diag["components"]) > 1:
        warnings.append(f"{label}: graph is disconnected; effect comparison is composition-sensitive.")
    rho = float(fit["rho"])
    lo, hi = float(fit["rho_lower"]), float(fit["rho_upper"])
    span = hi - lo
    if min(rho - lo, hi - rho) < 0.01 * span:
        warnings.append(f"{label}: rho is near the admissible boundary; inspect identification/numerics.")
    return warnings


def save_df(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")


def plot_W_heatmap(W: np.ndarray, labels: Sequence[str], path: Path, title: str) -> None:
    fig, ax = plt.subplots(figsize=(9, 8))
    im = ax.imshow(W, aspect="auto")
    ax.set_title(title)
    ax.set_xticks(range(len(labels)))
    ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=90, fontsize=6)
    ax.set_yticklabels(labels, fontsize=6)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_neighbor_counts(A: np.ndarray, labels: Sequence[str], path: Path, title: str) -> None:
    counts = (A > 0).sum(axis=1)
    order = np.argsort(counts)
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(np.arange(len(labels)), counts[order])
    ax.set_yticks(np.arange(len(labels)))
    ax.set_yticklabels(np.asarray(labels)[order], fontsize=7)
    ax.set_xlabel("Neighbor count")
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_moran_scatter(x: np.ndarray, W: np.ndarray, labels: Sequence[str], path: Path, title: str) -> None:
    z = (x - np.mean(x)) / np.std(x, ddof=0)
    lag = W @ z
    slope = float((z @ lag) / (z @ z))
    xx = np.linspace(z.min(), z.max(), 100)
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.scatter(z, lag)
    ax.plot(xx, slope * xx)
    ax.axhline(0, linewidth=0.8)
    ax.axvline(0, linewidth=0.8)
    for i, lab in enumerate(labels):
        ax.annotate(lab, (z[i], lag[i]), fontsize=6, alpha=0.7)
    ax.set_xlabel("Standardized value")
    ax.set_ylabel("Spatial lag")
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_threshold_linkage(results: pd.DataFrame, path: Path) -> None:
    """Link threshold, graph density and indirect effect in one estimand-safe chart.

    x = mean neighbor count, y = indirect effect, point label = distance threshold.
    This avoids a dual-axis plot while still showing all three quantities.
    """
    fig, ax = plt.subplots(figsize=(9, 6))
    x = results["mean_neighbors"].to_numpy(float)
    y = results["indirect"].to_numpy(float)
    ax.scatter(x, y)
    ax.axhline(0, linewidth=0.8)
    for xx, yy, cutoff in zip(x, y, results["cutoff_km"]):
        ax.annotate(f"{int(cutoff)}", (xx, yy), xytext=(3, 3), textcoords="offset points", fontsize=7)
    ax.set_xlabel("Mean neighbor count")
    ax.set_ylabel("Indirect effect")
    ax.set_title("Threshold–neighbor density–indirect effect linkage")
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_moran_trend(results: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.plot(results["year"], results["Y_MoranI"], marker="o", label="Global Moran I: Y")
    ax.plot(results["year"], results["Bivariate_I"], marker="o", label="Bivariate I: X -> W Y")
    ax.axhline(0, linewidth=0.8)
    ax.set_xlabel("Year")
    ax.set_ylabel("Moran's I")
    ax.set_title("Spatial autocorrelation over time")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_lisa_counts(results: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(9, 6))
    for key in ["HH", "LL", "HL", "LH"]:
        ax.plot(results["year"], results[key], marker="o", label=key)
    ax.set_xlabel("Year")
    ax.set_ylabel("Number of significant units")
    ax.set_title("LISA cluster counts over time (p < 0.05)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def lisa_map_if_boundary(
    lisa: pd.DataFrame,
    boundary_path: str,
    boundary_id_col: str,
    output_path: Path,
) -> None:
    try:
        import geopandas as gpd
    except Exception as exc:
        raise RuntimeError("LISA map requires geopandas.") from exc
    gdf = gpd.read_file(boundary_path)
    if boundary_id_col not in gdf.columns: raise ValueError("Missing boundary id column")
    gdf[boundary_id_col] = gdf[boundary_id_col].astype(str)
    merged = gdf.merge(lisa, left_on=boundary_id_col, right_on="unit", how="inner", validate="one_to_one")
    if len(merged) != len(lisa): raise ValueError("Boundary and LISA ids do not match")
    ax = merged.plot(column="cluster", categorical=True, legend=True, figsize=(10, 8))
    ax.set_axis_off()
    ax.set_title("LISA cluster map")
    ax.figure.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(ax.figure)


def load_config(config_path: str):
    path = Path(config_path).resolve()
    cfg = json.loads(path.read_text(encoding='utf-8'))
    for key in ('panel', 'coordinates', 'columns', 'output_dir'):
        if key not in cfg: raise ValueError(f'Missing config key: {key}')
    def resolve(v):
        q=Path(v)
        return str(q if q.is_absolute() else path.parent/q)
    cfg['panel']=resolve(cfg['panel'])
    cfg['coordinates']=resolve(cfg['coordinates'])
    cfg['output_dir']=resolve(cfg['output_dir'])
    if cfg.get('boundary_path'): cfg['boundary_path']=resolve(cfg['boundary_path'])
    return cfg


def read_inputs(cfg):
    p=Path(cfg['panel']); c=cfg['columns']
    df=pd.read_excel(p, sheet_name=cfg.get('sheet_name',0)) if p.suffix.lower() in {'.xlsx','.xls'} else pd.read_csv(p, encoding='utf-8-sig')
    coords=pd.read_csv(cfg['coordinates'], encoding='utf-8-sig')
    id_col,time_col,y_col,x_col=c['id'],c['time'],c['y'],c['x']
    controls=list(c.get('controls',[])); ec=c.get('economic_anchor')
    needed=[id_col,time_col,y_col,x_col,*controls,*([ec] if ec else [])]
    for col in needed:
        if col not in df: raise ValueError(f'Panel column missing: {col}')
    if len(set(needed))!=len(needed):
        # The economic anchor is allowed to also appear among controls.
        if ec is None or len(set(needed)) != len(needed)-1: raise ValueError('Duplicate model column configuration')
    for col in ('unit','lat','lon'):
        if col not in coords: raise ValueError(f'Coordinate column missing: {col}')
    if df[[id_col,time_col]].isna().any().any(): raise ValueError('Missing panel keys')
    df[id_col]=df[id_col].astype(str); coords['unit']=coords['unit'].astype(str)
    if coords['unit'].duplicated().any(): raise ValueError('Duplicate coordinate ids')
    if df.duplicated([id_col,time_col]).any(): raise ValueError('Duplicate (unit,time) panel rows')
    labels=coords['unit'].tolist()
    if len(labels)<4 or set(labels)!=set(df[id_col]): raise ValueError('Coordinate ids must exactly equal panel ids (N>=4)')
    if coords[['lat','lon']].isna().any().any(): raise ValueError('Missing coordinates')
    if not coords['lat'].between(-90,90).all() or not coords['lon'].between(-180,180).all(): raise ValueError('Invalid latitude/longitude')
    numeric=list(dict.fromkeys([y_col,x_col,*controls,*([ec] if ec else [])]))
    for name in numeric: df[name]=pd.to_numeric(df[name], errors='raise')
    if not np.isfinite(df[numeric].to_numpy(float)).all(): raise ValueError('Missing or nonfinite model inputs')
    years=sorted(df[time_col].unique())
    if df.shape[0]!=len(labels)*len(years): raise ValueError('Panel must be complete balanced N x T')
    idx=pd.MultiIndex.from_product([years,labels],names=[time_col,id_col])
    df=df.set_index([time_col,id_col]).reindex(idx)
    if df[numeric].isna().any().any(): raise ValueError('Missing unit-year combinations')
    df=df.reset_index()
    return df,labels,years,{r['unit']:(float(r['lat']),float(r['lon'])) for _,r in coords.iterrows()}


def _safe_fit(engine, A, label, warnings_list, covariance=True):
    W=row_standardize(A)
    diag=diagnose_W(A,W,engine.labels)
    rec={'matrix':label, **{k:v for k,v in diag.items() if not isinstance(v,list)}, 'status':'ok'}
    if diag['isolates'] or diag['components']!=1:
        rec['status']='diagnostic_only_disconnected'
        warnings_list.append(f'{label}: isolate/disconnected graph; SDM skipped (no silent zero-row handling).')
        return W,diag,rec,None,None
    try:
        fit=engine.fit_sdm(W,covariance=covariance)
        effects=engine.data_impacts(W,fit)
        rec.update({'rho':fit['rho'],'rho_lower':fit['rho_lower'],'rho_upper':fit['rho_upper'],**effects})
        warnings_list.extend(distance_claim_guard(diag,fit,label))
        return W,diag,rec,fit,effects
    except (ValueError,RuntimeError,np.linalg.LinAlgError) as ex:
        rec['status']='estimation_failed'; rec['error']=str(ex)
        warnings_list.append(f'{label}: estimation failed: {ex}')
        return W,diag,rec,None,None


def run_all(config_path: str):
    cfg=load_config(config_path)
    panel,labels,years,coords=read_inputs(cfg)
    c=cfg['columns']; idc,timec,ycol,xcol=c['id'],c['time'],c['y'],c['x']
    controls=tuple(c.get('controls',[])); ec=c.get('economic_anchor')
    out=Path(cfg['output_dir']); (out/'plots').mkdir(parents=True,exist_ok=True)
    (out/'weights').mkdir(parents=True,exist_ok=True)
    seed=int(cfg.get('seed',SEED)); reps=int(cfg.get('permutations',999))
    if reps<99: raise ValueError('Set permutations >=99 for meaningful demonstrations')
    engine=PanelEngine(panel, ycol, (xcol,*controls), idc,timec,tuple(labels))
    D=build_distance_matrix(labels,coords)
    A_geo=inverse_distance_A(D,float(cfg.get('distance_power',1.0)))
    matrices={'geo_inverse':A_geo}
    for k in cfg.get('knn',[4,6]):
        k=int(k)
        if k<1 or k>=len(labels): raise ValueError('k must be in [1,N-1]')
        matrices[f'knn{k}_union']=knn_A(D,k,'union')
    for threshold in cfg.get('weight_distance_bands_km',[]):
        matrices[f'band_{threshold}km']=distance_band_A(D,float(threshold),True)
    econ_meta={}
    if ec:
        a=economic_anchor(panel,ec,idc,labels)
        A_gaussian, gaussian_meta=economic_A(a,'gaussian',bandwidth=cfg.get('economic_bandwidth'))
        A_inverse, inverse_meta=economic_A(a,'inverse',epsilon=cfg.get('economic_epsilon'))
        econ_meta={'gaussian':gaussian_meta,'inverse':inverse_meta}
        matrices['economic_gaussian']=A_gaussian
        matrices['economic_inverse']=A_inverse
        nested_method=cfg.get('economic_method','gaussian')
        if nested_method not in ('gaussian','inverse'): raise ValueError('economic_method must be gaussian or inverse')
        matrices['geo_economic_nested']=geo_economic_nested_A(A_geo,A_gaussian if nested_method=='gaussian' else A_inverse)
    if cfg.get('boundary_path'):
        if not cfg.get('boundary_id_col'): raise ValueError('boundary_id_col required when boundary_path supplied')
        for typ in ['queen','rook']:
            matrices[typ]=contiguity_A_from_boundary_file(cfg['boundary_path'],cfg['boundary_id_col'],typ,labels)
    guards=[]; diagnostic_rows=[]; effect_rows=[]
    for name,A in matrices.items():
        W,diag,rec,fit,imp=_safe_fit(engine,A,name,guards)
        diagnostic_rows.append({'matrix':name,**diag})
        effect_rows.append(rec)
        pd.DataFrame(W,index=labels,columns=labels).to_csv(out/'weights'/f'{name}_row.csv',encoding='utf-8-sig')
        plot_W_heatmap(W,labels,out/'plots'/f'W_{name}.png',f'W: {name}')
        plot_neighbor_counts(A,labels,out/'plots'/f'neighbors_{name}.png',f'Neighbors: {name}')
    save_df(pd.DataFrame(diagnostic_rows),out/'v02_weight_diagnostics.csv')
    save_df(pd.DataFrame(effect_rows),out/'v02_weight_sensitivity_sdm.csv')
    normalizers={'row':row_standardize(A_geo),'spectral':spectral_standardize(A_geo),'symmetric':symmetric_standardize(A_geo),'global_sum_N':global_standardize(A_geo)}
    nrows=[]
    for mode,W in normalizers.items():
        try:
            fit=engine.fit_sdm(W,covariance=True)
            nrows.append({'normalization':mode,'rho':fit['rho'],'min_row_sum':W.sum(axis=1).min(),'max_row_sum':W.sum(axis=1).max(),**engine.data_impacts(W,fit)})
        except Exception as ex: nrows.append({'normalization':mode,'error':str(ex)})
    save_df(pd.DataFrame(nrows),out/'v02_normalization_sensitivity.csv')
    (out/'v02_economic_weight_metadata.json').write_text(json.dumps({'anchor_column':ec,'construction':'period mean, fixed over time','parameters':econ_meta},indent=2),encoding='utf-8')
    if ec:
        gaps=np.abs(a[:,None]-a[None,:]);np.fill_diagonal(gaps,np.inf)
        positive_gaps=gaps[np.isfinite(gaps)&(gaps>0)]
        erows=[]
        for q in (0.01,0.025,0.05,0.10,0.25,0.50):
            epsilon=float(np.quantile(positive_gaps,q)) if positive_gaps.size else 1.0
            A_q,_=economic_A(a,'inverse',epsilon=epsilon)
            _,diag,rec,fit,imp=_safe_fit(engine,A_q,f'economic_inverse_eps_q{q:g}',guards)
            erows.append({'epsilon_quantile':q,'epsilon':epsilon,**rec})
        save_df(pd.DataFrame(erows),out/'v02_economic_inverse_stabilizer_sensitivity.csv')
    # v0.3: one common baseline W, spatial alignment follows coords.csv row order.
    W0=row_standardize(A_geo); mrows=[]; lisa_rows=[]; lisa_summ=[]
    for ti,yr in enumerate(years):
        d=panel[panel[timec]==yr]; x=d[xcol].to_numpy(float); y=d[ycol].to_numpy(float)
        iy,py=permutation_global_moran(y,W0,reps,seed+1000+ti)
        ix,px=permutation_global_moran(x,W0,reps,seed+2000+ti)
        ib,pb=permutation_bivariate_moran(x,y,W0,reps,seed+3000+ti)
        mrows.append({'year':yr,'X_MoranI':ix,'X_p_one_sided':px,'Y_MoranI':iy,'Y_p_one_sided':py,'Bivariate_I':ib,'Bivariate_p_one_sided':pb})
        lisa=local_moran(y,W0,reps,seed+4000+ti)
        lisa.insert(0,'unit',labels);lisa.insert(0,'year',yr)
        lisa_rows.append(lisa)
        counts=lisa['cluster'].value_counts()
        lisa_summ.append({'year':yr,**{k:int(counts.get(k,0)) for k in ('HH','LL','HL','LH','NS')}})
        if ti in {0,len(years)//2,len(years)-1}:
            plot_moran_scatter(y,W0,labels,out/'plots'/f'moran_scatter_Y_{yr}.png',f'Moran scatter Y: {yr}')
    moran_df=pd.DataFrame(mrows);lisa_df=pd.concat(lisa_rows,ignore_index=True)
    save_df(moran_df,out/'v03_global_bivariate_moran.csv');save_df(lisa_df,out/'v03_lisa_Y.csv')
    save_df(pd.DataFrame(lisa_summ),out/'v03_lisa_summary.csv')
    plot_moran_trend(moran_df,out/'plots'/'moran_trend.png')
    plot_lisa_counts(pd.DataFrame(lisa_summ),out/'plots'/'lisa_counts_over_time.png')
    if cfg.get('boundary_path'):
        lisa_map_if_boundary(lisa_df[lisa_df['year']==years[-1]],cfg['boundary_path'],cfg['boundary_id_col'],out/'plots'/f'lisa_map_Y_{years[-1]}.png')
    # v0.4: never invent an optimal radius from p-values.
    threshold_rows=[]
    for threshold in cfg.get('cumulative_thresholds_km',[]):
        A=distance_band_A(D,float(threshold),True)
        W,diag,rec,fit,imp=_safe_fit(engine,A,f'threshold_{threshold}km',guards)
        threshold_rows.append({'cutoff_km':threshold,'min_neighbors':diag['min_neighbors'],'mean_neighbors':diag['mean_neighbors'],'isolates':diag['isolates'],'components':diag['components'],**{k:v for k,v in rec.items() if k not in {'matrix','min_neighbors','mean_neighbors','isolates','components'}}})
    if threshold_rows:
        tdf=pd.DataFrame(threshold_rows)
        save_df(tdf,out/'v04_cumulative_thresholds.csv')
        if 'indirect' in tdf.columns and tdf['indirect'].notna().any():
            plot_threshold_linkage(tdf.dropna(subset=['indirect']),out/'plots'/'threshold_neighbor_effect_linkage.png')
    ring_rows=[]
    ring_edges=cfg.get('ring_edges_km',[])
    if any(float(b)<=float(a) for a,b in zip(ring_edges[:-1],ring_edges[1:])): raise ValueError('ring_edges_km must be strictly increasing')
    for lo,hi in zip(ring_edges[:-1],ring_edges[1:]):
        A=distance_ring_A(D,float(lo),float(hi),True)
        W,diag,rec,fit,imp=_safe_fit(engine,A,f'ring_({lo},{hi}]km',guards,covariance=False)
        ring_rows.append({'lower_km':lo,'upper_km':hi,'mean_neighbors':diag['mean_neighbors'],'isolates':diag['isolates'],'components':diag['components'],**{k:v for k,v in rec.items() if k not in {'matrix','mean_neighbors','isolates','components'}}})
    if ring_rows: save_df(pd.DataFrame(ring_rows),out/'v04_distance_rings.csv')
    decay_rows=[]
    for fam,params in cfg.get('decay',{}).items():
        for param in params:
            A=decay_A(D,fam,float(param))
            W,diag,rec,fit,imp=_safe_fit(engine,A,f'decay_{fam}_{param}',guards)
            decay_rows.append({'family':fam,'param':param,**rec})
    if decay_rows: save_df(pd.DataFrame(decay_rows),out/'v04_decay_sensitivity.csv')
    guards.insert(0,'Never interpret the largest coefficient / smallest p-value as an optimal distance or the last significant threshold as a maximum spillover radius.')
    guards.insert(1,'Changing distance threshold changes both the graph and row normalization. Ring estimates may have isolated units and are exploratory.')
    guards.insert(2,'LISA clusters use unadjusted two-sided conditional-randomization pseudo p-values; report multiple-testing limitations. Global Moran uses one-sided sign-directed randomization p-values.')
    (out/'v04_identification_guard.txt').write_text('\n'.join(guards)+'\n',encoding='utf-8')
    (out/'run_metadata.json').write_text(json.dumps({'config':cfg,'n_units':len(labels),'n_years':len(years),'observations':len(panel),'permutations':reps,'seed':seed,'economic_W_time_varying':False,'estimator':'two-way demeaned Gaussian concentrated likelihood; numeric Hessian / delta method impacts','warning':'Demonstration estimator, does not by itself establish causal identification.'},ensure_ascii=False,indent=2),encoding='utf-8')
    print('Completed v0.2–v0.4 generic extensions:',out)


def main():
    parser=argparse.ArgumentParser(description='Spatial panel v0.2-v0.4 generic skill runner')
    parser.add_argument('config',help='JSON configuration path')
    args=parser.parse_args()
    run_all(args.config)

if __name__=='__main__': main()
