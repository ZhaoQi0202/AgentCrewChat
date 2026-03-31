import argparse

from agentloom import bootstrap


def main() -> None:
    parser = argparse.ArgumentParser(prog="agentloom")
    parser.add_argument("--cli", action="store_true", help="headless, no GUI")
    args = parser.parse_args()
    bootstrap.ensure_layout()
    if args.cli:
        print("AgentLoom")
        return
    from agentloom.ui.app import run_app

    raise SystemExit(run_app())


if __name__ == "__main__":
    main()
