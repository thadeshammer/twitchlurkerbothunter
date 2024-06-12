# Twitch Lurker Bot Recon Bot

<div align="center">

CURRENTLY IN DEVELOPMENT

| Issues and Milestones                    | Status |
| ---------------------------------------- | ------ |
| Base schema implemeneted                 | ✅     |
| Boilerplate nailed down                  | ✅     |
| Test routes working                      | ✅     |
| Twitch OAuth flow                        | ✅     |
| Viewer list fetch for target channel     | ❌     |
| Crawl the streams.                       | ❌     |
| Collections metrics and visualizer       | ❌     |
| Documentation pass                       | ❌     |
| white list / ignore list (for good bots) | ❌     |
| ignore list for channels that opt-out    | ❌     |
| Profiling (Consider a db table for it.)  | ❌     |
| Parallelization                          | ❌     |
| Get hard-coded config stuff into config. | ❌     |
| Unit tests                               | ❌     |

</div>

## Why am I doing this?

**Lurker Bots** are Twitch accounts which remain resident in thousands of chat channels across Twitch for large spans of time, either to quietly collect data on those channels and their discussions, or simply to serve as a passive advertisement. They're hoping the curious folks click, think they're cute, and subscribe, I guess. While in some ways they're harmless, and some perhaps appreciate the padding on their viewer counts, almost everyone I've spoken to about the topic finds them distasteful, creepy, frustrating, or all three. Why doesn't Twitch do anything about these accounts? I have no idea, but in light of that, there are really only two champions in the space addressing this issue in any capacity.

