"""Axon CLI: `axon start` (server + browser) and `axon run <workflow>` (headless execution)."""

from __future__ import annotations

import argparse
import json
import sys
import threading
from pathlib import Path


def cmd_start(args) -> int:
    import uvicorn

    from axon.server.app import create_app

    app = create_app()
    url = f"http://127.0.0.1:{args.port}"
    if not args.no_browser:
        import webbrowser

        threading.Timer(1.2, lambda: webbrowser.open(url)).start()
    print(f"\n  Axon is starting at {url}\n")
    uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="warning")
    return 0


def cmd_run(args) -> int:
    import threading as _threading

    from axon.engine.cache import Cache
    from axon.engine.executor import execute_workflow
    from axon.engine.graph import Workflow, validate_workflow
    from axon.sdk.registry import REGISTRY
    from axon.storage.workspace import Workspace

    path = Path(args.workflow)
    if not path.exists():
        print(f"error: no such file: {path}", file=sys.stderr)
        return 1

    REGISTRY.load_builtin()
    wf = Workflow.model_validate_json(path.read_text())
    # Relative file params resolve against the workflow's own directory.
    wf.meta["base_dir"] = str(path.resolve().parent)

    issues = validate_workflow(wf, REGISTRY)
    errors = [i for i in issues if i.level == "error"]
    if errors:
        for i in errors:
            print(f"invalid: [{i.node_id or '-'}] {i.message}", file=sys.stderr)
        return 1

    ws = Workspace()
    failed = False
    metrics_lines: list[str] = []

    def emit(e):
        nonlocal failed
        if e.type == "node_started":
            print(f"  ▶ {e.node_id} ({e.data.get('name', '')})")
        elif e.type == "node_finished":
            tag = "cached" if e.data.get("cached") else "done"
            print(f"  ✔ {e.node_id} [{tag}]")
            preview = e.data.get("preview") or {}
            for socket, p in preview.items():
                if isinstance(p, dict) and p.get("type") == "metrics":
                    metrics_lines.append(f"    {e.node_id}.{socket}: {json.dumps(p['values'])}")
        elif e.type == "node_failed":
            failed = True
            if e.data.get("skipped"):
                print(f"  ⤼ {e.node_id} skipped (upstream failed)")
            else:
                print(f"  ✘ {e.node_id}: {e.data.get('error')}", file=sys.stderr)
                if e.data.get("hint"):
                    print(f"    hint: {e.data['hint']}", file=sys.stderr)

    print(f"Running {wf.name} ({len(wf.nodes)} nodes)")
    execute_workflow(
        wf,
        REGISTRY,
        Cache(ws.cache_dir),
        workspace=ws.root,
        settings=ws.settings,
        emit=emit,
        cancel=_threading.Event(),
        run_id="cli",
    )
    if metrics_lines:
        print("Metrics:")
        print("\n".join(metrics_lines))
    print("FAILED" if failed else "OK")
    return 1 if failed else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="axon", description="Axon: build real AI visually.")
    sub = parser.add_subparsers(dest="command")

    p_start = sub.add_parser("start", help="Start the Axon app (server + browser)")
    p_start.add_argument("--port", type=int, default=8700)
    p_start.add_argument("--no-browser", action="store_true")

    p_run = sub.add_parser("run", help="Run a .axon.json workflow headlessly")
    p_run.add_argument("workflow")

    args = parser.parse_args(argv)
    if args.command == "start":
        return cmd_start(args)
    if args.command == "run":
        return cmd_run(args)
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
