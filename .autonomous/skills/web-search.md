# Skill: Web Search

**Purpose:** Search the web for real-time information using SearXNG metasearch engine
**Trigger:** Need current information, research, fact-checking, or data not in training
**Input:** Search query (string), optional: number of results, safe search level
**Output:** Structured search results with titles, URLs, and snippets

## Overview

This skill enables agents to search the web for up-to-date information using a self-hosted SearXNG instance. SearXNG aggregates results from multiple search engines (Google, Bing, DuckDuckGo, etc.) without tracking or ads.

## Prerequisites

1. SearXNG instance deployed (see Setup section)
2. `WEB_SEARCH_URL` environment variable set, or
3. Config file at `~/.config/blackbox5/web-search.conf`

## Setup

### Option 1: Deploy on Render (Free Tier)

1. Fork the SearXNG deployment template
2. Connect to Render (free tier: 750 hours/month)
3. Get your service URL: `https://your-search.onrender.com`
4. Set the URL in your environment or config

### Option 2: Deploy on Railway

1. Use the Railway template
2. Note: Requires $5/month after 30-day trial

### Configuration

```bash
# Environment variable
export WEB_SEARCH_URL="https://your-search.onrender.com"

# Or create config file
mkdir -p ~/.config/blackbox5
echo "WEB_SEARCH_URL=https://your-search.onrender.com" > ~/.config/blackbox5/web-search.conf
```

## Commands

| Command | Description | Usage |
|---------|-------------|-------|
| `web-search` | Search the web | `web-search "query here"` |
| `web-search --json` | Output JSON | `web-search "query" --json` |
| `web-search --count 10` | Get 10 results | `web-search "query" --count 10` |

## Procedure

### Basic Search

1. Formulate a clear, specific search query
2. Run: `web-search "your query here"`
3. Review results
4. Use `web-fetch` to retrieve full content from promising URLs

### Research Workflow

1. **Initial search**: `web-search "topic overview"`
2. **Refine query**: Based on initial results, narrow the search
3. **Deep dive**: Use `web-fetch` on 3-5 most relevant URLs
4. **Synthesize**: Combine information into findings

### Example Usage

```bash
# Search for latest React patterns
web-search "React 19 patterns 2025"

# Search with more results
web-search "best vector databases" --count 10

# Get structured JSON output
web-search "MCP server examples" --json

# Fetch full content from a result
web-fetch "https://example.com/article"
```

## Output Format

### Default (Human-readable)
```
1. Title of First Result
   URL: https://example.com/page1
   Snippet: Description of the page content...

2. Title of Second Result
   URL: https://example.com/page2
   Snippet: Description of the page content...
```

### JSON (--json flag)
```json
{
  "query": "search query",
  "results": [
    {
      "title": "Result Title",
      "url": "https://example.com",
      "snippet": "Description...",
      "engine": "google"
    }
  ]
}
```

## Verification

- [ ] SearXNG instance is accessible
- [ ] Search returns results
- [ ] Results include titles, URLs, and snippets
- [ ] JSON output is valid (when using --json)

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "No search URL configured" | Set WEB_SEARCH_URL env var or config file |
| "Connection timeout" | SearXNG instance may be sleeping (Render free tier). Retry after 10 seconds |
| "No results" | Try a different query or check SearXNG instance health |
| Rate limited | Wait 1 second between requests |

## Integration with Other Skills

- **bmad-analyst**: Use for research tasks (RS command)
- **deep-research**: Use as a source in research plans
- **web-fetch**: Combine to get full page content from search results

## Notes

- Free tier instances (Render) sleep after 15 min inactivity
- First request after sleep takes ~5 seconds to wake up
- SearXNG respects robots.txt and may not return results from all sites
- For production use, consider upgrading to paid tier for always-on service
