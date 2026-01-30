#!/usr/bin/env python3
"""
Interactive Agent Coordination Demo

Try out the agent output format interactively.
Choose different scenarios and see how agents coordinate.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from AgentOutputParser import (
    parse_agent_output,
    create_agent_output,
    chain_agent_outputs,
)


def demo_create_output():
    """Demo: Create a structured agent output."""
    print("=" * 70)
    print("DEMO: Create Your Own Agent Output")
    print("=" * 70)
    print()

    # Get user input
    print("What did your agent accomplish?")
    summary = input("Summary (one line): ").strip()

    print("\nWhat files/artifacts were created?")
    files_input = input("Deliverables (comma-separated, or press Enter to skip): ").strip()
    deliverables = [f.strip() for f in files_input.split(",")] if files_input else []

    print("\nWhat should happen next?")
    steps_input = input("Next steps (comma-separated, or press Enter to skip): ").strip()
    next_steps = [s.strip() for s in steps_input.split(",")] if steps_input else []

    print("\nAny details to add?")
    print("Type your explanation (press Enter twice when done):")
    lines = []
    while True:
        line = input()
        if line == "" and lines:
            break
        lines.append(line)
    human_content = "\n".join(lines)

    # Create the output
    output = create_agent_output(
        status="success",
        summary=summary,
        deliverables=deliverables,
        next_steps=next_steps,
        human_content=human_content,
        agent_name="demo-agent",
        task_id="interactive-demo",
        duration_seconds=0,
    )

    print()
    print("=" * 70)
    print("YOUR AGENT OUTPUT:")
    print("=" * 70)
    print(output)
    print()

    # Parse it back to show it works
    print("=" * 70)
    print("PARSED BACK:")
    print("=" * 70)
    parsed = parse_agent_output(output)
    print(f"Status: {parsed.status}")
    print(f"Summary: {parsed.summary}")
    print(f"Deliverables: {parsed.deliverables}")
    print(f"Next Steps: {parsed.next_steps}")


def demo_parse_output():
    """Demo: Paste an agent output and parse it."""
    print("=" * 70)
    print("DEMO: Parse Agent Output")
    print("=" * 70)
    print()
    print("Paste an agent output (press Enter twice when done):")

    lines = []
    empty_count = 0
    while True:
        line = input()
        if line == "":
            empty_count += 1
            if empty_count >= 2:
                break
        else:
            empty_count = 0
        lines.append(line)

    output = "\n".join(lines)

    try:
        parsed = parse_agent_output(output)

        print()
        print("=" * 70)
        print("PARSED SUCCESSFULLY:")
        print("=" * 70)
        print(f"Status:     {parsed.status}")
        print(f"Summary:    {parsed.summary}")
        print(f"Deliverables: {parsed.deliverables}")
        print(f"Next Steps:  {parsed.next_steps}")
        print()
        print("METADATA:")
        for key, value in parsed.metadata.items():
            print(f"  {key}: {value}")
        print()
        print("HUMAN CONTENT (first 200 chars):")
        print(parsed.human_content[:200] + "...")
        print()

    except Exception as e:
        print()
        print("=" * 70)
        print(f"PARSING FAILED: {e}")
        print("=" * 70)


def demo_coordination_scenario():
    """Demo: Simulate a multi-agent coordination scenario."""
    print("=" * 70)
    print("DEMO: Multi-Agent Coordination Scenario")
    print("=" * 70)
    print()

    scenarios = {
        "1": "Build a user authentication API",
        "2": "Fix a bug in the payment system",
        "3": "Add a new feature to the dashboard",
        "4": "Refactor the database layer",
        "5": "Create a custom scenario",
    }

    print("Choose a scenario:")
    for key, description in scenarios.items():
        print(f"  {key}. {description}")

    choice = input("\nEnter choice (1-5): ").strip()

    if choice == "1":
        scenario_auth_api()
    elif choice == "2":
        scenario_fix_bug()
    elif choice == "3":
        scenario_add_feature()
    elif choice == "4":
        scenario_refactor()
    elif choice == "5":
        scenario_custom()
    else:
        print("Invalid choice")


def scenario_auth_api():
    """Scenario 1: Build authentication API."""
    print()
    print("Scenario: Building JWT Authentication API")
    print("-" * 70)
    print()

    # Agent 1: Architect
    print("[ARCHITECT] Designing API structure...")
    architect_output = create_agent_output(
        status="success",
        summary="Designed JWT-based authentication API structure",
        deliverables=["api-design.md", "api-spec.yaml"],
        next_steps=["Implement the endpoints"],
        human_content="""
