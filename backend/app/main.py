import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import routes, ws_meeting
from .config import settings
from .models import db
from .services.llm import LLMClient
from .services.room import RoomManager

logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)  # one INFO line per LLM call is noise


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    app.state.llm = LLMClient()
    await app.state.llm.startup_check()
    app.state.rooms = RoomManager(app.state.llm)
    logging.getLogger("wisemouth").info(
        "stt=%s llm=%s", "assemblyai" if settings.assemblyai_api_key else "OFF (demo/typed only)", app.state.llm.name)
    yield


app = FastAPI(title="WiseMouth", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    # Strip whitespace and trailing slashes: browsers send Origin without one, so "https://x.vercel.app/" would never match.
    allow_origins=[o.strip().rstrip("/") for o in settings.cors_origins.split(",") if o.strip()],
    # Optional regex so Vercel preview deploys (https://<project>-<hash>-<team>.vercel.app) work without listing each one.
    allow_origin_regex=settings.cors_origin_regex or None,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(routes.router)
app.include_router(ws_meeting.router)
