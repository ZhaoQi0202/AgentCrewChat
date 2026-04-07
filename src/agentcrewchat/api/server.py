import uvicorn

from agentcrewchat.api.app import create_app


def main(host: str = "127.0.0.1", port: int = 9800) -> None:
    app = create_app()
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
