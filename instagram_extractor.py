"""
Instagram Reel Music Extractor

Extracts music information from Instagram Reels by parsing the page content.
"""

import re
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from typing import Optional


class InstagramExtractor:
    """Extracts music information from Instagram Reels."""

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

    def extract_reel_id(self, url: str) -> Optional[str]:
        """Extract the reel ID from an Instagram URL."""
        # Handle various Instagram URL formats
        patterns = [
            r'instagram\.com/reel/([A-Za-z0-9_-]+)',
            r'instagram\.com/reels/([A-Za-z0-9_-]+)',
            r'instagram\.com/p/([A-Za-z0-9_-]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def get_music_info(self, url: str) -> Optional[dict]:
        """
        Extract music information from an Instagram Reel URL.

        Returns:
            dict with 'title', 'artist', and optionally 'original_audio_url'
            or None if extraction fails
        """
        reel_id = self.extract_reel_id(url)
        if not reel_id:
            print(f"Could not extract reel ID from URL: {url}")
            return None

        # Try multiple methods to extract music info
        music_info = self._try_oembed(url)
        if music_info:
            return music_info

        music_info = self._try_page_scrape(url)
        if music_info:
            return music_info

        music_info = self._try_graphql(reel_id)
        if music_info:
            return music_info

        return None

    def _try_oembed(self, url: str) -> Optional[dict]:
        """Try to get info via Instagram's oEmbed endpoint."""
        try:
            oembed_url = f"https://api.instagram.com/oembed/?url={url}"
            response = self.session.get(oembed_url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                title = data.get('title', '')

                # Sometimes the title contains music info
                music_info = self._parse_title_for_music(title)
                if music_info:
                    return music_info
        except Exception as e:
            print(f"oEmbed method failed: {e}")

        return None

    def _try_page_scrape(self, url: str) -> Optional[dict]:
        """Try to scrape the page directly for music info."""
        try:
            response = self.session.get(url, timeout=15)

            if response.status_code != 200:
                return None

            soup = BeautifulSoup(response.text, 'html.parser')

            # Look for JSON-LD structured data
            scripts = soup.find_all('script', type='application/ld+json')
            for script in scripts:
                try:
                    data = json.loads(script.string)
                    music_info = self._extract_from_jsonld(data)
                    if music_info:
                        return music_info
                except json.JSONDecodeError:
                    continue

            # Look for music info in meta tags
            music_info = self._extract_from_meta(soup)
            if music_info:
                return music_info

            # Look for music info in embedded JSON
            music_info = self._extract_from_embedded_json(response.text)
            if music_info:
                return music_info

        except Exception as e:
            print(f"Page scrape method failed: {e}")

        return None

    def _try_graphql(self, reel_id: str) -> Optional[dict]:
        """Try Instagram's GraphQL endpoint."""
        try:
            # This endpoint may require authentication
            graphql_url = f"https://www.instagram.com/api/v1/media/{reel_id}/info/"
            response = self.session.get(graphql_url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                return self._extract_from_api_response(data)
        except Exception as e:
            print(f"GraphQL method failed: {e}")

        return None

    def _extract_from_jsonld(self, data: dict) -> Optional[dict]:
        """Extract music info from JSON-LD data."""
        if isinstance(data, list):
            for item in data:
                result = self._extract_from_jsonld(item)
                if result:
                    return result
            return None

        # Look for audio/music related fields
        if data.get('@type') == 'MusicRecording':
            return {
                'title': data.get('name', ''),
                'artist': data.get('byArtist', {}).get('name', '') if isinstance(data.get('byArtist'), dict) else str(data.get('byArtist', '')),
            }

        # Check for music in video object
        if data.get('@type') == 'VideoObject':
            audio = data.get('audio', {})
            if audio:
                return {
                    'title': audio.get('name', ''),
                    'artist': audio.get('byArtist', ''),
                }

        return None

    def _extract_from_meta(self, soup: BeautifulSoup) -> Optional[dict]:
        """Extract music info from meta tags."""
        # Look for og:title or description that might contain music info
        og_title = soup.find('meta', property='og:title')
        og_desc = soup.find('meta', property='og:description')

        title_content = og_title.get('content', '') if og_title else ''
        desc_content = og_desc.get('content', '') if og_desc else ''

        # Try to parse music info from title/description
        for content in [title_content, desc_content]:
            music_info = self._parse_title_for_music(content)
            if music_info:
                return music_info

        return None

    def _extract_from_embedded_json(self, html: str) -> Optional[dict]:
        """Extract music info from embedded JSON in the page."""
        # Look for music_info or audio_info patterns
        patterns = [
            r'"music_info":\s*(\{[^}]+\})',
            r'"audio_title":\s*"([^"]+)"',
            r'"original_sound_info":\s*(\{[^}]+\})',
            r'"clips_music_attribution_info":\s*(\{[^}]+\})',
        ]

        for pattern in patterns:
            match = re.search(pattern, html)
            if match:
                try:
                    if pattern.startswith('"audio_title"'):
                        # Direct title match
                        return {'title': match.group(1), 'artist': ''}

                    data = json.loads(match.group(1))

                    # Extract based on the structure found
                    title = data.get('song_name') or data.get('title') or data.get('audio_title', '')
                    artist = data.get('artist_name') or data.get('artist') or data.get('ig_artist', {}).get('username', '')

                    if title:
                        return {'title': title, 'artist': artist}
                except (json.JSONDecodeError, AttributeError):
                    continue

        # Try to find music in the larger JSON blob
        json_pattern = r'<script type="application/json"[^>]*>([^<]+)</script>'
        matches = re.findall(json_pattern, html)

        for json_str in matches:
            try:
                data = json.loads(json_str)
                music_info = self._deep_search_music(data)
                if music_info:
                    return music_info
            except json.JSONDecodeError:
                continue

        return None

    def _deep_search_music(self, data, depth=0) -> Optional[dict]:
        """Recursively search for music info in nested JSON."""
        if depth > 10:  # Prevent infinite recursion
            return None

        if isinstance(data, dict):
            # Check for music-related keys
            if 'music_info' in data:
                music = data['music_info']
                if isinstance(music, dict):
                    title = music.get('song_name') or music.get('title', '')
                    artist = music.get('artist_name') or music.get('artist', '')
                    if title:
                        return {'title': title, 'artist': artist}

            if 'clips_music_attribution_info' in data:
                music = data['clips_music_attribution_info']
                if isinstance(music, dict):
                    title = music.get('song_name', '')
                    artist = music.get('artist_name', '')
                    if title:
                        return {'title': title, 'artist': artist}

            if 'audio' in data and isinstance(data['audio'], dict):
                audio = data['audio']
                title = audio.get('title') or audio.get('song_name', '')
                artist = audio.get('artist') or audio.get('artist_name', '')
                if title:
                    return {'title': title, 'artist': artist}

            # Recurse into nested objects
            for value in data.values():
                result = self._deep_search_music(value, depth + 1)
                if result:
                    return result

        elif isinstance(data, list):
            for item in data:
                result = self._deep_search_music(item, depth + 1)
                if result:
                    return result

        return None

    def _extract_from_api_response(self, data: dict) -> Optional[dict]:
        """Extract music info from Instagram API response."""
        items = data.get('items', [])
        if not items:
            return None

        item = items[0]

        # Check for music info in various locations
        music_metadata = item.get('music_metadata', {})
        if music_metadata:
            music_info = music_metadata.get('music_info', {})
            if music_info:
                return {
                    'title': music_info.get('song_name', ''),
                    'artist': music_info.get('artist_name', ''),
                }

        # Check clips_metadata
        clips_metadata = item.get('clips_metadata', {})
        if clips_metadata:
            music_info = clips_metadata.get('music_info', {})
            if music_info:
                music_asset = music_info.get('music_asset_info', {})
                return {
                    'title': music_asset.get('title', ''),
                    'artist': music_asset.get('display_artist', ''),
                }

        return None

    def _parse_title_for_music(self, text: str) -> Optional[dict]:
        """Try to parse music info from a text string."""
        if not text:
            return None

        # Common patterns for music attribution
        # "Song Title by Artist"
        # "Song Title - Artist"
        # "🎵 Song Title · Artist"

        patterns = [
            r'[🎵🎶♪♫]\s*(.+?)\s*[·•-]\s*(.+)',  # Emoji followed by title · artist
            r'"([^"]+)"\s+by\s+(.+)',  # "Title" by Artist
            r'(.+?)\s+by\s+([^|]+)',  # Title by Artist
            r'(.+?)\s*[-–—]\s*([^|]+)',  # Title - Artist
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                title = match.group(1).strip()
                artist = match.group(2).strip()

                # Clean up common suffixes
                artist = re.sub(r'\s*\|.*$', '', artist)
                artist = re.sub(r'\s*on Instagram.*$', '', artist, flags=re.IGNORECASE)

                if title and len(title) > 1:
                    return {'title': title, 'artist': artist}

        return None


def extract_music_from_reel(url: str) -> Optional[dict]:
    """
    Convenience function to extract music from an Instagram Reel.

    Args:
        url: Instagram Reel URL

    Returns:
        dict with 'title' and 'artist' keys, or None if extraction fails
    """
    extractor = InstagramExtractor()
    return extractor.get_music_info(url)


if __name__ == '__main__':
    # Test with a sample URL
    import sys

    if len(sys.argv) > 1:
        url = sys.argv[1]
        print(f"Extracting music from: {url}")

        result = extract_music_from_reel(url)
        if result:
            print(f"Found: {result['title']} by {result['artist']}")
        else:
            print("Could not extract music information")
    else:
        print("Usage: python instagram_extractor.py <instagram_reel_url>")
