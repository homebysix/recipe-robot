#!/usr/local/autopkg/python
# This Python file uses the following encoding: utf-8

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


from __future__ import absolute_import

import json
import os
import unittest

from recipe_robot_lib import curler


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

    def test_parse_curl_error(self):
        """Verify we can report a curl failure."""
        actual = curler.parse_curl_error(
            "curl: (6) Could not resolve host: example.none"
        )
        expected = "Could not resolve host: example.none"
        self.assertEqual(expected, actual)

        actual = curler.parse_curl_error("")
        expected = ""
        self.assertEqual(expected, actual)

    def test_parse_ftp_header(self):
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

    def test_parse_headers(self):
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
        with open(filepath, "r") as openfile:
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

    def test_check_url(self):
        """Verify we can test a URL's headers, and switch to HTTPS if available."""
        url, headers, _ = curler.check_url("http://www.example.com")
        expected = "https://www.example.com"
        self.assertEqual(expected, url)
        self.assertEqual(headers.get("content-type"), "text/html")
        self.assertEqual(headers.get("http_result_code"), "200")


if __name__ == "__main__":
    unittest.main()
