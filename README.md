## Overview

This project provides a YouTube channel scraping tool that collects:
- Channel metadata
- Long-form videos
- YouTube Shorts

The scraper uses Selenium for browser automation and SQLite for storage.  
Duplicate videos or shorts are skipped automatically using database checks.

---

## Features

- Scrapes:
  - Channel details
  - All uploaded videos
  - All shorts
- Saves all data into an SQLite database
- Detects duplicate videos/shorts and skips them
- Uses `INSERT OR REPLACE` for channel records
- Modular database wrapper (`db.py`)

---

## Folder Structure

```
project/
│
├── scraper.py        # Main scraper logic
├── db.py             # Database functions and schema
├── youtube.db        # SQLite database (auto-created)
└── README.docx       # This file
```

---

## Requirements

Install dependencies:

```
pip install -r requirements.txt
```

WebDriver requirement:

- Chrome browser
- Matching ChromeDriver version

---

## How It Works

### 1. Initialize Database
Tables for channels, videos and shorts are created automatically.

### 2. Scrape Channel Metadata
Extracts:
- Country
- Join date
- Subscribers
- Number of videos
- Total views

### 3. Scrape Videos
Loads channel `/videos` tab and scrolls to the bottom.  
For each video:
- Extracts ID, title, description, views, likes, comments
- Skips if video ID already exists in the DB

### 4. Scrape Shorts
Same as videos but from `/shorts` tab.

---

## Running the Scraper

Edit the channel URL in `scraper.py`:

```
URL = "https://www.youtube.com/@channelname"
```

Run:

```
python scraper.py
```

Data will be stored in `youtube.db`.

---

## Database Schema

### `channels`
| Field | Type | Notes |
|-------|------|--------|
| channel_id | TEXT | Primary Key |
| url | TEXT |  |
| country | TEXT |  |
| joined | TEXT |  |
| subscribers | TEXT |  |
| video_count | TEXT |  |
| views | TEXT |  |

### `videos`
| Field | Type |
|-------|------|
| video_id | TEXT PRIMARY KEY |
| channel_id | TEXT |
| url | TEXT |
| title | TEXT |
| published | TEXT |
| views | TEXT |
| likes | TEXT |
| comments | TEXT |
| description | TEXT |
| type | TEXT |

### `shorts`
Same structure as videos but for shorts.

---

## Duplicate Handling

Before scraping each video or short, the scraper checks:

```
video_exists(video_id)
short_exists(short_id)
```

If found, scraping is skipped.

---

## Notes

- Heavy scrolling may require tuning of sleep delays.
- You may use headless mode by uncommenting Chromium flags.
- Ensure ChromeDriver version matches your installed Chrome browser.

---

## License

Free to use and modify.

