from __future__ import annotations

from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import HTMLResponse
from rdflib import Graph

from app.core.config import settings
from app.services.graph_viz import visualize_rdflib_graph_to_html

router = APIRouter(tags=["visualize"])


@router.post("/visualize", response_class=HTMLResponse)
def visualize(turtle: str = Form(...), include_literals: bool = Form(True)):
    if not turtle or turtle.strip() == "":
        raise HTTPException(status_code=422, detail="No Turtle content provided.")
    if len(turtle) > settings.max_turtle_chars:
        raise HTTPException(
            status_code=413,
            detail=f"Turtle exceeds {settings.max_turtle_chars} characters.",
        )

    try:
        g = Graph()
        g.parse(data=turtle, format="turtle")
    except Exception as e:
        # Keep message terse for UX; detailed logs can carry full exception.
        raise HTTPException(status_code=400, detail=f"Parse error: {e}") from e

    html = visualize_rdflib_graph_to_html(
        graph=g,
        include_literals=include_literals,
        bgcolor=settings.theme_bgcolor,
        fontcolor=settings.theme_fontcolor,
    )
    return HTMLResponse(html)
