# RALF VPS Integration Guide

Complete guide for running the autonomous agent system on a VPS with self-verification and multi-agent coordination.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         YOUR VPS                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   PLANNER   │  │  EXECUTOR   │  │  VERIFIER   │             │
│  │             │  │             │  │             │             │
│  │ • Plans     │  │ • Executes  │  │ • Verifies  │             │
│  │ • Analyzes  │  │ • Commits   │  │ • Scores    │             │
│  │ • Prioritize│  │ • Reports   │  │ • Retests   │             │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘             │
│         │                │                │                    │
│         └────────────────┼────────────────┘                    │
│                          │                                     │
│                   ┌──────┴──────┐                              │
│                   │ Shared State │                              │
│                   │              │                              │
│                   │ • queue.yaml │                              │
│                   │ • events.yaml│                              │
│                   │ • verify.yaml│                              │
│                   └──────────────┘                              │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Verification Decision Flow                              │   │
│  │                                                          │   │
│  │  Executor completes ──> Verifier runs checks            │   │
│  │                              │                          │   │
│  │                              ▼                          │   │
│  │                    Calculate confidence                 │   │
│  │                              │                          │   │
│  │              ┌───────────────┼───────────────┐         │   │
│  │              ▼               ▼               ▼         │   │
│  │        ┌─────────┐    ┌─────────┐    ┌─────────┐      │   │
│  │        │ ≥ 0.85  │    │ 0.6-0.85│    │  < 0.6  │      │   │
│  │        │ AUTO    │    │ QUEUE   │    │ HUMAN   │      │   │
│  │        │ COMMIT  │    │ REVIEW  │    │ REVIEW  │      │   │
│  │        └─────────┘    └─────────┘    └─────────┘      │   │
│  │                                                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### 1. VPS Requirements

- Ubuntu 22.04 LTS (recommended)
- 4GB+ RAM (8GB preferred)
- 20GB+ disk space
- Docker & Docker Compose installed

### 2. Deploy

```bash
# Clone repository
git clone https://github.com/yourusername/blackbox5.git
cd blackbox5/2-engine/.autonomous/vps-deployment

# Configure environment
cp .env.example .env
vim .env  # Add your API keys

# Deploy
chmod +x deploy.sh
sudo ./deploy.sh
```

### 3. Verify

```bash
# Check services
docker-compose ps

# View logs
docker-compose logs -f planner
docker-compose logs -f executor
docker-compose logs -f verifier

# Check API
curl http://localhost:8000/health
```

---

## How It Works

### Agent Coordination

1. **Planner** (every 30s):
   - Checks queue depth
   - Creates new tasks if needed
   - Updates `queue.yaml`

2. **Executor** (every 30s):
   - Reads `queue.yaml` for pending tasks
   - Claims task (updates status)
   - Executes using Claude Code CLI
   - Writes completion to `events.yaml`

3. **Verifier** (event-driven):
   - Watches `events.yaml` for completions
   - Runs verification suite
   - Calculates confidence score
   - Decides action based on thresholds

### Verification Scoring

| Check | Weight | Description |
|-------|--------|-------------|
| File existence | 20% | Claimed files exist |
| Code imports | 15% | Python/JS imports work |
| Unit tests | 20% | Tests pass |
| Linting | 10% | No lint errors |
| Documentation | 20% | THOUGHTS.md, RESULTS.md exist |
| Git state | 15% | Clean working directory |

**Decision Matrix:**
- **≥ 0.85**: Auto-commit (safe and valuable)
- **0.60 - 0.85**: Queue for another agent review
- **< 0.60**: Escalate to human review

### Confidence-Based Actions

```bash
# Auto-commit (high confidence)
git add -A
git commit -m "ralf: [TASK-XXX] verified auto-commit"
git push

# Queue review (medium confidence)
echo "task_id: TASK-XXX" >> verify.yaml
echo "status: pending_review" >> verify.yaml

# Human review (low confidence)
echo "task_id: TASK-XXX" >> human-review.yaml
notify_webhook "Human review required"
```

---

## Integration with Claude Code Task System

### Local Development → VPS Sync