## API Design

I've designed a JWT-based authentication system with:

### Endpoints
- POST /api/auth/login - Authenticate and get token
- POST /api/auth/refresh - Refresh expired token
- POST /api/auth/logout - Invalidate token
- GET /api/auth/me - Get current user from token

### Security Considerations
- Tokens expire after 24 hours
- Refresh tokens for extending sessions
- Password hashing with bcrypt
- Rate limiting on login attempts
""",
        agent_name="architect",
        task_id="auth-1",
        duration_seconds=120,
    )

    parsed_arch = parse_agent_output(architect_output)
    print(f"✓ {parsed_arch.summary}")
    print(f"  Files: {', '.join(parsed_arch.deliverables)}")
    print()

    # Agent 2: Coder
    print("[CODER] Implementing based on design...")
    coder_output = create_agent_output(
        status="success",
        summary="Implemented all 4 authentication endpoints",
        deliverables=["api/auth/login.ts", "api/auth/refresh.ts", "api/auth/logout.ts", "api/auth/me.ts"],
        next_steps=["Write tests"],
        human_content="""
## Implementation

All endpoints implemented with:

### Dependencies
- jsonwebtoken for JWT
- bcrypt for password hashing
- zod for validation

### Code Sample
```typescript
export async function login(req: Request, res: Response) {
  const { email, password } = req.body;
  const user = await db.users.findByEmail(email);
  if (!user || !await bcrypt.compare(password, user.passwordHash)) {
    return res.status(401).json({ error: 'Invalid credentials' });
  }
  const token = jwt.sign({ userId: user.id }, SECRET, { expiresIn: '24h' });
  res.json({ token, user: { id: user.id, email: user.email } });
}
```
""",
        agent_name="coder",
        task_id="auth-2",
        duration_seconds=300,
    )

    parsed_coder = parse_agent_output(coder_output)
    print(f"✓ {parsed_coder.summary}")
    print(f"  Files: {', '.join(parsed_coder.deliverables)}")
    print()

    # Agent 3: Tester
    print("[TESTER] Testing the implementation...")
    tester_output = create_agent_output(
        status="partial",
        summary="Tests passing but missing edge case coverage",
        deliverables=["tests/auth.test.ts"],
        next_steps=["Add edge case tests"],
        human_content="""
## Test Results

**Passing:** 8/10 tests

### Issues Found
1. Missing test for expired token refresh
2. No test for concurrent login attempts

### Recommendation
Add the missing edge case tests before deploying.
""",
        agent_name="tester",
        task_id="auth-3",
        duration_seconds=90,
        completion_percentage=80,
    )

    parsed_tester = parse_agent_output(tester_output)
    print(f"✓ {parsed_tester.summary}")
    print(f"  Completion: {parsed_tester.metadata.get('completion_percentage')}%")
    print()

    # Manager aggregates
    print("[MANAGER] Aggregating results...")
    results = chain_agent_outputs([architect_output, coder_output, tester_output])

    print()
    print("=" * 70)
    print("COORDINATION SUMMARY:")
    print("=" * 70)
    print(f"Total agents: {results['total']}")
    print(f"Success: {results['success_count']}")
    print(f"Partial: {results['partial_count'] if 'partial_count' in results else 0}")
    print(f"Failed: {results['failed_count']}")
    print(f"Overall: {results['overall_status'].upper()}")
    print()
    print(f"All deliverables: {', '.join(results['all_deliverables'])}")
    print()
    print(f"Next steps to take: {', '.join(results['all_next_steps'])}")


def scenario_fix_bug():
    """Scenario 2: Fix a bug."""
    print()
    print("Scenario: Fixing Payment Processing Bug")
    print("-" * 70)
    print()

    # Coder tries to fix
    print("[CODER] Attempting to fix bug...")
    coder_output = create_agent_output(
        status="failed",
        summary="Could not fix bug - missing Stripe SDK dependency",
        deliverables=[],
        next_steps=["Install Stripe SDK", "Retry fix"],
        human_content="""
