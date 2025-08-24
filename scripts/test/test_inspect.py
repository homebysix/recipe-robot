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
test_inspect.py

Unit tests for inspect-related functions.
"""


import unittest
from unittest.mock import patch, MagicMock

from scripts.recipe_robot_lib.inspect import (
    get_app_description,
    html_decode,
    inspect_sparkle_feed_url,
    process_input_path,
)
from scripts.recipe_robot_lib.facts import RoboDict


class TestInspect(unittest.TestCase):
    """Tests for the inspect-related functions."""

    def test_html_decode(self):
        """Test that HTML entities are properly decoded."""
        test_cases = [
            ("&gt;", ">"),
            ("&lt;", "<"),
            ("&amp;", "&"),
            ("&quot;", '"'),
            ("&#39;", "'"),
            ("Powerful &amp; fast editor", "Powerful & fast editor"),
        ]

        for encoded, expected in test_cases:
            with self.subTest(encoded=encoded):
                result = html_decode(encoded)
                self.assertEqual(result, expected)

    @patch("scripts.recipe_robot_lib.inspect.curler.download")
    def test_get_app_description_xmplify_macupdate(self, mock_download):
        """Test that MacUpdate.com returns 'Powerful XML editor.' for Xmplify."""
        # Mock the HTML response from MacUpdate.com for Xmplify search
        mock_html_response = """
        <html>
        <body>
            <a class="link_app undefined" href="https://xmplify.macupdate.com"><picture><source type="image/webp" srcset="https://static.macupdate.com/products/33862/s/xmplify-logo.webp?v=1643876984"><source type="image/png" srcset="https://static.macupdate.com/products/33862/s/xmplify-logo.png?v=1643876986">
                <img class="mu_card_complex_line_img" src="https://static.macupdate.com/products/33862/s/xmplify-logo.png?v=1643876986" alt="Xmplify"></picture>
                <div class="mu_card_complex_line_info">
                    <div class="mu_card_complex_line_info_top">
                        <div class="mu_card_complex_line_info_name">Xmplify</div>
                        <div class="mu_card_complex_line_info_version" title="1.11.8">1.11.8</div>
                        <div class="mu_card_complex_line_info_price">$59.00</div>
                    </div>
                    <div class="mu_card_complex_line_info_description">Powerful XML editor.</div>
                </div>
            </a>
        </body>
        </html>
        """

        # Configure the mock to return different responses based on URL
        def mock_download_side_effect(url, **_kwargs):
            if "macupdate.com" in url and "Xmplify" in url:
                return mock_html_response
            # Return empty responses for other sources to simulate no match
            return "<html><body>No match</body></html>"

        mock_download.side_effect = mock_download_side_effect

        # Test the function
        description, source = get_app_description("Xmplify")

        # Verify the result
        self.assertEqual(description, "Powerful XML editor.")
        self.assertEqual(source, "MacUpdate.com")

        # Verify that the download function was called
        self.assertTrue(mock_download.called)

        # Verify that the MacUpdate.com URL was called with the correct app name
        called_urls = [call[0][0] for call in mock_download.call_args_list]
        macupdate_url = next(
            (url for url in called_urls if "macupdate.com" in url), None
        )
        self.assertIsNotNone(macupdate_url)
        if macupdate_url:
            self.assertIn("Xmplify", macupdate_url)

    @patch("scripts.recipe_robot_lib.inspect.curler.download")
    def test_get_app_description_no_match(self, mock_download):
        """Test that function returns None when no description is found."""
        # Mock all sources to return no matching content
        mock_download.return_value = "<html><body>No matching content</body></html>"

        description, source = get_app_description("NonexistentApp")

        self.assertIsNone(description)
        self.assertIsNone(source)

    @patch("scripts.recipe_robot_lib.inspect.curler.download")
    def test_get_app_description_html_tags_removal(self, mock_download):
        """Test that HTML tags like <b> are properly removed from descriptions."""
        mock_html_response = """
        <div class="mu_card_complex_line_info_description">A <b>powerful</b> editor for XML.</div>
        """

        mock_download.return_value = mock_html_response

        description, source = get_app_description("TestApp")

        self.assertEqual(description, "A powerful editor for XML.")
        self.assertEqual(source, "MacUpdate.com")

    @patch("scripts.recipe_robot_lib.inspect.curler.download")
    def test_get_app_description_multiple_sources_fallback(self, mock_download):
        """Test that the function tries multiple sources and returns the first match."""

        def mock_download_side_effect(url, **_kwargs):
            if "macupdate.com" in url:
                # MacUpdate returns no match
                return "<html><body>No match</body></html>"
            elif "download.cnet.com" in url:
                # Download.com returns a match
                return '<div class="c-productCard_summary g-text-small g-color-gray">Found on Download.com</div>'
            else:
                return "<html><body>No match</body></html>"

        mock_download.side_effect = mock_download_side_effect

        description, source = get_app_description("TestApp")

        self.assertEqual(description, "Found on Download.com")
        self.assertEqual(source, "Download.com")


class TestInspectSparkleFeed(unittest.TestCase):
    """Tests for the inspect_sparkle_feed_url function."""

    def setUp(self):
        """Set up test fixtures."""
        self.facts = RoboDict()
        self.facts["inspections"] = []
        self.facts["warnings"] = []
        self.args = MagicMock()

    def create_sample_sparkle_xml(
        self,
        include_version=True,
        include_short_version=True,
        include_enclosure_version=True,
    ):
        """Create a sample Sparkle XML feed for testing."""
        version_elem = (
            "<sparkle:version>2000</sparkle:version>" if include_version else ""
        )
        short_version_elem = (
            "<sparkle:shortVersionString>2.0.0</sparkle:shortVersionString>"
            if include_short_version
            else ""
        )
        enclosure_version = (
            'sparkle:version="2000"' if include_enclosure_version else ""
        )

        xml_content = f"""<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0" xmlns:sparkle="http://www.andymatuschak.org/xml-namespaces/sparkle">
    <channel>
        <title>App Updates</title>
        <link>https://example.com/</link>
        <description>Most recent changes with links to updates.</description>
        <language>en</language>
        <item>
            <title>Version 2.0.0</title>
            {version_elem}
            {short_version_elem}
            <pubDate>Wed, 15 Jan 2025 10:00:00 +0000</pubDate>
            <enclosure url="https://example.com/app-2.0.0.dmg"
                       {enclosure_version}
                       length="12345678"
                       type="application/octet-stream" />
        </item>
        <item>
            <title>Version 1.5.0</title>
            <sparkle:version>1500</sparkle:version>
            <sparkle:shortVersionString>1.5.0</sparkle:shortVersionString>
            <pubDate>Mon, 01 Dec 2024 10:00:00 +0000</pubDate>
            <enclosure url="https://example.com/app-1.5.0.dmg"
                       sparkle:version="1500"
                       length="11111111"
                       type="application/octet-stream" />
        </item>
    </channel>
