from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agentcrewchat.bootstrap import ensure_layout


def create_app() -> FastAPI:
    ensure_layout()
    app = FastAPI(title="AgentCrewChat API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:25527",
            "http://127.0.0.1:25527",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
        ],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from agentcrewchat.api.routes import config_router, tasks_router, graph_router

    app.include_router(config_router, prefix="/api")
    app.include_router(tasks_router, prefix="/api")
    app.include_router(graph_router, prefix="/api")

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app
