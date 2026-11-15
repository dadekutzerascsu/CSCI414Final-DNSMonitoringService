import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import dns.exception

from dns_lookup import lookup_a_record, normalize_domain


class NormalizeDomainTests(unittest.TestCase):
    def test_normalizes_case_and_fully_qualified_name(self):
        self.assertEqual(normalize_domain("Example.COM."), "example.com")

    def test_rejects_invalid_hostnames_and_ip_addresses(self):
        for value in ("", "bad_domain.example", "example.com..", "192.0.2.1"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                normalize_domain(value)


class LookupTests(unittest.TestCase):
    @patch("dns_lookup.dns.resolver.Resolver")
    def test_records_successful_a_answer_and_ttl(self, resolver_class):
        answer = MagicMock()
        answer.response.rcode.return_value = 0
        answer.rrset.ttl = 60
        answer.__iter__.return_value = iter([SimpleNamespace(address="192.0.2.1")])
        resolver_class.return_value.resolve.return_value = answer

        result = lookup_a_record("example.com")

        self.assertTrue(result.success)
        self.assertEqual(result.addresses, ["192.0.2.1"])
        self.assertEqual(result.ttl, 60)
        self.assertIsNone(result.error)

    @patch("dns_lookup.dns.resolver.Resolver")
    def test_records_dns_timeouts_as_failed_measurements(self, resolver_class):
        resolver_class.return_value.resolve.side_effect = dns.exception.Timeout("timed out")

        result = lookup_a_record("example.com")

        self.assertFalse(result.success)
        self.assertEqual(result.response_code, "Timeout")
        self.assertEqual(result.error, "timed out")


if __name__ == "__main__":
    unittest.main()
