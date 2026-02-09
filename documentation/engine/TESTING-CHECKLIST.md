# Tier 2 Skills - Testing Checklist

## ✅ Completed Tests

### Day 1: Core Infrastructure
- [x] SkillManager Tier 2 support
- [x] AgentSkill dataclass parsing
- [x] YAML frontmatter parsing
- [x] Tag normalization (string → list conversion)
- [x] Tier 2 skill discovery from ~/.claude/skills/
- [x] Test skill creation and loading

### Day 2: BaseAgent Integration
- [x] BaseAgent skill loading methods
- [x] Progressive disclosure (summary vs full)
- [x] Skill manager lazy loading
- [x] Token usage tracking
- [x] Skill unloading

### Day 3: ContextManager & Skill Conversion
- [x] ContextManager integration
- [x] Skill caching methods
- [x] Converted 6 high-priority skills
- [x] Tag-based search
- [x] Cache statistics

### Day 4: Agent Integration
- [x] Test with Amelia (DeveloperAgent)
- [x] Test with Mary (AnalystAgent)
- [x] Test with Alex (ArchitectAgent)
- [x] Skill discovery (15 Tier 2 skills)
- [x] Progressive disclosure efficiency
- [x] Load/unload cycles

---

## 🧪 Remaining Tests

### 1. Real Workflow Integration
**Priority**: HIGH
**Estimate**: 2-3 hours

**What to test**:
- [ ] Agents using skills in actual tasks
  - [ ] Amelia: Debug a real bug using git-workflows
  - [ ] Mary: Analyze feedback using feedback-triage
  - [ ] Alex: Design system using supabase-operations
- [ ] Measure actual token usage in real workflows
- [ ] Compare before/after token consumption
- [ ] Validate skill utility and accuracy

**Test approach**:
```python
# Create real task scenarios
scenarios = [
    {
        'agent': 'Amelia',
        'task': 'Debug login failure in auth module',
        'skills': ['git-workflows', 'testing-patterns'],
        'expected': 'Locate auth code, identify bug, suggest fix'
    },
    {
        'agent': 'Mary',
        'task': 'Triage 10 user feedback items',
        'skills': ['feedback-triage'],
        'expected': 'Prioritized backlog with ownership'
    },
    {
        'agent': 'Alex',
        'task': 'Design task management system',
        'skills': ['supabase-operations', 'git-workflows'],
        'expected': 'Schema design with RLS policies'
    }
]
```

**Why important**: Validates that skills actually help agents complete real tasks

---

### 2. Concurrent Skill Loading
**Priority**: MEDIUM
**Estimate**: 1 hour

**What to test**:
- [ ] Multiple agents loading skills simultaneously
- [ ] Same skill loaded by multiple agents
- [ ] Race conditions in skill manager
- [ ] Cache consistency under concurrent access
- [ ] Memory leaks from concurrent loads

**Test approach**:
```python
async def test_concurrent_loading():
    agents = [DeveloperAgent(), AnalystAgent(), ArchitectAgent()]
    tasks = [
        agent.load_skill('git-workflows')
        for agent in agents
    ]
    results = await asyncio.gather(*tasks)
    assert all(results)  # All succeed
```

**Why important**: Agents will run in parallel in production

---

### 3. Error Handling & Edge Cases
**Priority**: HIGH
**Estimate**: 2 hours

**What to test**:
- [ ] Missing skill file
- [ ] Invalid YAML frontmatter
- [ ] Corrupted skill content
- [ ] Empty skill directory
- [ ] Skill with no tags
- [ ] Skill with special characters in name
- [ ] Network errors (if fetching remote skills)
- [ ] Permission errors reading skill files
- [ ] Malformed skill content

**Test approach**:
```python
# Test various error conditions
error_cases = [
    'nonexistent-skill',
    'skill-with-bad-yaml',
    'skill-with-empty-content',
    'skill-with-no-tags',
    # ... etc
]
```

**Why important**: Production systems must handle errors gracefully

---

### 4. Performance Under Load
**Priority**: MEDIUM
**Estimate**: 2 hours

**What to test**:
- [ ] Load all 15 skills sequentially
- [ ] Load all 15 skills in parallel
- [ ] Repeated load/unload cycles (memory leaks)
- [ ] Large skill files (100KB+)
- [ ] Skill manager with 100+ skills
- [ ] Memory usage over time
- [ ] CPU usage during load

**Test approach**:
```python
# Performance benchmarks
benchmarks = {
    'cold_load_all': measure_time(load_all_skills),
    'warm_load_one': measure_time(load_single_skill),
    'memory_usage': measure_memory(load_all_skills),
    'concurrent_load': measure_time(concurrent_load)
}
```

**Why important**: Ensure system scales with more skills

---

### 5. ContextManager Caching
**Priority**: MEDIUM
**Estimate**: 1-2 hours