</rss>"""
        return xml_content

    @patch("scripts.recipe_robot_lib.inspect.inspect_download_url")
    @patch("scripts.recipe_robot_lib.inspect.curler.download")
    @patch("scripts.recipe_robot_lib.inspect.curler.check_url")
    def test_basic_sparkle_feed_processing(
        self, mock_check_url, mock_download, mock_inspect_download
    ):
        """Test basic processing of a valid Sparkle feed."""
        # Setup mocks
        mock_check_url.return_value = (
            "https://example.com/appcast.xml",
            {"http_result_code": "200"},
            None,
        )
        mock_download.return_value = self.create_sample_sparkle_xml()
        mock_inspect_download.return_value = self.facts

        # Call the function
        result = inspect_sparkle_feed_url(
            "https://example.com/appcast.xml", self.args, self.facts
        )

        # Verify results
        self.assertEqual(result["sparkle_feed"], "https://example.com/appcast.xml")
        self.assertIn("sparkle_feed_url", result["inspections"])
        self.assertTrue(result["sparkle_provides_version"])

        # Verify that download URL inspection was called with the latest version URL
        mock_inspect_download.assert_called_once()
        call_args = mock_inspect_download.call_args[0]
        self.assertEqual(call_args[0], "https://example.com/app-2.0.0.dmg")

    @patch("scripts.recipe_robot_lib.inspect.inspect_download_url")
    @patch("scripts.recipe_robot_lib.inspect.curler.download")
    @patch("scripts.recipe_robot_lib.inspect.curler.check_url")
    def test_sparkle_feed_always_provides_version(
        self, mock_check_url, mock_download, mock_inspect_download
    ):
        """Test that Sparkle feeds always provide version regardless of version info presence."""
        # Test with XML that has no explicit version info
        xml_without_versions = """<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0" xmlns:sparkle="http://www.andymatuschak.org/xml-namespaces/sparkle">
    <channel>
        <title>App Updates</title>
        <item>
            <title>Version 2.0.0</title>
            <enclosure url="https://example.com/App-2.0.0.zip"
                       length="12345678"
                       type="application/octet-stream" />
        </item>
    </channel>
