"""Explicit compatibility for the SQLite initialization fix of October 10, 2026.

Only these two reviewed runner/storage revisions produce equivalent models.
Every scientific setting, input, environment and other source hash must match.
Original archive definitions are retained; arbitrary code edits are rejected.
"""

import json

from experiment.design import canonical, digest


RUNTIME_PATHS = ("experiment/runner.py", "experiment/results.py")
RUNTIME_REVISIONS = (
    ("855eaf7f81c1a982433dfb1054fd0ec9f1d9e37cc3f2e5beb9249e312d179f61",
     "79ac55035172c59dbcc46df592c9da3953528a7075a5e8630c30bae456422918"),
    ("0fe3fdc9b270e8b74e037f5d60f73ead201c82716cce1773bcadd89f0b8be1bd",
     "9da7a33adc792e172184924d7beaa3f0c31a769c9debcedfc63c440180a1225c"),
)


def definitions_match(saved, current):
    if canonical(saved) == canonical(current):
        return True
    normalized = []
    for definition in (saved, current):
        value = json.loads(canonical(definition))
        try:
            inputs = value["inputs"]
            code = inputs["code"]
            revision = tuple(code[path] for path in RUNTIME_PATHS)
            signature = digest(dict(parameters=value["parameters"], inputs=inputs,
                                    participants=value["participants"]))
            if revision not in RUNTIME_REVISIONS or value["signature"] != signature:
                return False
            code.update(zip(RUNTIME_PATHS, RUNTIME_REVISIONS[0]))
            value["signature"] = digest(dict(parameters=value["parameters"], inputs=inputs,
                                             participants=value["participants"]))
        except KeyError:
            return False
        normalized.append(canonical(value))
    return normalized[0] == normalized[1]
