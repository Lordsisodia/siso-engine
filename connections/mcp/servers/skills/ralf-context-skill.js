/**
 * User Context Skill for Moltbot
 * Loads Shaan's preferences and project context
 */

const fs = require('fs');
const path = require('path');

const CONTEXT_FILE = '/opt/moltbot/user-context.json';

class UserContextSkill {
  constructor() {
    this.name = 'user-context';
    this.description = 'Load and provide user context';
    this.context = null;
  }

  loadContext() {
    try {
      if (fs.existsSync(CONTEXT_FILE)) {
        this.context = JSON.parse(fs.readFileSync(CONTEXT_FILE, 'utf8'));
        return this.context;
      }
    } catch (e) {
      console.error('Failed to load user context:', e);
    }
    return null;
  }

  getUserName() {
    return this.context?.user?.preferred_name || 'Shaan';
  }

  getUserContext() {
    return this.context;
  }
}

module.exports = UserContextSkill;
