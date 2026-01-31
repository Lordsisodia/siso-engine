# SearXNG Deployment for Blackbox5

One-click deployment of SearXNG metasearch engine for the web-search skill.

## Quick Deploy

### Option 1: Render (Recommended - Free Tier)

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/yourusername/searxng-render)

Or manual deploy:
1. Fork this repository
2. Create account on [Render](https://render.com)
3. Click "New +" → "Web Service"
4. Connect your forked repo
5. Select "Docker" runtime
6. Deploy

**Free Tier Limits:**
- 750 hours/month (enough for 24/7 operation)
- Sleeps after 15 min inactivity (wakes on next request)
- 512 MB RAM, 0.1 vCPU

### Option 2: Railway

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/your-template)

**Note:** Railway requires $5/month after 30-day trial.

### Option 3: Self-Hosted (Docker)

```bash
docker run -d \
  -p 8080:8080 \
  -v "$(pwd)/settings.yml":/etc/searxng/settings.yml \
  --name searxng \
  searxng/searxng:latest
```

## Configuration

After deployment:

1. Get your service URL (e.g., `https://blackbox5-search.onrender.com`)
2. Configure the CLI tool:
   ```bash
   web-search --setup
   # Enter your URL when prompted
   ```

Or set environment variable:
```bash
export WEB_SEARCH_URL="https://your-search.onrender.com"
```

## Testing

```bash
# Test the search endpoint
curl "https://your-search.onrender.com/search?q=test&format=json"

# Test via CLI
web-search "hello world"
```

## Troubleshooting

### "Service Unavailable" on Render
The free tier sleeps after 15 minutes. First request wakes it up (takes ~5 seconds).

To keep it awake, set up a ping service:
- [UptimeRobot](https://uptimerobot.com) (free)
- [Cron-Job.org](https://cron-job.org) (free)
- Ping every 10 minutes

### No Results
Check that search engines are enabled in `settings.yml`. Some engines may block cloud IPs.

### Slow Response
Normal for free tier. Consider upgrading to paid tier for always-on service.

## Files

- `Dockerfile` - Container definition
- `settings.yml` - SearXNG configuration
- `render.yaml` - Render blueprint

## Resources

- [SearXNG Documentation](https://docs.searxng.org)
- [SearXNG GitHub](https://github.com/searxng/searxng)
- [Blackbox5 Web Search Skill](../web-search.md)
