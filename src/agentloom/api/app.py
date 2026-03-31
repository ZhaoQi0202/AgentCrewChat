from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agentloom.bootstrap import ensure_layout


def create_app() -> FastAPI:
    ensure_layout()
    app = FastAPI(title="AgentLoom API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:3000"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from agentloom.api.routes import config_router, tasks_router, graph_router

    app.include_router(config_router, prefix="/api")
    app.include_router(tasks_router, prefix="/api")
    app.include_router(graph_router, prefix="/api")

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app
