# TripMate AI

TripMate AI is a web-based travel planner powered by a LangGraph multi-agent workflow. Describe a trip in natural language, review the generated draft, and approve it or request changes before the system produces a final plan.

The application combines a FastAPI web app, a browser interface, LLM-based planning agents, external travel and weather tools exposed through Model Context Protocol (MCP), and PostgreSQL-backed workflow checkpoints.

## Features

- **Travel request routing:** a supervisor interprets the request and selects relevant specialist agents.
- **Input guardrail:** checks whether a request is travel-related before planning.
- **Flight research:** queries AviationStack MCP tools.
- **Hotel and web research:** searches the web using Tavily MCP.
- **Weather information:** retrieves current weather and forecast data with a local OpenWeather MCP server.
- **Budget analysis and itinerary planning:** creates an integrated, budget-aware draft.
- **Human review:** pause the workflow to approve the draft or provide revision feedback.
- **Persistent conversations:** LangGraph checkpoints workflow state in PostgreSQL and uses a thread ID to resume a plan.
- **Web interface:** submit prompts, see the agents selected, review results, copy the plan, or download it as a PDF.
- **HTTP API and health endpoint:** use the planner from the included UI or another client.

Travel search results and generated plans are informational. Verify schedules, prices, availability, entry requirements, and other details with the relevant provider before booking.

## How it works

1. The browser sends a travel prompt to `POST /api/travel`.
2. The supervisor checks the prompt and chooses among flight, hotel, weather, budget, and itinerary agents.
3. Selected agents gather information through the MCP client and produce specialist results.
4. The itinerary agent combines the results into a draft. LangGraph checkpoints the workflow and pauses for human review.
5. The UI sends approval or revision feedback to `POST /api/travel/approve` with the same thread ID.
6. The workflow resumes and returns the final response.

## Technology

- Python 3.11 (the supplied Docker image uses Python 3.11)
- FastAPI, Uvicorn, and Jinja2
- LangGraph, LangChain, and Groq
- PostgreSQL with Psycopg and the LangGraph PostgreSQL checkpointer
- Tavily MCP, AviationStack MCP, and a local OpenWeather MCP server
- HTML, CSS, and JavaScript frontend

## Repository layout

```text
.
├── app.py                     # FastAPI app, web page, and API endpoints
├── backend.py                 # LangGraph state, agents, routing, and persistence
├── mcp_client.py              # LLM setup and external/local MCP tool clients
├── custom_weather_mcp_server.py # OpenWeather MCP tool server
├── utils/                     # MCP transport/session compatibility helpers
├── templates/index.html       # Planner page
├── static/                    # Frontend CSS, JavaScript, and images
├── assets/                    # Additional static assets
├── requirements.txt           # Python dependencies
├── dockerfile                 # Container build and Uvicorn command
└── .dockerignore
```

## Requirements

- Python 3.11 or newer
- A PostgreSQL database reachable by the application
- API credentials for Groq, Tavily, AviationStack, and OpenWeather
- Node.js and `uvx` available on `PATH` for the AviationStack MCP server (`uvx` is provided by `uv`)
- Internet access for the external model and travel/weather services

The Dockerfile installs the Python dependencies, but it does not install Node.js or `uv`/`uvx`. If running in a container, provide those executables in the image/runtime for the AviationStack MCP server, or adapt that server configuration to your deployment environment.

## Configuration

Create a `.env` file in the repository root. Keep this file private; it contains credentials and is excluded from version control.

```dotenv
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key
AVIATIONSTACK_API_KEY=your_aviationstack_api_key
OPENWEATHER_API_KEY=your_openweather_api_key
DATABASE_URL=postgresql://username:password@hostname:5432/database_name
```

`DATABASE_URL` must point to a PostgreSQL database. The application adds `sslmode=require` when the URL does not specify an `sslmode` parameter. `GROQ_API_KEY` and `DATABASE_URL` are required at backend startup; the corresponding services and credentials are also needed for their agents to work. The AviationStack MCP subprocess receives `AVIATIONSTACK_API_KEY` from the environment. The Tavily API key is used to configure the hosted Tavily MCP endpoint.

