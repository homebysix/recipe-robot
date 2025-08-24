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


if __name__ == "__main__":
    unittest.main()
