"""
Spotify Search Module

Searches for songs on Spotify and returns track information including URLs.
"""

import os
import re
from typing import Optional, List
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials


class SpotifySearcher:
    """Searches for songs on Spotify."""

    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None):
        """
        Initialize the Spotify searcher.

        Args:
            client_id: Spotify API client ID (or set SPOTIFY_CLIENT_ID env var)
            client_secret: Spotify API client secret (or set SPOTIFY_CLIENT_SECRET env var)
        """
        self.client_id = client_id or os.getenv('SPOTIFY_CLIENT_ID')
        self.client_secret = client_secret or os.getenv('SPOTIFY_CLIENT_SECRET')

        if not self.client_id or not self.client_secret:
            raise ValueError(
                "Spotify credentials required. Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET "
                "environment variables or pass them to the constructor."
            )

        self.sp = spotipy.Spotify(
            auth_manager=SpotifyClientCredentials(
                client_id=self.client_id,
                client_secret=self.client_secret
            )
        )

    def search_track(self, title: str, artist: str = '') -> Optional[dict]:
        """
        Search for a track on Spotify.

        Args:
            title: Song title
            artist: Artist name (optional but recommended)

        Returns:
            dict with track info including 'name', 'artist', 'album', 'url', 'uri'
            or None if not found
        """
        # Build search query
        query = self._build_query(title, artist)

        try:
            results = self.sp.search(q=query, type='track', limit=5)
            tracks = results.get('tracks', {}).get('items', [])

            if not tracks:
                # Try a simpler search with just the title
                results = self.sp.search(q=title, type='track', limit=5)
                tracks = results.get('tracks', {}).get('items', [])

            if not tracks:
                return None

            # Find the best match
            best_match = self._find_best_match(tracks, title, artist)
            return self._format_track(best_match)

        except Exception as e:
            print(f"Spotify search error: {e}")
            return None

    def search_tracks(self, title: str, artist: str = '', limit: int = 5) -> List[dict]:
        """
        Search for multiple tracks on Spotify.

        Args:
            title: Song title
            artist: Artist name (optional)
            limit: Maximum number of results

        Returns:
            List of track dicts
        """
        query = self._build_query(title, artist)

        try:
            results = self.sp.search(q=query, type='track', limit=limit)
            tracks = results.get('tracks', {}).get('items', [])
            return [self._format_track(track) for track in tracks]
        except Exception as e:
            print(f"Spotify search error: {e}")
            return []

    def _build_query(self, title: str, artist: str) -> str:
        """Build a Spotify search query."""
        # Clean up the title and artist
        title = self._clean_text(title)
        artist = self._clean_text(artist)

        if artist:
            return f'track:"{title}" artist:"{artist}"'
        return f'track:"{title}"'

    def _clean_text(self, text: str) -> str:
        """Clean up text for search."""
        if not text:
            return ''

        # Remove common suffixes/prefixes
        text = re.sub(r'\s*\(Official.*?\)', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\s*\[Official.*?\]', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\s*\(Audio\)', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\s*\(Video\)', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\s*\(Lyrics?\)', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\s*ft\.?\s*.*$', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\s*feat\.?\s*.*$', '', text, flags=re.IGNORECASE)

        # Remove special characters that might interfere with search
        text = re.sub(r'[^\w\s\'-]', ' ', text)
        text = re.sub(r'\s+', ' ', text)

        return text.strip()

    def _find_best_match(self, tracks: List[dict], title: str, artist: str) -> dict:
        """Find the best matching track from search results."""
        if not tracks:
            return None

        title_lower = title.lower()
        artist_lower = artist.lower() if artist else ''

        best_score = -1
        best_track = tracks[0]

        for track in tracks:
            score = 0
            track_name = track.get('name', '').lower()
            track_artists = [a.get('name', '').lower() for a in track.get('artists', [])]

            # Title similarity
            if title_lower in track_name or track_name in title_lower:
                score += 10
            elif self._fuzzy_match(title_lower, track_name):
                score += 5

            # Artist similarity
            if artist_lower:
                for track_artist in track_artists:
                    if artist_lower in track_artist or track_artist in artist_lower:
                        score += 10
                        break
                    elif self._fuzzy_match(artist_lower, track_artist):
                        score += 5
                        break

            # Popularity bonus (slight)
            score += track.get('popularity', 0) / 100

            if score > best_score:
                best_score = score
                best_track = track

        return best_track

    def _fuzzy_match(self, str1: str, str2: str, threshold: float = 0.6) -> bool:
        """Simple fuzzy string matching."""
        if not str1 or not str2:
            return False

        # Check word overlap
        words1 = set(str1.split())
        words2 = set(str2.split())

        if not words1 or not words2:
            return False

        intersection = words1 & words2
        union = words1 | words2

        similarity = len(intersection) / len(union)
        return similarity >= threshold

    def _format_track(self, track: dict) -> dict:
        """Format a Spotify track into a standardized dict."""
        if not track:
            return None

        artists = track.get('artists', [])
        artist_names = ', '.join([a.get('name', '') for a in artists])

        album = track.get('album', {})

        return {
            'name': track.get('name', ''),
            'artist': artist_names,
            'album': album.get('name', ''),
            'url': track.get('external_urls', {}).get('spotify', ''),
            'uri': track.get('uri', ''),
            'preview_url': track.get('preview_url'),
            'duration_ms': track.get('duration_ms', 0),
            'popularity': track.get('popularity', 0),
            'album_art': album.get('images', [{}])[0].get('url', '') if album.get('images') else '',
        }


def search_spotify(title: str, artist: str = '') -> Optional[dict]:
    """
    Convenience function to search for a track on Spotify.

    Args:
        title: Song title
        artist: Artist name (optional)

    Returns:
        dict with track info or None if not found
    """
    try:
        searcher = SpotifySearcher()
        return searcher.search_track(title, artist)
    except ValueError as e:
        print(f"Error: {e}")
        return None


if __name__ == '__main__':
    import sys
    from dotenv import load_dotenv

    load_dotenv()

    if len(sys.argv) > 1:
        title = sys.argv[1]
        artist = sys.argv[2] if len(sys.argv) > 2 else ''

        print(f"Searching for: {title}" + (f" by {artist}" if artist else ""))

        result = search_spotify(title, artist)
        if result:
            print(f"\nFound: {result['name']} by {result['artist']}")
            print(f"Album: {result['album']}")
            print(f"Spotify URL: {result['url']}")
        else:
            print("Track not found on Spotify")
    else:
        print("Usage: python spotify_search.py <title> [artist]")
