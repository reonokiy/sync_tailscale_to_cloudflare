"""Module entry point for running tsync via `python -m tsync`."""

from .cli import main


def run() -> int:
    """Invoke the CLI and return an exit code."""
    return main()


if __name__ == "__main__":
    raise SystemExit(run())
