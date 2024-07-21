# Twitch Lurker Bot Hunter

<div align="center">

CURRENTLY IN DEVELOPMENT

| Issues and Milestones                    | Status |
| ---------------------------------------- | ------ |
| Base schema implemeneted                 | ✅     |
| Boilerplate nailed down                  | ✅     |
| Test routes working                      | ✅     |
| Twitch OAuth flow                        | ✅     |
| Step up OAuth to HTTPS                   | ✅     |
| Scan Conductor                           | ❌     |
| Stream Fetcher (multiproc, single proc)  | ❌     |
| Stream Viewer List Fetcher (multiproc)   | ❌     |
| User Data Enricher (multiproc)           | ❌     |
| Viewer Sightings Aggregator              | ❌     |
| Simplistic Classifier                    | ❌     |
| Collections metrics and visualizer       | ❌     |
| Reconsider schema needs and indexing     | ✅     |
| Documentation pass                       | ❌     |
| white list / ignore list (for good bots) | ❌     |
| Profiling                                | ❌     |
| Parallelization                          | ❌     |
| Get hard-coded config stuff into config. | ✅     |
| Unit tests                               | ✅     |

</div>

## Why am I doing this?

**Lurker Bots** are Twitch accounts which remain resident in thousands of chat channels across
Twitch for large spans of time, for a number of reasons including (but not limited to):

- quietly farming channelpoints, gift subs, or giveaways;
- collecting data on those channels and their chatters' discussions;
- "billboarding," i.e. serving as a passive advertisement, hoping the curious folks click,
  think they're cute, and subscribe, I guess.

