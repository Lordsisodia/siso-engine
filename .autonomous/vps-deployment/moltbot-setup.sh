#!/bin/bash
# Moltbot (OpenClaw) Setup for RALF VPS
# Provides Discord bot for real-time RALF loop updates

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${BLUE}[MOLTBOT]${NC} $1"; }
success() { echo -e "${GREEN}[MOLTBOT]${NC} $1"; }
warn() { echo -e "${YELLOW}[MOLTBOT]${NC} $1"; }

MOLT_DIR="/opt/moltbot"
RALF_DIR="/opt/ralf"

log "Setting up Moltbot (OpenClaw) on VPS..."

# =============================================================================
# INSTALL DEPENDENCIES
# =============================================================================

log "Installing dependencies..."

# Install Node.js 22+ if not present
if ! command -v node &> /dev/null || [ "$(node -v | cut -d'v' -f2 | cut -d'.' -f1)" -lt 22 ]; then
    log "Installing Node.js 22..."
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
    apt-get install -y nodejs
fi

# Install Chrome for browser automation
log "Installing Chrome..."
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
echo "deb http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google.list
apt-get update
apt-get install -y google-chrome-stable

# =============================================================================
# INSTALL MOLTBOT
# =============================================================================

log "Installing Moltbot..."
npm install -g openclaw@latest

# =============================================================================
# CREATE DIRECTORIES
# =============================================================================

log "Creating directories..."
mkdir -p "$MOLT_DIR"
mkdir -p "$MOLT_DIR/logs"
mkdir -p "$MOLT_DIR/skills"
mkdir -p "$HOME/.openclaw"

# =============================================================================
# CREATE RALF INTEGRATION SKILL
# =============================================================================

log "Creating RALF integration skill..."

