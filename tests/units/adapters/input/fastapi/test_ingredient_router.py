import pytest
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

from adapters.input.fastapi.dependencies import inject_tenant_uri, require_auth
from adapters.input.fastapi.routers import AdminRouter, IngredientRouter
from application.services.ingredient_service import IngredientService
from infrastructure.purge_registry import PurgeRegistry


def _payload(**kwargs) -> dict:
    return {"name": "Farine", "unit": "kg", **kwargs}


@pytest.fixture
def service(repo, logger):
    return IngredientService(repo, logger)


@pytest.fixture
def app(service, logger):
    fastapi_app = FastAPI()
    registry = PurgeRegistry()
    registry.register("ingredients", service.purge)
    fastapi_app.include_router(IngredientRouter(service, logger).router)
    fastapi_app.include_router(AdminRouter(registry).router)
    fastapi_app.dependency_overrides[inject_tenant_uri] = lambda: None
    fastapi_app.dependency_overrides[require_auth] = lambda: {"sub": "test-user"}
    return fastapi_app


@pytest.fixture
async def client(app):
    async with AsyncClient(transport = ASGITransport(app = app), base_url = "http://test") as c:
        yield c


@pytest.fixture
async def created(client):
    response = await client.post("/v1/ingredients/", json=_payload())
    return response.json()["data"]


# --- POST / ---

async def test_create_returns_201(client):
    response = await client.post("/v1/ingredients/", json=_payload())
    assert response.status_code == 201


async def test_create_returns_uuid(client):
    response = await client.post("/v1/ingredients/", json=_payload())
    data = response.json()
    assert data["status"] == "success"
    assert "uuid" in data["data"]


# --- GET /{uuid} ---

async def test_get_found(client, created):
    uuid = created["uuid"]
    response = await client.get(f"/v1/ingredients/{uuid}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["data"]["name"] == "Farine"
    assert data["data"]["unit"] == "kg"


async def test_get_not_found(client):
    response = await client.get("/v1/ingredients/01951234-5678-7abc-def0-000000000000")
    assert response.status_code == 404


# --- PUT /{uuid} ---

async def test_update_returns_204(client, created):
    uuid = created["uuid"]
    response = await client.put(f"/v1/ingredients/{uuid}", json = _payload(name = "Farine complète", unit = "g"))
    assert response.status_code == 204


async def test_update_reflects_on_get(client, created):
    uuid = created["uuid"]
    await client.put(f"/v1/ingredients/{uuid}", json=_payload(name="Farine complète", unit="g"))
    response = await client.get(f"/v1/ingredients/{uuid}")
    assert response.json()["data"]["name"] == "Farine complète"


# --- PATCH /{uuid} ---

async def test_patch_found_returns_204(client, created):
    uuid = created["uuid"]
    response = await client.patch(f"/v1/ingredients/{uuid}", json=_payload(name="Farine T80"))
    assert response.status_code == 204


async def test_patch_preserves_unset_fields(client, created):
    uuid = created["uuid"]
    await client.patch(f"/v1/ingredients/{uuid}", json=_payload(name="Farine T80"))
    response = await client.get(f"/v1/ingredients/{uuid}")
    data = response.json()["data"]
    assert data["name"] == "Farine T80"
    assert data["unit"] == "kg"


async def test_patch_not_found_returns_404(client):
    response = await client.patch(
        "/v1/ingredients/01951234-5678-7abc-def0-000000000000",
        json = _payload(name = "X"),
    )
    assert response.status_code == 404


# --- DELETE /{uuid} ---

async def test_delete_returns_204(client, created):
    uuid = created["uuid"]
    response = await client.delete(f"/v1/ingredients/{uuid}")
    assert response.status_code == 204


async def test_delete_hides_from_get(client, created):
    uuid = created["uuid"]
    await client.delete(f"/v1/ingredients/{uuid}")
    response = await client.get(f"/v1/ingredients/{uuid}")
    assert response.status_code == 404


# --- GET / ---

async def test_list_empty(client):
    response = await client.get("/v1/ingredients/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["data"] == []
    assert data["pagination"]["total"] == 0


async def test_list_returns_all(client):
    await client.post("/v1/ingredients/", json=_payload(name="Farine"))
    await client.post("/v1/ingredients/", json=_payload(name="Sel"))
    response = await client.get("/v1/ingredients/")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 2
    assert data["pagination"]["total"] == 2
    assert response.headers.get("x-total-count") == "2"


async def test_list_filtered_by_name(client):
    await client.post("/v1/ingredients/", json=_payload(name="Farine de blé"))
    await client.post("/v1/ingredients/", json=_payload(name="Sel fin"))
    response = await client.get("/v1/ingredients/", params={"name": "farine"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 1
    assert data["data"][0]["name"] == "Farine de blé"
    assert data["pagination"]["total"] == 1


async def test_list_filter_no_match(client):
    await client.post("/v1/ingredients/", json=_payload(name="Sel"))
    response = await client.get("/v1/ingredients/", params={"name": "sucre"})
    assert response.status_code == 200
    data = response.json()
    assert data["data"] == []
    assert data["pagination"]["total"] == 0


# --- POST /{uuid}/duplicate ---

async def test_duplicate_returns_201(client, created):
    uuid = created["uuid"]
    response = await client.post(f"/v1/ingredients/{uuid}/duplicate")
    assert response.status_code == 201


async def test_duplicate_has_different_uuid(client, created):
    uuid = created["uuid"]
    response = await client.post(f"/v1/ingredients/{uuid}/duplicate")
    data = response.json()
    assert data["status"] == "success"
    assert data["data"]["uuid"] != uuid


# --- DELETE /admin/purge ---

async def test_purge_returns_200(client):
    response = await client.delete("/admin/purge")
    assert response.status_code == 200


async def test_purge_returns_count(client):
    response = await client.delete("/admin/purge")
    data = response.json()
    assert "purged" in data
    assert "total" in data


async def test_purge_count_is_zero_when_nothing_eligible(client):
    await client.post("/v1/ingredients/", json=_payload())
    response = await client.delete("/admin/purge")
    assert response.json()["total"] == 0
