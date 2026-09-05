from app.main import app


def test_openapi_exposes_jwt_bearer_authorization() -> None:
    schema = app.openapi()

    assert schema["components"]["securitySchemes"]["BearerAuth"] == {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "Paste a valid Neon Auth access token.",
    }
    assert schema["security"] == [{"BearerAuth": []}]
