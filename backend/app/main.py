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
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(routes.router)
app.include_router(ws_meeting.router)
