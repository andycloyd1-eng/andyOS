"""
Markdown File Manager

Manages a markdown file for storing saved songs with their Spotify links.
"""

import os
from datetime import datetime
from typing import List, Optional


class MarkdownManager:
    """Manages a markdown file for storing saved songs."""

    DEFAULT_FILE = 'saved_songs.md'

    def __init__(self, file_path: Optional[str] = None):
        """
        Initialize the markdown manager.

        Args:
            file_path: Path to the markdown file (default: saved_songs.md)
        """
        self.file_path = file_path or os.getenv('SONGS_FILE', self.DEFAULT_FILE)

        # Create file with header if it doesn't exist
        if not os.path.exists(self.file_path):
            self._create_file()

    def _create_file(self):
        """Create a new markdown file with a header."""
        header = f"""# Saved Songs from Instagram Reels

A collection of songs discovered from Instagram Reels, with Spotify links.

---

"""
        with open(self.file_path, 'w', encoding='utf-8') as f:
            f.write(header)

    def add_song(self, title: str, artist: str, spotify_url: str,
                 album: str = '', instagram_url: str = '', notes: str = '') -> bool:
        """
        Add a song to the markdown file.

        Args:
            title: Song title
            artist: Artist name
            spotify_url: Spotify URL for the song
            album: Album name (optional)
            instagram_url: Original Instagram Reel URL (optional)
            notes: Additional notes (optional)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if song already exists
            if self._song_exists(spotify_url):
                print(f"Song already saved: {title} by {artist}")
                return False

            # Build the entry
            entry = self._format_entry(title, artist, spotify_url, album, instagram_url, notes)

            # Append to file
            with open(self.file_path, 'a', encoding='utf-8') as f:
                f.write(entry)

            return True

        except Exception as e:
            print(f"Error saving song: {e}")
            return False

    def _format_entry(self, title: str, artist: str, spotify_url: str,
                      album: str = '', instagram_url: str = '', notes: str = '') -> str:
        """Format a song entry for the markdown file."""
        date = datetime.now().strftime('%Y-%m-%d')

        entry = f"""## {title}

- **Artist:** {artist}
"""

        if album:
            entry += f"- **Album:** {album}\n"

        entry += f"- **Spotify:** [{title} - {artist}]({spotify_url})\n"

        if instagram_url:
            entry += f"- **Source:** [Instagram Reel]({instagram_url})\n"

        entry += f"- **Added:** {date}\n"

        if notes:
            entry += f"- **Notes:** {notes}\n"

        entry += "\n---\n\n"

        return entry

    def _song_exists(self, spotify_url: str) -> bool:
        """Check if a song with the given Spotify URL already exists."""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                return spotify_url in content
        except FileNotFoundError:
            return False

    def get_all_songs(self) -> List[dict]:
        """
        Parse and return all songs from the markdown file.

        Returns:
            List of song dicts with 'title', 'artist', 'spotify_url', etc.
        """
        songs = []

        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Split by song entries (## headers)
            sections = content.split('\n## ')

            for section in sections[1:]:  # Skip the header section
                song = self._parse_section(section)
                if song:
                    songs.append(song)

        except FileNotFoundError:
            pass

        return songs

    def _parse_section(self, section: str) -> Optional[dict]:
        """Parse a song section from the markdown file."""
        lines = section.strip().split('\n')
        if not lines:
            return None

        song = {
            'title': lines[0].strip(),
            'artist': '',
            'album': '',
            'spotify_url': '',
            'instagram_url': '',
            'added': '',
            'notes': '',
        }

        for line in lines[1:]:
            line = line.strip()

            if line.startswith('- **Artist:**'):
                song['artist'] = line.replace('- **Artist:**', '').strip()
            elif line.startswith('- **Album:**'):
                song['album'] = line.replace('- **Album:**', '').strip()
            elif line.startswith('- **Spotify:**'):
                # Extract URL from markdown link
                import re
                match = re.search(r'\]\(([^)]+)\)', line)
                if match:
                    song['spotify_url'] = match.group(1)
            elif line.startswith('- **Source:**'):
                import re
                match = re.search(r'\]\(([^)]+)\)', line)
                if match:
                    song['instagram_url'] = match.group(1)
            elif line.startswith('- **Added:**'):
                song['added'] = line.replace('- **Added:**', '').strip()
            elif line.startswith('- **Notes:**'):
                song['notes'] = line.replace('- **Notes:**', '').strip()

        return song if song['title'] else None

    def get_song_count(self) -> int:
        """Get the number of songs saved."""
        return len(self.get_all_songs())

    def remove_song(self, spotify_url: str) -> bool:
        """
        Remove a song from the markdown file by its Spotify URL.

        Args:
            spotify_url: Spotify URL of the song to remove

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Find and remove the section containing this URL
            sections = content.split('\n## ')
            header = sections[0]
            new_sections = [header]

            removed = False
            for section in sections[1:]:
                if spotify_url not in section:
                    new_sections.append('## ' + section)
                else:
                    removed = True

            if removed:
                new_content = '\n'.join(new_sections)
                # Clean up extra newlines
                new_content = new_content.replace('\n\n\n', '\n\n')

                with open(self.file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)

            return removed

        except Exception as e:
            print(f"Error removing song: {e}")
            return False

    def export_playlist(self, output_file: str = 'playlist.txt') -> bool:
        """
        Export all Spotify URLs to a plain text file (for importing to Spotify).

        Args:
            output_file: Output file path

        Returns:
            True if successful, False otherwise
        """
        try:
            songs = self.get_all_songs()
            urls = [song['spotify_url'] for song in songs if song['spotify_url']]

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(urls))

            print(f"Exported {len(urls)} songs to {output_file}")
            return True

        except Exception as e:
            print(f"Error exporting playlist: {e}")
            return False


def save_song(title: str, artist: str, spotify_url: str, **kwargs) -> bool:
    """
    Convenience function to save a song to the markdown file.

    Args:
        title: Song title
        artist: Artist name
        spotify_url: Spotify URL
        **kwargs: Additional arguments (album, instagram_url, notes)

    Returns:
        True if successful, False otherwise
    """
    manager = MarkdownManager()
    return manager.add_song(title, artist, spotify_url, **kwargs)


if __name__ == '__main__':
    import sys

    manager = MarkdownManager()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == 'list':
            songs = manager.get_all_songs()
            print(f"\nSaved Songs ({len(songs)} total):\n")
            for i, song in enumerate(songs, 1):
                print(f"{i}. {song['title']} by {song['artist']}")
                print(f"   {song['spotify_url']}\n")

        elif command == 'export':
            output = sys.argv[2] if len(sys.argv) > 2 else 'playlist.txt'
            manager.export_playlist(output)

        elif command == 'count':
            print(f"Total songs saved: {manager.get_song_count()}")

        else:
            print(f"Unknown command: {command}")

    else:
        print("Usage:")
        print("  python markdown_manager.py list    - List all saved songs")
        print("  python markdown_manager.py count   - Show song count")
        print("  python markdown_manager.py export [file]  - Export Spotify URLs")
