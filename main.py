#!/usr/bin/env python3
"""
Instagram Reel to Spotify Extractor

Extract music from Instagram Reels and save Spotify links to a markdown file.

Usage:
    python main.py <instagram_reel_url>
    python main.py --interactive
    python main.py --list
    python main.py --export [filename]
"""

import sys
import os
import argparse
from dotenv import load_dotenv

from instagram_extractor import InstagramExtractor
from spotify_search import SpotifySearcher
from markdown_manager import MarkdownManager


class ReelToSpotify:
    """Main application class for extracting music from Instagram Reels."""

    def __init__(self):
        """Initialize the application."""
        load_dotenv()

        self.instagram = InstagramExtractor()
        self.markdown = MarkdownManager()
        self._spotify = None

    @property
    def spotify(self):
        """Lazy-load Spotify client."""
        if self._spotify is None:
            try:
                self._spotify = SpotifySearcher()
            except ValueError as e:
                print(f"\nError: {e}")
                print("\nTo use this app, you need Spotify API credentials.")
                print("1. Go to https://developer.spotify.com/dashboard")
                print("2. Create an app and get your Client ID and Client Secret")
                print("3. Copy .env.example to .env and fill in your credentials")
                print("\nOr set environment variables:")
                print("  export SPOTIFY_CLIENT_ID=your_client_id")
                print("  export SPOTIFY_CLIENT_SECRET=your_client_secret")
                sys.exit(1)
        return self._spotify

    def process_url(self, url: str, manual_title: str = None, manual_artist: str = None) -> bool:
        """
        Process an Instagram Reel URL to extract and save the song.

        Args:
            url: Instagram Reel URL
            manual_title: Manually provided song title (optional)
            manual_artist: Manually provided artist name (optional)

        Returns:
            True if successful, False otherwise
        """
        print(f"\n{'='*60}")
        print(f"Processing: {url}")
        print('='*60)

        # Step 1: Extract music info from Instagram
        if manual_title:
            print(f"\nUsing manual input: {manual_title}" + (f" by {manual_artist}" if manual_artist else ""))
            music_info = {'title': manual_title, 'artist': manual_artist or ''}
        else:
            print("\n[1/3] Extracting music info from Instagram Reel...")
            music_info = self.instagram.get_music_info(url)

            if not music_info:
                print("\nCould not automatically extract music info from the Reel.")
                print("This might happen if:")
                print("  - The Reel uses original audio instead of a song")
                print("  - Instagram's page structure has changed")
                print("  - The Reel is private or unavailable")

                # Ask for manual input
                if self._confirm("\nWould you like to enter the song info manually?"):
                    title = input("Enter song title: ").strip()
                    artist = input("Enter artist name (optional): ").strip()
                    if title:
                        music_info = {'title': title, 'artist': artist}
                    else:
                        print("No title provided. Skipping.")
                        return False
                else:
                    return False

        print(f"\nFound: {music_info['title']}" + (f" by {music_info['artist']}" if music_info.get('artist') else ""))

        # Step 2: Search for the song on Spotify
        print("\n[2/3] Searching for song on Spotify...")
        spotify_track = self.spotify.search_track(
            music_info['title'],
            music_info.get('artist', '')
        )

        if not spotify_track:
            print(f"\nCould not find '{music_info['title']}' on Spotify.")

            # Try searching with alternative terms
            if self._confirm("Would you like to search with different terms?"):
                title = input("Enter search title: ").strip()
                artist = input("Enter artist (optional): ").strip()

                spotify_track = self.spotify.search_track(title, artist)

                if not spotify_track:
                    print("Still could not find the track. Skipping.")
                    return False
            else:
                return False

        print(f"\nSpotify Match:")
        print(f"  Title:  {spotify_track['name']}")
        print(f"  Artist: {spotify_track['artist']}")
        print(f"  Album:  {spotify_track['album']}")
        print(f"  URL:    {spotify_track['url']}")

        # Confirm if the match looks correct
        if not self._confirm("\nIs this the correct song?", default=True):
            # Show alternative results
            print("\nSearching for alternatives...")
            alternatives = self.spotify.search_tracks(
                music_info['title'],
                music_info.get('artist', ''),
                limit=5
            )

            if len(alternatives) > 1:
                print("\nAlternative matches:")
                for i, track in enumerate(alternatives, 1):
                    print(f"  {i}. {track['name']} by {track['artist']} ({track['album']})")

                choice = input("\nSelect a number (or 's' to skip, 'm' for manual search): ").strip()

                if choice == 's':
                    return False
                elif choice == 'm':
                    title = input("Enter search title: ").strip()
                    artist = input("Enter artist (optional): ").strip()
                    spotify_track = self.spotify.search_track(title, artist)
                    if not spotify_track:
                        print("Could not find the track. Skipping.")
                        return False
                elif choice.isdigit() and 1 <= int(choice) <= len(alternatives):
                    spotify_track = alternatives[int(choice) - 1]
                else:
                    print("Invalid choice. Skipping.")
                    return False
            else:
                return False

        # Step 3: Save to markdown file
        print(f"\n[3/3] Saving to {self.markdown.file_path}...")

        success = self.markdown.add_song(
            title=spotify_track['name'],
            artist=spotify_track['artist'],
            spotify_url=spotify_track['url'],
            album=spotify_track['album'],
            instagram_url=url
        )

        if success:
            print(f"\nSaved: {spotify_track['name']} by {spotify_track['artist']}")
            print(f"Spotify: {spotify_track['url']}")
            return True
        else:
            print("\nSong was already saved or an error occurred.")
            return False

    def _confirm(self, message: str, default: bool = False) -> bool:
        """Ask for confirmation."""
        suffix = " [Y/n] " if default else " [y/N] "
        response = input(message + suffix).strip().lower()

        if not response:
            return default
        return response in ('y', 'yes')

    def interactive_mode(self):
        """Run in interactive mode, accepting URLs continuously."""
        print("\n" + "="*60)
        print("Instagram Reel to Spotify Extractor - Interactive Mode")
        print("="*60)
        print("\nPaste Instagram Reel URLs to extract music and save to Spotify.")
        print("Commands:")
        print("  list     - Show all saved songs")
        print("  count    - Show number of saved songs")
        print("  export   - Export Spotify URLs to a file")
        print("  quit/q   - Exit the program")
        print("\n")

        while True:
            try:
                user_input = input("Enter URL (or command): ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ('quit', 'q', 'exit'):
                    print("\nGoodbye!")
                    break

                if user_input.lower() == 'list':
                    self._list_songs()
                    continue

                if user_input.lower() == 'count':
                    count = self.markdown.get_song_count()
                    print(f"\nTotal songs saved: {count}\n")
                    continue

                if user_input.lower() == 'export':
                    filename = input("Export filename (default: playlist.txt): ").strip()
                    self.markdown.export_playlist(filename or 'playlist.txt')
                    continue

                # Check if it looks like an Instagram URL
                if 'instagram.com' in user_input:
                    self.process_url(user_input)
                else:
                    print("Please enter a valid Instagram URL or command.")

            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except EOFError:
                print("\n\nGoodbye!")
                break

    def _list_songs(self):
        """List all saved songs."""
        songs = self.markdown.get_all_songs()

        if not songs:
            print("\nNo songs saved yet.\n")
            return

        print(f"\n{'='*60}")
        print(f"Saved Songs ({len(songs)} total)")
        print('='*60)

        for i, song in enumerate(songs, 1):
            print(f"\n{i}. {song['title']}")
            print(f"   Artist: {song['artist']}")
            if song['album']:
                print(f"   Album:  {song['album']}")
            print(f"   Spotify: {song['spotify_url']}")
            if song['added']:
                print(f"   Added:  {song['added']}")

        print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Extract music from Instagram Reels and save Spotify links.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s https://www.instagram.com/reel/ABC123/
  %(prog)s --interactive
  %(prog)s --list
  %(prog)s --title "Song Name" --artist "Artist Name"
        """
    )

    parser.add_argument('url', nargs='?', help='Instagram Reel URL to process')
    parser.add_argument('-i', '--interactive', action='store_true',
                        help='Run in interactive mode')
    parser.add_argument('-l', '--list', action='store_true',
                        help='List all saved songs')
    parser.add_argument('-e', '--export', nargs='?', const='playlist.txt',
                        metavar='FILE', help='Export Spotify URLs to a file')
    parser.add_argument('-c', '--count', action='store_true',
                        help='Show number of saved songs')
    parser.add_argument('-t', '--title', help='Manually specify song title')
    parser.add_argument('-a', '--artist', help='Manually specify artist name')
    parser.add_argument('-f', '--file', help='Path to the markdown file for saving songs')

    args = parser.parse_args()

    # Initialize the app
    if args.file:
        os.environ['SONGS_FILE'] = args.file

    app = ReelToSpotify()

    # Handle different modes
    if args.list:
        app._list_songs()
        return

    if args.count:
        count = app.markdown.get_song_count()
        print(f"Total songs saved: {count}")
        return

    if args.export:
        app.markdown.export_playlist(args.export)
        return

    if args.interactive:
        app.interactive_mode()
        return

    if args.url:
        success = app.process_url(args.url, args.title, args.artist)
        sys.exit(0 if success else 1)

    if args.title:
        # Search by title/artist directly without Instagram URL
        print(f"\nSearching Spotify for: {args.title}" + (f" by {args.artist}" if args.artist else ""))
        track = app.spotify.search_track(args.title, args.artist or '')

        if track:
            print(f"\nFound: {track['name']} by {track['artist']}")
            print(f"Album: {track['album']}")
            print(f"URL: {track['url']}")

            if app._confirm("\nSave this song?", default=True):
                app.markdown.add_song(
                    title=track['name'],
                    artist=track['artist'],
                    spotify_url=track['url'],
                    album=track['album']
                )
                print("Saved!")
        else:
            print("Track not found on Spotify.")
        return

    # No arguments provided - show help
    parser.print_help()


if __name__ == '__main__':
    main()
