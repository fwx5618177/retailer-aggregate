"""Click CLI entry point for the SEA data pipeline."""

from __future__ import annotations

import sys

import click

from sea_pipeline.config import load_config
from sea_pipeline.runner import PipelineRunner


@click.group()
def main() -> None:
    """SEA Retailer Data Pipeline CLI."""
    pass


@main.command()
@click.option(
    "--config",
    "config_path",
    default="config/default.yaml",
    type=click.Path(exists=True),
    help="Path to the base YAML configuration file.",
)
@click.option(
    "--config-override",
    "override_path",
    default=None,
    type=click.Path(exists=True),
    help="Optional override YAML that is deep-merged on top of the base config.",
)
@click.option(
    "--event-date",
    default=None,
    type=str,
    help="Override the event date (YYYY-MM-DD). Defaults to today.",
)
@click.option(
    "--run-id",
    default=None,
    type=str,
    help="Override the run ID. Defaults to a new UUID.",
)
def run(
    config_path: str,
    override_path: str | None,
    event_date: str | None,
    run_id: str | None,
) -> None:
    """Execute a full pipeline run."""
    cfg = load_config(config_path, override_path)
    runner = PipelineRunner(cfg)
    manifest = runner.run(event_date=event_date, run_id=run_id)

    click.echo(f"\nPipeline run completed.")
    click.echo(f"  Run ID:     {manifest.run_id}")
    click.echo(f"  Event date: {manifest.event_date}")
    click.echo(f"  DQ status:  {manifest.dq_status}")
    click.echo(f"  Duration:   {manifest.duration_seconds}s")
    click.echo(f"  Alerts:     {manifest.alerts_count}")
    click.echo(f"  Manifest:   {manifest.manifest_path}")

    if manifest.row_counts:
        click.echo("  Row counts:")
        for table, count in manifest.row_counts.items():
            click.echo(f"    {table}: {count}")

    if manifest.dq_status == "FAILED":
        click.echo("\nDQ checks FAILED. See manifest for details.")
        sys.exit(1)
