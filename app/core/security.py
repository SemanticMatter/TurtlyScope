from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        resp: Response = await call_next(request)
        # Note: PyVis uses inline scripts; CSP below allows it for the visualization page.
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "DENY")
        resp.headers.setdefault("Referrer-Policy", "no-referrer")
        # Loosened CSP due to PyVis 'in_line' resources; scope route-level CSP if you tighten later.
        resp.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self' data: blob:; img-src 'self' data: blob:; "
            "style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline';",
        )
        return resp
