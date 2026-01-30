# Project-Specific Context

What Ralph needs to know about the projects being managed.

---

## Projects Overview

### 1. E-Commerce Client Project
**Priority:** HIGH
**Path:** `../ecommerce-client` (relative to ralph.p/)
**Branch:** `dev`

**Work Areas:**
- Admin section pages and functionality
- Feature implementation (core logic, UI later)
- Documentation improvements
- Small architecture refactors (only if required)
- Idea generation from existing documents

**Tech Stack:**
- Frontend: React/Next.js
- Backend: Supabase (database + auth)
- APIs: GLM 4.7, Kimi 2.5

**Supabase:**
- Project ref: [configure in CONFIG.yaml]
- Must test all DB connections
- RLS policies required

---

### 2. SISO Internal App
**Priority:** MEDIUM
**Path:** `.` (current project)
**Branch:** `dev`

**Work Areas:**
- Setup and organization
- Error prevention
- Idea generation and testing
- Feature implementation
- Project memory management

**Existing Infrastructure:**
- BlackBox 5 project memory system
- STATE.yaml tracking
- GitHub integration
- Ralph runtime (in operations/agents/)

---

## API Configuration

**GLM 4.7** (Primary)
- Command: `claude`
- Rate: 2,000 prompts / 5 hours
- Use for: coding, documentation, research, testing

**Kimi 2.5** (Secondary)
- Command: `cso-kimi`
- Rate: 500 prompts / 5 hours
- Use for: architecture, complex reasoning, code review

---

## Quality Gates

Before marking complete:
- [ ] Code follows project patterns
- [ ] Tests pass (if applicable)
- [ ] Supabase connections verified
- [ ] No secrets in code
- [ ] Documentation updated