Do not commit real API keys, database passwords, or production environment files. Configure secrets through your hosting provider's environment settings when deployed.

## Run locally

### 1. Create and activate a virtual environment

PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies and MCP prerequisites

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Install Node.js and `uv` separately, and make sure the `node` and `uvx` commands resolve in the same environment that runs the app. `mcp_client.py` starts the AviationStack server with `uvx aviationstack-mcp` and starts the weather server with the current Python interpreter.

### 3. Configure services

Create the root `.env` file using the variables above. Start or provision PostgreSQL and confirm the database URL is reachable from the machine running TripMate AI.

### 4. Start the web app

```bash
python app.py
```

Open [http://localhost:8000](http://localhost:8000). The app binds to `0.0.0.0` and uses the `PORT` environment variable when set (default: `8000`). For development with automatic reload, run:

```bash
uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

## Docker

Build and run from the repository root:

```bash
docker build -f dockerfile -t tripmate-ai .
docker run --rm -p 8000:8000 --env-file .env tripmate-ai
```

The container needs network access to PostgreSQL and the external APIs. As noted in Requirements, the supplied image does not install Node.js or `uvx`, both needed by the configured MCP subprocesses; add them to a deployment image before relying on the AviationStack integration.

## HTTP API

Interactive API documentation is available at `/docs` while the server is running.

### `GET /health`

Returns a basic application health response. It does not verify database connectivity or external API credentials.

### `POST /api/travel`

Starts a planning run. `thread_id` is optional; omit it to create a new conversation or provide an existing workflow thread ID to continue that run.

```json
{
  "message": "Plan a 5-day trip to Tokyo from Delhi for two people under $2500, including flights and hotels."
}
```

Example with curl:

```bash
curl -X POST http://localhost:8000/api/travel \
  -H "Content-Type: application/json" \
  -d '{"message":"Plan a 5-day trip to Tokyo from Delhi for two people under $2500."}'
```

The JSON response includes `success`, `thread_id`, the agent/workflow results, and approval fields such as `requires_approval` and `approval_request`. Keep the returned thread ID for the review request.

### `POST /api/travel/approve`

Resumes a paused plan. Set `approved` to `true` to accept the draft or `false` to request a revision; a revision requires non-empty `feedback`.

```json
{
  "thread_id": "THREAD_ID_FROM_TRAVEL_RESPONSE",
  "approved": false,
  "feedback": "Reduce hotel costs and include a slower-paced day."
}
```

To approve instead:

```json
{
  "thread_id": "THREAD_ID_FROM_TRAVEL_RESPONSE",
  "approved": true,
  "feedback": ""
}
```

## Troubleshooting

- **Missing `GROQ_API_KEY` or `DATABASE_URL`:** add them to `.env` for local runs or to the hosting environment configuration, then restart the app.
- **Database connection errors:** check the PostgreSQL hostname, credentials, network access, and SSL requirements. The graph initializes a PostgreSQL connection pool during backend startup.
- **MCP command not found:** install Node.js and `uv` and ensure `node` and `uvx` are on `PATH` for the app process.
- **Weather or search tool errors:** check the OpenWeather and Tavily credentials and whether the service is reachable.
- **A plan is waiting for review:** call `/api/travel/approve` with the original `thread_id`; a new thread will not resume the paused workflow.
- **Port binding on a hosting platform:** ensure the platform supplies `PORT`; `python app.py` reads it automatically. The Docker command currently uses port 8000.

## Contributing

1. Fork the repository and create a feature branch.
2. Make a focused change and update documentation where needed.
3. Run the application or relevant checks for your change.
4. Open a pull request describing the behavior and configuration impact.

## License

No license file is currently included. Unless the repository owner adds a license, the project should not be assumed to grant permissions beyond those provided by applicable law.