**What to test**:
- [ ] Skill content caching
- [ ] Cache hit/miss ratios
- [ ] Cache eviction policies
- [ ] Cache persistence across sessions
- [ ] Cache invalidation
- [ ] Cache size limits
- [ ] Auto-compaction working

**Test approach**:
```python
# Cache testing
await sm.cache_skill_content('test-skill', content, tags)
cached = await sm.get_cached_skill_content('test-skill')
assert cached == content

# Test cache statistics
stats = sm.get_cache_stats()
assert stats['total_cached_items'] > 0
```

**Why important**: Advanced caching provides additional token savings

---

### 6. Skill Versioning & Updates
**Priority**: LOW
**Estimate**: 1 hour

**What to test**:
- [ ] Skill file updates detected
- [ ] Modified skills reload correctly
- [ ] Version conflicts handled
- [ ] Deprecated skill warnings
- [ ] Skill migration between versions

**Test approach**:
```python
# Modify skill file and verify reload
original = sm.get_skill('test-skill')
# Modify file...
await sm.load_all()
updated = sm.get_skill('test-skill')
assert updated.version != original.version
```

**Why important**: Skills will evolve over time

---

### 7. Skill Dependencies
**Priority**: LOW
**Estimate**: 1-2 hours

**What to test**:
- [ ] Skills that reference other skills
- [ ] Circular dependency detection
- [ ] Dependency load order
- [ ] Missing dependency handling

**Test approach**:
```python
# Add "depends_on" field to YAML frontmatter
# Test dependency resolution
```

**Why important**: Complex skills may need other skills

---

### 8. Multi-Project Skill Isolation
**Priority**: MEDIUM
**Estimate**: 1-2 hours

**What to test**:
- [ ] Different projects with different skill sets
- [ ] Project-specific skill directories
- [ ] Skill name conflicts across projects
- [ ] Environment-specific skills

**Test approach**:
```python
# Test with BLACKBOX5_ENGINE_PATH pointing to different projects
```

**Why important**: Multiple BB5 projects may need different skills

---

### 9. CLI Skill Execution
**Priority**: HIGH
**Estimate**: 2-3 hours

**What to test**:
- [ ] Agents actually executing CLI commands from skills
- [ ] Command output parsing
- [ ] Error handling from CLI commands
- [ ] Interactive command handling
- [ ] Long-running command management

**Test approach**:
```python
# Test that agent can use skill to execute command
agent.load_skill('siso-tasks-cli')
result = await agent.execute_cli_command(
    'supabase db execute --sql "SELECT * FROM tasks LIMIT 5"'
)
assert result.success
```

**Why important**: Skills are useless if agents can't execute them

---

### 10. Integration with Agent Orchestration
**Priority**: HIGH
**Estimate**: 2-3 hours

**What to test**:
- [ ] Skills work in multi-agent workflows
- [ ] Agent handoffs with loaded skills
- [ ] Skill context preserved across handoffs
- [ ] Orchestration layer aware of skills
- [ ] Task routing based on skill availability

**Test approach**:
```python
# Multi-agent workflow
orchestrator = Orchestrator()
orchestrator.register_agent(amelia)
orchestrator.register_agent(mary)

task = Task(description="Debug and analyze issue")
result = await orchestrator.execute(task, agents=[amelia, mary])
```

**Why important**: Real workflows involve multiple agents collaborating

---

### 11. Token Accounting Accuracy
**Priority**: MEDIUM
**Estimate**: 1 hour

**What to test**:
- [ ] Actual token usage vs estimates
- [ ] Token counting across skill loads
- [ ] Token usage in agent context
- [ ] Token savings validation
- [ ] Token usage reporting

**Test approach**:
```python
# Compare estimated vs actual
estimated = agent.get_token_usage()['total_tokens']
# Use actual tokenizer if available
actual = count_tokens(str(agent._loaded_skills))
assert abs(estimated - actual) < 0.1 * actual  # Within 10%
```

**Why important**: Token savings are key value proposition

---

### 12. Skill Search & Discovery
**Priority**: LOW
**Estimate**: 1 hour

**What to test**:
- [ ] Fuzzy search for skills
- [ ] Search by description
- [ ] Search by content
- [ ] Tag-based search accuracy
- [ ] Category browsing
- [ ] Skill recommendation

**Test approach**:
```python
# Test search accuracy
results = sm.search_skills("git")
assert 'git-workflows' in results

results = sm.search_skills_by_tag('database')
assert any(s.name == 'supabase-operations' for s in results)
```

**Why important**: Agents need to find relevant skills

---

### 13. Backward Compatibility
**Priority**: MEDIUM
**Estimate**: 1 hour

**What to test**:
- [ ] Old Tier 1 skills still work
- [ ] Mixed Tier 1/Tier 2 usage
- [ ] Migration from old to new
- [ ] Legacy code compatibility