</rss>"""

        # Setup mocks
        mock_check_url.return_value = (
            "https://example.com/appcast.xml",
            {"http_result_code": "200"},
            None,
        )
        mock_download.return_value = xml_without_versions
        mock_inspect_download.return_value = self.facts

        # Call the function
        result = inspect_sparkle_feed_url(
            "https://example.com/appcast.xml", self.args, self.facts
        )

        # Verify that sparkle_provides_version is still True
        # This tests our fix - AutoPkg's SparkleUpdateInfoProvider can extract version from URL
        self.assertTrue(result["sparkle_provides_version"])

    @patch("scripts.recipe_robot_lib.inspect.curler.check_url")
    def test_sparkle_feed_http_error(self, mock_check_url):
        """Test handling of HTTP errors when accessing Sparkle feed."""
        # Setup mock to return 404 error
        mock_check_url.return_value = (
            "https://example.com/appcast.xml",
            {"http_result_code": "404"},
            None,
        )

        # Call the function
        result = inspect_sparkle_feed_url(
            "https://example.com/appcast.xml", self.args, self.facts
        )

        # Verify that sparkle_feed is removed due to error
        self.assertNotIn("sparkle_feed", result)

    @patch("scripts.recipe_robot_lib.inspect.curler.download")
    @patch("scripts.recipe_robot_lib.inspect.curler.check_url")
    def test_sparkle_feed_invalid_xml(self, mock_check_url, mock_download):
        """Test handling of invalid XML in Sparkle feed."""
        # Setup mocks
        mock_check_url.return_value = (
            "https://example.com/appcast.xml",
            {"http_result_code": "200"},
            None,
        )
        mock_download.return_value = "<invalid>xml</not_closed>"

        # Call the function
        result = inspect_sparkle_feed_url(
            "https://example.com/appcast.xml", self.args, self.facts
        )

        # Verify error handling
        self.assertNotIn("sparkle_feed", result)
        self.assertTrue(
            any(
                "Error occurred while parsing Sparkle feed" in warning
                for warning in result["warnings"]
            )
        )

    @patch("scripts.recipe_robot_lib.inspect.inspect_download_url")
    @patch("scripts.recipe_robot_lib.inspect.curler.download")
    @patch("scripts.recipe_robot_lib.inspect.curler.check_url")
    def test_sparkle_feed_no_usable_items(
        self, mock_check_url, mock_download, mock_inspect_download
    ):
        """Test handling of Sparkle feed with no usable items."""
        # XML with no enclosures
        xml_no_enclosures = """<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0" xmlns:sparkle="http://www.andymatuschak.org/xml-namespaces/sparkle">
    <channel>
        <title>App Updates</title>
        <item>
            <title>Version 2.0.0</title>
            <!-- No enclosure element -->
        </item>
    </channel>
