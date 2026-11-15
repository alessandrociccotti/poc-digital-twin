# Digital Twin of a Three-Station Production Line

The baseline line runs from die casting through two finite FIFO buffers, with CNC machining between them and leak testing at the end. See the [project charter](docs/01-project-charter.md) for context.

## Local setup

Use Python 3.11 or later. From the repository root:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev,dashboard]'
python -m pytest
```

## Shared event contract

The initial baseline contract lives in [events.py](src/digital_twin/events.py). Each JSONL row describes one event. `time_s` is elapsed simulation time in seconds. Events are written in ascending `seq` order and time is nondecreasing. For equal timestamps, `seq` determines the order. Sequence numbers start at 1 for each trace.

A buffer entry or exit records the actual transfer. If a part is blocked after processing, its `process_end` and downstream `buffer_enter` occur at different times. Count completions from `part_complete` after leak testing. Keep the source on every event and preserve missing observations when designing the NIST adapter.

Use [baseline-small.jsonl](tests/fixtures/baseline-small.jsonl) to start replay and KPI work. It is a hand-written synthetic trace with two completions and a two-second wait for the second part in Buffer 1. Keep generated run logs under the ignored `outputs/` directory.

## Workstreams

- **Simulation** implements the reference plant and exports baseline events.
- **Telemetry** reads those events to update independent twin state and audits archived NIST CNC observations.
- **Analytics** computes KPIs from the events and presents them in the dashboard.

Use short-lived branches and PRs. Coordinate contract and fixture changes together so all three streams can use the same example.

## LaTeX report and user manual

Use a TeX distribution with `latexmk` and `pdflatex`. Each workstream edits its own section files in both documents. From the repository root:

```sh
(cd docs/report && latexmk -pdf -halt-on-error -outdir=build main.tex)
(cd docs/manual && latexmk -pdf -halt-on-error -outdir=build main.tex)
```

The PDFs are written to the respective local `build/` directories.