**Test approach**:
```python
# Test that old code still works
agent = DeveloperAgent()
old_skill_usage = agent.use_skill('old_python_skill')
new_skill_usage = agent.load_skill('new_tier2_skill')
# Both should work
```

**Why important**: Don't break existing functionality

---

### 14. Documentation & Examples
**Priority**: LOW
**Estimate**: 2-3 hours

**What to create**:
- [ ] Usage examples for each skill
- [ ] Video tutorials
- [ ] API documentation
- [ ] Best practices guide
- [ ] Troubleshooting guide
- [ ] FAQ

**Why important**: Adoption requires good documentation

---

### 15. Production Monitoring
**Priority**: HIGH
**Estimate**: 2 hours

**What to implement**:
- [ ] Skill usage metrics
- [ ] Token savings tracking
- [ ] Error rate monitoring
- [ ] Performance dashboards
- [ ] Alerting for failures
- [ ] A/B testing framework

**Test approach**:
```python
# Add monitoring to skill manager
sm = SkillManager()
sm.enable_monitoring(metrics_backend='prometheus')
```

**Why important**: Need to track production performance

---

## 📊 Test Priority Matrix

| Test | Priority | Estimate | Impact | Effort |
|------|----------|----------|--------|--------|
| Real Workflow Integration | HIGH | 2-3h | ⭐⭐⭐⭐⭐ | Medium |
| Error Handling | HIGH | 2h | ⭐⭐⭐⭐⭐ | Medium |
| CLI Execution | HIGH | 2-3h | ⭐⭐⭐⭐⭐ | Medium |
| Orchestration Integration | HIGH | 2-3h | ⭐⭐⭐⭐⭐ | Medium |
| Production Monitoring | HIGH | 2h | ⭐⭐⭐⭐ | Low |
| Concurrent Loading | MEDIUM | 1h | ⭐⭐⭐ | Low |
| Performance Under Load | MEDIUM | 2h | ⭐⭐⭐⭐ | Medium |
| ContextManager Caching | MEDIUM | 1-2h | ⭐⭐⭐ | Low |
| Multi-Project Isolation | MEDIUM | 1-2h | ⭐⭐⭐ | Low |
| Token Accounting | MEDIUM | 1h | ⭐⭐⭐⭐ | Low |
| Backward Compatibility | MEDIUM | 1h | ⭐⭐⭐⭐ | Low |
| Skill Search | LOW | 1h | ⭐⭐ | Low |
| Skill Versioning | LOW | 1h | ⭐⭐ | Low |
| Skill Dependencies | LOW | 1-2h | ⭐⭐ | Low |
| Documentation | LOW | 2-3h | ⭐⭐⭐ | Medium |

**Total Estimated Time**: 25-35 hours

---

## 🎯 Recommended Next Steps

### Phase 1: Production Readiness (8-10 hours)

Do these first before deploying to production:

1. **Error Handling & Edge Cases** (2h) - Must handle failures gracefully
2. **Real Workflow Integration** (2-3h) - Validate actual utility
3. **CLI Execution** (2-3h) - Ensure commands work
4. **Production Monitoring** (2h) - Track performance

### Phase 2: Scalability (5-7 hours)

After production deployment:

5. **Concurrent Loading** (1h) - Support parallel agents
6. **Performance Under Load** (2h) - Ensure scale
7. **Orchestration Integration** (2-3h) - Multi-agent workflows

### Phase 3: Polish (12-18 hours)

Long-term improvements:

8. **ContextManager Caching** (1-2h)
9. **Multi-Project Isolation** (1-2h)
10. **Token Accounting** (1h)
11. **Backward Compatibility** (1h)
12. **Skill Versioning** (1h)
13. **Skill Dependencies** (1-2h)
14. **Skill Search** (1h)
15. **Documentation** (2-3h)

---

## 💡 Quick Win Tests

If you only have 1 hour, do these:

```python
# 1. Real workflow test (30 min)
async def quick_real_workflow_test():
    agent = DeveloperAgent()
    await agent.load_skill('git-workflows')
    # Give agent a real debugging task
    result = await agent.execute_task("Find login bug in auth module")
    assert result.success
    print(f"✓ Agent completed task using skill")

# 2. Error handling test (30 min)
async def quick_error_test():
    sm = SkillManager()
    bad_skill = sm.get_skill('nonexistent-skill')
    assert bad_skill is None
    print(f"✓ Handles missing skill gracefully")
```

---

## 📝 Summary

**What's been tested** (Days 1-4):
- ✅ Core infrastructure
- ✅ Skill loading/unloading
- ✅ Progressive disclosure
- ✅ Agent integration
- ✅ Basic functionality

**What still needs testing**:
- 🧪 Real-world workflows
- 🧪 Error handling
- 🧪 CLI execution
- 🧪 Production monitoring
- 🧪 Concurrent usage
- 🧪 Performance at scale

**Recommendation**: Complete Phase 1 tests (8-10 hours) before production deployment.
