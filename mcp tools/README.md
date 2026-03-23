# Obsidian MCP Tools

Connects an Obsidian vault to Open WebUI via MCP, allowing AI models to read and search your notes.

## Architecture

```
Open WebUI → mcpo (port 8000) → mcp-obsidian → Obsidian Local REST API
```

- **mcp-obsidian** — MCP server that wraps the Obsidian REST API
- **mcpo** — Translates MCP tools into an OpenAPI endpoint Open WebUI can call

## Prerequisites

- Docker Desktop
- Obsidian with the [Local REST API](https://github.com/coddingtonbear/obsidian-local-rest-api) community plugin enabled
- Open WebUI running separately

## Setup

1. Copy your API key from Obsidian → Settings → Community Plugins → Local REST API

2. Set it in `docker-compose.yml`:
   ```yaml
   - OBSIDIAN_API_KEY=your_key_here
   ```

3. Start the stack:
   ```bash
   docker compose up -d
   ```

4. In Open WebUI, add a tool server at:
   ```
   http://host.docker.internal:8000/obsidian
   ```

## Files

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Service definitions |
| `config.json` | mcpo server routing config |
| `obsidian.py` | Patched Obsidian client — adds env var support for host/port/protocol |

## Notes

- `obsidian.py` patches the upstream image to respect `OBSIDIAN_HOST`, `OBSIDIAN_PORT`, and `OBSIDIAN_PROTOCOL` env vars (the original hardcodes `127.0.0.1:27124`)
- SSL verification is disabled by default (required for Obsidian's self-signed cert)
