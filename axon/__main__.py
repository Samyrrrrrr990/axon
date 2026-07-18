try:
    from axon.cli import main
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "Axon's CLI failed to import. Run `uv sync` in the repo root first."
    ) from exc

if __name__ == "__main__":
    main()
