"""CLI entry point for the matching engine."""

from __future__ import annotations

import logging
import sys

import click

from sea_matching.config import load_config, merge_configs
from sea_matching.runner import MatchingRunner


@click.command()
@click.option("--config", "config_path", default="config/default.yaml", help="Configuration file path")
@click.option("--config-override", "override_path", default=None, help="Override config file path")
@click.option("--event-date", default=None, help="Event date to process (YYYY-MM-DD)")
@click.option("--run-id", default=None, help="Override run ID")
@click.option("--verbose", "-v", is_flag=True, help="Enable debug logging")
def main(config_path: str, override_path: str | None, event_date: str | None, run_id: str | None, verbose: bool):
    """Run the SEA Retailer cross-platform matching engine."""
    # Setup logging
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    try:
        config = load_config(config_path)
        if override_path:
            override = load_config(override_path)
            config = merge_configs(config, override)

        runner = MatchingRunner(config)
        if run_id:
            runner.run_id = run_id
            runner.batch_id = f"match-{run_id}"

        result = runner.run(event_date=event_date)

        click.echo(f"\nMatching complete:")
        click.echo(f"  Run ID: {result.get('run_id')}")
        click.echo(f"  Duration: {result.get('duration_seconds', 0):.1f}s")
        counts = result.get("result_counts", {})
        click.echo(f"  Matched pairs: {counts.get('matched_pairs', 0)}")
        click.echo(f"    Auto accepted: {counts.get('auto_accepted', 0)}")
        click.echo(f"    Needs review: {counts.get('needs_review', 0)}")
        click.echo(f"    Overridden: {counts.get('overridden', 0)}")

    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        logging.exception("Matching failed")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