</rss>"""

        # Setup mocks
        mock_check_url.return_value = (
            "https://example.com/appcast.xml",
            {"http_result_code": "200"},
            None,
        )
        mock_download.return_value = xml_no_enclosures

        # Call the function
        result = inspect_sparkle_feed_url(
            "https://example.com/appcast.xml", self.args, self.facts
        )

        # Verify that function returns early when no usable items found
        self.assertEqual(result["sparkle_feed"], "https://example.com/appcast.xml")
        mock_inspect_download.assert_not_called()

    @patch("scripts.recipe_robot_lib.inspect.inspect_download_url")
    @patch("scripts.recipe_robot_lib.inspect.curler.download")
    @patch("scripts.recipe_robot_lib.inspect.curler.check_url")
    def test_sparkle_feed_user_agent_required(
        self, mock_check_url, mock_download, mock_inspect_download
    ):
        """Test handling when user-agent is required to access feed."""
        # Setup mocks
        mock_check_url.return_value = (
            "https://example.com/appcast.xml",
            {"http_result_code": "200"},
            "Mozilla/5.0",
        )
        mock_download.return_value = self.create_sample_sparkle_xml()
        mock_inspect_download.return_value = self.facts

        # Call the function
        result = inspect_sparkle_feed_url(
            "https://example.com/appcast.xml", self.args, self.facts
        )

        # Verify user-agent was recorded
        self.assertEqual(result["user-agent"], "Mozilla/5.0")
        self.assertTrue(any("user-agent" in warning for warning in result["warnings"]))

    @patch("scripts.recipe_robot_lib.inspect.inspect_download_url")
    @patch("scripts.recipe_robot_lib.inspect.curler.download")
    @patch("scripts.recipe_robot_lib.inspect.curler.check_url")
    def test_sparkle_feed_https_warning(
        self, mock_check_url, mock_download, mock_inspect_download
    ):
        """Test warning for non-HTTPS Sparkle feeds."""
        # Setup mocks with HTTP URL
        mock_check_url.return_value = (
            "http://example.com/appcast.xml",
            {"http_result_code": "200"},
            None,
        )
        mock_download.return_value = self.create_sample_sparkle_xml()
        mock_inspect_download.return_value = self.facts

        # Call the function
        result = inspect_sparkle_feed_url(
            "http://example.com/appcast.xml", self.args, self.facts
        )

        # Verify HTTPS warning was added
        https_warnings = [w for w in result["warnings"] if "not using HTTPS" in w]
        self.assertTrue(len(https_warnings) > 0)

    @patch("scripts.recipe_robot_lib.inspect.inspect_download_url")
    @patch("scripts.recipe_robot_lib.inspect.curler.download")
    @patch("scripts.recipe_robot_lib.inspect.curler.check_url")
    def test_sparkle_feed_skip_already_inspected(
        self, mock_check_url, mock_download, mock_inspect_download
    ):
        """Test that function skips processing if already inspected."""
        # Pre-populate inspections
        self.facts["inspections"] = ["sparkle_feed_url"]

        # Call the function
        inspect_sparkle_feed_url(
            "https://example.com/appcast.xml", self.args, self.facts
        )

        # Verify that no processing occurred
        mock_check_url.assert_not_called()
        mock_download.assert_not_called()
        mock_inspect_download.assert_not_called()

    @patch("scripts.recipe_robot_lib.inspect.inspect_download_url")
    @patch("scripts.recipe_robot_lib.inspect.curler.download")
    @patch("scripts.recipe_robot_lib.inspect.curler.check_url")
    def test_sparkle_feed_version_priority(
        self, mock_check_url, mock_download, mock_inspect_download
    ):
        """Test that latest version is correctly determined by version priority."""
        # XML with mixed version info
        xml_mixed_versions = """<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0" xmlns:sparkle="http://www.andymatuschak.org/xml-namespaces/sparkle">
    <channel>
        <title>App Updates</title>
        <item>
            <title>Version 1.0.0</title>
            <sparkle:version>3000</sparkle:version>
            <enclosure url="https://example.com/app-1.0.0.dmg" type="application/octet-stream" />
        </item>
        <item>
            <title>Version 2.0.0</title>
            <sparkle:version>2000</sparkle:version>
            <enclosure url="https://example.com/app-2.0.0.dmg" type="application/octet-stream" />
        </item>
    </channel>
