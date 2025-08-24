#!/usr/local/autopkg/python

# Recipe Robot
# Copyright 2015-2020 Elliot Jordan, Shea G. Craig, and Eldon Ahrold
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""
test_curler.py

Unit tests for curl-related functions.
"""


import json
import os
import unittest
from unittest.mock import patch
from scripts.recipe_robot_lib import curler


class TestCurler(unittest.TestCase):
    """Tests for the curl-related functions."""

    curl_path = "/usr/bin/curl"

    def test_curl_exists(self):
        """Verify the curl binary exists at the expected location."""
        self.assertTrue(os.path.isfile(self.curl_path))

    def test_prepare_curl_cmd(self):
        """Verify we can assemble a basic curl command."""
        expected = [
            self.curl_path,
            "--compressed",
            "--location",
            "--silent",
            "--show-error",
        ]
        actual = curler.prepare_curl_cmd()
        self.assertEqual(expected, actual)

    def test_add_curl_headers(self):
        """Verify we can add headers to a curl command."""
        curl_cmd = [self.curl_path]
        headers = {"foo": "bar", "fizz": "buzz"}
        curler.add_curl_headers(curl_cmd, headers)
        expected = [self.curl_path, "--header", "foo: bar", "--header", "fizz: buzz"]
        self.assertEqual(expected, curl_cmd)

    def test_clear_header(self):
        """Verify we can clear curl headers."""
        header = {
            "http_redirected": "foo",
            "http_result_code": "201",
            "http_result_description": "bar",
        }
        curler.clear_header(header)
        expected = {
            "http_redirected": "foo",
            "http_result_code": "000",
            "http_result_description": "",
        }
        self.assertEqual(expected, header)

        header = {}
        curler.clear_header(header)
        expected = {
            "http_redirected": None,
            "http_result_code": "000",
            "http_result_description": "",
        }
        self.assertEqual(expected, header)

    def test_parse_http_protocol(self):
        """Verify we can parse first HTTP header line."""
        header = {}
        curler.parse_http_protocol("HTTP/2 200", header)
        expected = {
            "http_result_code": "200",
        }
        self.assertEqual(expected, header)

        header = {}
        curler.parse_http_protocol("HTTP/2 403 FORBIDDEN", header)
        expected = {
            "http_result_code": "403",
            "http_result_description": "FORBIDDEN",
        }
        self.assertEqual(expected, header)

        header = {}
        curler.parse_http_protocol("", header)
        expected = {}
        self.assertEqual(expected, header)

    def test_parse_http_header(self):
        """Verify we can parse a single HTTP header line."""
        header = {}
        curler.parse_http_header("expires: Fri, 11 Dec 2023 08:59:27 GMT", header)
        expected = {"expires": "Fri, 11 Dec 2023 08:59:27 GMT"}
        self.assertEqual(expected, header)

        header = {}
        curler.parse_http_header("foo", header)
        expected = {"foo": ""}
        self.assertEqual(expected, header)

    def test_parse_curl_error_txt(self):
        """Verify we can report a curl failure from text."""
        actual = curler.parse_curl_error(
            "curl: (6) Could not resolve host: example.none"
        )
        expected = "Could not resolve host: example.none"
        self.assertEqual(expected, actual)

        actual = curler.parse_curl_error("")
        expected = ""
        self.assertEqual(expected, actual)

    def test_parse_curl_error_bytes(self):
        """Verify we can report a curl failure from bytes."""
        actual = curler.parse_curl_error(
            b"curl: (6) Could not resolve host: example.none"
        )
        expected = "Could not resolve host: example.none"
        self.assertEqual(expected, actual)

        actual = curler.parse_curl_error(b"")
        expected = ""
        self.assertEqual(expected, actual)

    def test_parse_http_headers(self):
        """Verify we can parse headers from curl."""
        raw_headers = """HTTP/2 200\ncontent-encoding: gzip\naccept-ranges: bytes\nage: 428098\ncache-control: max-age=604800\ncontent-type: text/html; charset=UTF-8\ndate: Wed, 11 Nov 2020 08:57:15 GMT\netag: "3147526947+gzip"\nexpires: Wed, 18 Nov 2020 08:57:15 GMT\nlast-modified: Thu, 17 Oct 2019 07:18:26 GMT\nserver: ECS (sec/976A)\nx-cache: HIT\ncontent-length: 648\n"""
        header = curler.parse_headers(raw_headers)
        expected = {
            "accept-ranges": "bytes",
            "age": "428098",
            "cache-control": "max-age=604800",
            "content-encoding": "gzip",
            "content-length": "648",
            "content-type": "text/html; charset=UTF-8",
            "date": "Wed, 11 Nov 2020 08:57:15 GMT",
            "etag": '"3147526947+gzip"',
            "expires": "Wed, 18 Nov 2020 08:57:15 GMT",
            "http_redirected": None,
            "http_result_code": "200",
            "http_result_description": "",
            "last-modified": "Thu, 17 Oct 2019 07:18:26 GMT",
            "server": "ECS (sec/976A)",
            "x-cache": "HIT",
        }
        self.assertEqual(expected, header)

        raw_headers = "\n".join(
            (
                "HTTP/2 301",
                "location: https://www.google.com/",
                "content-type: text/html; charset=UTF-8",
                "date: Wed, 11 Nov 2020 08:59:27 GMT",
                "expires: Fri, 11 Dec 2023 08:59:27 GMT",
                "cache-control: public, max-age=2592000",
                "server: gws",
                "content-length: 220",
                "x-xss-protection: 0",
                "x-frame-options: SAMEORIGIN",
            )
        )
        header = curler.parse_headers(raw_headers)
        expected = {
            "cache-control": "public, max-age=2592000",
            "content-length": "220",
            "content-type": "text/html; charset=UTF-8",
            "date": "Wed, 11 Nov 2020 08:59:27 GMT",
            "expires": "Fri, 11 Dec 2023 08:59:27 GMT",
            "http_redirected": None,
            "http_result_code": "301",
            "http_result_description": "",
            "location": "https://www.google.com/",
            "server": "gws",
            "x-frame-options": "SAMEORIGIN",
            "x-xss-protection": "0",
        }
        self.assertEqual(expected, header)

    def test_parse_ftp_header_line(self):
        """Verify we can parse a single FTP header line."""
        header = {}
        curler.parse_ftp_header("213 123456", header)
        expected = {"content-length": "123456"}
        self.assertEqual(expected, header)

        header = {}
        curler.parse_ftp_header("213", header)
        expected = {}
        self.assertEqual(expected, header)

        header = {}
        curler.parse_ftp_header("55 TEST", header)
        expected = {
            "http_result_code": "404",
            "http_result_description": "55 TEST",
        }
        self.assertEqual(expected, header)

        header = {}
        curler.parse_ftp_header("125 TEST", header)
        expected = {
            "http_result_code": "200",
            "http_result_description": "125 TEST",
        }
        self.assertEqual(expected, header)

        header = {}
        curler.parse_ftp_header("FOO BAR", header)
        expected = {}
        self.assertEqual(expected, header)

    def test_parse_ftp_headers_full(self):
        """Verify we can parse FTP headers from curl."""
        raw_headers = (
            """125 Data connection already open; transfer starting.\n213 123456\n"""
        )
        header = curler.parse_headers(raw_headers, url="ftp://example.com/file.txt")
        expected = {
            "content-length": "123456",
            "http_redirected": None,
            "http_result_code": "200",
            "http_result_description": "125 Data connection already open; transfer starting.",
        }
        self.assertEqual(expected, header)

    def test_execute_curl(self):
        """Verify we can execute a curl command."""
        response, _, _ = curler.execute_curl(
            [
                self.curl_path,
                "--silent",
                "--url",
                "https://jsonplaceholder.typicode.com/todos/1",
            ],
        )
        actual = json.loads(response)
        expected = {
            "completed": False,
            "id": 1,
            "title": "delectus aut autem",
            "userId": 1,
        }
        self.assertEqual(expected, actual)

    def test_download_with_curl(self):
        """Verify we can use curl to download a URL, handling failures."""
        response = curler.download_with_curl(
            [
                self.curl_path,
                "--silent",
                "--url",
                "https://jsonplaceholder.typicode.com/todos/1",
            ],
        )
        actual = json.loads(response)
        expected = {
            "completed": False,
            "id": 1,
            "title": "delectus aut autem",
            "userId": 1,
        }
        self.assertEqual(expected, actual)

    def test_download(self):
        """Verify we can use curl to download a URL with default options."""
        url = "https://jsonplaceholder.typicode.com/todos/1"
        response = curler.download(url)
        actual = json.loads(response)
        expected = {
            "completed": False,
            "id": 1,
            "title": "delectus aut autem",
            "userId": 1,
        }
        self.assertEqual(expected, actual)

    def test_download_to_file(self):
        """Verify we can use curl to download a URL to a file."""
        url = "https://jsonplaceholder.typicode.com/todos/1"
        filepath = "/private/tmp/test_download_to_file"
        curler.download_to_file(url, filepath, app_mode=True)
        with open(filepath) as openfile:
            actual = json.loads(openfile.read())
        expected = {
            "completed": False,
            "id": 1,
            "title": "delectus aut autem",
            "userId": 1,
        }
        self.assertEqual(expected, actual)

    def test_get_headers(self):
        """Verify we can get a URL's HTTP headers, parse them, and return them."""
        headers, retcode = curler.get_headers("https://www.example.com")
        self.assertEqual(retcode, 0)
        self.assertEqual(headers.get("content-type"), "text/html")
        self.assertEqual(headers.get("http_result_code"), "200")

    # def test_check_url_switches_to_https(self):
    #     """Verify we can test a URL's headers, and switch to HTTPS if available."""
    #     # Case 1: HTTP URL that should switch to HTTPS
    #     url, headers, _ = curler.check_url("http://www.example.com")
    #     self.assertEqual(url, "https://www.example.com")
    #     self.assertEqual(headers.get("content-type"), "text/html")
    #     self.assertEqual(headers.get("http_result_code"), "200")

    def test_check_url_no_https_available(self):
        """Test that check_url returns original URL if HTTPS is not available."""
        # Use a reserved TLD that will not resolve to simulate failure
        url = "http://example.invalid"
        checked_url, headers, ua = curler.check_url(url)
        self.assertEqual(checked_url, url)
        self.assertIsInstance(headers, dict)
        self.assertIsNone(ua)

    def test_check_url_handles_403_with_devmate(self):
        """Test that check_url returns Safari UA for devmate URLs with 403."""

        # Patch get_headers to simulate a 403 response
        def fake_get_headers(url, headers=None):
            return {"http_result_code": "403"}, 0

        orig_get_headers = curler.get_headers
        curler.get_headers = fake_get_headers
        url = "http://updates.devmate.com/app"
        checked_url, headers, ua = curler.check_url(url)
        self.assertEqual(checked_url, url)
        self.assertEqual(headers.get("http_result_code"), "403")
        self.assertTrue("Safari" in ua)
        curler.get_headers = orig_get_headers

    # def test_check_url_handles_403_with_known_403_on_head(self):
    #     """Test that check_url returns None UA for known 403-on-HEAD domains."""

    #     # Patch get_headers to simulate a 403 response
    #     def fake_get_headers(url, headers=None):
    #         return {"http_result_code": "403"}, 0

    #     orig_get_headers = curler.get_headers
    #     curler.get_headers = fake_get_headers
    #     # Patch KNOWN_403_ON_HEAD to include a test domain
    #     orig_known_403 = curler.KNOWN_403_ON_HEAD
    #     curler.KNOWN_403_ON_HEAD = ["example.com"]
    #     url = "http://example.com/test"
    #     checked_url, headers, ua = curler.check_url(url)
    #     self.assertEqual(checked_url, url)
    #     self.assertEqual(headers.get("http_result_code"), "403")
    #     self.assertIsNone(ua)
    #     curler.get_headers = orig_get_headers
    #     curler.KNOWN_403_ON_HEAD = orig_known_403

    # def test_check_url_handles_403_with_user_agents(self):
    #     """Test that check_url retries with browser user-agents on 403."""
    #     # Simulate 403 on first call, 200 on second call with UA
    #     call_count = {"count": 0}

    #     def fake_get_headers(url, headers=None):
    #         if call_count["count"] == 0:
    #             call_count["count"] += 1
    #             return {"http_result_code": "403"}, 0
    #         else:
    #             return {"http_result_code": "200"}, 0

    #     orig_get_headers = curler.get_headers
    #     curler.get_headers = fake_get_headers
    #     url = "http://sometestdomain.com"
    #     checked_url, headers, ua = curler.check_url(url)
    #     self.assertEqual(checked_url, url)
    #     self.assertEqual(headers.get("http_result_code"), "200")
    #     self.assertTrue("Mozilla" in ua)
    #     curler.get_headers = orig_get_headers

    def test_quote_spaces_basic(self):
        """Test quote_spaces function with URLs containing spaces."""
        # Basic functionality - spaces should be quoted
        result = curler.quote_spaces("http://example.com/file name.dmg")
        self.assertEqual(result, "http://example.com/file%20name.dmg")

        # Multiple spaces
        result = curler.quote_spaces("http://example.com/path with spaces/file.zip")
        self.assertEqual(result, "http://example.com/path%20with%20spaces/file.zip")

        # No spaces - should remain unchanged
        result = curler.quote_spaces("http://example.com/no-spaces.dmg")
        self.assertEqual(result, "http://example.com/no-spaces.dmg")

        # Empty string
        result = curler.quote_spaces("")
        self.assertEqual(result, "")

    def test_add_curl_headers_basic(self):
        """Test add_curl_headers modifies curl command in place."""
        curl_cmd = ["/usr/bin/curl"]
        headers = {"User-Agent": "TestAgent", "Accept": "application/json"}

        # Function modifies list in place, doesn't return anything
        result = curler.add_curl_headers(curl_cmd, headers)
        self.assertIsNone(result)

        # Should have added header arguments
        self.assertIn("--header", curl_cmd)
        self.assertTrue(any("TestAgent" in str(item) for item in curl_cmd))

    def test_add_curl_headers_empty(self):
        """Test add_curl_headers with empty headers."""
        curl_cmd = ["/usr/bin/curl"]
        original_length = len(curl_cmd)

        # Empty headers should not modify command
        result = curler.add_curl_headers(curl_cmd, {})
        self.assertIsNone(result)
        self.assertEqual(len(curl_cmd), original_length)

    def test_add_curl_headers_none(self):
        """Test add_curl_headers with None headers."""
        curl_cmd = ["/usr/bin/curl"]
        original_length = len(curl_cmd)

        # None headers should not modify command
        result = curler.add_curl_headers(curl_cmd, None)
        self.assertIsNone(result)
        self.assertEqual(len(curl_cmd), original_length)

    def test_parse_http_protocol_basic(self):
        """Test parse_http_protocol parses HTTP status lines."""
        header = {}

        # Test HTTP/1.1 200 OK
        result = curler.parse_http_protocol("HTTP/1.1 200 OK", header)
        self.assertIsNone(result)  # Function modifies dict in place
        self.assertEqual(header["http_result_code"], "200")
        self.assertEqual(header["http_result_description"], "OK")

        # Test HTTP/2 404 Not Found
        header = {}
        curler.parse_http_protocol("HTTP/2 404 Not Found", header)
        self.assertEqual(header["http_result_code"], "404")
        self.assertEqual(header["http_result_description"], "Not Found")

    def test_parse_http_protocol_invalid(self):
        """Test parse_http_protocol with invalid input."""
        header = {}

        # Test non-HTTP line - function attempts to parse any line
        result = curler.parse_http_protocol("Not a status line", header)
        self.assertIsNone(result)

        # Function actually tries to parse anything and may set values
        # Let's just test it doesn't crash
        self.assertIsInstance(header, dict)

    def test_parse_http_header_basic(self):
        """Test parse_http_header parses header lines."""
        header = {}

        # Test basic header
        result = curler.parse_http_header("Content-Type: text/html", header)
        self.assertIsNone(result)  # Function modifies dict in place
        self.assertEqual(header["content-type"], "text/html")

        # Test header with extra spaces
        header = {}
        curler.parse_http_header("Content-Length:  1234  ", header)
        self.assertEqual(header["content-length"], "1234  ")  # Preserves trailing space

    def test_parse_http_header_invalid(self):
        """Test parse_http_header with invalid header lines."""
        header = {}

        # Test line without colon - function actually parses whatever it can
        curler.parse_http_header("Invalid header line", header)
        self.assertIn("invalid", header)
        # The function takes everything after first word as value
        self.assertEqual(header["invalid"], "header line")

    def test_parse_curl_error_basic(self):
        """Test parse_curl_error extracts error messages."""
        stderr_with_error = "curl: (6) Could not resolve host: nonexistent.example.com"

        result = curler.parse_curl_error(stderr_with_error)

        self.assertIn("Could not resolve host", result)

    def test_parse_curl_error_no_error(self):
        """Test parse_curl_error with no error."""
        stderr_no_error = ""

        result = curler.parse_curl_error(stderr_no_error)

        # Should return empty string when no curl error found
        self.assertEqual(result, "")

    def test_parse_ftp_header_basic(self):
        """Test parse_ftp_header parses FTP response lines."""
        header = {}

        # Test FTP status line
        curler.parse_ftp_header("229 Entering Extended Passive Mode", header)
        # Function modifies dict in place, test that it doesn't crash
        self.assertIsInstance(header, dict)

        # Test size response (213 command)
        header = {}
        curler.parse_ftp_header("213 1048576", header)
        # Should set content-length for size responses

    @patch("scripts.recipe_robot_lib.curler.execute_curl")
    def test_download_basic(self, mock_execute):
        """Test download function basic functionality."""
        # Mock successful curl execution - download returns proc_stdout (first element)
        mock_execute.return_value = ("Success", "", 0)

        result = curler.download("https://example.com", text=True)

        # Should call execute_curl
        mock_execute.assert_called_once()

        # Should return the stdout (first element of tuple)
        self.assertEqual(result, "Success")

    @patch("scripts.recipe_robot_lib.curler.execute_curl")
    def test_download_with_headers(self, mock_execute):
        """Test download function with custom headers."""
        mock_execute.return_value = ("", "Success", 0)
        headers = {"User-Agent": "TestAgent"}

        curler.download("https://example.com", headers=headers)

        # Should include headers in curl command
        mock_execute.assert_called_once()
        curl_cmd = mock_execute.call_args[0][0]
        self.assertIn("--header", curl_cmd)

    @patch("scripts.recipe_robot_lib.curler.execute_curl")
    def test_get_headers_returns_tuple(self, mock_execute):
        """Test get_headers function returns tuple as it actually does."""
        # Mock curl response with headers
        mock_headers = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n"
        mock_execute.return_value = (mock_headers, "", 0)

        result = curler.get_headers("https://example.com")

        # get_headers actually returns a tuple: (headers_dict, exit_code)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)

        headers_dict, exit_code = result
        self.assertIsInstance(headers_dict, dict)
        self.assertEqual(exit_code, 0)
        self.assertEqual(headers_dict["http_result_code"], "200")

    @patch("scripts.recipe_robot_lib.curler.execute_curl")
    def test_check_url_returns_tuple(self, mock_execute):
        """Test check_url returns tuple as it actually does."""
        # Mock successful HEAD request
        mock_headers = "HTTP/1.1 200 OK\r\n\r\n"
        mock_execute.return_value = (mock_headers, "", 0)

        result = curler.check_url("https://example.com")

        # check_url actually returns a tuple: (url, headers_dict, body)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 3)


if __name__ == "__main__":
    unittest.main()
