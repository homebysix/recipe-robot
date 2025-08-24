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
from unittest.mock import patch

from scripts.recipe_robot_lib.inspect import get_app_description, html_decode


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


if __name__ == "__main__":
    unittest.main()