cat > "$MOLT_DIR/skills/ralf-status.js" << 'EOF'
/**
 * RALF Status Skill for Moltbot
 * Provides real-time updates on RALF autonomous loops
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const RALF_DIR = '/opt/ralf';
const QUEUE_FILE = path.join(RALF_DIR, '5-project-memory/blackbox5/.autonomous/agents/communications/queue.yaml');
const EVENTS_FILE = path.join(RALF_DIR, '5-project-memory/blackbox5/.autonomous/agents/communications/events.yaml');
const VERIFY_FILE = path.join(RALF_DIR, '5-project-memory/blackbox5/.autonomous/agents/communications/verify.yaml');

class RalfStatusSkill {
  constructor() {
    this.name = 'ralf-status';
    this.description = 'Get real-time status of RALF autonomous loops';
  }

  async getQueueStatus() {
    try {
      const content = fs.readFileSync(QUEUE_FILE, 'utf8');
      const pending = (content.match(/status: pending/g) || []).length;
      const inProgress = (content.match(/status: in_progress/g) || []).length;
      const completed = (content.match(/status: completed/g) || []).length;
      const claimed = (content.match(/status: claimed/g) || []).length;

      return {
        pending,
        inProgress,
        completed,
        claimed,
        total: pending + inProgress + completed + claimed
      };
    } catch (e) {
      return { error: 'Could not read queue' };
    }
  }

  async getRecentEvents(limit = 5) {
    try {
      const content = fs.readFileSync(EVENTS_FILE, 'utf8');
      const events = [];
      const matches = content.matchAll(/- timestamp: "([^"]+)"\s+task_id: "([^"]+)"\s+type: (\w+)/g);

      for (const match of matches) {
        events.push({
          timestamp: match[1],
          taskId: match[2],
          type: match[3]
        });
      }

      return events.slice(-limit);
    } catch (e) {
      return [];
    }
  }

  async getVerificationStatus() {
    try {
      const content = fs.readFileSync(VERIFY_FILE, 'utf8');
      const autoCommit = (content.match(/decision: AUTO_COMMIT/g) || []).length;
      const queueReview = (content.match(/decision: QUEUE_REVIEW/g) || []).length;
      const humanReview = (content.match(/decision: HUMAN_REVIEW/g) || []).length;

      return { autoCommit, queueReview, humanReview };
    } catch (e) {
      return { error: 'No verifications yet' };
    }
  }

  async getGitStatus() {
    try {
      const stdout = execSync('cd /opt/ralf && git log --oneline -3 && echo "---" && git status --short', {
        encoding: 'utf8',
        timeout: 5000
      });
      return stdout;
    } catch (e) {
      return 'Git status unavailable';
    }
  }

  async getSystemHealth() {
    try {
      const uptime = execSync('uptime -p', { encoding: 'utf8' }).trim();
      const disk = execSync('df -h /opt/ralf | tail -1', { encoding: 'utf8' }).trim();
      const memory = execSync('free -h | grep Mem', { encoding: 'utf8' }).trim();

      return { uptime, disk, memory };
    } catch (e) {
      return { error: 'System stats unavailable' };
    }
  }

  formatStatusReport() {
    return new Promise(async (resolve) => {
      const queue = await this.getQueueStatus();
      const events = await this.getRecentEvents(3);
      const verifications = await this.getVerificationStatus();
      const git = await this.getGitStatus();
      const health = await this.getSystemHealth();

      let report = `🤖 **RALF Status Report**\n\n`;

      // Queue status
      report += `📋 **Queue**\n`;
      if (queue.error) {
        report += `  ${queue.error}\n`;
      } else {
        report += `  • Pending: ${queue.pending}\n`;
        report += `  • In Progress: ${queue.inProgress}\n`;
        report += `  • Claimed: ${queue.claimed}\n`;
        report += `  • Completed: ${queue.completed}\n`;
        report += `  • Total: ${queue.total}\n`;
      }
      report += `\n`;

      // Recent events
      report += `📊 **Recent Events**\n`;
      if (events.length === 0) {
        report += `  No recent events\n`;
      } else {
        events.forEach(e => {
          const emoji = e.type === 'completed' ? '✅' : e.type === 'started' ? '🚀' : '📝';
          report += `  ${emoji} ${e.taskId} - ${e.type}\n`;
        });
      }
      report += `\n`;

      // Verifications
      report += `🔍 **Verifications**\n`;
      if (verifications.error) {
        report += `  ${verifications.error}\n`;
      } else {
        report += `  • Auto-committed: ${verifications.autoCommit}\n`;
        report += `  • Queued for review: ${verifications.queueReview}\n`;
        report += `  • Human review: ${verifications.humanReview}\n`;
      }
      report += `\n`;

      // Git status
      report += `📝 **Git Status**\n`;
      report += `\`\`\`\n${git}\`\`\`\n\n`;

      // System health
      report += `💻 **System**\n`;
      if (health.error) {
        report += `  ${health.error}\n`;
      } else {
        report += `  • Uptime: ${health.uptime}\n`;
        report += `  • Disk: ${health.disk.split(/\s+/).pop()}\n`;
      }

      resolve(report);
    });
  }

  // Command handlers
  async handleStatusCommand() {
    return await this.formatStatusReport();
  }

  async handleQueueCommand() {
    const queue = await this.getQueueStatus();
    if (queue.error) return queue.error;

    return `📋 **RALF Queue**\n\n` +
           `Pending: ${queue.pending}\n` +
           `In Progress: ${queue.inProgress}\n` +
           `Claimed: ${queue.claimed}\n` +
           `Completed: ${queue.completed}\n` +
           `Total: ${queue.total}`;
  }

  async handleTaskCommand(taskId) {
    try {
      const taskFile = path.join(RALF_DIR, '5-project-memory/blackbox5/tasks/active', taskId, 'task.md');
      if (!fs.existsSync(taskFile)) {
        return `❌ Task ${taskId} not found`;
      }

      const content = fs.readFileSync(taskFile, 'utf8');
      const title = content.match(/^#\s+(.+)$/m)?.[1] || 'Unknown';
      const status = content.match(/\*\*Status:\*\*\s*(\w+)/)?.[1] || 'unknown';

      return `📄 **${taskId}**\n\n` +
             `Title: ${title}\n` +
             `Status: ${status}\n\n` +
             `[View on GitHub](https://github.com/Lordsisodia/blackbox5/tree/main/5-project-memory/blackbox5/tasks/active/${taskId})`;
    } catch (e) {
      return `❌ Error reading task: ${e.message}`;
    }
  }
}

module.exports = RalfStatusSkill;

// CLI usage for testing
if (require.main === module) {
  const skill = new RalfStatusSkill();
  skill.formatStatusReport().then(console.log);
}
EOF

success "RALF skill created"

# =============================================================================
# CREATE SYSTEMD SERVICE
# =============================================================================

log "Creating systemd service..."

cat > /etc/systemd/system/moltbot.service << EOF
[Unit]
Description=Moltbot (OpenClaw) AI Assistant
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/moltbot
Environment="HOME=/root"
Environment="OPENCLAW_CONFIG=/root/.openclaw"
ExecStart=/usr/bin/openclaw daemon
Restart=always
RestartSec=10
StandardOutput=append:/opt/moltbot/logs/moltbot.log
StandardError=append:/opt/moltbot/logs/moltbot-error.log

[Install]
WantedBy=multi-user.target
EOF

# =============================================================================
# CREATE CONFIGURATION
# =============================================================================

log "Creating configuration template..."

cat > "$HOME/.openclaw/openclaw.json" << 'EOF'
{
  "agent": {
    "model": "anthropic/claude-sonnet-4-5",
    "baseUrl": "https://api.z.ai/api/anthropic"
  },
  "channels": {
    "discord": {
      "enabled": true,
      "token": "YOUR_DISCORD_BOT_TOKEN_HERE"
    }
  },
  "skills": {
    "ralf-status": {
      "enabled": true,
      "path": "/opt/moltbot/skills/ralf-status.js"
    }
  },
  "gateway": {
    "port": 18789,
    "host": "0.0.0.0"
  }
}
EOF

# =============================================================================
# CREATE RALF WATCHER SCRIPT
# =============================================================================

log "Creating RALF watcher for real-time updates..."

cat > "$MOLT_DIR/ralf-watcher.sh" << 'EOF'
#!/bin/bash
# Watch RALF events and send notifications to Discord via Moltbot

RALF_DIR="/opt/ralf"
EVENTS_FILE="$RALF_DIR/5-project-memory/blackbox5/.autonomous/agents/communications/events.yaml"
LAST_CHECK_FILE="/tmp/ralf-watcher-last"
MOLT_GATEWAY="http://localhost:18789"

# Get last check time
last_check=0
if [ -f "$LAST_CHECK_FILE" ]; then
    last_check=$(cat "$LAST_CHECK_FILE")
fi

# Check for new events
if [ -f "$EVENTS_FILE" ]; then
    current_time=$(stat -c %Y "$EVENTS_FILE")

    if [ "$current_time" -gt "$last_check" ]; then
        # New events detected
        new_events=$(tail -20 "$EVENTS_FILE" | grep -E "^  - timestamp:" | tail -5)

        if [ -n "$new_events" ]; then
            # Send notification via Moltbot gateway (if available)
            curl -s -X POST "$MOLT_GATEWAY/notify" \
                -H "Content-Type: application/json" \
                -d "{\"source\": \"ralf\", \"message\": \"New RALF activity detected\", \"events\": $(echo "$new_events" | jq -R -s -c 'split("\n")')}" \
                2>/dev/null || true
        fi

        echo "$current_time" > "$LAST_CHECK_FILE"
    fi
fi
EOF

chmod +x "$MOLT_DIR/ralf-watcher.sh"

# Add to crontab
(crontab -l 2>/dev/null | grep -v "ralf-watcher"; echo "*/2 * * * * /opt/moltbot/ralf-watcher.sh") | crontab -

