import argparse
import csv
import os
from datetime import datetime, timezone

from pymongo import ASCENDING, MongoClient

from dns_lookup import normalize_domain


def import_domains(source_path: str, limit: int, database_uri: str, database_name: str) -> int:
    client = MongoClient(database_uri, serverSelectionTimeoutMS=5000)
    try:
        database = client[database_name]
        database.command("ping")
        collection = database.domains
        collection.create_index([("domain", ASCENDING)], unique=True)

        imported = 0
        now = datetime.now(timezone.utc)
        with open(source_path, newline="", encoding="utf-8-sig") as source:
            for row in csv.reader(source):
                if not row:
                    continue
                candidate = row[1] if len(row) > 1 else row[0]
                if candidate.strip().lower() in {"domain", "hostname"}:
                    continue
                try:
                    domain = normalize_domain(candidate)
                except ValueError:
                    continue
                collection.update_one(
                    {"domain": domain},
                    {
                        "$setOnInsert": {
                            "domain": domain,
                            "source": "Tranco",
                            "enabled": True,
                            "created_at": now,
                            "updated_at": now,
                        }
                    },
                    upsert=True,
                )
                imported += 1
                if imported >= limit:
                    break
        return imported
    finally:
        client.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Import ranked domains from a Tranco CSV file.")
    parser.add_argument("source", help="Path to a Tranco CSV (rank,domain) or one-domain-per-line file")
    parser.add_argument("--limit", type=int, default=1000, help="Maximum number of source rows to import")
    args = parser.parse_args()
    if args.limit < 1:
        parser.error("--limit must be at least 1")

    count = import_domains(
        args.source,
        args.limit,
        os.getenv("MONGODB_URI", "mongodb://dnsapp:dnsapp-local-only@mongodb:27017/dns_monitor?authSource=dns_monitor"),
        os.getenv("DATABASE_NAME", "dns_monitor"),
    )
    print(f"Imported or confirmed {count} domain records.")


if __name__ == "__main__":
    main()