[Twitch Insights Bots](https://twitchinsights.net/bots) is everyone's favorite tool for bot identification: it does the job, why do we need another tool? The Twitch Insights used an endpoint that was removed, and now uses an undocumented endpoint to fetch the viewer list in one go. The developer of the project made an announcment on 4/20 (not a typo) about the potential loss of that undocumented endpoint, and the risks that posed to the developer's ability to maintain the bot i.d. feature if it's lost. This rattled me. I thought, if that goes away, what do we have?

I briefly looked at the remarkably few other sites that do this (both seems to depend on Twitch Insights) and the one open source project, [TwitchTV-Bots-List](https://github.com/arrowgent/Twitchtv-Bots-List) - which is also great and updates once a month - also seems to lean at least in part on Twitch Insights. So if we lose that, the jig is up.

So, there's two humans with their hats in the ring. Here's mine. Maybe I can make a proper bot that does the grunt work for us. Maybe I can help?

Thus, I got fired up and, after a feverish back-of-the-napkin schema design on how I could do this, as well as some rough math on whether I could run this cheaply, I determined...honestly, I don't know. The only way to find out is to try and collect metrics on how well this performs, if it performs at all. It will be a fun project either way.

I'm [live streaming](https://twitch.tv/thadeshammer) portions of my development of this as well as answering questions about it, if you're curious.

## Project Overview

This application will - within the 20 channel-joins per 10 seconds ratelimit - crawl over Twitch live streams to collect their publically available viewer lists and publically available user data to help identify lurker bots. Multiple methods will be used to fingerprint lurkerbots, including:

- aggregate viewer list data to identify accounts (by account id) who are concurrently in large numbers of live channels;
- account age;
- ratios between following and follower counts;
- comparisons of follower and following lists across suspect accounts.

This bot will not remain resident in channels, so it will be unable to track whether lurker bots speak vs. don't speak ever, or their specific entry and exit times; however we may estimate entry and exit times within some (potentially wide) margin of error depending on how frequently it can conduct scans.

The bot will also randomize when it performs as sweep and what channels are included in a given sweep so as to be less predictable to those that wish to evade its detection.

The bot utilizes Flask, SQLAlchemy, Docker, and Pydantic to validate and manage data from Twitch. The project adheres to Twitch's TOS by using the Twitch IRC interface to scrape viewer lists manually without using undocumented endpoints or exceeding prescribed ratelimits.

There's a second app - a single file Flask servlet - whose only job is to take care of the Twitch OAuth flow and secure a token. I did this for the experience; it was painful because the fetch_token() method wasn't recognizing the access_token was in fact in the response, and this ate a couple of my hours. Unless you also want the experience, may I recommend you just use [Twitch Token Generator](https://twitchtokengenerator.com/) as needed.

## Frameworks and Features

- **Flask**: Web framework used to create the backend API.
- **SQLAlchemy**: ORM for interacting with the MySQL database.
- **Docker**: Containerization for easy deployment and management.
- **Pydantic**: Data validation and settings management.
- **Twitch IRC Interface**: For collecting viewer lists in compliance with Twitch's TOS.
- **Twitch Helix API**: To query for live streams to include in the sweep.
- **Parallel Processing**: Considering using Python coroutines, multiprocesses, or microservices for parallelizing tasks.

## Regarding foundational tech choices

- **Why Python?**: Python as an ecosystem and community has a lot of well documented and maintained projects that are useful in data analysis. In addition, I wanted to use Python because I want to keep my Python skills sharp in the current market. And I happen to enjoy Python. Mostly.
- **Why Flask?**: There are several twitch-api Python modules I came across that seem to be geared towards Flask, which is in part why we're here. In addition, I wanted recent work with Flask since it's been a year since I've used it, and this is my first time setting up a Flask app from the studs, which was a valuable if painful experience.
- **Why not JavaScript?**: The honest answer is, I already have a JS project in-flight right now and wanted a balance. The availability of stats analysis tools in Python was also important, but was secondary.
- **Why not Rust?**: I will no doubt continue asking myself this question as the project goes on.

## Getting Started

This is very, very early development, so if you fork it, you're really just getting the preliminary data schemas and some boilerplate. I hope it serves you well.

### Prerequisites

- Docker + Docker Compose
- Python 3.11+ (See requirements.txt for additional details)
- A Twitch account with your own client id and secret if you want to fork it.

### Installation

1. **Clone the repository**:

   ```bash
   git clone https://github.com/yourusername/twitch-lurker-bot-recon.git
   cd twitch-lurker-bot-recon
   ```

2. **Set up the Docker environment**:
   Ensure you have Docker and Docker Compose installed on your machine. The provided `docker-compose.yaml` will handle the setup of the MySQL database and the Flask application.

3. **Start the Docker containers**:

   ```bash
   docker-compose up --build
   ```

4. **Check the logs**:
   To verify everything is running correctly, you can check the logs:

   ```bash
   docker-compose logs
   ```

### Configuration

- **Database Configuration**:
  The database configuration is managed through environment variables set in the `docker-compose.yaml`.

- **Logging Configuration**:
  Logging is configured through `logging_config.yaml`. Logs are written to both standard error and `server.log`. **NOTE** This is currently busted, repairs are my next step. We gotta have logging.

## Usage

Currently, the bot doesn't do anything beyond standing up and creating the tables if they don't exist yet. Stay tuned.

### API Endpoints

- **GET /**: Returns a summary of collected user data.
- **GET /test**: Confirms the server is in fact up.
- **POST /store_token**: Receiver for a token from the twitch-oauth servlet. (Stub.)
- **POST /scan_channel**: Pull viewer list from specified channel. (Not implemented.)
- **POST /start_sweep**: Sweep live streams. (Not implemented.)
- **POST /add_user**: Adds a new user to the database.
- **POST /add_observation**: Adds a new observation to the database.

### Data Model

The bot uses SQLAlchemy models to define the database schema, including tables for Twitch user data, observations, and suspects. Data validation will be performed using Pydantic models.

## Future Plans

- Implementing parallel processing using Python coroutines or multiprocesses.
- Potentially splitting the project into microservices for better scalability.
- Enhancing data analysis and reporting capabilities.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Acknowledgments

Special thanks to:

- [AlphaDuplo](https://twitch.tv/alphaduplo) for maintaining Twitch Insights Bot list. Everyone I know uses it when they're trying to boot lurker bots out of their chats.
- The [Twitchtv-Bots-List project](https://github.com/arrowgent/Twitchtv-Bots-List) for their profound efforts in the space.
