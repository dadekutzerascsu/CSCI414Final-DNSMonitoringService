import ipaddress
import re
import time
from dataclasses import dataclass

import dns.exception
import dns.rcode
import dns.resolver

_LABEL = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")


@dataclass(frozen=True)
class LookupResult:
    success: bool
    latency_ms: float
    response_code: str
    addresses: list[str]
    ttl: int | None
    error: str | None


def normalize_domain(value: str) -> str:
    domain = value.strip()
    if domain.endswith("."):
        domain = domain[:-1]
    if not domain:
        raise ValueError("Domain must not be empty")

    try:
        ascii_domain = domain.encode("idna").decode("ascii").lower()
    except UnicodeError as exc:
        raise ValueError("Domain is not a valid internationalized hostname") from exc

    if len(ascii_domain) > 253:
        raise ValueError("Domain must be at most 253 characters")
    labels = ascii_domain.split(".")
    if any(not _LABEL.fullmatch(label) for label in labels):
        raise ValueError("Domain contains an invalid hostname label")
    try:
        ipaddress.ip_address(ascii_domain)
    except ValueError:
        pass
    else:
        raise ValueError("Expected a hostname, not an IP address")

    return ascii_domain


def lookup_a_record(domain: str, timeout: float = 3.0) -> LookupResult:
    resolver = dns.resolver.Resolver()
    started = time.perf_counter()
    try:
        answer = resolver.resolve(domain, "A", lifetime=timeout, raise_on_no_answer=False)
        response_code = dns.rcode.to_text(answer.response.rcode())
        addresses = [record.address for record in answer] if answer.rrset else []
        success = response_code == "NOERROR" and bool(addresses)
        return LookupResult(
            success=success,
            latency_ms=round((time.perf_counter() - started) * 1000, 3),
            response_code=response_code,
            addresses=addresses,
            ttl=answer.rrset.ttl if answer.rrset else None,
            error=None if success else ("No A records found" if not addresses else response_code),
        )
    except (dns.exception.DNSException, OSError) as exc:
        return LookupResult(
            success=False,
            latency_ms=round((time.perf_counter() - started) * 1000, 3),
            response_code=type(exc).__name__,
            addresses=[],
            ttl=None,
            error=str(exc) or type(exc).__name__,
        )
