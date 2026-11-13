"""Replot the existing IDETC threshold cache with explicit outcome labels.

This script does not run the organizational model or refit its surrogate.
The adjacent CSV is a byte-for-byte copy of the cached input used in the
conference figure. Q + L denotes the favorable-opinion fraction; it is not
the fraction currently using AI.

Original cache:
    /Users/aslan/Projects/idetc-ai-adoption-paper/figures/cached_min_accuracy/
    min_accuracy_cache_target_0.500_neg_-0.250_pos_0.250_teamsnum_1_5_10_15_20_25_30_teamssize_5_10_15_20.csv

Reproduce from any directory:
    python3 experiment/analysis/paper_figures/idetc/plot_structure_min_accuracy_clarified.py
"""

from __future__ import annotations

import csv
import os
import tempfile
from pathlib import Path

# Keep font/cache initialization inside a writable temporary directory.
os.environ.setdefault(
    "MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "idetc-threshold-matplotlib")
)

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np


ASSET_DIR = Path(__file__).resolve().parent
CACHE_PATH = ASSET_DIR / "structure_min_accuracy_cache.csv"
OUTPUT_STEM = ASSET_DIR / "structure_min_accuracy_clarified"


def main() -> None:
    with CACHE_PATH.open(newline="") as handle:
        rows = list(csv.DictReader(handle))

    team_counts = sorted({int(row["teams_num"]) for row in rows})
    team_sizes = sorted({int(row["teams_size"]) for row in rows})
    by_configuration = {
        (int(row["teams_num"]), int(row["teams_size"])): row for row in rows
    }

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 11,
            "axes.titlesize": 12,
            "axes.labelsize": 12,
            "xtick.labelsize": 11,
            "ytick.labelsize": 11,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )

    fig, axes = plt.subplots(
        1,
        2,
        figsize=(10.4, 4.8),
        sharey=True,
        gridspec_kw={"wspace": 0.08},
    )
    minimum, maximum = 0.65, 0.95
    norm = matplotlib.colors.Normalize(vmin=minimum, vmax=maximum)
    cmap = plt.get_cmap("viridis")

    for ax, attitude, column in zip(
        axes,
        ("negative", "positive"),
        ("min_accuracy_negative", "min_accuracy_positive"),
    ):
        values = np.array(
            [
                [
                    float(by_configuration[(count, size)][column])
                    for size in team_sizes
                ]
                for count in team_counts
            ]
        )
        image = ax.imshow(
            values,
            origin="lower",
            aspect="auto",
            cmap=cmap,
            norm=norm,
        )
        ax.set_title(f"Initial attitude: {attitude}", pad=10)
        ax.set_xticks(range(len(team_sizes)), team_sizes)
        ax.set_yticks(range(len(team_counts)), team_counts)
        ax.set_xlabel("People per team")
        ax.tick_params(length=0, pad=7)
        ax.set_xticks(np.arange(-0.5, len(team_sizes), 1), minor=True)
        ax.set_yticks(np.arange(-0.5, len(team_counts), 1), minor=True)
        ax.grid(which="minor", color="white", linewidth=1.0, alpha=0.65)
        ax.tick_params(which="minor", bottom=False, left=False)
        for spine in ax.spines.values():
            spine.set_visible(False)
        for row, count in enumerate(team_counts):
            for col, size in enumerate(team_sizes):
                value = values[row, col]
                red, green, blue, _ = cmap(norm(value))
                luminance = 0.2126 * red + 0.7152 * green + 0.0722 * blue
                ax.text(
                    col,
                    row,
                    f"{value:.3f}",
                    ha="center",
                    va="center",
                    color="black" if luminance > 0.53 else "white",
                    fontsize=11,
                )

    axes[0].set_ylabel("Number of teams")
    fig.subplots_adjust(left=0.08, right=0.84, bottom=0.15, top=0.81)
    colorbar_ax = fig.add_axes((0.87, 0.15, 0.022, 0.66))
    colorbar = fig.colorbar(image, cax=colorbar_ax)
    colorbar.set_label("Minimum AI success probability", labelpad=10)
    colorbar.set_ticks(np.arange(0.65, 0.951, 0.05))
    colorbar.outline.set_visible(False)
    fig.suptitle(
        "AI success probability needed for 50% favorable attitudes",
        fontsize=14,
        x=0.47,
        y=0.96,
    )
    fig.savefig(OUTPUT_STEM.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(OUTPUT_STEM.with_suffix(".png"), dpi=240, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
