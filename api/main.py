import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query, Request, status
from pydantic import BaseModel, ConfigDict, field_validator
from pymongo import ASCENDING, DESCENDING, MongoClient, ReturnDocument
from pymongo.errors import DuplicateKeyError

from dns_lookup import lookup_a_record, normalize_domain

MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb://dnsapp:dnsapp-local-only@mongodb:27017/dns_monitor?authSource=dns_monitor",
)
DATABASE_NAME = os.getenv("DATABASE_NAME", "dns_monitor")


class DomainCreate(BaseModel):
    domain: str
    source: str = "manual"

    @field_validator("domain")
    @classmethod
    def validate_domain(cls, value: str) -> str:
        try:
            return normalize_domain(value)
        except ValueError as exc:
            raise ValueError(str(exc)) from exc

    @field_validator("source")
    @classmethod
    def validate_source(cls, value: str) -> str:
        source = value.strip()
        if not source or len(source) > 80:
            raise ValueError("Source must contain 1 to 80 characters")
        return source


class DomainUpdate(BaseModel):
    enabled: bool


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    database = client[DATABASE_NAME]
    database.domains.create_index([("domain", ASCENDING)], unique=True)
    database.checks.create_index([("domain", ASCENDING), ("checked_at", DESCENDING)])
    app.state.mongo_client = client
    app.state.database = database
    try:
        yield
    finally:
        client.close()


app = FastAPI(title="Distributed DNS Monitoring Service", lifespan=lifespan)


def get_database(request: Request):
    return request.app.state.database


def serialize(document: dict) -> dict:
    document.pop("_id", None)
    return document


@app.get("/health")
def health(request: Request):
    get_database(request).command("ping")
    return {"status": "ok", "database": "connected"}


@app.post("/domains", status_code=status.HTTP_201_CREATED)
def create_domain(payload: DomainCreate, request: Request):
    now = datetime.now(timezone.utc)
    document = {
        "domain": payload.domain,
        "source": payload.source,
        "enabled": True,
        "created_at": now,
        "updated_at": now,
    }
    try:
        get_database(request).domains.insert_one(document)
    except DuplicateKeyError as exc:
        raise HTTPException(status_code=409, detail="Domain is already being monitored") from exc
    return serialize(document)


@app.get("/domains")
def list_domains(
    request: Request,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    skip: Annotated[int, Query(ge=0)] = 0,
):
    documents = get_database(request).domains.find().sort("domain", ASCENDING).skip(skip).limit(limit)
    return [serialize(document) for document in documents]


@app.get("/domains/{domain}")
def get_domain(domain: str, request: Request):
    try:
        normalized = normalize_domain(domain)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    document = get_database(request).domains.find_one({"domain": normalized})
    if document is None:
        raise HTTPException(status_code=404, detail="Domain is not registered")
    return serialize(document)


@app.patch("/domains/{domain}")
def update_domain(domain: str, payload: DomainUpdate, request: Request):
    try:
        normalized = normalize_domain(domain)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    document = get_database(request).domains.find_one_and_update(
        {"domain": normalized},
        {"$set": {"enabled": payload.enabled, "updated_at": datetime.now(timezone.utc)}},
        return_document=ReturnDocument.AFTER,
    )
    if document is None:
        raise HTTPException(status_code=404, detail="Domain is not registered")
    return serialize(document)


@app.post("/domains/{domain}/checks", status_code=status.HTTP_201_CREATED)
def check_domain(domain: str, request: Request):
    try:
        normalized = normalize_domain(domain)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    database = get_database(request)
    registered_domain = database.domains.find_one({"domain": normalized})
    if registered_domain is None:
        raise HTTPException(status_code=404, detail="Domain is not registered")
    if not registered_domain["enabled"]:
        raise HTTPException(status_code=409, detail="Domain monitoring is disabled")

    result = lookup_a_record(normalized)
    document = {
        "domain": normalized,
        "checked_at": datetime.now(timezone.utc),
        "success": result.success,
        "latency_ms": result.latency_ms,
        "response_code": result.response_code,
        "addresses": result.addresses,
        "ttl": result.ttl,
        "error": result.error,
    }
    database.checks.insert_one(document)
    return serialize(document)


@app.get("/domains/{domain}/checks")
def list_checks(
    domain: str,
    request: Request,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
):
    try:
        normalized = normalize_domain(domain)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    database = get_database(request)
    if database.domains.find_one({"domain": normalized}, {"_id": 1}) is None:
        raise HTTPException(status_code=404, detail="Domain is not registered")
    documents = database.checks.find({"domain": normalized}).sort("checked_at", DESCENDING).limit(limit)
    return [serialize(document) for document in documents]