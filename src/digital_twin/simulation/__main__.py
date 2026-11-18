"""Command line entry point for baseline simulation and JSONL export."""

import argparse
from dataclasses import asdict
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from digital_twin.simulation.model import SimulationConfig, run_simulation


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    defaults = SimulationConfig()
    for name in ("arrival_interval_s", "casting_time_s", "cnc_time_s",
                 "leak_test_time_s", "duration_s", "processing_cv"):
        parser.add_argument("--" + name.replace("_", "-"), type=float, default=getattr(defaults, name))
    for name in ("buffer_1_capacity", "buffer_2_capacity", "seed"):
        parser.add_argument("--" + name.replace("_", "-"), type=int, default=getattr(defaults, name))
    parser.add_argument("--output", type=Path, default=Path("outputs/baseline"))
    arguments = vars(parser.parse_args())
    output = arguments.pop("output")
    try:
        config = SimulationConfig(**arguments)
        if output.exists():
            raise ValueError(f"Output already exists: {output}. Choose a fresh --output directory.")
        result = run_simulation(config)
        output.parent.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(prefix=".simulation-", dir=output.parent) as temporary:
            staging = Path(temporary) / "run"
            staging.mkdir()
            with (staging / "events.jsonl").open("w", encoding="utf-8") as stream:
                for event in result.events:
                    stream.write(json.dumps(asdict(event), allow_nan=False) + "\n")
            (staging / "run.json").write_text(
                json.dumps(result.summary(), indent=2, allow_nan=False) + "\n", encoding="utf-8",
            )
            staging.rename(output)
    except (ValueError, OSError) as error:
        parser.error(str(error))
    print(f"Exported {len(result.events)} events to {output}")
    print(f"Completed {result.summary()['completed']} parts; {len(result.unfinished_parts)} remain in progress.")


if __name__ == "__main__":
    main()