## Issue Encountered

Tried to implement the fix but the Stripe SDK is not installed.

### Error
```
Error: Cannot find module 'stripe'
```

### Resolution Required
Run: `npm install stripe @types/stripe`
""",
        agent_name="coder",
        task_id="bugfix-1",
        duration_seconds=30,
        error_type="DependencyError",
        error_message="Stripe SDK not installed",
    )

    parsed = parse_agent_output(coder_output)
    print(f"✗ {parsed.summary}")
    print(f"  Error: {parsed.metadata.get('error_message')}")
    print(f"  Recovery: {parsed.next_steps}")
    print()

    # Show how another agent could handle this
    print("[DEVOPS] Detecting failure, installing dependency...")
    devops_output = create_agent_output(
        status="success",
        summary="Installed Stripe SDK dependency",
        deliverables=["package-lock.json"],
        next_steps=["Retry the bug fix"],
        human_content="""
## Action Taken

Ran `npm install stripe @types/stripe`

### Result
- stripe@14.0.0 installed
- @types/stripe@14.0.0 installed
- package-lock.json updated

Ready for retry.
""",
        agent_name="devops",
        task_id="bugfix-2",
        duration_seconds=45,
    )

    parsed_devops = parse_agent_output(devops_output)
    print(f"✓ {parsed_devops.summary}")
    print()
    print("→ Bug fix can now be retried with dependencies installed.")


def scenario_add_feature():
    """Scenario 3: Add a new feature."""
    print()
    print("Scenario: Adding Dashboard Analytics Feature")
    print("-" * 70)
    print()

    # Product owner specs the feature
    product_output = create_agent_output(
        status="success",
        summary="Specified analytics dashboard feature requirements",
        deliverables=["specs/analytics.md"],
        next_steps=["Design UI", "Implement backend"],
        human_content="""
## Feature Requirements

### User Stories
1. As a user, I want to see a graph of my activity over time
2. As a user, I want to filter by date range
3. As a user, I want to export data as CSV

### Requirements
- Line chart for activity
- Date range picker
- Export button
- Must load in < 2 seconds
""",
        agent_name="product-owner",
        task_id="feature-1",
        duration_seconds=60,
    )

    parsed_product = parse_agent_output(product_output)
    print(f"[PRODUCT] {parsed_product.summary}")
    print(f"  Deliverables: {parsed_product.deliverables}")
    print()

    # Frontend dev implements
    frontend_output = create_agent_output(
        status="success",
        summary="Built dashboard UI with charts and filters",
        deliverables=["src/components/Dashboard.tsx", "src/components/ActivityChart.tsx"],
        next_steps=["Connect to backend API"],
        human_content="""
## Frontend Implementation

### Components Created
- Dashboard.tsx - Main dashboard page
- ActivityChart.tsx - Line chart component
- DateRangePicker.tsx - Date filter component

### Libraries Used
- recharts for charts
- date-fns for date formatting
- tailwind for styling
""",
        agent_name="frontend-dev",
        task_id="feature-2",
        duration_seconds=180,
    )

    parsed_frontend = parse_agent_output(frontend_output)
    print(f"[FRONTEND] {parsed_frontend.summary}")
    print(f"  Files: {', '.join(parsed_frontend.deliverables)}")
    print()


def scenario_refactor():
    """Scenario 4: Refactor database layer."""
    print()
    print("Scenario: Refactoring Database Layer for Performance")
    print("-" * 70)
    print()

    # Analyst analyzes
    analyst_output = create_agent_output(
        status="success",
        summary="Analyzed database queries, found N+1 problem",
        deliverables=["analysis/db-performance.md"],
        next_steps=["Implement data loader"],
        human_content="""
## Performance Analysis

### Findings
- N+1 query problem in user listing
- Missing indexes on foreign keys
- No query result caching

### Impact
- User list API: 5 second response time
- Database CPU at 80% during peak

### Recommendations
1. Implement DataLoader for batching
2. Add composite indexes
3. Add Redis caching layer
""",
        agent_name="analyst",
        task_id="refactor-1",
        duration_seconds=90,
    )

    parsed_analyst = parse_agent_output(analyst_output)
    print(f"[ANALYST] {parsed_analyst.summary}")
    print(f"  Finding: N+1 query problem identified")
    print()

    # Coder implements fix
    coder_output = create_agent_output(
        status="success",
        summary="Refactored database layer with DataLoader and caching",
        deliverables=["db/DataLoader.ts", "db/cache.ts", "migrations/add-indexes.sql"],
        next_steps=["Run performance tests"],
        human_content="""
