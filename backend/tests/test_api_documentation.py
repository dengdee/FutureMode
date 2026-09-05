from pathlib import Path

from app.main import app
from app.api.teams import router as teams_router


def test_api_usage_documents_all_http_routes():
    documentation = (Path(__file__).parents[1] / "app" / "api" / "API_USAGE.md").read_text(
        encoding="utf-8"
    )
    excluded = {"/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc"}
    undocumented = []
    for route in app.routes:
        path = getattr(route, "path", None)
        methods = getattr(route, "methods", set())
        if not path or not methods or path in excluded:
            continue
        # Docs intentionally group GET/POST variants in one row; path coverage is the contract.
        if path not in documentation:
            undocumented.append(path)
    assert not undocumented, f"API_USAGE.md missing routes: {sorted(set(undocumented))}"


def test_in_app_invitation_routes_are_registered():
    routes = {
        (route.path, method)
        for route in teams_router.routes
        if hasattr(route, "methods")
        for method in (route.methods or set())
    }
    assert ("/api/v1/me/invitations", "GET") in routes
    assert ("/api/v1/me/invitations/{invitation_id}/{action}", "POST") in routes
