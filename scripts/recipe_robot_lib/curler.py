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


"""curler.py.

Various functions that use /usr/bin/curl for retrieving HTTP/HTTPS
content. Based on and borrowed from autopkg's URLGetter.
"""

from __future__ import absolute_import, print_function

import os.path
import subprocess
from urllib.parse import urlparse

from .exceptions import RoboError
from .tools import GITHUB_DOMAINS, LogLevel, any_item_in_string, robo_print


def prepare_curl_cmd():
    """Assemble basic curl command and return it."""
    return ["/usr/bin/curl", "--compressed", "--location", "--silent", "--show-error"]


def add_curl_headers(curl_cmd, headers):
    """Add headers to curl_cmd."""
    if headers:
        for header, value in headers.items():
            curl_cmd.extend(["--header", f"{header}: {value}"])


def clear_header(header):
    """Clear header dictionary."""
    # Save redirect URL before clear
    http_redirected = header.get("http_redirected", None)
    header.clear()
    header["http_result_code"] = "000"
    header["http_result_description"] = ""
    # Restore redirect URL
    header["http_redirected"] = http_redirected


def parse_http_protocol(line, header):
    """Parse first HTTP header line."""
    try:
        header["http_result_code"] = line.split(None, 2)[1]
        header["http_result_description"] = line.split(None, 2)[2]
    except IndexError:
        pass


def parse_http_header(line, header):
    """Parse single HTTP header line."""
    part = line.split(None, 1)
    fieldname = part[0].rstrip(":").lower()
    try:
        header[fieldname] = part[1]
    except IndexError:
        header[fieldname] = ""


def parse_curl_error(proc_stderr):
    """Report curl failure."""
    curl_err = ""
    if isinstance(proc_stderr, bytes):
        proc_stderr = proc_stderr.decode("utf-8")
    try:
        curl_err = proc_stderr.rstrip("\n")
        curl_err = curl_err.split(None, 2)[2]
    except IndexError:
        pass

    return curl_err


def parse_ftp_header(line, header):
    """Parse single FTP header line."""
    part = line.split(None, 1)
    responsecode = part[0]
    if responsecode == "213":
        # This is the reply to curl's SIZE command on the file
        # We can map it to the HTTP content-length header
        try:
            header["content-length"] = part[1]
        except IndexError:
            pass
    elif responsecode.startswith("55"):
        header["http_result_code"] = "404"
        header["http_result_description"] = line
    elif responsecode in ("125", "150"):
        header["http_result_code"] = "200"
        header["http_result_description"] = line


def parse_headers(raw_headers, url=""):
    """Parse headers from curl."""
    header = {}
    clear_header(header)
    for line in raw_headers.splitlines():
        if line.startswith("HTTP/"):
            parse_http_protocol(line, header)
        elif ": " in line:
            parse_http_header(line, header)
        elif url.startswith("ftp://"):
            parse_ftp_header(line, header)
        elif line == "":
            # we got an empty line; end of headers (or curl exited)
            if header.get("http_result_code") in ("301", "302", "303", "307", "308",):
                # redirect, so more headers are coming.
                # Throw away the headers we've received so far
                header["http_redirected"] = header.get("location", None)
                clear_header(header)
    return header


def execute_curl(curl_cmd, text=True, capture_output=True):
    """Execute curl command.

    Return stdout, stderr and return code.
    """
    try:
        result = subprocess.run(
            curl_cmd,
            shell=False,
            bufsize=1,
            capture_output=capture_output,
            check=True,
            text=text,
        )
    except subprocess.CalledProcessError as err:
        return err.stdout, err.stderr, err.returncode
    return result.stdout, result.stderr, result.returncode


def download_with_curl(curl_cmd, text=True, capture_output=True):
    """Launch curl, return its output, and handle failures."""
    proc_stdout, proc_stderr, retcode = execute_curl(
        curl_cmd, text=text, capture_output=capture_output
    )
    robo_print(f"Curl command: {curl_cmd}", LogLevel.DEBUG, 4)
    if retcode:  # Non-zero exit code from curl => problem with download
        curl_err = parse_curl_error(proc_stderr)
        robo_print(f"curl failure: {curl_err} (exit code {retcode})", LogLevel.WARNING)
    return proc_stdout


def download(url, headers=None, text=False):
    """Download content with default curl options."""
    curl_cmd = prepare_curl_cmd()
    add_curl_headers(curl_cmd, headers)
    curl_cmd.extend(["--url", url])
    output = download_with_curl(curl_cmd, text=text)
    return output


def download_to_file(url, filename, headers=None, app_mode=False):
    """Download content to a file with default curl options."""
    curl_cmd = prepare_curl_cmd()
    add_curl_headers(curl_cmd, headers)
    # Disable silent mode in order to display download progress bar.
    if not app_mode:
        curl_cmd.remove("--silent")
        curl_cmd.append("--progress-bar")
    curl_cmd.extend(["--output", filename, "--url", url])
    download_with_curl(curl_cmd, text=False, capture_output=False)
    if os.path.exists(filename):
        return filename
    raise RoboError(f"{filename} was not written!")


def get_headers(url, headers=None):
    """Get a URL's HTTP headers, parse them, and return them."""
    curl_cmd = prepare_curl_cmd()
    add_curl_headers(curl_cmd, headers)
    curl_cmd.extend(["--head", "--url", url])
    out, err, retcode = execute_curl(curl_cmd, text=True)
    parsed_headers = parse_headers(out, url=url)
    return parsed_headers, retcode


def check_url(url, headers=None):
    """Test a URL's headers, and switch to HTTPS if available."""

    # Switch to HTTPS if possible.
    if url.startswith("http:"):
        robo_print("Checking for HTTPS URL...", LogLevel.VERBOSE)
        head, retcode = get_headers("https" + url[4:], headers=headers)
        if retcode == 0 and int(head.get("http_result_code")) < 400:
            url = "https" + url[4:]
            robo_print("Found HTTPS URL: %s" % url, LogLevel.VERBOSE, 4)
            return url, head, None
        else:
            robo_print("No usable HTTPS URL found.", LogLevel.VERBOSE, 4)

    # Get URL headers.
    head, retcode = get_headers(url, headers=headers)
    http_result = int(head.get("http_result_code"))
    if retcode == 0 and http_result < 400:
        return url, head, None

    # Try to mitigate errors.
    if http_result == 403:
        headers["user-agent"] = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) "
            "Version/13.0.5 Safari/605.1.15"
        )
        head, retcode = get_headers(url, headers=headers)
        if int(head.get("http_result_code")) < 400:
            robo_print(
                "Using Safari user-agent.", LogLevel.VERBOSE, 4,
            )
            return url, head, headers["user-agent"]

    return url, head, None
