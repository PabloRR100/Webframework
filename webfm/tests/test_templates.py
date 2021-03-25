import pytest

from api import API
from constants import BASE_URL


def test_template(api, client):
    @api.route("/html")
    def html_handler(req, resp):
        resp.body = api.template(
            "index.html",
            context={
                "title": "Some title",
                "name": "Some name"
            }
        ).encode()

    response = client.get(f"{BASE_URL}/html")

    assert "text/html" in response.headers["Content-Type"]
    assert "Some title" in response.text
    assert "Some name" in response.text