## Refactoring Complete

### Changes Made
- Implemented DataLoader for user queries
- Added Redis caching with 5-minute TTL
- Created composite indexes on (user_id, created_at)

### Expected Improvement
- Response time: 5s → 200ms (25x faster)
- Database CPU: 80% → 20%
- Cache hit rate: ~85%
""",
        agent_name="coder",
        task_id="refactor-2",
        duration_seconds=240,
    )

    parsed_coder = parse_agent_output(coder_output)
    print(f"[CODER] {parsed_coder.summary}")
    print(f"  Files: {', '.join(parsed_coder.deliverables)}")
    print()
    print("  Expected: 25x performance improvement")
    print()


def scenario_custom():
    """Scenario 5: Custom scenario."""
    print()
    print("Create your own scenario!")
    print()
    print("This will walk you through creating outputs from multiple agents.")
    print()

    # Get scenario description
    scenario = input("Describe the scenario: ").strip()
    if not scenario:
        print("No scenario provided.")
        return

    print()
    print("Now let's simulate agent outputs for this scenario.")
    print("Press Enter to skip an agent.")
    print()

    outputs = []

    # Agent 1
    print("\n--- Agent 1 ---")
    summary1 = input("What did Agent 1 accomplish? ").strip()
    if summary1:
        output1 = create_agent_output(
            status="success",
            summary=summary1,
            deliverables=[],
            next_steps=[],
            human_content="Completed task.",
            agent_name="agent-1",
            task_id="custom-1",
            duration_seconds=60,
        )
        outputs.append(output1)
        print(f"✓ Created output for Agent 1")

    # Agent 2
    print("\n--- Agent 2 ---")
    summary2 = input("What did Agent 2 accomplish? ").strip()
    if summary2:
        output2 = create_agent_output(
            status="success",
            summary=summary2,
            deliverables=[],
            next_steps=[],
            human_content="Completed task.",
            agent_name="agent-2",
            task_id="custom-2",
            duration_seconds=60,
        )
        outputs.append(output2)
        print(f"✓ Created output for Agent 2")

    # Aggregate
    if outputs:
        print()
        print("=" * 70)
        print("AGGREGATED RESULTS:")
        print("=" * 70)
        results = chain_agent_outputs(outputs)
        print(f"Total agents: {results['total']}")
        print(f"Status: {results['overall_status']}")
        print()


def main():
    """Interactive demo menu."""
    print()
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 18 + "AGENT COORDINATION INTERACTIVE DEMO" + " " * 18 + "║")
    print("╚" + "=" * 68 + "╝")
    print()

    while True:
        print()
        print("What would you like to do?")
        print()
        print("  1. Create your own agent output")
        print("  2. Parse an existing agent output")
        print("  3. Run a coordination scenario")
        print("  4. View example output format")
        print("  5. Exit")
        print()

        choice = input("Enter choice (1-5): ").strip()

        if choice == "1":
            demo_create_output()
        elif choice == "2":
            demo_parse_output()
        elif choice == "3":
            demo_coordination_scenario()
        elif choice == "4":
            show_example()
        elif choice == "5":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please enter 1-5.")


def show_example():
    """Show an example of the output format."""
    print()
    print("=" * 70)
    print("EXAMPLE: Agent Output Format")
    print("=" * 70)
    print()

    example = create_agent_output(
        status="success",
        summary="Implemented user authentication API",
        deliverables=["api/auth.ts", "middleware/jwt.ts"],
        next_steps=["write tests", "deploy"],
        human_content="""
## What I Did

I implemented a JWT-based authentication system with login, logout,
and token refresh endpoints.

### Code Example
```typescript
export async function login(req: Request, res: Response) {
  const token = jwt.sign({ userId }, SECRET);
  res.json({ token });
}
```

### Next Steps
Write unit tests and deploy to staging.
""",
        agent_name="coder",
        task_id="example-1",
        duration_seconds=120,
    )

    print(example)
    print()


if __name__ == "__main__":
    main()
