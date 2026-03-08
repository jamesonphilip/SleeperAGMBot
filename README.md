# Sleeper AGM Bot

A Streamlit web app that helps Dynasty fantasy football managers analyze their teams and make smarter decisions using AI-powered insights.

## Features

- **Team Roster Analysis** — View your starters and bench with dynasty rankings and estimated trade values
- **AI Team Analysis** — Get a full breakdown of your roster's strengths, weaknesses, and recommended actions
- **Waiver Wire Recommendations** — AI scans available free agents and surfaces the best pickups for your specific team needs
- **Dynasty Rankings** — Pulled live from FantasyPros
- **Rookie Tracking** — See which available players are rookies
- **League Info Dashboard** — View scoring settings and league configuration

## Requirements

- Python 3.9+
- A [Sleeper](https://sleeper.com) account
- A free [Google Gemini API key](https://aistudio.google.com/apikey)

## Setup

1. **Clone the repo**
   ```bash
   git clone https://github.com/jamesonphilip/SleeperAGMBot.git
   cd SleeperAGMBot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set your Gemini API key**
   ```bash
   cp .env.example .env
   # Edit .env and add your key
   export GEMINI_API_KEY=your_key_here
   ```

4. **Run the app**
   ```bash
   streamlit run app.py
   ```

## Usage

1. Enter your Sleeper username and the current NFL season year
2. Select your league from the dropdown
3. Browse your roster with dynasty rankings and trade values
4. Click **Run Full Team Analysis** for an AI-powered team assessment
5. Click **Analyze Waiver Wire** for personalized free agent recommendations

## API Keys

| Key | Required | Where to get it |
|-----|----------|-----------------|
| `GEMINI_API_KEY` | Yes | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) — free tier: 1,500 requests/day |

## Notes

- **Sleeper's API is read-only.** This app analyzes and recommends — you execute moves manually in Sleeper.
- Dynasty rankings and rookie lists are scraped live from FantasyPros. If their site is unreachable, rankings will be unavailable but the rest of the app still works.
- Gemini 2.0 Flash is used for AI analysis (free tier is sufficient for personal use).

## Tech Stack

- [Streamlit](https://streamlit.io) — UI framework
- [Sleeper API](https://docs.sleeper.com) — Fantasy football data
- [FantasyPros](https://www.fantasypros.com) — Dynasty rankings (scraped)
- [Google Gemini 2.0 Flash](https://aistudio.google.com) — AI analysis
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) — HTML parsing
