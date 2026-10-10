"""Run in VS Code to compare all shared tracks, or edit SELECTED_TRACKS below."""

import csv
import json
from pathlib import Path
import sys

if __package__ in (None, ""):
    root = Path(__file__).resolve().parents[2]
    sys.path[:0] = [str(root), str(root/"src")]

import matplotlib.pyplot as plt
import numpy as np

from experiment.config import TRACKS_DIR

SELECTED_TRACKS = None  # For example: ["low_p0_0", "normal_p0_0", "high_p0_0"].
SMOOTHING_WINDOW = 10  # 1 displays the raw binary complexity instead.


def visualize(selected=SELECTED_TRACKS, window=SMOOTHING_WINDOW, directory=TRACKS_DIR):
    if not isinstance(window,int) or window<1:
        raise ValueError("Smoothing window must be a positive integer.")
    registry = json.loads((Path(directory)/"manifest.json").read_text())["tracks"]
    metadata = {track["name"]: track for track in registry}
    paths = [Path(directory)/f"{track['name']}.csv" for track in registry] if selected is None else [Path(directory)/f"{name}.csv" for name in selected]
    if not paths:
        raise FileNotFoundError("No tracks found. Run generate_tracks.py first.")
    figure, axes = plt.subplots(figsize=(12, 6))
    colors = {"low":"tab:green", "normal":"tab:blue", "high":"tab:red"}
    styles = ("-", "--", "-.", ":", (0,(5,1,1,1,1,1)))
    for path in paths:
        with path.open(newline="") as stream:
            rows = list(csv.DictReader(stream))
        values = np.array([int(row["task_complexity"]) for row in rows])
        if not len(values):
            raise ValueError(f"Empty track: {path}")
        size = min(window,len(values))
        smooth = np.convolve(values,np.ones(size),mode="full")[:len(values)]/np.minimum(np.arange(1,len(values)+1),size)
        track = metadata[path.stem]
        difficulty = track["difficulty"]
        persistence = metadata[path.stem]["persistence"]
        axes.plot(np.arange(1,len(values)+1),smooth,label=f"{path.stem} (persistence {persistence:g}, mean {values.mean():.2f})",
                  color=colors.get(difficulty),linestyle=styles[track["persistence_index"]%len(styles)],alpha=0.8,
                  drawstyle="steps-post" if window==1 else "default")
    axes.set(xlabel="Simulation step",ylabel=f"High-complexity fraction ({window}-step trailing window)" if window>1 else "Task complexity",
             title="Shared driving tracks",ylim=(-0.05,1.05))
    axes.grid(alpha=0.2)
    axes.legend(ncol=3,fontsize=8)
    figure.tight_layout()
    plt.show()
    return figure


if __name__ == "__main__":
    visualize()
