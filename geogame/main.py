import logging
from dataclasses import dataclass
from enum import Enum
from sqlite3 import Connection
from typing import Any, Dict, cast
from uuid import uuid4

from fast_autocomplete import AutoComplete
from fastapi import Depends, FastAPI, Request, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi_utils.timing import add_timing_middleware

from geogame.utils.db import convert_results, get_db
from geogame.utils.load_db import load_cities
from geogame.utils.models import CityInDb

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
add_timing_middleware(app, record=logger.info, prefix="app", exclude="untimed")


@app.on_event("startup")
async def load_data():
    logger.debug("Started data loading")
    load_cities()
    logger.debug("Finished data loading")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html.jinja2", {"request": request})


@dataclass
class Level:
    name: str
    population: int


class Levels(Enum):
    VERY_EASY = Level(name="very easy", population=1_000_000)
    EASY = Level(name="easy", population=500_000)
    MEDIUM = Level(name="medium", population=100_000)
    HARD = Level(name="hard", population=50_000)


# NOTE:
# Add option to choose continent
# 2 tips
# - map with locations
# - list of 5 cities to choose from, 5 next cities ordered by population


@app.get("/game/options")
async def get_game_options(request: Request, db: Connection = Depends(get_db)):
    timezones = convert_results(
        db.cursor()
        .execute(
            """
            select distinct timezone_general from cities
            group by timezone_general having count(*) > 5
            """
        )
        .fetchall()
    )

    return templates.TemplateResponse(
        "game_options.html.jinja2",
        {
            "request": request,
            "timezones": ["any", *[t["timezone_general"] for t in timezones]],
            "levels": Levels,
        },
    )


_cities_cache: Dict[str, Any] = {}


def get_cities_for_search(db: Connection):
    global _cities_cache
    if not _cities_cache:
        q = """select distinct name from cities"""
        _cities_cache = {
            c["name"]: {} for c in convert_results(db.cursor().execute(q).fetchall())
        }
    return _cities_cache


@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    db: Connection = Depends(get_db),
):
    await websocket.accept()
    autocomplete = AutoComplete(words=get_cities_for_search(db))
    while True:
        data = await websocket.receive_text()
        results = autocomplete.search(word=data, max_cost=3, size=5)
        await websocket.send_json(results)


@app.get("/game/start", response_class=HTMLResponse)
async def get_game(
    request: Request,
    level: str,
    timezone: str,
    cities_count: int,
    db: Connection = Depends(get_db),
):
    id = str(uuid4())

    selected_level: Levels = Levels[level]

    selected_timezone = None if timezone == "any" else timezone

    if selected_timezone is not None:
        q = """
        select distinct country_name_en, country_code, count(*) number from cities
        where population >= ? and timezone_general = ? group by country_code having count(*) >= ?
        """
        params = (
            cast(int, selected_level.value.population),
            selected_timezone,
            cities_count,
        )
    else:
        q = """
        select distinct country_name_en, country_code, count(*) number from cities
        where population >= ? group by country_code having count(*) >= ?
        """
        params = (selected_level.value.population, cities_count)  # type: ignore

    countries = convert_results(db.cursor().execute(q, params).fetchall())

    import random

    country = random.choice(countries)

    cities = convert_results(
        db.cursor()
        .execute(
            "select * from cities where country_code = ? order by population desc limit ?",
            (country["country_code"], cities_count),
        )
        .fetchall()
    )

    max_pop = max(c["population"] for c in cities)

    cities = [
        CityInDb(
            **{
                **c,
                "coordinates": c["coordinates"].split(","),
                "dot_size": c["population"] / max_pop,
            }
        )
        for c in cities
    ]

    index_to_find = random.randint(1, cities_count)

    return templates.TemplateResponse(
        "game.html.jinja2",
        {
            "request": request,
            "id": id,
            "cities": cities,
            "timezone": selected_timezone,
            "country": country["country_name_en"],
            "level": selected_level.value.name,
            "level_population": selected_level.value.population,
            "index_to_find": index_to_find,
        },
    )