While in some ways they're harmless, and some perhaps appreciate the padding on their viewer counts,
almost everyone I've spoken to about the topic finds them distasteful, creepy, frustrating, or all
three. Why doesn't Twitch do anything about these accounts? I have no idea. [One of their own said
in 2019 it was
"PLANNED"](https://twitch.uservoice.com/forums/933812-safety/suggestions/19429897-kick-unwanted-users-bots-from-channel-completely)
(note the question answered was posed in 2017) but in light of that, there are really only two
champions in the space addressing this issue in any capacity.

[Twitch Insights Bots](https://twitchinsights.net/bots) is everyone's favorite tool for bot identification: it does the job, why do we need another tool? The Twitch Insights used an endpoint that was removed, and now uses an undocumented endpoint to fetch the viewer list in one go. The developer of the project made an announcment on 4/20 (not a typo) about the potential loss of that undocumented endpoint, and the risks that posed to the developer's ability to maintain the bot i.d. feature if it's lost. This rattled me. I thought, if that goes away, what do we have?

I briefly looked at the remarkably few other sites that do this (both seems to depend on Twitch Insights) and the one open source project, [TwitchTV-Bots-List](https://github.com/arrowgent/Twitchtv-Bots-List) - which is also great and updates once a month - also seems to lean at least in part on Twitch Insights. So if we lose that, the jig is up.

So, it appears there are two humans with their hats in the ring. Here's mine. Maybe I can make a proper bot that does the grunt work for us. Maybe I can help?

Thus, I got fired up and, after a feverish back-of-the-napkin schema design on how I could do this, as well as some rough math on whether I could run this cheaply, I determined...honestly, I don't know. The only way to find out is to try and collect metrics on how well this performs, if it performs at all. It will be a fun project either way.

I'm [live streaming](https://twitch.tv/thadeshammer) portions of my development of this as well as answering questions about it, if you're curious.

## Project Overview

See the current data model [here](uml/lurker-bot-hunter%20data%20model.pdf).

This application will - within the 20 channel-joins per 10 seconds ratelimit - crawl over Twitch live streams to collect their publically available viewer lists via the IRC 353 messages, as well as publically available user data (but NOT their email addresses) to help identify lurker bots. Multiple methods will be used to fingerprint lurkerbots, including:

- aggregate viewer list data to identify accounts (by account id) who are concurrently in large numbers of live channels;
- account age;
- ratios between following and follower counts;
- has the account ever streamed before;
- (EVENTUALLY) comparisons of follower and following lists across suspect accounts.

This bot will not remain resident in channels, so it will be unable to track whether lurker bots speak or don't speak ever, or their specific entry and exit times; however we may estimate entry and exit times within some (potentially wide) margin of error depending on how frequently and quickly it can conduct scans. Nor will it request or record user emails from the Helix API.

The bot will also randomize when it performs as scan and what channels/categories are included in a given scan so as to be less predictable to those that wish to evade its detection.

The bot utilizes FastAPI, SQLModel, Docker, and Pydantic V2 to validate and manage data from Twitch. The project adheres to Twitch's TOS by using the Twitch IRC interface to scrape viewer lists manually without using undocumented endpoints or exceeding prescribed ratelimits.

There's a second app - a single file Flask servlet - whose only job is to take care of the Twitch OAuth flow and secure a token. I did this for the experience; it was painful because the fetch_token() method wasn't recognizing the access_token was in fact in the response, and this ate a couple of my hours. Unless you also want the experience, may I recommend you just use [Twitch Token Generator](https://twitchtokengenerator.com/) as needed. Or write a tiny Node.js app, that was way less painful.

## Frameworks

- **FastAPI**: Web framework used to create the backend API.
- **SQLModel**: ORM for interacting with the MySQL database.
- **Pydantic**: Data validation and settings management.
- **Twitch IRC Interface**: For collecting viewer lists in compliance with Twitch's TOS.
- **Twitch Helix API**: For collecting additional data on viewers and channels.

## Supporting Apps

- **Docker**: Containerization for easy deployment and management.
- **Redis**: Simple caching for viewer-list fetching and async safe data sharing between processes.

## Features

- **Parallel Processing**: Will be using using Python coroutines and multiprocesses.

## Regarding foundational tech choices

- **Why Python?**: Python as an ecosystem and community has a lot of well documented and maintained projects that are useful in data analysis. In addition, I wanted to use Python because I want to keep my Python skills sharp in the current market. And I happen to enjoy Python. Mostly.
- **Why FastAPI?**: I tried Flask (because several twitch-api Python modules I came across that seem to be geared towards Flask) but I wasn't able to jury rig it to be happy with async in a way that satisfied. FastAPI is just easier and will allow me to grow the app out to allow others to interface with it some day. Maybe.
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
   git clone https://github.com/yourusername/twitchbotfinder.git
   cd twitchbotfinder
   ```

2. **Set up the Docker environment**:
   Ensure you have Docker and Docker Compose installed on your machine. The provided `docker-compose.yaml` will handle the setup of the MySQL database and the Flask application. You'll need to make your own self-signed cert, and get your own Twitch Developer client secret and client id. Put them in /secrets at the same level as /app (or modify the docker-compose accordingly) and inject your cert passkey into docker.

   Note that the twitch-oauth.py servlet script for the Twitch Oauth will need the bot to be up and running so it can pass the tokens to it via its API; they're short-lived and will be kept in the secrets table in MySQL, so they can be easily shared accross services if I scale out horizontally later in the project. Also, so they can be used after an app restart, which happens frequenty during development.

3. **Start the Docker containers**:

   ```bash
   docker-compose up --build
   ```

4. **Check the logs**:
   To verify everything is running correctly, you can check the logs:

   ```bash
   docker-compose logs
   ```

5. **Authenticate with Twitch using twitch-oauth.py**:
   Run twitch-oauth.py in your local. For me it runs in Windows, you may need to make slight adjustments if you're doing development in a better OS.

### Configuration

- **Database Configuration**:
  The database configuration is managed through environment variables set in the `docker-compose.yaml`.

- **Logging Configuration**:
  Logging is configured through `logging_config.yaml`. Logs are written to both standard error and `server.log`. **NOTE** This is currently busted, repairs are my next step. We gotta have logging.

## Usage

IN DEVELOPMENT, usage is limited.

See **/docs** for existing endpoints, summarized below.

### API Endpoints

- **GET /healthcheck**: Confirms the server is in fact up.
- **POST /store_token**: Receiver for a token from the twitch-oauth servlet.
- **GET /streams:** proof-of-concept, fetches the first page of a 'Get Streams' request. Requires Oauth flow success prior.
- **GET /user/\{username\}:** fetches a single user profile. Requires Oauth flow success prior.
- **POST /fetch_viewer_list**: Pull viewer list from specified channel. (Not implemented.)
- **POST /start_scan**: Start a scanning session of a set of live streams. (Not implemented.)

### Data Model

The bot uses SQLAlchemy models to define the database schema, including tables for Twitch user data, sightings, and suspects. Data validation will be performed using Pydantic models.

## Future Plans

- Implementing parallel processing using Python asyncio coroutines and multiprocesses.
- Potentially splitting the project into microservices for better scalability.
- Enhancing data analysis and reporting capabilities.
- Applying to Twitch to become a verified bot, increasing my rate limit by two orders of magnitude.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Acknowledgments

Special thanks to:

- [AlphaDuplo](https://twitch.tv/alphaduplo) for maintaining Twitch Insights Bot list. Everyone I know uses it when they're trying to boot lurker bots out of their chats.
- The [Twitchtv-Bots-List project](https://github.com/arrowgent/Twitchtv-Bots-List) for their profound efforts in the space.
