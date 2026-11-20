"""Port REST client for ContextCost Lab's isolated demo service blueprint.

Uses PORT_API_BASE, PORT_CLIENT_ID, and PORT_CLIENT_SECRET from .env.
The calling script (seed_port.py) loads .env before constructing PortClient.
"""

import os
import requests

BLUEPRINT = "contextcost_service"


class PortClient:
    def __init__(self, client_id=None, client_secret=None, base=None):
        self.client_id = client_id or os.getenv("PORT_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("PORT_CLIENT_SECRET")
        self.base = (base or os.getenv("PORT_API_BASE") or "https://api.port.io/v1").rstrip("/")
        if not self.client_id or not self.client_secret:
            raise ValueError("Set PORT_CLIENT_ID and PORT_CLIENT_SECRET in your .env file")
        self.session = requests.Session()
        self.token = None

    def auth(self):
        response = self.session.post(
            self.base + "/auth/access_token",
            json={"clientId": self.client_id, "clientSecret": self.client_secret},
            timeout=30,
        )
        self._check(response)
        self.token = response.json()["accessToken"]

    @staticmethod
    def _check(response):
        if not response.ok:
            try:
                details = response.json()
            except ValueError:
                details = response.text
            raise RuntimeError(
                "Port API request failed\n"
                f"HTTP status: {response.status_code}\n"
                f"URL: {response.url}\n"
                f"Port response: {details}"
            )

    def request(self, method, path, **kwargs):
        if not self.token:
            self.auth()
        headers = dict(kwargs.pop("headers", {}))
        headers.update({
            "Authorization": "Bearer " + self.token,
            "Content-Type": "application/json",
        })
        response = self.session.request(
            method, self.base + path, headers=headers, timeout=30, **kwargs
        )
        if response.status_code == 401:
            self.auth()
            headers["Authorization"] = "Bearer " + self.token
            response = self.session.request(
                method, self.base + path, headers=headers, timeout=30, **kwargs
            )
        self._check(response)
        return response.json() if response.content else {}

    def create_blueprint(self):
        # Define nested object fields explicitly rather than an unconstrained object.
        schema = {
            "identifier": BLUEPRINT,
            "title": "ContextCost Demo Service",
            "icon": "Microservice",
            "schema": {
                "properties": {
                    "team": {"type": "string"},
                    "repo": {"type": "string", "format": "url"},
                    "environment": {"type": "string"},
                    "dependencies": {"type": "array", "items": {"type": "string"}},
                    "runbook": {"type": "string"},
                    "latest_deployment": {
                        "type": "object",
                        "properties": {
                            "version": {"type": "string"},
                            "status": {"type": "string"},
                            "change": {"type": "string"},
                        },
                    },
                    "health": {"type": "string"},
                    "notes": {"type": "string"},
                }
            },
        }
        # Port's blueprint creation endpoint does not accept an `upsert` query
        # parameter. Create it once; update the existing demo blueprint on 409.
        try:
            return self.request("POST", "/blueprints", json=schema)
        except RuntimeError as exc:
            if "HTTP status: 409" not in str(exc):
                raise
            return self.request("PUT", f"/blueprints/{BLUEPRINT}", json=schema)

    def upsert_service(self, service):
        entity = {
            "identifier": service["identifier"],
            "title": service["title"],
            "properties": {
                key: value
                for key, value in service.items()
                if key not in ("identifier", "title")
            },
        }
        return self.request(
            "POST", f"/blueprints/{BLUEPRINT}/entities",
            params={"upsert": "true"}, json=entity,
        )

    def list_services(self):
        """Fetch demo entities without unsupported page/per_page parameters.

        This demo seeds 12 services. For a larger catalog, implement Port's
        supported cursor-based pagination rather than numeric page parameters.
        """
        payload = self.request("GET", f"/blueprints/{BLUEPRINT}/entities")
        items = payload.get("entities", [])
        return [
            {"identifier": item["identifier"], **item.get("properties", {})}
            for item in items
        ]

    def get_service_entity(self, identifier):
        """Read a single live Port entity (no cached local fixture)."""
        from urllib.parse import quote
        return self.request("GET", f"/blueprints/{BLUEPRINT}/entities/{quote(identifier, safe='')}")["entity"]

    def update_demo_owner(self, identifier, new_owner):
        """Update only the owner field while retaining all other entity properties.

        Uses the entity upsert endpoint already exercised by seed_port.py.
        """
        entity = self.get_service_entity(identifier)
        properties = dict(entity.get("properties", {}))
        properties["team"] = new_owner
        payload = {"identifier": entity["identifier"], "title": entity.get("title", identifier), "properties": properties}
        return self.request("POST", f"/blueprints/{BLUEPRINT}/entities", params={"upsert": "true"}, json=payload)