---
id: codebase-navigation
name: Codebase Navigation
version: 1.0.0
category: utility
description: Navigate and understand codebases efficiently
trigger: When exploring unfamiliar code, locating functionality
inputs:
  - name: query
    type: string
    required: true
    description: What to find or understand
  - name: search_type
    type: string
    required: false
    description: "file | function | pattern | concept"
    default: concept
outputs:
  - name: search_results
    type: array
    description: Matching files/locations
  - name: context_summary
    type: string
    description: Explanation of what was found
commands:
  - find
  - locate-file
  - find-function
  - search-pattern
  - understand-concept
---

# Codebase Navigation

## Purpose

Quickly locate and understand code in unfamiliar or large codebases.

## When to Use

- Starting work on a new codebase
- Finding where a feature is implemented
- Understanding how something works
- Locating configuration

---

## Command: find

### Input
- `query`: What to find
- `search_type`: How to search

### Process

1. **Analyze query**
   - What is being looked for?
   - Best search strategy?

2. **Execute search**
   - Use grep for patterns
   - Use glob for files
   - Use knowledge for concepts

3. **Rank results**
   - Relevance to query
   - Importance in codebase
   - Recent activity

4. **Summarize findings**
   - What was found
   - Where to look
   - Key files

### Output

```yaml
search_results:
  query: "user authentication"
  type: "concept"

  files:
    - path: "src/auth/index.ts"
      relevance: "high"
      description: "Main auth module"
    - path: "src/auth/login.tsx"
      relevance: "high"
      description: "Login UI component"
    - path: "src/middleware/auth.ts"
      relevance: "medium"
      description: "Auth middleware"

  functions:
    - name: "authenticateUser"
      location: "src/auth/index.ts:45"
      description: "Main authentication function"
    - name: "requireAuth"
      location: "src/middleware/auth.ts:12"
      description: "Middleware guard"

  summary: |
    Authentication is implemented in src/auth/ with:
    - Core logic in index.ts
    - UI components in login.tsx and signup.tsx
    - Middleware protection in src/middleware/
```

---

## Search Strategies

### Find File
```
Pattern: **/auth*.ts
Look for: auth.ts, auth.test.ts, auth-utils.ts
```

### Find Function
```
Pattern: function authenticateUser
Or: const authenticateUser =
Or: export async function authenticateUser
```

### Find Pattern
```
Pattern: useAuth\(
Find all uses of useAuth hook
```

### Understand Concept
```
Query: "How does authentication work?"
Find: Entry points, flow, key files
```

---

## Examples

### Example: Finding API Routes

```markdown
**Query:** "Where are API routes defined?"
**Type:** pattern

**Results:**
- src/api/routes.ts (main router)
- src/api/users.ts (user routes)
- src/api/auth.ts (auth routes)

**Pattern:** Express router definitions
```

### Example: Understanding State Management

```markdown
**Query:** "How is state managed?"
**Type:** concept

**Results:**
- Uses Zustand for global state
- React Query for server state
- Context for theme/auth

**Key Files:**
- src/store/index.ts (Zustand stores)
- src/hooks/useQuery.ts (React Query setup)
```
