import argparse

from agentloom import bootstrap


def main() -> None:
    parser = argparse.ArgumentParser(prog="agentloom")
    parser.add_argument("--cli", action="store_true", help="headless, no GUI")
    args = parser.parse_args()
    bootstrap.ensure_layout()
    if args.cli:
        if not bootstrap.check_writable_root():
            print("安装目录不可写，请将程序放在可写目录后重试。")
        print("AgentLoom")
        return
    from agentloom.ui.app import run_app

    raise SystemExit(run_app())


if __name__ == "__main__":
    main()
