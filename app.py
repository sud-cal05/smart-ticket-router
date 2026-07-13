"""FastAPI service exposing the router over HTTP. Serves the web form at / and
JSON routing at /v1/route. The API key stays server-side — the browser never sees it."""

from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.responses import HTMLResponse  # noqa: E402
from pydantic import BaseModel  # noqa: E402

from router.core import route_ticket  # noqa: E402
from router.guards import EmptyInputError  # noqa: E402
from router.store import get_metrics  # noqa: E402

app = FastAPI(title="Smart Ticket Router", version="1.0")

_FORM_HTML = (Path(__file__).parent / "static" / "index.html").read_text()


class RouteRequest(BaseModel):
    text: str


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return _FORM_HTML


@app.get("/v1/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/v1/metrics")
def metrics() -> dict:
    return get_metrics()
@app.get("/manual", response_class=HTMLResponse)

def manual() -> str:
    return (Path(__file__).parent / "static" / "manual.html").read_text()

@app.post("/v1/route")
def route(req: RouteRequest) -> dict:
    try:
        result = route_ticket(req.text)
    except EmptyInputError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    return result.model_dump()