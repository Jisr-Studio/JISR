"""Transient provider failures retry within bounds, without hiding bad keys."""
import io
import json
import sys
import unittest
import urllib.error
from email.message import Message
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server


def error(code, retry_after=None):
    headers = Message()
    if retry_after is not None:
        headers["Retry-After"] = str(retry_after)
    return urllib.error.HTTPError("https://api.openai.com/v1/responses", code, "provider failure", headers, io.BytesIO(b"{}"))


class ServiceRetriesTests(unittest.TestCase):
    def run_request(self):
        return server.post_json("https://api.openai.com/v1/responses", {"store": False}, {"Authorization": "Bearer test-only"})

    @patch.object(server.time, "sleep")
    @patch.object(server.urllib.request, "urlopen")
    def test_transient_outage_retries_identical_payload_and_then_succeeds(self, urlopen, sleep):
        urlopen.side_effect = [error(503), error(502), io.BytesIO(json.dumps({"status": "completed"}).encode())]
        self.assertEqual(self.run_request()["status"], "completed")
        self.assertEqual(urlopen.call_count, 3)
        self.assertEqual(sleep.call_count, 2)
        self.assertEqual(len({call.args[0].data for call in urlopen.call_args_list}), 1)
        for attempt, call in enumerate(sleep.call_args_list):
            self.assertGreaterEqual(call.args[0], 2 ** attempt)
            self.assertLess(call.args[0], 2 ** attempt + .25)

    @patch.object(server.time, "sleep")
    @patch.object(server.urllib.request, "urlopen")
    def test_exhausted_attempts_keep_original_http_status(self, urlopen, sleep):
        urlopen.side_effect = [error(503), error(503), error(503)]
        with self.assertRaises(urllib.error.HTTPError) as result:
            self.run_request()
        self.assertEqual(result.exception.code, 503)
        self.assertEqual(urlopen.call_count, 3)

    @patch.object(server.time, "sleep")
    @patch.object(server.urllib.request, "urlopen")
    def test_bad_keys_schema_errors_and_long_quota_waits_are_not_retried(self, urlopen, sleep):
        for failure in (error(400), error(401), error(403), error(429, 120)):
            with self.subTest(code=failure.code):
                urlopen.reset_mock()
                urlopen.side_effect = failure
                with self.assertRaises(urllib.error.HTTPError):
                    self.run_request()
                self.assertEqual(urlopen.call_count, 1)
        sleep.assert_not_called()

    @patch.object(server.time, "sleep")
    @patch.object(server.urllib.request, "urlopen")
    def test_short_retry_after_is_respected(self, urlopen, sleep):
        urlopen.side_effect = [error(429, 5), io.BytesIO(b'{"status":"completed"}')]
        self.run_request()
        self.assertGreaterEqual(sleep.call_args.args[0], 5)
        self.assertLess(sleep.call_args.args[0], 5.25)

    @patch.object(server.time, "sleep")
    @patch.object(server.urllib.request, "urlopen", side_effect=TimeoutError("unknown provider outcome"))
    def test_transport_timeout_does_not_duplicate_a_potentially_completed_call(self, urlopen, sleep):
        with self.assertRaises(TimeoutError):
            self.run_request()
        self.assertEqual(urlopen.call_count, 1)
        sleep.assert_not_called()


if __name__ == "__main__":
    unittest.main()
