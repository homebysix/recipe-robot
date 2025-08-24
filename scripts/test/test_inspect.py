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
    get_download_link_from_xattr,
    html_decode,
    inspect_download_url,
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


class TestInspectApp(unittest.TestCase):
    """Tests for the inspect_app function."""

    def setUp(self):
        """Set up test fixtures."""
        self.facts = RoboDict()
        self.facts["inspections"] = []
        self.facts["warnings"] = []
        self.facts["blocking_applications"] = []
        self.facts["codesign_authorities"] = []
        self.args = MagicMock()
        self.args.skip_icon = False
        self.test_app_path = "/tmp/test.app"

    def create_mock_info_plist(self, **kwargs):
        """Create a mock Info.plist with default values that can be overridden."""
        default_plist = {
            "CFBundleName": "Test App",
            "CFBundleIdentifier": "com.example.testapp",
            "CFBundleShortVersionString": "1.0.0",
            "CFBundleVersion": "100",
            "CFBundleIconFile": "icon.icns",
        }
        default_plist.update(kwargs)
        return default_plist

    @patch("scripts.recipe_robot_lib.inspect.get_app_description")
    @patch("scripts.recipe_robot_lib.inspect.get_exitcode_stdout_stderr")
    @patch("scripts.recipe_robot_lib.inspect.os.path.exists")
    @patch("scripts.recipe_robot_lib.inspect.os.path.basename")
    @patch("builtins.open")
    @patch("scripts.recipe_robot_lib.inspect.plistlib.load")
    def test_basic_app_inspection(
        self,
        mock_plist_load,
        _mock_open_builtin,
        mock_basename,
        mock_exists,
        mock_get_exitcode,
        mock_get_description,
    ):
        """Test basic app inspection with valid plist."""
        # Setup mocks
        mock_plist_load.return_value = self.create_mock_info_plist()
        mock_basename.return_value = "test.app"
        mock_exists.side_effect = lambda path: "_MASReceipt" not in path
        mock_get_exitcode.return_value = (1, "", "")  # unsigned app
        mock_get_description.return_value = ("Test app description", "TestSource")

        # Import the function to test
        from scripts.recipe_robot_lib.inspect import inspect_app

        # Call function
        result = inspect_app(self.test_app_path, self.args, self.facts)

        # Verify basic results
        self.assertEqual(result["app_name"], "Test App")
        self.assertEqual(result["bundle_id"], "com.example.testapp")
        self.assertEqual(result["version_key"], "CFBundleShortVersionString")
        self.assertEqual(result["app_path"], self.test_app_path)
        self.assertIn("app", result["inspections"])
        self.assertIn("test.app", result["blocking_applications"])
        self.assertEqual(result["description"], "Test app description")
        self.assertFalse(result["is_from_app_store"])

    @patch("scripts.recipe_robot_lib.inspect.get_app_description")
    @patch("scripts.recipe_robot_lib.inspect.get_exitcode_stdout_stderr")
    @patch("scripts.recipe_robot_lib.inspect.os.path.exists")
    @patch("scripts.recipe_robot_lib.inspect.os.path.basename")
    @patch("builtins.open")
    @patch("scripts.recipe_robot_lib.inspect.plistlib.load")
    def test_app_already_inspected(
        self,
        mock_plist_load,
        _mock_open_builtin,
        _mock_basename,
        _mock_exists,
        _mock_get_exitcode,
        _mock_get_description,
    ):
        """Test that function returns early if app already inspected."""
        # Pre-populate inspections
        self.facts["inspections"] = ["app"]

        from scripts.recipe_robot_lib.inspect import inspect_app

        result = inspect_app(self.test_app_path, self.args, self.facts)

        # Should return facts unchanged without processing
        self.assertEqual(result, self.facts)
        mock_plist_load.assert_not_called()

    @patch("scripts.recipe_robot_lib.inspect.get_app_description")
    @patch("scripts.recipe_robot_lib.inspect.get_exitcode_stdout_stderr")
    @patch("scripts.recipe_robot_lib.inspect.os.path.exists")
    @patch("scripts.recipe_robot_lib.inspect.os.path.basename")
    @patch("builtins.open")
    @patch("scripts.recipe_robot_lib.inspect.plistlib.load")
    def test_app_name_fallback_chain(
        self,
        mock_plist_load,
        _mock_open_builtin,
        mock_basename,
        mock_exists,
        mock_get_exitcode,
        mock_get_description,
    ):
        """Test app name determination fallback chain."""
        test_cases = [
            # (plist_data, expected_name)
            ({"CFBundleName": "Test App"}, "Test App"),
            ({"CFBundleExecutable": "TestExec"}, "TestExec"),
            ({}, "test"),  # falls back to filename
        ]

        mock_basename.return_value = "test.app"
        mock_exists.side_effect = lambda path: "_MASReceipt" not in path
        mock_get_exitcode.return_value = (1, "", "")
        mock_get_description.return_value = (None, None)

        from scripts.recipe_robot_lib.inspect import inspect_app

        for plist_data, expected_name in test_cases:
            with self.subTest(plist_data=plist_data, expected_name=expected_name):
                # Reset facts for each test
                test_facts = RoboDict()
                test_facts["inspections"] = []
                test_facts["warnings"] = []
                test_facts["blocking_applications"] = []
                test_facts["codesign_authorities"] = []

                plist_with_defaults = self.create_mock_info_plist(**plist_data)
                # Remove CFBundleName if not explicitly set
                if "CFBundleName" not in plist_data:
                    plist_with_defaults.pop("CFBundleName", None)
                if "CFBundleExecutable" not in plist_data:
                    plist_with_defaults.pop("CFBundleExecutable", None)

                mock_plist_load.return_value = plist_with_defaults

                result = inspect_app(self.test_app_path, self.args, test_facts)
                self.assertEqual(result["app_name"], expected_name)

    @patch("scripts.recipe_robot_lib.inspect.get_app_description")
    @patch("scripts.recipe_robot_lib.inspect.get_exitcode_stdout_stderr")
    @patch("scripts.recipe_robot_lib.inspect.os.path.exists")
    @patch("scripts.recipe_robot_lib.inspect.os.path.basename")
    @patch("builtins.open")
    @patch("scripts.recipe_robot_lib.inspect.plistlib.load")
    def test_app_file_different_from_name(
        self,
        mock_plist_load,
        _mock_open_builtin,
        mock_basename,
        mock_exists,
        mock_get_exitcode,
        mock_get_description,
    ):
        """Test handling when app filename differs from bundle name."""
        mock_plist_load.return_value = self.create_mock_info_plist(
            CFBundleName="Different Name"
        )
        mock_basename.return_value = "test.app"
        mock_exists.side_effect = lambda path: "_MASReceipt" not in path
        mock_get_exitcode.return_value = (1, "", "")
        mock_get_description.return_value = (None, None)

        from scripts.recipe_robot_lib.inspect import inspect_app

        result = inspect_app(self.test_app_path, self.args, self.facts)

        self.assertEqual(result["app_name"], "Different Name")
        self.assertEqual(result["app_file"], "test")

    @patch("scripts.recipe_robot_lib.inspect.get_app_description")
    @patch("scripts.recipe_robot_lib.inspect.get_exitcode_stdout_stderr")
    @patch("scripts.recipe_robot_lib.inspect.os.path.exists")
    @patch("scripts.recipe_robot_lib.inspect.os.path.basename")
    @patch("builtins.open")
    @patch("scripts.recipe_robot_lib.inspect.plistlib.load")
    def test_missing_bundle_identifier(
        self,
        mock_plist_load,
        _mock_open_builtin,
        mock_basename,
        mock_exists,
        mock_get_exitcode,
        mock_get_description,
    ):
        """Test handling of missing bundle identifier."""
        plist_data = self.create_mock_info_plist()
        del plist_data["CFBundleIdentifier"]
        mock_plist_load.return_value = plist_data
        mock_basename.return_value = "test.app"
        mock_exists.side_effect = lambda path: "_MASReceipt" not in path
        mock_get_exitcode.return_value = (1, "", "")
        mock_get_description.return_value = (None, None)

        from scripts.recipe_robot_lib.inspect import inspect_app

        result = inspect_app(self.test_app_path, self.args, self.facts)

        warning_found = any(
            "doesn't seem to have a bundle identifier" in warning
            for warning in result["warnings"]
        )
        self.assertTrue(warning_found)

    @patch("scripts.recipe_robot_lib.inspect.get_app_description")
    @patch("scripts.recipe_robot_lib.inspect.get_exitcode_stdout_stderr")
    @patch("scripts.recipe_robot_lib.inspect.os.path.exists")
    @patch("scripts.recipe_robot_lib.inspect.os.path.basename")
    @patch("builtins.open")
    @patch("scripts.recipe_robot_lib.inspect.plistlib.load")
    def test_recipe_robot_special_case(
        self,
        mock_plist_load,
        _mock_open_builtin,
        mock_basename,
        mock_exists,
        mock_get_exitcode,
        mock_get_description,
    ):
        """Test special case handling for Recipe Robot itself."""
        mock_plist_load.return_value = self.create_mock_info_plist(
            CFBundleIdentifier="com.elliotjordan.recipe-robot"
        )
        mock_basename.return_value = "recipe-robot.app"
        mock_exists.side_effect = lambda path: "_MASReceipt" not in path
        mock_get_exitcode.return_value = (1, "", "")
        mock_get_description.return_value = (None, None)

        from scripts.recipe_robot_lib.inspect import inspect_app

        result = inspect_app(self.test_app_path, self.args, self.facts)

        warning_found = any(
            "I see what you did there" in warning for warning in result["warnings"]
        )
        self.assertTrue(warning_found)

    @patch("scripts.recipe_robot_lib.inspect.get_app_description")
    @patch("scripts.recipe_robot_lib.inspect.get_exitcode_stdout_stderr")
    @patch("scripts.recipe_robot_lib.inspect.os.path.exists")
    @patch("scripts.recipe_robot_lib.inspect.os.path.basename")
    @patch("builtins.open")
    @patch("scripts.recipe_robot_lib.inspect.plistlib.load")
    def test_disaster_warning(
        self,
        mock_plist_load,
        _mock_open_builtin,
        mock_basename,
        mock_exists,
        mock_get_exitcode,
        mock_get_description,
    ):
        """Test disaster-related humor warning."""
        mock_plist_load.return_value = self.create_mock_info_plist(
            CFBundleName="Disaster Recovery App"
        )
        mock_basename.return_value = "disaster.app"
        mock_exists.side_effect = lambda path: "_MASReceipt" not in path
        mock_get_exitcode.return_value = (1, "", "")
        mock_get_description.return_value = (None, None)

        from scripts.recipe_robot_lib.inspect import inspect_app

        result = inspect_app(self.test_app_path, self.args, self.facts)

        warning_found = any(
            "recipe for disaster" in warning for warning in result["warnings"]
        )
        self.assertTrue(warning_found)

    @patch("scripts.recipe_robot_lib.inspect.get_app_description")
    @patch("scripts.recipe_robot_lib.inspect.get_exitcode_stdout_stderr")
    @patch("scripts.recipe_robot_lib.inspect.os.path.exists")
    @patch("scripts.recipe_robot_lib.inspect.os.path.basename")
    @patch("builtins.open")
    @patch("scripts.recipe_robot_lib.inspect.plistlib.load")
    def test_installer_app_warning(
        self,
        mock_plist_load,
        _mock_open_builtin,
        mock_basename,
        mock_exists,
        mock_get_exitcode,
        mock_get_description,
    ):
        """Test warning for installer apps."""
        test_cases = [
            "Install TestApp",
            "TestApp Installer.app",
        ]

        mock_basename.return_value = "installer.app"
        mock_exists.side_effect = lambda path: "_MASReceipt" not in path
        mock_get_exitcode.return_value = (1, "", "")
        mock_get_description.return_value = (None, None)

        from scripts.recipe_robot_lib.inspect import inspect_app

        for app_name in test_cases:
            with self.subTest(app_name=app_name):
                test_facts = RoboDict()
                test_facts["inspections"] = []
                test_facts["warnings"] = []
                test_facts["blocking_applications"] = []
                test_facts["codesign_authorities"] = []

                mock_plist_load.return_value = self.create_mock_info_plist(
                    CFBundleName=app_name
                )

                result = inspect_app(self.test_app_path, self.args, test_facts)

                warning_found = any(
                    "installer app rather than the actual app" in warning
                    for warning in result["warnings"]
                )
                self.assertTrue(warning_found)

    @patch("scripts.recipe_robot_lib.inspect.get_app_description")
    @patch("scripts.recipe_robot_lib.inspect.get_exitcode_stdout_stderr")
    @patch("scripts.recipe_robot_lib.inspect.os.path.exists")
    @patch("scripts.recipe_robot_lib.inspect.os.path.basename")
    @patch("builtins.open")
    @patch("scripts.recipe_robot_lib.inspect.plistlib.load")
    def test_app_store_detection(
        self,
        mock_plist_load,
        _mock_open_builtin,
        mock_basename,
        mock_exists,
        mock_get_exitcode,
        mock_get_description,
    ):
        """Test Mac App Store app detection."""
        mock_plist_load.return_value = self.create_mock_info_plist()
        mock_basename.return_value = "test.app"
        mock_exists.side_effect = lambda path: "_MASReceipt/receipt" in path
        mock_get_exitcode.return_value = (1, "", "")
        mock_get_description.return_value = (None, None)

        from scripts.recipe_robot_lib.inspect import inspect_app

        result = inspect_app(self.test_app_path, self.args, self.facts)

        self.assertTrue(result["is_from_app_store"])

    @patch("scripts.recipe_robot_lib.inspect.get_app_description")
    @patch("scripts.recipe_robot_lib.inspect.get_exitcode_stdout_stderr")
    @patch("scripts.recipe_robot_lib.inspect.os.path.exists")
    @patch("scripts.recipe_robot_lib.inspect.os.path.basename")
    @patch("builtins.open")
    @patch("scripts.recipe_robot_lib.inspect.plistlib.load")
    def test_version_key_selection(
        self,
        mock_plist_load,
        _mock_open_builtin,
        mock_basename,
        mock_exists,
        mock_get_exitcode,
        mock_get_description,
    ):
        """Test version key selection logic."""
        test_cases = [
            # (plist_data, expected_version_key)
            ({"CFBundleShortVersionString": "1.0.0"}, "CFBundleShortVersionString"),
            ({"CFBundleVersion": "100"}, "CFBundleVersion"),
            (
                {"CFBundleShortVersionString": "1.0.0", "CFBundleVersion": "100"},
                "CFBundleShortVersionString",
            ),
            (
                {"CFBundleShortVersionString": "invalid", "CFBundleVersion": "1.0.0"},
                "CFBundleVersion",
            ),
            (
                {"CFBundleShortVersionString": "123", "CFBundleVersion": "invalid"},
                "CFBundleShortVersionString",
            ),
            (
                {"CFBundleShortVersionString": "invalid", "CFBundleVersion": "456"},
                "CFBundleVersion",
            ),
            (
                {
                    "CFBundleShortVersionString": "invalid",
                    "CFBundleVersion": "also_invalid",
                },
                "CFBundleShortVersionString",
            ),
        ]

        mock_basename.return_value = "test.app"
        mock_exists.side_effect = lambda path: "_MASReceipt" not in path
        mock_get_exitcode.return_value = (1, "", "")
        mock_get_description.return_value = (None, None)

        from scripts.recipe_robot_lib.inspect import inspect_app

        for plist_data, expected_key in test_cases:
            with self.subTest(plist_data=plist_data, expected_key=expected_key):
                test_facts = RoboDict()
                test_facts["inspections"] = []
                test_facts["warnings"] = []
                test_facts["blocking_applications"] = []
                test_facts["codesign_authorities"] = []

                base_plist = self.create_mock_info_plist()
                # Remove default version keys and add test-specific ones
                base_plist.pop("CFBundleShortVersionString", None)
                base_plist.pop("CFBundleVersion", None)
                base_plist.update(plist_data)
                mock_plist_load.return_value = base_plist

                result = inspect_app(self.test_app_path, self.args, test_facts)
                self.assertEqual(result["version_key"], expected_key)

    @patch("scripts.recipe_robot_lib.inspect.get_app_description")
    @patch("scripts.recipe_robot_lib.inspect.get_exitcode_stdout_stderr")
    @patch("scripts.recipe_robot_lib.inspect.os.path.exists")
    @patch("scripts.recipe_robot_lib.inspect.os.path.basename")
    @patch("builtins.open")
    @patch("scripts.recipe_robot_lib.inspect.plistlib.load")
    def test_icon_detection(
        self,
        mock_plist_load,
        _mock_open_builtin,
        mock_basename,
        mock_exists,
        mock_get_exitcode,
        mock_get_description,
    ):
        """Test icon path detection."""
        mock_plist_load.return_value = self.create_mock_info_plist(
            CFBundleIconFile="MyIcon.icns"
        )
        mock_basename.return_value = "test.app"
        mock_exists.side_effect = lambda path: "_MASReceipt" not in path
        mock_get_exitcode.return_value = (1, "", "")
        mock_get_description.return_value = (None, None)

        from scripts.recipe_robot_lib.inspect import inspect_app

        result = inspect_app(self.test_app_path, self.args, self.facts)

        expected_icon_path = "/tmp/test.app/Contents/Resources/MyIcon.icns"
        self.assertEqual(result["icon_path"], expected_icon_path)

    @patch("scripts.recipe_robot_lib.inspect.get_app_description")
    @patch("scripts.recipe_robot_lib.inspect.get_exitcode_stdout_stderr")
    @patch("scripts.recipe_robot_lib.inspect.os.path.exists")
    @patch("scripts.recipe_robot_lib.inspect.os.path.basename")
    @patch("builtins.open")
    @patch("scripts.recipe_robot_lib.inspect.plistlib.load")
    def test_skip_icon_flag(
        self,
        mock_plist_load,
        _mock_open_builtin,
        mock_basename,
        mock_exists,
        mock_get_exitcode,
        mock_get_description,
    ):
        """Test that icon detection is skipped when flag is set."""
        self.args.skip_icon = True
        mock_plist_load.return_value = self.create_mock_info_plist()
        mock_basename.return_value = "test.app"
        mock_exists.side_effect = lambda path: "_MASReceipt" not in path
        mock_get_exitcode.return_value = (1, "", "")
        mock_get_description.return_value = (None, None)

        from scripts.recipe_robot_lib.inspect import inspect_app

        result = inspect_app(self.test_app_path, self.args, self.facts)

        self.assertNotIn("icon_path", result)

    @patch("scripts.recipe_robot_lib.inspect.get_app_description")
    @patch("scripts.recipe_robot_lib.inspect.get_exitcode_stdout_stderr")
    @patch("scripts.recipe_robot_lib.inspect.os.path.exists")
    @patch("scripts.recipe_robot_lib.inspect.os.path.basename")
    @patch("builtins.open")
    @patch("scripts.recipe_robot_lib.inspect.plistlib.load")
    def test_missing_icon_warning(
        self,
        mock_plist_load,
        _mock_open_builtin,
        mock_basename,
        mock_exists,
        mock_get_exitcode,
        mock_get_description,
    ):
        """Test warning when icon cannot be determined."""
        plist_data = self.create_mock_info_plist()
        del plist_data["CFBundleIconFile"]
        mock_plist_load.return_value = plist_data
        mock_basename.return_value = "test.app"
        mock_exists.side_effect = lambda path: "_MASReceipt" not in path
        mock_get_exitcode.return_value = (1, "", "")
        mock_get_description.return_value = (None, None)

        from scripts.recipe_robot_lib.inspect import inspect_app

        result = inspect_app(self.test_app_path, self.args, self.facts)

        warning_found = any(
            "Can't determine icon" in warning for warning in result["warnings"]
        )
        self.assertTrue(warning_found)

    @patch("scripts.recipe_robot_lib.inspect.get_app_description")
    @patch("scripts.recipe_robot_lib.inspect.get_exitcode_stdout_stderr")
    @patch("scripts.recipe_robot_lib.inspect.os.path.exists")
    @patch("scripts.recipe_robot_lib.inspect.os.path.basename")
    @patch("builtins.open")
    @patch("scripts.recipe_robot_lib.inspect.plistlib.load")
    def test_codesign_unsigned_app(
        self,
        mock_plist_load,
        _mock_open_builtin,
        mock_basename,
        mock_exists,
        mock_get_exitcode,
        mock_get_description,
    ):
        """Test handling of unsigned app."""
        mock_plist_load.return_value = self.create_mock_info_plist()
        mock_basename.return_value = "test.app"
        mock_exists.side_effect = lambda path: "_MASReceipt" not in path
        mock_get_exitcode.return_value = (1, "", "")  # codesign failure
        mock_get_description.return_value = (None, None)

        from scripts.recipe_robot_lib.inspect import inspect_app

        result = inspect_app(self.test_app_path, self.args, self.facts)

        self.assertEqual(result.get("codesign_reqs", ""), "")
        self.assertEqual(len(result["codesign_authorities"]), 0)

    @patch("scripts.recipe_robot_lib.inspect.get_app_description")
    @patch("scripts.recipe_robot_lib.inspect.get_exitcode_stdout_stderr")
    @patch("scripts.recipe_robot_lib.inspect.os.path.exists")
    @patch("scripts.recipe_robot_lib.inspect.os.path.basename")
    @patch("builtins.open")
    @patch("scripts.recipe_robot_lib.inspect.plistlib.load")
    def test_codesign_signed_app(
        self,
        mock_plist_load,
        _mock_open_builtin,
        mock_basename,
        mock_exists,
        mock_get_exitcode,
        mock_get_description,
    ):
        """Test handling of signed app."""
        mock_plist_load.return_value = self.create_mock_info_plist()
        mock_basename.return_value = "test.app"
        mock_exists.side_effect = lambda path: "_MASReceipt" not in path

        # Mock codesign output for signed app
        stdout = 'designated => identifier "com.example.testapp" and certificate leaf[subject.CN] = "Developer ID Application: Test Developer (TEAM123456)"'
        stderr = """Format=app bundle with Mach-O universal (x86_64 arm64)
Authority=Developer ID Application: Test Developer (TEAM123456)
Authority=Developer ID Certification Authority
Authority=Apple Root CA
TeamIdentifier=TEAM123456
Sealed Resources version=2 rules=13 files=245"""

        mock_get_exitcode.return_value = (0, stdout, stderr)
        mock_get_description.return_value = (None, None)

        from scripts.recipe_robot_lib.inspect import inspect_app

        result = inspect_app(self.test_app_path, self.args, self.facts)

        expected_reqs = 'identifier "com.example.testapp" and certificate leaf[subject.CN] = "Developer ID Application: Test Developer (TEAM123456)"'
        self.assertEqual(result["codesign_reqs"], expected_reqs)
        self.assertIn(
            "Developer ID Application: Test Developer (TEAM123456)",
            result["codesign_authorities"],
        )
        self.assertEqual(result["developer"], "Test Developer")
        self.assertEqual(result["codesign_input_filename"], "test.app")

    @patch("scripts.recipe_robot_lib.inspect.get_app_description")
    @patch("scripts.recipe_robot_lib.inspect.get_exitcode_stdout_stderr")
    @patch("scripts.recipe_robot_lib.inspect.os.path.exists")
    @patch("scripts.recipe_robot_lib.inspect.os.path.basename")
    @patch("builtins.open")
    @patch("scripts.recipe_robot_lib.inspect.plistlib.load")
    def test_codesign_obsolete_signature(
        self,
        mock_plist_load,
        _mock_open_builtin,
        mock_basename,
        mock_exists,
        mock_get_exitcode,
        mock_get_description,
    ):
        """Test handling of obsolete code signature."""
        mock_plist_load.return_value = self.create_mock_info_plist()
        mock_basename.return_value = "test.app"
        mock_exists.side_effect = lambda path: "_MASReceipt" not in path

        # Mock codesign output with obsolete signature
        stdout = "designated => anchor apple generic"
        stderr = "Sealed Resources version=1 rules=5 files=10"

        mock_get_exitcode.return_value = (0, stdout, stderr)
        mock_get_description.return_value = (None, None)

        from scripts.recipe_robot_lib.inspect import inspect_app

        result = inspect_app(self.test_app_path, self.args, self.facts)

        # Should be treated as unsigned due to obsolete signature
        self.assertEqual(result.get("codesign_reqs", ""), "")
        self.assertEqual(len(result["codesign_authorities"]), 0)

        warning_found = any(
            "obsolete code signature" in warning for warning in result["warnings"]
        )
        self.assertTrue(warning_found)

    @patch("scripts.recipe_robot_lib.inspect.get_app_description")
    @patch("scripts.recipe_robot_lib.inspect.get_exitcode_stdout_stderr")
    @patch("scripts.recipe_robot_lib.inspect.os.path.exists")
    @patch("scripts.recipe_robot_lib.inspect.os.path.basename")
    @patch("builtins.open")
    @patch("scripts.recipe_robot_lib.inspect.plistlib.load")
    def test_codesign_loose_requirements_warning(
        self,
        mock_plist_load,
        _mock_open_builtin,
        mock_basename,
        mock_exists,
        mock_get_exitcode,
        mock_get_description,
    ):
        """Test warning for loose code signing requirements."""
        mock_plist_load.return_value = self.create_mock_info_plist()
        mock_basename.return_value = "test.app"
        mock_exists.side_effect = lambda path: "_MASReceipt" not in path

        loose_requirements = [
            "anchor apple generic",
            "anchor trusted",
            "certificate anchor trusted",
        ]

        mock_get_description.return_value = (None, None)

        from scripts.recipe_robot_lib.inspect import inspect_app

        for req in loose_requirements:
            with self.subTest(requirement=req):
                test_facts = RoboDict()
                test_facts["inspections"] = []
                test_facts["warnings"] = []
                test_facts["blocking_applications"] = []
                test_facts["codesign_authorities"] = []

                stdout = f"designated => {req}"
                stderr = "Authority=Some Authority"
                mock_get_exitcode.return_value = (0, stdout, stderr)

                result = inspect_app(self.test_app_path, self.args, test_facts)

                warning_found = any(
                    "code signing designated requirements are set very broadly"
                    in warning
                    for warning in result["warnings"]
                )
                self.assertTrue(warning_found)

    @patch("scripts.recipe_robot_lib.inspect.get_app_description")
    @patch("scripts.recipe_robot_lib.inspect.get_exitcode_stdout_stderr")
    @patch("scripts.recipe_robot_lib.inspect.os.path.exists")
    @patch("scripts.recipe_robot_lib.inspect.os.path.basename")
    @patch("builtins.open")
    @patch("scripts.recipe_robot_lib.inspect.plistlib.load")
    def test_non_app_bundle_type(
        self,
        mock_plist_load,
        _mock_open_builtin,
        mock_basename,
        mock_exists,
        mock_get_exitcode,
        mock_get_description,
    ):
        """Test inspection of non-app bundle types like screen savers."""
        mock_plist_load.return_value = self.create_mock_info_plist()
        mock_basename.return_value = "test.saver"
        mock_exists.side_effect = lambda path: "_MASReceipt" not in path
        mock_get_exitcode.return_value = (1, "", "")
        mock_get_description.return_value = (None, None)

        from scripts.recipe_robot_lib.inspect import inspect_app

        result = inspect_app(
            "/tmp/test.saver", self.args, self.facts, bundle_type="saver"
        )

        self.assertEqual(result["saver_name"], "Test App")
        self.assertIn("saver", result["inspections"])
        # Non-app bundles shouldn't be added to blocking_applications
        self.assertEqual(len(result["blocking_applications"]), 0)

    @patch("scripts.recipe_robot_lib.inspect.inspect_sparkle_feed_url")
    @patch("scripts.recipe_robot_lib.inspect.get_app_description")
    @patch("scripts.recipe_robot_lib.inspect.get_exitcode_stdout_stderr")
    @patch("scripts.recipe_robot_lib.inspect.os.path.exists")
    @patch("scripts.recipe_robot_lib.inspect.os.path.basename")
    @patch("builtins.open")
    @patch("scripts.recipe_robot_lib.inspect.plistlib.load")
    def test_sparkle_feed_detection(
        self,
        mock_plist_load,
        _mock_open_builtin,
        mock_basename,
        mock_exists,
        mock_get_exitcode,
        mock_get_description,
        mock_inspect_sparkle,
    ):
        """Test detection and inspection of Sparkle feed URLs."""
        mock_plist_load.return_value = self.create_mock_info_plist(
            SUFeedURL="https://example.com/appcast.xml"
        )
        mock_basename.return_value = "test.app"
        mock_exists.side_effect = lambda path: "_MASReceipt" not in path
        mock_get_exitcode.return_value = (1, "", "")
        mock_get_description.return_value = (None, None)
        mock_inspect_sparkle.return_value = self.facts

        from scripts.recipe_robot_lib.inspect import inspect_app

        inspect_app(self.test_app_path, self.args, self.facts)

        mock_inspect_sparkle.assert_called_once_with(
            "https://example.com/appcast.xml", self.args, self.facts
        )

    @patch("scripts.recipe_robot_lib.inspect.inspect_barebones_feed_url")
    @patch("scripts.recipe_robot_lib.inspect.get_app_description")
    @patch("scripts.recipe_robot_lib.inspect.get_exitcode_stdout_stderr")
    @patch("scripts.recipe_robot_lib.inspect.os.path.exists")
    @patch("scripts.recipe_robot_lib.inspect.os.path.basename")
    @patch("builtins.open")
    @patch("scripts.recipe_robot_lib.inspect.plistlib.load")
    def test_barebones_feed_detection(
        self,
        mock_plist_load,
        _mock_open_builtin,
        mock_basename,
        mock_exists,
        mock_get_exitcode,
        mock_get_description,
        mock_inspect_barebones,
    ):
        """Test detection and inspection of Bare Bones feed URLs."""
        mock_plist_load.return_value = self.create_mock_info_plist(
            SUFeedURL="https://versioncheck.barebones.com/TestApp.xml"
        )
        mock_basename.return_value = "test.app"
        mock_exists.side_effect = lambda path: "_MASReceipt" not in path
        mock_get_exitcode.return_value = (1, "", "")
        mock_get_description.return_value = (None, None)
        mock_inspect_barebones.return_value = self.facts

        from scripts.recipe_robot_lib.inspect import inspect_app

        inspect_app(self.test_app_path, self.args, self.facts)

        mock_inspect_barebones.assert_called_once_with(
            "https://versioncheck.barebones.com/TestApp.xml", self.args, self.facts
        )

    @patch("scripts.recipe_robot_lib.inspect.inspect_sparkle_feed_url")
    @patch("scripts.recipe_robot_lib.inspect.get_app_description")
    @patch("scripts.recipe_robot_lib.inspect.get_exitcode_stdout_stderr")
    @patch("scripts.recipe_robot_lib.inspect.os.path.exists")
    @patch("scripts.recipe_robot_lib.inspect.os.path.basename")
    @patch("builtins.open")
    @patch("scripts.recipe_robot_lib.inspect.plistlib.load")
    def test_devmate_feed_detection(
        self,
        mock_plist_load,
        _mock_open_builtin,
        mock_basename,
        mock_exists,
        mock_get_exitcode,
        mock_get_description,
        mock_inspect_sparkle,
    ):
        """Test detection of DevMate framework and auto-generated feed URL."""
        mock_plist_load.return_value = self.create_mock_info_plist()
        mock_basename.return_value = "test.app"

        def mock_exists_devmate(path):
            if "_MASReceipt" in path:
                return False
            elif "DevMateKit.framework" in path:
                return True
            return False

        mock_exists.side_effect = mock_exists_devmate
        mock_get_exitcode.return_value = (1, "", "")
        mock_get_description.return_value = (None, None)
        mock_inspect_sparkle.return_value = self.facts

        from scripts.recipe_robot_lib.inspect import inspect_app

        inspect_app(self.test_app_path, self.args, self.facts)

        expected_devmate_url = "https://updates.devmate.com/com.example.testapp.xml"
        mock_inspect_sparkle.assert_called_once_with(
            expected_devmate_url, self.args, self.facts
        )


