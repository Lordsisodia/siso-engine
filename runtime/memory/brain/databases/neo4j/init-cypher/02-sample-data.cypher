// Blackbox4 Brain - Sample Data for Testing
// This creates a small test graph to verify the system

// Create sample artifacts
CREATE (orchestrator:Artifact {
  id: 'orchestrator-agent-v1',
  type: 'agent',
  name: 'Orchestrator Agent',
  category: 'specialist',
  version: '1.0.0',
  path: '1-agents/4-specialists/orchestrator.md',
  created: '2026-01-15',
  modified: '2026-01-15',
  description: 'Main orchestrator agent for coordinating other agents',
  tags: ['orchestration', 'coordination', 'agent-handoff'],
  status: 'active',
  stability: 'high',
  owner: 'core-team'
});

CREATE (deepResearch:Artifact {
  id: 'deep-research-skill',
  type: 'skill',
  name: 'Deep Research Skill',
  category: 'core',
  version: '2.0.0',
  path: '1-agents/.skills/1-core/deep-research.md',
  created: '2026-01-10',
  modified: '2026-01-15',
  description: 'Core skill for performing deep research',
  tags: ['research', 'web-search', 'synthesis'],
  status: 'active',
  stability: 'high',
  owner: 'core-team'
});

CREATE (contextVars:Artifact {
  id: 'context-variables-lib',
  type: 'library',
  name: 'Context Variables Library',
  category: 'context-variables',
  version: '1.0.0',
  path: '4-scripts/lib/context-variables/',
  created: '2026-01-05',
  modified: '2026-01-15',
  description: 'Python library for managing context variables',
  tags: ['context', 'variables', 'state-management'],
  phase: 1,
  layer: 'execution',
  status: 'active',
  stability: 'high',
  owner: 'core-team'
});

CREATE (ralph:Artifact {
  id: 'ralph-agent',
  type: 'agent',
  name: 'Ralph Agent',
  category: 'specialist',
  version: '2.0.0',
  path: '1-agents/4-specialists/ralph.md',
  created: '2026-01-12',
  modified: '2026-01-15',
  description: 'Specialist agent for task execution',
  tags: ['execution', 'tasks', 'specialist'],
  status: 'active',
  stability: 'high',
  owner: 'core-team'
});

// Create relationships
CREATE (orchestrator)-[:DEPENDS_ON {strength: 'required', version: '>=2.0.0'}]->(deepResearch);
CREATE (ralph)-[:DEPENDS_ON {strength: 'required', version: '>=1.0.0'}]->(contextVars);
CREATE (ralph)-[:USED_BY {strength: 'direct'}]->(orchestrator);
CREATE (deepResearch)-[:USED_BY {strength: 'direct'}]->(orchestrator);

// Add relationship metadata
CREATE (ralph)-[:RELATES_TO {
  relationship: 'extends',
  strength: 'strong',
  description: 'Extends orchestrator capabilities'
}]->(orchestrator);
