"""Small, validated views of the comparison table and exact matches across tracks."""
from pathlib import Path
from contextlib import closing
import json
import sqlite3
import numpy as np
from experiment.analysis.shared.output import comparison_directory
from experiment.analysis.shared.table import cache_key

PAIRS = ('decision', 'cognition', 'cross')
PAIR_LABELS = ('Decision / solo', 'Cognition / solo', 'Decision / cognition')


def selected_columns(names, directory=None):
    cache = comparison_directory(directory) / 'comparisons.sqlite'
    stored = cache.parent / 'analysis_table.npz'
    if not stored.exists():
        raise FileNotFoundError('Run compare_modes, then baseline_similarity to build the shared analysis table.')
    with np.load(stored, allow_pickle=False) as saved:
        if str(saved['_key']) != cache_key(cache):
            raise ValueError('Comparison table is stale; rebuild it before running this analysis.')
        table = {name: saved[name] for name in names}
        table['_drivers'] = saved['_drivers'].tolist()
        table['_tracks'] = saved['_tracks'].tolist()
    return table


def matched_tracks(table):
    """Return indices (car, track), restricted to keys present on EVERY track.

    Driver/composition/start identify the same passengers and initial conditions.
    No averaging of unmatched cars, and no filling missing results with zeros.
    """
    keys = np.rec.fromarrays([table[k] for k in ('driver', 'composition', 'start')], names='driver,composition,start')
    per_track, common = [], None
    for track in range(len(table['_tracks'])):
        indices = np.flatnonzero(table['track'] == track)
        order = indices[np.argsort(keys[indices], kind='stable')]
        ordered = keys[order]
        if len(np.unique(ordered)) != len(ordered):
            raise ValueError('Duplicate car keys in one track')
        per_track.append((order, ordered))
        common = ordered if common is None else np.intersect1d(common, ordered, assume_unique=True)
    if common is None or not len(common):
        raise ValueError('No cars have completed comparisons on every track')
    return np.stack([order[np.searchsorted(ordered, common)] for order, ordered in per_track], axis=1)


def balanced_weights(driver, passenger_count):
    """Each driver gets equal weight; each observed passenger count within driver does too."""
    strata, inverse, count = np.unique(np.stack([driver, passenger_count], axis=1), axis=0,
                                      return_inverse=True, return_counts=True)
    drivers, driver_counts = np.unique(strata[:, 0], return_counts=True)
    per_stratum = 1 / (len(drivers) * driver_counts[np.searchsorted(drivers, strata[:, 0])])
    return per_stratum[inverse] / count[inverse]


def archive_definition(runs, driver, track):
    path = Path(runs) / f'{driver}_{track}.sqlite'
    with closing(sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True)) as db:
        return json.loads(db.execute("SELECT value FROM metadata WHERE key='definition'").fetchone()[0])


def correlation(x, y):
    """Spearman association, with constants represented as missing rather than zero."""
    from scipy.stats import rankdata
    x, y = np.asarray(x), np.asarray(y)
    valid = np.isfinite(x) & np.isfinite(y)
    x, y = x[valid], y[valid]
    if len(x) < 3 or np.ptp(x) == 0 or np.ptp(y) == 0:
        return None
    return float(np.corrcoef(rankdata(x), rankdata(y))[0, 1])