class TestGetDownloadLinkFromXattr(unittest.TestCase):
    """Tests for the get_download_link_from_xattr function."""

    def setUp(self):
        """Set up test fixtures."""
        self.facts = RoboDict()
        self.facts["warnings"] = []
        self.args = MagicMock()
        self.test_path = "/tmp/test_file.dmg"

    @patch("scripts.recipe_robot_lib.inspect.plistlib.loads")
    @patch("scripts.recipe_robot_lib.inspect.xattr.getxattr")
    @patch("scripts.recipe_robot_lib.inspect.robo_print")
    def test_successful_xattr_extraction(
        self, mock_robo_print, mock_getxattr, mock_plistlib_loads
    ):
        """Test successful extraction of download URL from xattr metadata."""
        # Mock the extended attributes data
        mock_getxattr.return_value = b"test_plist_data"
        mock_plistlib_loads.return_value = [
            "https://example.com/download.dmg",
            "https://example.com/mirror.dmg",
        ]

        # Call the function
        get_download_link_from_xattr(self.test_path, self.args, self.facts)

        # Verify the correct xattr was queried
        mock_getxattr.assert_called_once_with(
            self.test_path, "com.apple.metadata:kMDItemWhereFroms"
        )

        # Verify plistlib.loads was called with the xattr data
        mock_plistlib_loads.assert_called_once_with(b"test_plist_data")

        # Verify the first URL was set as download_url
        self.assertEqual(self.facts["download_url"], "https://example.com/download.dmg")

        # Verify the success message was printed
        mock_robo_print.assert_called_once()
        call_args = mock_robo_print.call_args[0]
        self.assertIn("Download URL found in file metadata", call_args[0])
        self.assertIn("https://example.com/download.dmg", call_args[0])

    @patch("scripts.recipe_robot_lib.inspect.plistlib.loads")
    @patch("scripts.recipe_robot_lib.inspect.xattr.getxattr")
    @patch("scripts.recipe_robot_lib.inspect.robo_print")
    def test_empty_where_froms_list(
        self, mock_robo_print, mock_getxattr, mock_plistlib_loads
    ):
        """Test when the where froms list is empty."""
        # Mock empty list from plistlib
        mock_getxattr.return_value = b"empty_plist_data"
        mock_plistlib_loads.return_value = []

        # Call the function
        get_download_link_from_xattr(self.test_path, self.args, self.facts)

        # Verify xattr was queried
        mock_getxattr.assert_called_once_with(
            self.test_path, "com.apple.metadata:kMDItemWhereFroms"
        )

        # Verify plistlib.loads was called
        mock_plistlib_loads.assert_called_once_with(b"empty_plist_data")

        # Verify no download_url was set
        self.assertNotIn("download_url", self.facts)

        # Verify no success message was printed (only called on failure)
        mock_robo_print.assert_not_called()

    @patch("scripts.recipe_robot_lib.inspect.xattr.getxattr")
    @patch("scripts.recipe_robot_lib.inspect.robo_print")
    def test_keyerror_handling(self, mock_robo_print, mock_getxattr):
        """Test handling of KeyError when xattr doesn't exist."""
        # Mock KeyError from getxattr
        mock_getxattr.side_effect = KeyError("No such xattr")

        # Call the function
        get_download_link_from_xattr(self.test_path, self.args, self.facts)

        # Verify xattr was queried
        mock_getxattr.assert_called_once_with(
            self.test_path, "com.apple.metadata:kMDItemWhereFroms"
        )

        # Verify no download_url was set
        self.assertNotIn("download_url", self.facts)

        # Verify error message was printed
        mock_robo_print.assert_called_once()
        call_args = mock_robo_print.call_args[0]
        self.assertIn(
            "Unable to derive a download URL from file metadata", call_args[0]
        )

    @patch("scripts.recipe_robot_lib.inspect.xattr.getxattr")
    @patch("scripts.recipe_robot_lib.inspect.robo_print")
    def test_oserror_handling(self, mock_robo_print, mock_getxattr):
        """Test handling of OSError when file doesn't exist or can't be accessed."""
        # Mock OSError from getxattr
        mock_getxattr.side_effect = OSError("File not found")

        # Call the function
        get_download_link_from_xattr(self.test_path, self.args, self.facts)

        # Verify xattr was queried
        mock_getxattr.assert_called_once_with(
            self.test_path, "com.apple.metadata:kMDItemWhereFroms"
        )

        # Verify no download_url was set
        self.assertNotIn("download_url", self.facts)

        # Verify error message was printed
        mock_robo_print.assert_called_once()
        call_args = mock_robo_print.call_args[0]
        self.assertIn(
            "Unable to derive a download URL from file metadata", call_args[0]
        )

    @patch("scripts.recipe_robot_lib.inspect.plistlib.loads")
    @patch("scripts.recipe_robot_lib.inspect.xattr.getxattr")
    @patch("scripts.recipe_robot_lib.inspect.robo_print")
    def test_plistlib_exception_handling(
        self, mock_robo_print, mock_getxattr, mock_plistlib_loads
    ):
        """Test handling when plistlib fails to parse the xattr data."""
        # Mock successful xattr retrieval but failed plist parsing
        mock_getxattr.return_value = b"invalid_plist_data"
        mock_plistlib_loads.side_effect = Exception("Invalid plist format")

        # Call the function - this should raise the exception since it's not caught
        with self.assertRaises(Exception):
            get_download_link_from_xattr(self.test_path, self.args, self.facts)

        # Verify xattr was queried
        mock_getxattr.assert_called_once_with(
            self.test_path, "com.apple.metadata:kMDItemWhereFroms"
        )

        # Verify plistlib.loads was called
        mock_plistlib_loads.assert_called_once_with(b"invalid_plist_data")

        # Verify no download_url was set
        self.assertNotIn("download_url", self.facts)

    @patch("scripts.recipe_robot_lib.inspect.plistlib.loads")
    @patch("scripts.recipe_robot_lib.inspect.xattr.getxattr")
    @patch("scripts.recipe_robot_lib.inspect.robo_print")
    def test_multiple_urls_takes_first(
        self, mock_robo_print, mock_getxattr, mock_plistlib_loads
    ):
        """Test that when multiple URLs exist, the first one is used."""
        # Mock multiple URLs in the where froms
        mock_getxattr.return_value = b"multi_url_plist_data"
        mock_plistlib_loads.return_value = [
            "https://first.example.com/download.dmg",
            "https://second.example.com/download.dmg",
            "https://third.example.com/download.dmg",
        ]

        # Call the function
        get_download_link_from_xattr(self.test_path, self.args, self.facts)

        # Verify the first URL was set as download_url
        self.assertEqual(
            self.facts["download_url"], "https://first.example.com/download.dmg"
        )

        # Verify the success message mentions the first URL
        mock_robo_print.assert_called_once()
        call_args = mock_robo_print.call_args[0]
        self.assertIn("https://first.example.com/download.dmg", call_args[0])

    @patch("scripts.recipe_robot_lib.inspect.plistlib.loads")
    @patch("scripts.recipe_robot_lib.inspect.xattr.getxattr")
    @patch("scripts.recipe_robot_lib.inspect.robo_print")
    def test_function_modifies_facts_in_place(
        self, mock_robo_print, mock_getxattr, mock_plistlib_loads
    ):
        """Test that the function modifies the facts dictionary in place."""
        # Mock successful xattr extraction
        mock_getxattr.return_value = b"test_plist_data"
        mock_plistlib_loads.return_value = ["https://example.com/download.dmg"]

        # Store original facts object reference
        original_facts = self.facts

        # Call the function
        get_download_link_from_xattr(self.test_path, self.args, self.facts)

        # Verify the same facts object was modified
        self.assertIs(self.facts, original_facts)
        self.assertEqual(self.facts["download_url"], "https://example.com/download.dmg")

    @patch("scripts.recipe_robot_lib.inspect.plistlib.loads")
    @patch("scripts.recipe_robot_lib.inspect.xattr.getxattr")
    @patch("scripts.recipe_robot_lib.inspect.robo_print")
    def test_preserves_existing_facts(
        self, mock_robo_print, mock_getxattr, mock_plistlib_loads
    ):
        """Test that function preserves existing facts when adding download_url."""
        # Pre-populate facts with some data
        self.facts["app_name"] = "Test App"
        self.facts["bundle_id"] = "com.example.testapp"

        # Mock successful xattr extraction
        mock_getxattr.return_value = b"test_plist_data"
        mock_plistlib_loads.return_value = ["https://example.com/download.dmg"]

        # Call the function
        get_download_link_from_xattr(self.test_path, self.args, self.facts)

        # Verify existing facts are preserved
        self.assertEqual(self.facts["app_name"], "Test App")
        self.assertEqual(self.facts["bundle_id"], "com.example.testapp")

        # Verify new fact was added
        self.assertEqual(self.facts["download_url"], "https://example.com/download.dmg")

    def test_function_signature_and_docstring(self):
        """Test that the function has the expected signature and docstring."""
        import inspect

        # Get function signature
        sig = inspect.signature(get_download_link_from_xattr)
        params = list(sig.parameters.keys())

        # Verify parameter names
        expected_params = ["input_path", "args", "facts"]
        self.assertEqual(params, expected_params)

        # Verify docstring exists and has expected content
        docstring = get_download_link_from_xattr.__doc__
        self.assertIsNotNone(docstring)
        if docstring:
            self.assertIn("Attempts to derive download URL", docstring)
            self.assertIn("extended attribute", docstring)
            self.assertIn("xattr", docstring)


