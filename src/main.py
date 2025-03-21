import importlib
import logging
import os
import yaml

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import TYPE_CHECKING

import config
from modules.db import get_db

if TYPE_CHECKING:
    from fastapi import APIRouter

# FastAPI requires a global variable named 'app' to be defined as the FastAPI
# instance.
app = FastAPI()
config.app = app
_log = logging.getLogger("uvicorn")
load_dotenv()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # This enables CORS for all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APP_CONFIG_DIR = os.path.join(BASE_DIR, "configs", "app_config.yaml")
ROUTERS_DIR = os.path.join(BASE_DIR, "web", "routers")


def _get_config() -> None:
    if not os.path.exists(APP_CONFIG_DIR):
        raise FileNotFoundError(
            f"App config file not found. Should be at {APP_CONFIG_DIR}"
        )

    with open(APP_CONFIG_DIR, "r") as f:
        config.app_config = yaml.safe_load(f)


def _import_routers() -> None:
    for filename in os.listdir(ROUTERS_DIR):
        if not filename.endswith(".py"):
            continue

        relative_dir = ROUTERS_DIR.replace(BASE_DIR, "")[1:]

        module_path = relative_dir.replace(os.path.sep, ".") + "." + filename[:-3]

        module = importlib.import_module(module_path)
        if hasattr(module, "router"):
            router: APIRouter = getattr(module, "router")
            app.include_router(router)
            _log.info(f"Included router: {filename[:-3]}")
        else:
            _log.warning(f"Router {filename} does not have a router object")


# Don't use if __name__ == "__main__": here.
# Can't use `fastapi` command otherwise.
_log.setLevel(logging.DEBUG)
_get_config()
_import_routers()

config.db = get_db(os.getenv("ASTRA_DB_APPLICATION_ENDPOINT"))

_log.info("App initialized")