# =============================================================================
# CREATE DISCORD COMMANDS
# =============================================================================

log "Creating Discord command handlers..."

cat > "$MOLT_DIR/discord-commands.js" << 'EOF'
/**
 * Discord command handlers for RALF integration
 * Add these to your Moltbot configuration
 */

const RalfStatusSkill = require('./skills/ralf-status');
const skill = new RalfStatusSkill();

const commands = {
  // !ralf status - Full status report
  'ralf status': async (message) => {
    const report = await skill.handleStatusCommand();
    message.reply(report);
  },

  // !ralf queue - Queue status only
  'ralf queue': async (message) => {
    const report = await skill.handleQueueCommand();
    message.reply(report);
  },

  // !ralf task TASK-XXX - Get task details
  'ralf task': async (message, args) => {
    if (!args[0]) {
      message.reply('Usage: !ralf task TASK-XXX');
      return;
    }
    const report = await skill.handleTaskCommand(args[0]);
    message.reply(report);
  },

  // !ralf health - System health
  'ralf health': async (message) => {
    const health = await skill.getSystemHealth();
    const report = `💻 **System Health**\n\n` +
                   `Uptime: ${health.uptime}\n` +
                   `Disk: ${health.disk}\n` +
                   `Memory: ${health.memory}`;
    message.reply(report);
  },

  // !ralf help - Show available commands
  'ralf help': async (message) => {
    const help = `🤖 **RALF Bot Commands**\n\n` +
                 `\`!ralf status\` - Full status report\n` +
                 `\`!ralf queue\` - Queue status\n` +
                 `\`!ralf task TASK-XXX\` - Task details\n` +
                 `\`!ralf health\` - System health\n` +
                 `\`!ralf help\` - Show this help`;
    message.reply(help);
  }
};

module.exports = commands;
EOF

# =============================================================================
# SUMMARY
# =============================================================================

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  Moltbot Setup Complete"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Configuration: $HOME/.openclaw/openclaw.json"
echo "Logs: /opt/moltbot/logs/"
echo "Skills: /opt/moltbot/skills/"
echo ""
echo "NEXT STEPS:"
echo ""
echo "1. Edit configuration:"
echo "   nano $HOME/.openclaw/openclaw.json"
echo ""
echo "2. Add your Discord bot token:"
echo "   - Go to https://discord.com/developers/applications"
echo "   - Create New Application → Bot → Copy Token"
echo "   - Paste in openclaw.json"
echo ""
echo "3. Start Moltbot:"
echo "   systemctl start moltbot"
echo "   systemctl enable moltbot"
echo ""
echo "4. In Discord, use commands:"
echo "   !ralf status  - Full RALF status"
echo "   !ralf queue   - Queue status"
echo "   !ralf task TASK-XXX - Task details"
echo "   !ralf health  - System health"
echo ""
echo "═══════════════════════════════════════════════════════════════"