class TestInspectDownloadUrl(unittest.TestCase):
    """Tests for the inspect_download_url function."""

    def setUp(self):
        """Set up test fixtures."""
        self.facts = RoboDict()
        self.facts["warnings"] = []
        self.facts["inspections"] = []
        self.args = MagicMock()
        self.args.app_mode = False
        self.facts["args"] = self.args  # Add args to facts as expected by function
        self.test_url = "https://example.com/test.dmg"

    @patch("scripts.recipe_robot_lib.inspect.inspect_sparkle_feed_url")
    @patch("scripts.recipe_robot_lib.inspect.inspect_disk_image")
    @patch("scripts.recipe_robot_lib.inspect.os.remove")
    @patch("builtins.open")
    @patch("scripts.recipe_robot_lib.inspect.curler.download_to_file")
    @patch("scripts.recipe_robot_lib.inspect.curler.check_url")
    @patch("scripts.recipe_robot_lib.inspect.robo_print")
    def test_basic_download_url_processing(
        self,
        mock_robo_print,
        mock_check_url,
        mock_download_to_file,
        mock_open,
        mock_remove,
        mock_inspect_disk_image,
        mock_inspect_sparkle,
    ):
        """Test basic processing of a download URL."""
        # Setup mocks
        mock_check_url.return_value = (
            "https://example.com/test.dmg",
            {
                "http_result_code": "200",
                "content-type": "application/x-apple-diskimage",
            },
            None,
        )
        mock_download_to_file.return_value = None

        # Mock file content reading to simulate a DMG file
        mock_file = MagicMock()
        mock_file.read.return_value = b"dmg_binary_content"
        mock_open.return_value.__enter__.return_value = mock_file

        mock_inspect_disk_image.return_value = self.facts

        # Call the function
        result = inspect_download_url(self.test_url, self.args, self.facts)

        # Verify basic results
        self.assertEqual(result["download_url"], self.test_url)
        self.assertFalse(result["is_from_app_store"])
        self.assertEqual(result["download_filename"], "test.dmg")
        self.assertEqual(result["download_format"], "dmg")
        self.assertFalse(result["specify_filename"])

        # Verify URL checking was called
        mock_check_url.assert_called_once_with(self.test_url, headers={})

        # Verify download was called
        mock_download_to_file.assert_called_once()

        # Verify disk image inspection was called
        mock_inspect_disk_image.assert_called_once()

    @patch("scripts.recipe_robot_lib.inspect.curler.check_url")
    @patch("scripts.recipe_robot_lib.inspect.robo_print")
    def test_url_stripping(self, mock_robo_print, mock_check_url):
        """Test that leading and trailing spaces are stripped from URLs."""
        # Setup mocks
        mock_check_url.return_value = (
            "https://example.com/test.dmg",
            {"http_result_code": "200"},
            None,
        )

        # Test URL with spaces
        url_with_spaces = "  https://example.com/test.dmg  "

        # Mock the rest of the function to avoid full execution
        with patch("scripts.recipe_robot_lib.inspect.curler.download_to_file"), patch(
            "builtins.open"
        ), patch("scripts.recipe_robot_lib.inspect.inspect_disk_image") as mock_inspect:
            mock_inspect.return_value = self.facts

            # Call the function
            result = inspect_download_url(url_with_spaces, self.args, self.facts)

        # Verify the URL was stripped
        self.assertEqual(result["download_url"], "https://example.com/test.dmg")

    @patch("scripts.recipe_robot_lib.inspect.inspect_github_url")
    @patch("scripts.recipe_robot_lib.inspect.curler.check_url")
    @patch("scripts.recipe_robot_lib.inspect.robo_print")
    def test_github_url_detection(
        self, mock_robo_print, mock_check_url, mock_inspect_github
    ):
        """Test detection and inspection of GitHub URLs."""
        test_urls = [
            "https://github.com/user/repo/releases/download/v1.0/app.dmg",
            "https://githubusercontent.com/user/repo/main/app.dmg",
        ]

        mock_check_url.return_value = (
            "https://github.com/user/repo/releases/download/v1.0/app.dmg",
            {"http_result_code": "200"},
            None,
        )
        mock_inspect_github.return_value = self.facts

        for test_url in test_urls:
            with self.subTest(url=test_url):
                # Reset mocks
                mock_inspect_github.reset_mock()
                test_facts = RoboDict()
                test_facts["warnings"] = []
                test_facts["inspections"] = []
                test_facts["args"] = self.args

                # Mock the rest of the function
                with patch(
                    "scripts.recipe_robot_lib.inspect.curler.download_to_file"
                ), patch("builtins.open"), patch(
                    "scripts.recipe_robot_lib.inspect.inspect_disk_image"
                ) as mock_inspect:
                    mock_inspect.return_value = test_facts

                    # Call the function
                    inspect_download_url(test_url, self.args, test_facts)

                # Verify GitHub inspection was called
                mock_inspect_github.assert_called_once_with(
                    test_url, self.args, test_facts
                )

    @patch("scripts.recipe_robot_lib.inspect.inspect_sourceforge_url")
    @patch("scripts.recipe_robot_lib.inspect.curler.check_url")
    @patch("scripts.recipe_robot_lib.inspect.robo_print")
    def test_sourceforge_url_detection(
        self, mock_robo_print, mock_check_url, mock_inspect_sourceforge
    ):
        """Test detection and inspection of SourceForge URLs."""
        test_url = "https://sourceforge.net/projects/test/files/app.dmg"

        mock_check_url.return_value = (test_url, {"http_result_code": "200"}, None)
        mock_inspect_sourceforge.return_value = self.facts

        # Mock the rest of the function
        with patch("scripts.recipe_robot_lib.inspect.curler.download_to_file"), patch(
            "builtins.open"
        ), patch("scripts.recipe_robot_lib.inspect.inspect_disk_image") as mock_inspect:
            mock_inspect.return_value = self.facts

            # Call the function
            inspect_download_url(test_url, self.args, self.facts)

        # Verify SourceForge inspection was called
        mock_inspect_sourceforge.assert_called_once_with(
            test_url, self.args, self.facts
        )

    @patch("scripts.recipe_robot_lib.inspect.curler.check_url")
    @patch("scripts.recipe_robot_lib.inspect.robo_print")
    def test_version_specific_url_warning(self, mock_robo_print, mock_check_url):
        """Test warning for version-specific URLs."""
        version_specific_url = "https://example.com/app-1.2.3.dmg"

        mock_check_url.return_value = (
            version_specific_url,
            {"http_result_code": "200"},
            None,
        )

        # Mock the rest of the function
        with patch("scripts.recipe_robot_lib.inspect.curler.download_to_file"), patch(
            "builtins.open"
        ), patch("scripts.recipe_robot_lib.inspect.inspect_disk_image") as mock_inspect:
            mock_inspect.return_value = self.facts

            # Call the function
            result = inspect_download_url(version_specific_url, self.args, self.facts)

        # Verify warning was added
        warning_found = any(
            "version-specific URL" in warning for warning in result["warnings"]
        )
        self.assertTrue(warning_found)

    @patch("scripts.recipe_robot_lib.inspect.curler.check_url")
    @patch("scripts.recipe_robot_lib.inspect.robo_print")
    def test_cdn_url_warning(self, mock_robo_print, mock_check_url):
        """Test warning for CDN URLs with expiration."""
        cdn_url = "https://cdn.example.com/file.dmg?Expires=1234567890"

        mock_check_url.return_value = (cdn_url, {"http_result_code": "200"}, None)

        # Mock the rest of the function
        with patch("scripts.recipe_robot_lib.inspect.curler.download_to_file"), patch(
            "builtins.open"
        ), patch("scripts.recipe_robot_lib.inspect.inspect_disk_image") as mock_inspect:
            mock_inspect.return_value = self.facts

            # Call the function
            result = inspect_download_url(cdn_url, self.args, self.facts)

        # Verify warning was added
        warning_found = any(
            "CDN-cached URL" in warning for warning in result["warnings"]
        )
        self.assertTrue(warning_found)

    @patch("scripts.recipe_robot_lib.inspect.curler.check_url")
    @patch("scripts.recipe_robot_lib.inspect.robo_print")
    def test_aws_access_key_warning(self, mock_robo_print, mock_check_url):
        """Test warning for AWS URLs with access keys."""
        aws_url = "https://s3.amazonaws.com/bucket/file.dmg?AWSAccessKeyId=AKIAIOSFODNN7EXAMPLE"

        mock_check_url.return_value = (aws_url, {"http_result_code": "200"}, None)

        # Mock the rest of the function
        with patch("scripts.recipe_robot_lib.inspect.curler.download_to_file"), patch(
            "builtins.open"
        ), patch("scripts.recipe_robot_lib.inspect.inspect_disk_image") as mock_inspect:
            mock_inspect.return_value = self.facts

            # Call the function
            result = inspect_download_url(aws_url, self.args, self.facts)

        # Verify warning was added
        warning_found = any(
            "AWSAccessKeyId parameter" in warning for warning in result["warnings"]
        )
        self.assertTrue(warning_found)

    @patch("scripts.recipe_robot_lib.inspect.curler.check_url")
    @patch("scripts.recipe_robot_lib.inspect.robo_print")
    def test_specify_filename_detection(self, mock_robo_print, mock_check_url):
        """Test detection of URLs that need filename specified."""
        test_cases = [
            ("https://example.com/download?id=123", True),  # needs filename
            ("https://example.com/app.dmg", False),  # doesn't need filename
        ]

        for url, should_specify in test_cases:
            with self.subTest(url=url, should_specify=should_specify):
                mock_check_url.return_value = (url, {"http_result_code": "200"}, None)

                test_facts = RoboDict()
                test_facts["warnings"] = []
                test_facts["inspections"] = []
                test_facts["args"] = self.args

                # Mock the rest of the function
                with patch(
                    "scripts.recipe_robot_lib.inspect.curler.download_to_file"
                ), patch("builtins.open"), patch(
                    "scripts.recipe_robot_lib.inspect.inspect_disk_image"
                ) as mock_inspect_disk, patch(
                    "scripts.recipe_robot_lib.inspect.inspect_archive"
                ) as mock_inspect_archive, patch(
                    "scripts.recipe_robot_lib.inspect.inspect_pkg"
                ) as mock_inspect_pkg:

                    # Make sure all inspection functions return without doing anything
                    mock_inspect_disk.return_value = test_facts
                    mock_inspect_archive.return_value = test_facts
                    mock_inspect_pkg.return_value = test_facts

                    # Call the function
                    result = inspect_download_url(url, self.args, test_facts)

                # Verify specify_filename is set correctly
                self.assertEqual(result["specify_filename"], should_specify)

    @patch("scripts.recipe_robot_lib.inspect.curler.check_url")
    @patch("scripts.recipe_robot_lib.inspect.robo_print")
    def test_github_token_headers(self, mock_robo_print, mock_check_url):
        """Test that GitHub token is included in headers when available."""
        github_url = "https://github.com/user/repo/releases/download/v1.0/app.dmg"

        # Mock GITHUB_TOKEN
        with patch(
            "scripts.recipe_robot_lib.inspect.GITHUB_TOKEN", "test_token"
        ), patch(
            "scripts.recipe_robot_lib.inspect.any_item_in_string", return_value=True
        ):

            mock_check_url.return_value = (
                github_url,
                {"http_result_code": "200"},
                None,
            )

            # Mock the rest of the function
            with patch(
                "scripts.recipe_robot_lib.inspect.curler.download_to_file"
            ) as mock_download, patch("builtins.open"), patch(
                "scripts.recipe_robot_lib.inspect.inspect_disk_image"
            ) as mock_inspect:
                mock_inspect.return_value = self.facts

                # Call the function
                inspect_download_url(github_url, self.args, self.facts)

            # Verify headers were passed correctly
            expected_headers = {"Authorization": "token test_token"}
            mock_check_url.assert_called_once_with(github_url, headers=expected_headers)
            mock_download.assert_called_once()
            call_args = mock_download.call_args
            self.assertEqual(call_args[1]["headers"], expected_headers)

    @patch("scripts.recipe_robot_lib.inspect.curler.check_url")
    @patch("scripts.recipe_robot_lib.inspect.robo_print")
    def test_http_error_warning(self, mock_robo_print, mock_check_url):
        """Test warning for HTTP error responses."""
        mock_check_url.return_value = (
            self.test_url,
            {"http_result_code": "404"},
            None,
        )

        # Mock the rest of the function
        with patch("scripts.recipe_robot_lib.inspect.curler.download_to_file"), patch(
            "builtins.open"
        ), patch("scripts.recipe_robot_lib.inspect.inspect_disk_image") as mock_inspect:
            mock_inspect.return_value = self.facts

            # Call the function
            result = inspect_download_url(self.test_url, self.args, self.facts)

        # Verify warning was added
        warning_found = any(
            "Error encountered during file download HEAD check" in warning
            for warning in result["warnings"]
        )
        self.assertTrue(warning_found)

    @patch("scripts.recipe_robot_lib.inspect.curler.check_url")
    @patch("scripts.recipe_robot_lib.inspect.robo_print")
    def test_user_agent_detection(self, mock_robo_print, mock_check_url):
        """Test detection and handling of required user-agent."""
        mock_check_url.return_value = (
            self.test_url,
            {"http_result_code": "200"},
            "Mozilla/5.0 Custom Agent",
        )

        # Mock the rest of the function
        with patch("scripts.recipe_robot_lib.inspect.curler.download_to_file"), patch(
            "builtins.open"
        ), patch("scripts.recipe_robot_lib.inspect.inspect_disk_image") as mock_inspect:
            mock_inspect.return_value = self.facts

            # Call the function
            result = inspect_download_url(self.test_url, self.args, self.facts)

        # Verify user-agent was recorded
        self.assertEqual(result["user-agent"], "Mozilla/5.0 Custom Agent")

        # Verify warning was added
        warning_found = any(
            "different user-agent" in warning for warning in result["warnings"]
        )
        self.assertTrue(warning_found)

    @patch("scripts.recipe_robot_lib.inspect.curler.check_url")
    @patch("scripts.recipe_robot_lib.inspect.robo_print")
    def test_http_url_warning(self, mock_robo_print, mock_check_url):
        """Test warning for non-HTTPS URLs."""
        http_url = "http://example.com/test.dmg"
        mock_check_url.return_value = (http_url, {"http_result_code": "200"}, None)

        # Mock the rest of the function
        with patch("scripts.recipe_robot_lib.inspect.curler.download_to_file"), patch(
            "builtins.open"
        ), patch("scripts.recipe_robot_lib.inspect.inspect_disk_image") as mock_inspect:
            mock_inspect.return_value = self.facts

            # Call the function
            result = inspect_download_url(http_url, self.args, self.facts)

        # Verify warning was added
        warning_found = any(
            "not using HTTPS" in warning for warning in result["warnings"]
        )
        self.assertTrue(warning_found)

    @patch("scripts.recipe_robot_lib.inspect.curler.check_url")
    @patch("scripts.recipe_robot_lib.inspect.robo_print")
    def test_unusual_content_type_warning(self, mock_robo_print, mock_check_url):
        """Test warning for unusual content types."""
        mock_check_url.return_value = (
            self.test_url,
            {
                "http_result_code": "200",
                "content-type": "text/html",
            },
            None,
        )

        # Mock the rest of the function
        with patch("scripts.recipe_robot_lib.inspect.curler.download_to_file"), patch(
            "builtins.open"
        ), patch("scripts.recipe_robot_lib.inspect.inspect_disk_image") as mock_inspect:
            mock_inspect.return_value = self.facts

            # Call the function
            result = inspect_download_url(self.test_url, self.args, self.facts)

        # Verify warning was added
        warning_found = any(
            "content-type (text/html) is unusual" in warning
            for warning in result["warnings"]
        )
        self.assertTrue(warning_found)

    @patch("scripts.recipe_robot_lib.inspect.curler.check_url")
    @patch("scripts.recipe_robot_lib.inspect.robo_print")
    def test_content_disposition_filename(self, mock_robo_print, mock_check_url):
        """Test filename extraction from content-disposition header."""
        mock_check_url.return_value = (
            "https://example.com/download?id=123",
            {
                "http_result_code": "200",
                "content-disposition": 'attachment; filename="actual-app.dmg";',
            },
            None,
        )

        # Mock the rest of the function
        with patch("scripts.recipe_robot_lib.inspect.curler.download_to_file"), patch(
            "builtins.open"
        ), patch("scripts.recipe_robot_lib.inspect.inspect_disk_image") as mock_inspect:
            mock_inspect.return_value = self.facts

            # Call the function
            result = inspect_download_url(
                "https://example.com/download?id=123", self.args, self.facts
            )

        # Verify filename was extracted from content-disposition
        self.assertEqual(result["download_filename"], "actual-app.dmg")

    @patch("scripts.recipe_robot_lib.inspect.inspect_sparkle_feed_url")
    @patch("scripts.recipe_robot_lib.inspect.os.remove")
    @patch("builtins.open")
    @patch("scripts.recipe_robot_lib.inspect.curler.download_to_file")
    @patch("scripts.recipe_robot_lib.inspect.curler.check_url")
    @patch("scripts.recipe_robot_lib.inspect.robo_print")
    def test_sparkle_feed_detection(
        self,
        mock_robo_print,
        mock_check_url,
        mock_download_to_file,
        mock_open,
        mock_remove,
        mock_inspect_sparkle,
    ):
        """Test detection of Sparkle feeds disguised as downloads."""
        mock_check_url.return_value = (self.test_url, {"http_result_code": "200"}, None)
        mock_download_to_file.return_value = None

        # Mock file content to simulate a Sparkle feed
        mock_file = MagicMock()
        mock_file.read.return_value = b'<?xml version="1.0" encoding="utf-8"?><rss xmlns:sparkle="http://www.andymatuschak.org/xml-namespaces/sparkle">'
        mock_open.return_value.__enter__.return_value = mock_file

        mock_inspect_sparkle.return_value = self.facts

        # Call the function
        _ = inspect_download_url(self.test_url, self.args, self.facts)

        # Verify file was removed and Sparkle inspection was called
        mock_remove.assert_called_once()
        mock_inspect_sparkle.assert_called_once_with(
            self.test_url, self.args, self.facts
        )

    @patch("builtins.open")
    @patch("scripts.recipe_robot_lib.inspect.curler.download_to_file")
    @patch("scripts.recipe_robot_lib.inspect.curler.check_url")
    @patch("scripts.recipe_robot_lib.inspect.robo_print")
    def test_xml_error_detection(
        self, mock_robo_print, mock_check_url, mock_download_to_file, mock_open
    ):
        """Test detection of XML error responses."""
        mock_check_url.return_value = (self.test_url, {"http_result_code": "200"}, None)
        mock_download_to_file.return_value = None

        # Mock file content to simulate an XML error
        mock_file = MagicMock()
        mock_file.read.return_value = b"<error>File not found</error>"
        mock_open.return_value.__enter__.return_value = mock_file

        # Mock the rest of the function to avoid format detection
        with patch(
            "scripts.recipe_robot_lib.inspect.inspect_disk_image"
        ) as mock_inspect:
            mock_inspect.return_value = self.facts

            # Call the function
            result = inspect_download_url(self.test_url, self.args, self.facts)

        # Verify warning was added
        warning_found = any(
            "XML file was downloaded instead" in warning
            for warning in result["warnings"]
        )
        self.assertTrue(warning_found)

    @patch("builtins.open")
    @patch("scripts.recipe_robot_lib.inspect.curler.download_to_file")
    @patch("scripts.recipe_robot_lib.inspect.curler.check_url")
    @patch("scripts.recipe_robot_lib.inspect.robo_print")
    def test_html_download_detection(
        self, mock_robo_print, mock_check_url, mock_download_to_file, mock_open
    ):
        """Test detection of HTML pages downloaded instead of files."""
        mock_check_url.return_value = (self.test_url, {"http_result_code": "200"}, None)
        mock_download_to_file.return_value = None

        # Mock file content to simulate HTML
        mock_file = MagicMock()
        mock_file.read.side_effect = [
            b"binary_data_first_256_bytes",  # First read for Sparkle check
            b"<html><head><title>404</title>",  # Second read for HTML check
        ]
        mock_open.return_value.__enter__.return_value = mock_file

        # Mock the rest of the function
        with patch(
            "scripts.recipe_robot_lib.inspect.inspect_disk_image"
        ) as mock_inspect:
            mock_inspect.return_value = self.facts

            # Call the function
            result = inspect_download_url(self.test_url, self.args, self.facts)

        # Verify warning was added
        warning_found = any(
            "webpage was downloaded instead" in warning
            for warning in result["warnings"]
        )
        self.assertTrue(warning_found)

    @patch("scripts.recipe_robot_lib.inspect.inspect_archive")
    @patch("builtins.open")
    @patch("scripts.recipe_robot_lib.inspect.curler.download_to_file")
    @patch("scripts.recipe_robot_lib.inspect.curler.check_url")
    @patch("scripts.recipe_robot_lib.inspect.robo_print")
    def test_archive_format_detection(
        self,
        mock_robo_print,
        mock_check_url,
        mock_download_to_file,
        mock_open,
        mock_inspect_archive,
    ):
        """Test detection and handling of archive formats."""
        archive_url = "https://example.com/test.zip"
        mock_check_url.return_value = (archive_url, {"http_result_code": "200"}, None)
        mock_download_to_file.return_value = None

        # Mock file content
        mock_file = MagicMock()
        mock_file.read.return_value = b"zip_binary_content"
        mock_open.return_value.__enter__.return_value = mock_file

        mock_inspect_archive.return_value = self.facts

        # Call the function
        result = inspect_download_url(archive_url, self.args, self.facts)

        # Verify archive inspection was called
        mock_inspect_archive.assert_called_once()
        self.assertEqual(result["download_format"], "zip")

    @patch("scripts.recipe_robot_lib.inspect.inspect_pkg")
    @patch("builtins.open")
    @patch("scripts.recipe_robot_lib.inspect.curler.download_to_file")
    @patch("scripts.recipe_robot_lib.inspect.curler.check_url")
    @patch("scripts.recipe_robot_lib.inspect.robo_print")
    def test_pkg_format_detection(
        self,
        mock_robo_print,
        mock_check_url,
        mock_download_to_file,
        mock_open,
        mock_inspect_pkg,
    ):
        """Test detection and handling of package formats."""
        pkg_url = "https://example.com/test.pkg"
        mock_check_url.return_value = (pkg_url, {"http_result_code": "200"}, None)
        mock_download_to_file.return_value = None

        # Mock file content
        mock_file = MagicMock()
        mock_file.read.return_value = b"pkg_binary_content"
        mock_open.return_value.__enter__.return_value = mock_file

        mock_inspect_pkg.return_value = self.facts

        # Call the function
        result = inspect_download_url(pkg_url, self.args, self.facts)

        # Verify package inspection was called
        mock_inspect_pkg.assert_called_once()
        self.assertEqual(result["download_format"], "pkg")

    @patch("scripts.recipe_robot_lib.inspect.inspect_disk_image")
    @patch("builtins.open")
    @patch("scripts.recipe_robot_lib.inspect.curler.download_to_file")
    @patch("scripts.recipe_robot_lib.inspect.curler.check_url")
    @patch("scripts.recipe_robot_lib.inspect.robo_print")
    def test_mime_type_format_detection(
        self,
        mock_robo_print,
        mock_check_url,
        mock_download_to_file,
        mock_open,
        mock_inspect_disk_image,
    ):
        """Test format detection based on MIME type when filename is ambiguous."""
        ambiguous_url = "https://example.com/download?id=123"
        mock_check_url.return_value = (
            ambiguous_url,
            {
                "http_result_code": "200",
                "content-type": "application/x-apple-diskimage",
            },
            None,
        )
        mock_download_to_file.return_value = None

        # Mock file content
        mock_file = MagicMock()
        mock_file.read.return_value = b"dmg_binary_content"
        mock_open.return_value.__enter__.return_value = mock_file

        mock_inspect_disk_image.return_value = self.facts

        # Call the function
        result = inspect_download_url(ambiguous_url, self.args, self.facts)

        # Verify disk image inspection was called based on MIME type
        mock_inspect_disk_image.assert_called_once()
        self.assertEqual(result["download_format"], "dmg")

    @patch("scripts.recipe_robot_lib.inspect.inspect_pkg")
    @patch("scripts.recipe_robot_lib.inspect.inspect_archive")
    @patch("scripts.recipe_robot_lib.inspect.inspect_disk_image")
    @patch("builtins.open")
    @patch("scripts.recipe_robot_lib.inspect.curler.download_to_file")
    @patch("scripts.recipe_robot_lib.inspect.curler.check_url")
    @patch("scripts.recipe_robot_lib.inspect.robo_print")
    def test_format_guessing_fallback(
        self,
        mock_robo_print,
        mock_check_url,
        mock_download_to_file,
        mock_open,
        mock_inspect_disk_image,
        mock_inspect_archive,
        mock_inspect_pkg,
    ):
        """Test fallback format guessing when no format can be determined."""
        ambiguous_url = "https://example.com/download"
        mock_check_url.return_value = (
            ambiguous_url,
            {"http_result_code": "200"},
            None,
        )
        mock_download_to_file.return_value = None

        # Mock file content
        mock_file = MagicMock()
        mock_file.read.return_value = b"unknown_binary_content"
        mock_open.return_value.__enter__.return_value = mock_file

        # Mock inspection functions to simulate unsuccessful attempts
        test_facts = RoboDict()
        test_facts["warnings"] = []
        test_facts["inspections"] = []
        test_facts["args"] = self.args

        mock_inspect_disk_image.return_value = test_facts
        mock_inspect_archive.return_value = test_facts
        mock_inspect_pkg.return_value = test_facts

        # Call the function
        result = inspect_download_url(ambiguous_url, self.args, test_facts)

        # Verify warning about unknown format was added
        warning_found = any(
            "not sure what the download format is" in warning
            for warning in result["warnings"]
        )
        self.assertTrue(warning_found)

        # Verify all inspection methods were tried
        mock_inspect_disk_image.assert_called()
        mock_inspect_archive.assert_called()
        mock_inspect_pkg.assert_called()

    @patch("scripts.recipe_robot_lib.inspect.inspect_disk_image")
    @patch("builtins.open")
    @patch("scripts.recipe_robot_lib.inspect.curler.download_to_file")
    @patch("scripts.recipe_robot_lib.inspect.curler.check_url")
    @patch("scripts.recipe_robot_lib.inspect.robo_print")
    def test_early_return_when_app_already_inspected(
        self,
        mock_robo_print,
        mock_check_url,
        mock_download_to_file,
        mock_open,
        mock_inspect_disk_image,
    ):
        """Test early return when app and download format are already known."""
        # Pre-populate facts
        self.facts["download_format"] = "dmg"
        self.facts["inspections"] = ["app"]

        mock_check_url.return_value = (self.test_url, {"http_result_code": "200"}, None)
        mock_download_to_file.return_value = None

        # Mock file content
        mock_file = MagicMock()
        mock_file.read.return_value = b"dmg_binary_content"
        mock_open.return_value.__enter__.return_value = mock_file

        # Call the function
        result = inspect_download_url(self.test_url, self.args, self.facts)

        # Verify disk image inspection was NOT called (early return)
        mock_inspect_disk_image.assert_not_called()

        # Verify basic facts were still set
        self.assertEqual(result["download_url"], self.test_url)
        self.assertEqual(result["download_format"], "dmg")

    def test_function_signature_and_docstring(self):
        """Test that the function has the expected signature and docstring."""
        import inspect

        # Get function signature
        sig = inspect.signature(inspect_download_url)
        params = list(sig.parameters.keys())

        # Verify parameter names
        expected_params = ["input_path", "args", "facts"]
        self.assertEqual(params, expected_params)

        # Verify docstring exists and has expected content
        docstring = inspect_download_url.__doc__
        self.assertIsNotNone(docstring)
        if docstring:
            self.assertIn("Process a download URL", docstring)
            self.assertIn("gathering information required", docstring)
            self.assertIn("AutoPkg recipes", docstring)


if __name__ == "__main__":
    unittest.main()