</rss>"""

        # Setup mocks
        mock_check_url.return_value = (
            "https://example.com/appcast.xml",
            {"http_result_code": "200"},
            None,
        )
        mock_download.return_value = xml_mixed_versions
        mock_inspect_download.return_value = self.facts

        # Call the function
        inspect_sparkle_feed_url(
            "https://example.com/appcast.xml", self.args, self.facts
        )

        # Verify that the highest version (3000) was selected
        mock_inspect_download.assert_called_once()
        call_args = mock_inspect_download.call_args[0]
        self.assertEqual(call_args[0], "https://example.com/app-1.0.0.dmg")


class TestProcessInputPath(unittest.TestCase):
    """Tests for the process_input_path function."""

    def setUp(self):
        """Set up test fixtures."""
        self.facts = RoboDict()
        self.args = MagicMock()
        self.args.input_path = None
        self.facts["args"] = self.args
        # Initialize required lists
        self.facts["warnings"] = []

    @patch("scripts.recipe_robot_lib.inspect.sys.exit")
    @patch("scripts.recipe_robot_lib.inspect.robo_print")
    def test_no_input_path_exits(self, mock_robo_print, mock_exit):
        """Test that function exits when no input path is provided."""
        # Make sys.exit raise an exception so we can catch it and verify it was called
        mock_exit.side_effect = SystemExit(0)
        self.args.input_path = None

        with self.assertRaises(SystemExit):
            process_input_path(self.facts)

        mock_exit.assert_called_once_with(0)

    @patch("scripts.recipe_robot_lib.inspect.inspect_sparkle_feed_url")
    def test_sparkle_feed_detection(self, mock_inspect_sparkle):
        """Test detection and processing of Sparkle feed URLs."""
        mock_inspect_sparkle.return_value = self.facts
        test_cases = [
            "https://example.com/appcast.xml",
            "https://example.com/updates.rss",
            "https://example.com/feed.php",
            "https://example.com/updates/appcast",
        ]

        for url in test_cases:
            with self.subTest(url=url):
                self.args.input_path = url
                mock_inspect_sparkle.reset_mock()

                process_input_path(self.facts)

                mock_inspect_sparkle.assert_called_once_with(url, self.args, self.facts)

    @patch("scripts.recipe_robot_lib.inspect.inspect_barebones_feed_url")
    def test_barebones_feed_detection(self, mock_inspect_barebones):
        """Test detection and processing of Bare Bones feed URLs."""
        mock_inspect_barebones.return_value = self.facts

        self.args.input_path = "https://versioncheck.barebones.com/TextSoap.xml"

        process_input_path(self.facts)

        mock_inspect_barebones.assert_called_once_with(
            "https://versioncheck.barebones.com/TextSoap.xml", self.args, self.facts
        )

    @patch("scripts.recipe_robot_lib.inspect.inspect_github_url")
    def test_github_url_detection(self, mock_inspect_github):
        """Test detection and processing of GitHub URLs."""
        mock_inspect_github.return_value = self.facts
        test_cases = [
            "https://github.com/user/repo",
            "https://github.com/user/repo/releases/latest",
            "https://api.github.com/repos/user/repo",
            "https://user.github.io/repo",
        ]

        for url in test_cases:
            with self.subTest(url=url):
                self.args.input_path = url
                mock_inspect_github.reset_mock()

                process_input_path(self.facts)

                mock_inspect_github.assert_called_once_with(url, self.args, self.facts)

    @patch("scripts.recipe_robot_lib.inspect.inspect_github_url")
    def test_github_download_url_warning(self, mock_inspect_github):
        """Test warning for GitHub download URLs that might be misinterpreted."""
        mock_inspect_github.return_value = self.facts

        self.args.input_path = (
            "https://github.com/user/repo/releases/download/v1.0/app.zip"
        )

        process_input_path(self.facts)

        # Check that warning was added
        warning_found = any(
            "processing the input path as a GitHub repo URL" in warning
            for warning in self.facts.get("warnings", [])
        )
        self.assertTrue(warning_found)

    @patch("scripts.recipe_robot_lib.inspect.inspect_sourceforge_url")
    def test_sourceforge_url_detection(self, mock_inspect_sourceforge):
        """Test detection and processing of SourceForge URLs."""
        mock_inspect_sourceforge.return_value = self.facts
        test_cases = [
            "https://sourceforge.net/projects/projectname",
            "https://sourceforge.net/projects/projectname/",
            "https://sourceforge.net/project/projectname",
            "https://projectname.sourceforge.net/",
        ]

        for url in test_cases:
            with self.subTest(url=url):
                self.args.input_path = url
                mock_inspect_sourceforge.reset_mock()

                process_input_path(self.facts)

                mock_inspect_sourceforge.assert_called_once_with(
                    url, self.args, self.facts
                )

    @patch("scripts.recipe_robot_lib.inspect.inspect_bitbucket_url")
    def test_bitbucket_url_detection(self, mock_inspect_bitbucket):
        """Test detection and processing of BitBucket URLs."""
        mock_inspect_bitbucket.return_value = self.facts

        self.args.input_path = "https://bitbucket.org/user/repo"

        process_input_path(self.facts)

        mock_inspect_bitbucket.assert_called_once_with(
            "https://bitbucket.org/user/repo", self.args, self.facts
        )

    @patch("scripts.recipe_robot_lib.inspect.inspect_bitbucket_url")
    def test_bitbucket_downloads_warning(self, mock_inspect_bitbucket):
        """Test warning for BitBucket downloads URLs that might be misinterpreted."""
        mock_inspect_bitbucket.return_value = self.facts

        self.args.input_path = "https://bitbucket.org/user/repo/downloads/file.zip"

        process_input_path(self.facts)

        # Check that warning was added
        warning_found = any(
            "processing the input path as a BitBucket repo URL" in warning
            for warning in self.facts.get("warnings", [])
        )
        self.assertTrue(warning_found)

    @patch("scripts.recipe_robot_lib.inspect.inspect_download_url")
    def test_dropbox_shared_link(self, mock_inspect_download):
        """Test processing of Dropbox shared links."""
        mock_inspect_download.return_value = self.facts

        self.args.input_path = "https://dropbox.com/s/abc123/file.zip?dl=0"

        process_input_path(self.facts)

        # Check that dl=0 was changed to dl=1
        expected_url = "https://dropbox.com/s/abc123/file.zip?dl=1"
        mock_inspect_download.assert_called_once_with(
            expected_url, self.args, self.facts
        )

    @patch("scripts.recipe_robot_lib.inspect.inspect_download_url")
    def test_http_download_url(self, mock_inspect_download):
        """Test processing of HTTP download URLs."""
        mock_inspect_download.return_value = self.facts
        test_cases = [
            "https://example.com/file.zip",
            "http://example.com/file.dmg",
            "ftp://example.com/file.pkg",
            "file:///path/to/file.zip",
        ]

        for url in test_cases:
            with self.subTest(url=url):
                self.args.input_path = url
                mock_inspect_download.reset_mock()

                process_input_path(self.facts)

                mock_inspect_download.assert_called_once_with(
                    url, self.args, self.facts
                )

    @patch("scripts.recipe_robot_lib.inspect.os.path.exists")
    @patch("scripts.recipe_robot_lib.inspect.inspect_app")
    def test_local_app_path(self, mock_inspect_app, mock_exists):
        """Test processing of local .app paths."""
        mock_exists.return_value = True
        mock_inspect_app.return_value = self.facts

        self.args.input_path = "/Applications/TestApp.app"

        process_input_path(self.facts)

        mock_inspect_app.assert_called_once_with(
            "/Applications/TestApp.app", self.args, self.facts
        )

    @patch("scripts.recipe_robot_lib.inspect.os.path.exists")
    @patch("scripts.recipe_robot_lib.inspect.inspect_pkg")
    def test_local_pkg_path(self, mock_inspect_pkg, mock_exists):
        """Test processing of local installer package paths."""
        mock_exists.return_value = True
        mock_inspect_pkg.return_value = self.facts
        test_cases = ["/path/to/installer.pkg", "/path/to/installer.mpkg"]

        for path in test_cases:
            with self.subTest(path=path):
                self.args.input_path = path
                mock_inspect_pkg.reset_mock()

                process_input_path(self.facts)

                mock_inspect_pkg.assert_called_once_with(path, self.args, self.facts)

    @patch("scripts.recipe_robot_lib.inspect.os.path.exists")
    @patch("scripts.recipe_robot_lib.inspect.inspect_disk_image")
    def test_local_disk_image_path(self, mock_inspect_disk_image, mock_exists):
        """Test processing of local disk image paths."""
        mock_exists.return_value = True
        mock_inspect_disk_image.return_value = self.facts
        test_cases = ["/path/to/image.dmg", "/path/to/image.iso"]

        for path in test_cases:
            with self.subTest(path=path):
                self.args.input_path = path
                mock_inspect_disk_image.reset_mock()

                process_input_path(self.facts)

                mock_inspect_disk_image.assert_called_once_with(
                    path, self.args, self.facts
                )

    @patch("scripts.recipe_robot_lib.inspect.os.path.exists")
    @patch("scripts.recipe_robot_lib.inspect.inspect_archive")
    def test_local_archive_path(self, mock_inspect_archive, mock_exists):
        """Test processing of local archive paths."""
        mock_exists.return_value = True
        mock_inspect_archive.return_value = self.facts
        test_cases = ["/path/to/archive.zip", "/path/to/archive.tar.gz"]

        for path in test_cases:
            with self.subTest(path=path):
                self.args.input_path = path
                mock_inspect_archive.reset_mock()

                process_input_path(self.facts)

                mock_inspect_archive.assert_called_once_with(
                    path, self.args, self.facts
                )

    def test_url_path_preserves_trailing_slash(self):
        """Test that URLs preserve trailing slashes (not stripped)."""
        with patch(
            "scripts.recipe_robot_lib.inspect.inspect_download_url"
        ) as mock_inspect_download:
            mock_inspect_download.return_value = self.facts

            self.args.input_path = "https://example.com/download/"

            process_input_path(self.facts)

            # URL should preserve the trailing slash
            mock_inspect_download.assert_called_once_with(
                "https://example.com/download/", self.args, self.facts
            )


if __name__ == "__main__":
    unittest.main()