```
Local Machine                    VPS
─────────────                   ────
Claude Code ──git push──>  Webhook Receiver
    │                            │
    │                            ▼
    │                      Update queue.yaml
    │                            │
    │                            ▼
    │                      Agent picks up task
    │                            │
    │                            ▼
    │                      Execute & verify
    │                            │
    │                            ▼
    │                      git push results
    │                            │
    └────────<─────────────  Sync complete
```

### Task Flow Example

1. **Create task locally**:
   ```bash
   # Create task spec
   vim tasks/active/TASK-XXX/task.md

   # Add to queue
   ralf-planner-queue.sh --fill
   ```

2. **Push to VPS**:
   ```bash
   git add .
   git commit -m "Add TASK-XXX"
   git push origin main
   ```

3. **VPS agents execute**:
   - Executor claims task
   - Runs implementation
   - Verifier checks output
   - Auto-commits if confident

4. **Pull results locally**:
   ```bash
   git pull origin main
   # Review completed work
   ```

---

## GLM Integration

To use GLM instead of Claude on VPS:

### 1. Update .env

```bash
# Comment out Claude
# ANTHROPIC_API_KEY=...

# Use GLM
GLM_API_KEY=your_glm_key
GLM_API_BASE=https://api.glm.ai/v1
RALF_MODEL=glm-4.7
```

### 2. Update Agent Dockerfile

```dockerfile
# Install GLM client
RUN pip3 install glm-api-client
```

### 3. Update Agent Startup

```bash
# In start-agent.sh
case "$RALF_AGENT_TYPE" in
    executor)
        if [ "$RALF_MODEL" = "glm-4.7" ]; then
            glm-client --prompt ... --api-key $GLM_API_KEY
        else
            claude --prompt ...
        fi
        ;;
esac
```

---

## Monitoring

### Grafana Dashboards

Access at `http://your-vps:3000`

Default dashboards:
- Agent health
- Queue depth
- Verification scores
- Task throughput

### Prometheus Metrics

Access at `http://your-vps:9090`

Key metrics:
- `ralf_tasks_completed_total`
- `ralf_verification_score`
- `ralf_agent_uptime`
- `ralf_queue_depth`

### Alerts

Configure in `prometheus/alerts.yml`:

```yaml
groups:
  - name: ralf
    rules:
      - alert: AgentDown
        expr: ralf_agent_up == 0
        for: 5m

      - alert: QueueBacklog
        expr: ralf_queue_depth > 10
        for: 10m
```

---

## Troubleshooting

### Agents not starting

```bash
# Check logs
docker-compose logs planner
docker-compose logs executor

# Verify environment
docker-compose exec planner env | grep RALF

# Restart
docker-compose restart
```

### Verification always failing

```bash
# Check verifier logs
docker-compose logs verifier

# Test manually
docker-compose exec verifier /opt/ralf/bin/ralf-verifier.sh --verify TASK-XXX

# Adjust thresholds in .env
RALF_VERIFY_THRESHOLD_AUTO=0.75
RALF_VERIFY_THRESHOLD_REVIEW=0.50
```

### Git push failing

```bash
# Check git config
docker-compose exec executor git config --list

# Test manually
docker-compose exec executor git push origin main

# Check SSH keys (if using SSH)
docker-compose exec executor ssh -T git@github.com
```

---

## Security

### API Keys

- Store in `.env` file (never commit)
- Use Docker secrets for production
- Rotate keys monthly

### Git Access

- Use deploy keys (read-only for most agents)
- Executor needs write access
- Enable branch protection rules

### Network

- Use firewall (ufw) to restrict ports
- Nginx reverse proxy for SSL
- VPN for admin access

---

## Next Steps

1. **Deploy to VPS** using `deploy.sh`
2. **Create first task** and push to git
3. **Monitor execution** via Grafana
4. **Tune thresholds** based on results
5. **Add more agents** for parallel execution

---

## Files Reference

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Multi-service orchestration |
| `Dockerfile.agent` | Agent container image |
| `deploy.sh` | One-command deployment |
| `.env.example` | Configuration template |
| `bin/ralf-verifier.sh` | Verification logic |
| `prompts/verifier/verifier-v1.md` | Verifier agent prompt |
