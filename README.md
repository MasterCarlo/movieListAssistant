# Movie List Assistant

A task-oriented dialogue system that helps users manage personal movie watchlists through natural language conversation.

## Overview

Movie List Assistant leverages **Large Language Models (LLMs)** to understand user requests and generate natural responses. It integrates with the **TMDb API** to provide real movie information.

## Features

- **Create** new movie/series watchlists
- **Modify** lists (add/remove movies, rename, delete)
- **View** list contents
- **Query movie info**: cast, director, year, genre, ratings, plot, duration
- **Multi-intent handling**: process multiple requests in a single message
- **Context-aware**: remembers conversation history

## Architecture

```
User Input → NLU → DST → DM → NLG → Response
                    ↓
              TMDb API + List Database
```

| Component | File | Description |
|-----------|------|-------------|
| NLU | `natural_language_understander.py` | Intent classification & slot filling |
| DST | `dialogue_state_tracker.py` | Conversation context management |
| DM | `dialogue_manager.py` | Action selection & dialogue flow |
| NLG | `natural_language_generator.py` | Response generation |
| Actions | `actions.py` | Business logic execution |
| API | `tmdb_api.py` | TMDb integration |

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set TMDb API key (get one at themoviedb.org)
export TMDB_API_KEY=your_api_key

# Run
python "main.py"
```
If the DEBUG variable in global_variables.py is set to True, the system doesn't start the LLM, and the LLM role is taken by you. In addition, a lot of values are printed during execution to ease the debug process. If the variable DEBUG_LLM is set to True, the LLM starts and the values are printed as with DEBUG. To see the instruction passed to the LLM, after setting DEBUG_LLM to True uncomment print("Instruction sent to LLM:", instruction), line 38 of utils.py.

## Example Dialogue

```
🤖: Hi! I can help you manage movie lists. What would you like to do?

👤: Create a list called "Sci-Fi Favorites" and add The Matrix to it.

🤖: Created 'Sci-Fi Favorites'. Added 'The Matrix' to the list.

👤: What year did Inception come out?

🤖: Inception was released in 2010 and directed by Christopher Nolan.
```

## Requirements

- Python 3.x
- `requests` library
- TMDb API key

