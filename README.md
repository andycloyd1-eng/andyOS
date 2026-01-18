# Instagram Reel to Spotify Extractor

Extract music from Instagram Reels and save Spotify links to a markdown file.

## Features

- Extracts music information from Instagram Reels
- Searches Spotify for matching tracks
- Saves songs to a markdown file with:
  - Song title and artist
  - Album name
  - Spotify link
  - Original Instagram Reel link
  - Date added
- Interactive mode for processing multiple URLs
- Export functionality for creating Spotify playlists

## Installation

1. Clone this repository:
   ```bash
   git clone <repo-url>
   cd andyOS
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Set up Spotify API credentials:
   - Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
   - Create a new app
   - Copy your Client ID and Client Secret
   - Copy `.env.example` to `.env` and fill in your credentials:
     ```bash
     cp .env.example .env
     ```

## Usage

### Process a single Instagram Reel

```bash
python main.py https://www.instagram.com/reel/ABC123/
```

### Interactive mode

Run in interactive mode to process multiple URLs:

```bash
python main.py --interactive
# or
python main.py -i
```

In interactive mode, you can:
- Paste Instagram Reel URLs to extract music
- Type `list` to see all saved songs
- Type `count` to see the number of saved songs
- Type `export` to export Spotify URLs
- Type `quit` or `q` to exit

### List saved songs

```bash
python main.py --list
# or
python main.py -l
```

### Export Spotify URLs

Export all saved Spotify URLs to a text file (useful for creating playlists):

```bash
python main.py --export
# or specify a filename
python main.py --export my_playlist.txt
```

### Manual song search

If you know the song title and artist, you can search directly:

```bash
python main.py --title "Song Name" --artist "Artist Name"
```

### Use a custom markdown file

```bash
python main.py -f my_songs.md https://www.instagram.com/reel/ABC123/
```

## How It Works

1. **Instagram Extraction**: The app extracts music metadata from Instagram Reels by:
   - Parsing the page's embedded JSON data
   - Extracting music attribution information
   - Falls back to manual input if automatic extraction fails

2. **Spotify Search**: Uses the Spotify Web API to find matching tracks:
   - Searches by song title and artist
   - Uses fuzzy matching to find the best result
   - Shows alternatives if the first match isn't correct

3. **Markdown Storage**: Saves songs to a markdown file with all metadata:
   - Prevents duplicates by checking Spotify URLs
   - Includes timestamps for when songs were added

## Output Format

Songs are saved to `saved_songs.md` in this format:

```markdown
## Song Title

- **Artist:** Artist Name
- **Album:** Album Name
- **Spotify:** [Song Title - Artist Name](https://open.spotify.com/track/...)
- **Source:** [Instagram Reel](https://www.instagram.com/reel/...)
- **Added:** 2024-01-15

---
```

## Limitations

- Instagram doesn't provide a public API for music extraction, so the app uses web scraping which may break if Instagram changes their page structure
- Some Reels use original audio instead of licensed music, which cannot be matched on Spotify
- Private or restricted Reels cannot be accessed

## Troubleshooting

### "Could not extract music info"
- The Reel might use original audio instead of a licensed song
- Try entering the song info manually when prompted
- Instagram's page structure may have changed

### "Spotify credentials required"
- Make sure you've set up your `.env` file with valid Spotify API credentials
- Check that your credentials are correct in the Spotify Developer Dashboard

### "Track not found on Spotify"
- The song might not be available on Spotify
- Try searching with different terms or variations of the title/artist

## License

MIT
