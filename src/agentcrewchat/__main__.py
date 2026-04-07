import argparse

from agentcrewchat import bootstrap


def main() -> None:
    parser = argparse.ArgumentParser(prog="agentcrewchat")
    parser.add_argument(
        "--cli",
        action="store_true",
        help="仅初始化布局后退出，不启动 HTTP 服务",
    )
    args = parser.parse_args()
    bootstrap.ensure_layout()
    if args.cli:
        if not bootstrap.check_writable_root():
            print("安装目录不可写，请将程序放在可写目录后重试。")
        print("AgentCrewChat")
        return
    from agentcrewchat.api.server import main as run_server

    run_server()


if __name__ == "__main__":
    main()
