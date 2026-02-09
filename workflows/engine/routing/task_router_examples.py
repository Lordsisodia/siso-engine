"""
Task Router Examples for BlackBox 5

This module contains practical examples demonstrating how to use
the TaskRouter for intelligent task routing in a multi-agent system.

All examples are runnable and demonstrate real-world use cases.
"""

import asyncio
from datetime import datetime
from typing import List

from task_types import (
    Task,
    TaskPriority,
    ExecutionStrategy,
    AgentType,
    AgentCapabilities,
    RoutingConfig,
)
from complexity import TaskComplexityAnalyzer, ComplexityThreshold
from task_router import TaskRouter


# ============================================================================
# Example 1: Basic Task Routing
# ============================================================================

def example_1_basic_routing():
    """
    Example 1: Basic task routing with default configuration.

    Demonstrates the simplest way to route tasks using the TaskRouter.
    """
    print("\n" + "="*60)
    print("Example 1: Basic Task Routing")
    print("="*60)

    # Create a task router with default configuration
    router = TaskRouter()

    # Register some agents
    router.register_agent(AgentCapabilities(
        agent_id="executor-1",
        agent_type=AgentType.EXECUTOR,
        domains={"general", "development"},
        tools={"read", "write", "bash"},
        max_complexity=0.5,
        avg_duration=30.0,
        success_rate=0.95
    ))

    router.register_agent(AgentCapabilities(
        agent_id="orchestrator-1",
        agent_type=AgentType.ORCHESTRATOR,
        domains={"general", "development", "architecture"},
        tools={"read", "write", "bash", "git", "mcp"},
        max_complexity=1.0,
        avg_duration=120.0,
        success_rate=0.90
    ))

    # Create and route a simple task
    simple_task = Task(
        description="Fix the typo in the README file",
        domain="development",
        tools_required=["read", "write"],
        files=["README.md"]
    )

    decision = router.route(simple_task)

    print(f"\nTask: {simple_task.description}")
    print(f"Strategy: {decision.strategy.value}")
    print(f"Agent Type: {decision.agent_type.value}")
    print(f"Recommended Agent: {decision.recommended_agent}")
    print(f"Complexity Score: {decision.complexity.aggregate_score:.2f}")
    print(f"Estimated Duration: {decision.estimated_duration:.1f}s")
    print(f"Reasoning: {decision.reasoning}")

    # Create and route a complex task
    complex_task = Task(
        description="Implement a new authentication system with OAuth2, "
                   "JWT tokens, and session management across multiple services",
        domain="development",
        tools_required=["read", "write", "bash", "git", "mcp", "database"],
        requirements=[
            "OAuth2 integration",
            "JWT token management",
            "Session persistence",
            "Multi-service coordination"
        ]
    )

    decision = router.route(complex_task)

    print(f"\nTask: {complex_task.description}")
    print(f"Strategy: {decision.strategy.value}")
    print(f"Agent Type: {decision.agent_type.value}")
    print(f"Complexity Score: {decision.complexity.aggregate_score:.2f}")
    print(f"Estimated Duration: {decision.estimated_duration:.1f}s")


# ============================================================================
# Example 2: Complexity Analysis
# ============================================================================

def example_2_complexity_analysis():
    """
    Example 2: Detailed complexity analysis.

    Demonstrates how to analyze task complexity in detail.
    """
    print("\n" + "="*60)
    print("Example 2: Complexity Analysis")
    print("="*60)

    analyzer = TaskComplexityAnalyzer()

    tasks = [
        Task(
            description="Update the copyright year in all files",
            domain="general",
            tools_required=["read", "write", "bash"],
            requirements=["Find all files with copyright", "Update year to 2025"]
        ),
        Task(
            description="Refactor the user authentication module to use "
                       "the new identity provider service",
            domain="development",
            tools_required=["read", "write", "git", "database"],
            requirements=[
                "Migrate existing users",
                "Update authentication flow",
                "Maintain backward compatibility"
            ]
        ),
        Task(
            description="Design and implement a microservices architecture "
                       "for the e-commerce platform with service mesh, API gateway, "
                       "and distributed tracing",
            domain="architecture",
            tools_required=["read", "write", "bash", "git", "docker", "kubernetes"],
            requirements=[
                "Service design",
                "Inter-service communication",
                "Observability",
                "Deployment automation"
            ]
        ),
    ]

    for task in tasks:
        complexity = analyzer.analyze(task)

        print(f"\n{'='*60}")
        print(f"Task: {task.description[:60]}...")
        print(f"{'='*60}")
        print(f"Domain: {task.domain}")
        print(f"Token Count: {complexity.token_count}")
        print(f"Step Complexity: {complexity.step_complexity} steps")
        print(f"\nComplexity Scores:")
        print(f"  - Token-based: {complexity.token_count / analyzer._analyze_token_complexity(complexity.token_count):.2f}")
        print(f"  - Tool Requirements: {complexity.tool_requirements:.2f}")
        print(f"  - Domain: {complexity.domain_complexity:.2f}")
        print(f"  - Aggregate: {complexity.aggregate_score:.2f}")
        print(f"  - Confidence: {complexity.confidence:.2f}")


# ============================================================================
# Example 3: Single-Agent Routing
# ============================================================================

def example_3_single_agent_routing():
    """
    Example 3: Tasks that route to single agents.

    Demonstrates what kinds of tasks are suitable for single-agent execution.
    """
    print("\n" + "="*60)
    print("Example 3: Single-Agent Routing")
    print("="*60)

    router = TaskRouter(config=RoutingConfig(complexity_threshold=0.7))

    # Register agents
    router.register_agent(AgentCapabilities(
        agent_id="executor-simple",
        agent_type=AgentType.EXECUTOR,
        domains={"general", "documentation", "testing"},
        tools={"read", "write"},
        max_complexity=0.4,
        avg_duration=20.0,
        success_rate=0.98
    ))

    router.register_agent(AgentCapabilities(
        agent_id="generalist-dev",
        agent_type=AgentType.GENERALIST,
        domains={"development"},
        tools={"read", "write", "bash", "git"},
        max_complexity=0.6,
        avg_duration=45.0,
        success_rate=0.92
    ))

    # Single-agent suitable tasks
    single_agent_tasks = [
        Task(
            description="Add a new API endpoint for user profile",
            domain="development",
            tools_required=["read", "write"],
            files=["src/api/users.py"]
        ),
        Task(
            description="Update the installation documentation",
            domain="documentation",
            tools_required=["read", "write"],
            files=["docs/installation.md"]
        ),
        Task(
            description="Fix the failing unit test for authentication",
            domain="testing",
            tools_required=["read", "write", "bash"],
            files=["tests/test_auth.py"]
        ),
    ]

    print("\nTasks suitable for single-agent execution:")
    print("-" * 60)

    single_count = 0
    for task in single_agent_tasks:
        decision = router.route(task)
        if decision.strategy == ExecutionStrategy.SINGLE_AGENT:
            single_count += 1
            print(f"\n✓ {task.description[:50]}...")
            print(f"  Agent: {decision.recommended_agent}")
            print(f"  Complexity: {decision.complexity.aggregate_score:.2f}")
            print(f"  Est. Duration: {decision.estimated_duration:.1f}s")

    print(f"\n{single_count}/{len(single_agent_tasks)} tasks routed to single agent")


# ============================================================================
# Example 4: Multi-Agent Routing
# ============================================================================

def example_4_multi_agent_routing():
    """
    Example 4: Tasks that require multi-agent coordination.

    Demonstrates complex tasks that benefit from multi-agent execution.
    """
    print("\n" + "="*60)
    print("Example 4: Multi-Agent Routing")
    print("="*60)

    router = TaskRouter(
        config=RoutingConfig(
            complexity_threshold=0.5,
            step_threshold=8
        )
    )

    # Register agents
    router.register_agent(AgentCapabilities(
        agent_id="orchestrator-main",
        agent_type=AgentType.ORCHESTRATOR,
        domains={"general", "development", "architecture", "integration"},
        tools={"read", "write", "bash", "git", "mcp", "database", "api"},
        max_complexity=1.0,
        avg_duration=180.0,
        success_rate=0.88
    ))

    # Multi-agent suitable tasks
    multi_agent_tasks = [
        Task(
            description="Migrate the monolithic application to microservices "
                       "architecture with service mesh and API gateway",
            domain="architecture",
            tools_required=["read", "write", "bash", "git", "docker", "kubernetes"],
            requirements=[
                "Design service boundaries",
                "Implement API gateway",
                "Setup service mesh",
                "Migrate data layer"
            ]
        ),
        Task(
            description="Implement a complete CI/CD pipeline with automated testing, "
                       "code quality checks, security scanning, and multi-stage deployments",
            domain="development",
            tools_required=["read", "write", "bash", "git", "docker"],
            requirements=[
                "Setup build pipeline",
                "Configure automated tests",
                "Integrate security scanning",
                "Setup deployment automation"
            ]
        ),
        Task(
            description="Research and evaluate different database solutions for "
                       "high-availability distributed systems and create a recommendation",
            domain="research",
            tools_required=["read", "bash", "mcp"],
            requirements=[
                "Evaluate PostgreSQL",
                "Evaluate MongoDB",
                "Evaluate distributed databases",
                "Create comparison matrix",
                "Provide recommendations"
            ]
        ),
    ]

    print("\nTasks requiring multi-agent coordination:")
    print("-" * 60)

    multi_count = 0
    for task in multi_agent_tasks:
        decision = router.route(task)
        if decision.strategy == ExecutionStrategy.MULTI_AGENT:
            multi_count += 1
            print(f"\n✓ {task.description[:60]}...")
            print(f"  Agent: {decision.recommended_agent}")
            print(f"  Complexity: {decision.complexity.aggregate_score:.2f}")
            print(f"  Steps: {decision.complexity.step_complexity}")
            print(f"  Est. Duration: {decision.estimated_duration:.1f}s")

    print(f"\n{multi_count}/{len(multi_agent_tasks)} tasks routed to multi-agent")


# ============================================================================
# Example 5: Custom Threshold Configuration
# ============================================================================

def example_5_custom_thresholds():
    """
    Example 5: Custom complexity thresholds.

    Demonstrates how to configure thresholds for different use cases.
    """
    print("\n" + "="*60)
    print("Example 5: Custom Threshold Configuration")
    print("="*60)

    # Same task, different thresholds
    task = Task(
        description="Implement a new feature with database integration, "
                   "API endpoints, and unit tests",
        domain="development",
        tools_required=["read", "write", "bash", "git", "database"],
        requirements=[
            "Database schema design",
            "API implementation",
            "Unit test coverage"
        ]
    )

    # Conservative: prefers multi-agent
    router_conservative = TaskRouter(
        config=RoutingConfig(complexity_threshold=ComplexityThreshold.conservative())
    )

    # Balanced: equal single/multi-agent
    router_balanced = TaskRouter(
        config=RoutingConfig(complexity_threshold=ComplexityThreshold.balanced())
    )

    # Aggressive: prefers single-agent
    router_aggressive = TaskRouter(
        config=RoutingConfig(complexity_threshold=ComplexityThreshold.aggressive())
    )

    # Register agents for all routers
    for router in [router_conservative, router_balanced, router_aggressive]:
        router.register_agent(AgentCapabilities(
            agent_id="executor",
            agent_type=AgentType.EXECUTOR,
            domains={"development"},
            tools={"read", "write", "bash", "git", "database"},
            max_complexity=0.7,
            avg_duration=60.0,
            success_rate=0.90
        ))
        router.register_agent(AgentCapabilities(
            agent_id="orchestrator",
            agent_type=AgentType.ORCHESTRATOR,
            domains={"development"},
            tools={"read", "write", "bash", "git", "database", "mcp"},
            max_complexity=1.0,
            avg_duration=180.0,
            success_rate=0.85
        ))

    print(f"\nTask: {task.description[:60]}...")
    print("-" * 60)

    for name, router in [
        ("Conservative (0.40)", router_conservative),
        ("Balanced (0.60)", router_balanced),
        ("Aggressive (0.80)", router_aggressive),
    ]:
        decision = router.route(task)
        print(f"\n{name}:")
        print(f"  Strategy: {decision.strategy.value}")
        print(f"  Complexity: {decision.complexity.aggregate_score:.2f}")
        print(f"  Threshold: {router.config.complexity_threshold:.2f}")


# ============================================================================
# Example 6: Agent Selection
# ============================================================================

def example_6_agent_selection():
    """
    Example 6: Intelligent agent selection based on capabilities.

    Demonstrates how the router selects the best agent for a task.
    """
    print("\n" + "="*60)
    print("Example 6: Agent Selection")
    print("="*60)

    router = TaskRouter()

    # Register multiple agents with different capabilities
    agents = [
        AgentCapabilities(
            agent_id="executor-junior",
            agent_type=AgentType.EXECUTOR,
            domains={"development"},
            tools={"read", "write"},
            max_complexity=0.3,
            avg_duration=30.0,
            success_rate=0.85
        ),
        AgentCapabilities(
            agent_id="generalist-senior",
            agent_type=AgentType.GENERALIST,
            domains={"development", "testing"},
            tools={"read", "write", "bash", "git"},
            max_complexity=0.6,
            avg_duration=45.0,
            success_rate=0.95
        ),
        AgentCapabilities(
            agent_id="specialist-db",
            agent_type=AgentType.SPECIALIST,
            domains={"development", "database"},
            tools={"read", "write", "bash", "git", "database", "mcp"},
            max_complexity=0.9,
            avg_duration=90.0,
            success_rate=0.92
        ),
    ]

    for agent in agents:
        router.register_agent(agent)

    # Task requiring database expertise
    task = Task(
        description="Optimize database queries for the user dashboard",
        domain="database",
        tools_required=["read", "write", "database", "bash"],
        files=["src/dashboard/queries.sql"]
    )

    decision = router.route(task)

    print(f"\nTask: {task.description}")
    print("-" * 60)
    print(f"Selected Agent: {decision.recommended_agent}")
    print(f"Agent Type: {decision.agent_type.value}")
    print(f"Reasoning: {decision.reasoning}")

    # Show all capable agents
    print(f"\nAll agents evaluated:")
    for agent in agents:
        can_handle = agent.can_handle_task(task, decision.complexity)
        print(f"  {agent.agent_id}: {'✓ Capable' if can_handle else '✗ Not capable'}")


# ============================================================================
# Example 7: Routing Statistics
# ============================================================================

def example_7_routing_statistics():
    """
    Example 7: Tracking routing statistics.

    Demonstrates how to monitor and analyze routing patterns.
    """
    print("\n" + "="*60)
    print("Example 7: Routing Statistics")
    print("="*60)

    router = TaskRouter()

    # Register agents
    router.register_agent(AgentCapabilities(
        agent_id="executor-1",
        agent_type=AgentType.EXECUTOR,
        domains={"general", "development", "documentation"},
        tools={"read", "write"},
        max_complexity=0.4,
        avg_duration=30.0,
        success_rate=0.95
    ))

    router.register_agent(AgentCapabilities(
        agent_id="orchestrator-1",
        agent_type=AgentType.ORCHESTRATOR,
        domains={"general", "development", "architecture"},
        tools={"read", "write", "bash", "git", "mcp"},
        max_complexity=1.0,
        avg_duration=120.0,
        success_rate=0.90
    ))

    # Route various tasks
    tasks = [
        Task(description="Fix typo in README", domain="documentation", tools_required=["read", "write"]),
        Task(description="Add new API endpoint", domain="development", tools_required=["read", "write"]),
        Task(description="Update dependencies", domain="development", tools_required=["read", "write", "bash"]),
        Task(description="Implement authentication system", domain="development", tools_required=["read", "write", "git", "database"]),
        Task(description="Design microservices architecture", domain="architecture", tools_required=["read", "write", "mcp"]),
        Task(description="Write unit tests", domain="testing", tools_required=["read", "write", "bash"]),
        Task(description="Update documentation", domain="documentation", tools_required=["read", "write"]),
        Task(description="Setup CI/CD pipeline", domain="development", tools_required=["read", "write", "bash", "git", "docker"]),
    ]

    for task in tasks:
        router.route(task)

    # Display statistics
    stats = router.get_statistics()

    print("\nRouting Statistics:")
    print("-" * 60)
    print(f"Total Tasks Routed: {stats['total_routed']}")
    print(f"Single-Agent: {stats['single_agent_routed']} "
          f"({stats['single_agent_percentage']:.1f}%)")
    print(f"Multi-Agent: {stats['multi_agent_routed']} "
          f"({100 - stats['single_agent_percentage']:.1f}%)")
    print(f"\nRegistered Agents: {stats['registered_agents']}")
    print("\nAgents by Type:")
    for agent_type, count in stats['agents_by_type'].items():
        print(f"  {agent_type}: {count}")

    print("\nTasks by Domain:")
    for domain, count in stats['by_domain'].items():
        print(f"  {domain}: {count}")


# ============================================================================
# Example 8: Domain-Specific Routing
# ============================================================================

def example_8_domain_routing():
    """
    Example 8: Domain-specific routing with specialized agents.

    Demonstrates routing across different domains with specialized agents.
    """
    print("\n" + "="*60)
    print("Example 8: Domain-Specific Routing")
    print("="*60)

    router = TaskRouter()

    # Register domain-specific specialists
    specialists = [
        ("dev-docs", AgentType.SPECIALIST, {"documentation"}, {"read", "write"}, 0.5, 25.0),
        ("dev-web", AgentType.SPECIALIST, {"development", "web"}, {"read", "write", "bash"}, 0.6, 45.0),
        ("dev-db", AgentType.SPECIALIST, {"development", "database"}, {"read", "write", "database"}, 0.7, 60.0),
        ("dev-ops", AgentType.SPECIALIST, {"development", "devops"}, {"read", "write", "bash", "git", "docker"}, 0.8, 90.0),
        ("arch-sys", AgentType.SPECIALIST, {"architecture"}, {"read", "write", "mcp"}, 1.0, 120.0),
    ]

    for agent_id, agent_type, domains, tools, max_comp, duration in specialists:
        router.register_agent(AgentCapabilities(
            agent_id=agent_id,
            agent_type=agent_type,
            domains=set(domains),
            tools=set(tools),
            max_complexity=max_comp,
            avg_duration=duration,
            success_rate=0.90
        ))

    # Domain-specific tasks
    tasks = [
        Task(description="Update API documentation", domain="documentation", tools_required=["read", "write"]),
        Task(description="Fix frontend bug", domain="web", tools_required=["read", "write"]),
        Task(description="Optimize database queries", domain="database", tools_required=["read", "database"]),
        Task(description="Setup Docker deployment", domain="devops", tools_required=["read", "write", "docker"]),
        Task(description="Design system architecture", domain="architecture", tools_required=["read", "mcp"]),
    ]

    print("\nDomain-Specific Task Routing:")
    print("-" * 60)

    for task in tasks:
        decision = router.route(task)
        print(f"\nDomain: {task.domain}")
        print(f"Task: {task.description}")
        print(f"Routed to: {decision.recommended_agent}")
        print(f"Strategy: {decision.strategy.value}")


# ============================================================================
# Example 9: Priority-Based Routing
# ============================================================================

def example_9_priority_routing():
    """
    Example 9: Priority-based task routing.

    Demonstrates how task priority affects routing and duration estimation.
    """
    print("\n" + "="*60)
    print("Example 9: Priority-Based Routing")
    print("="*60)

    router = TaskRouter()

    router.register_agent(AgentCapabilities(
        agent_id="executor-1",
        agent_type=AgentType.EXECUTOR,
        domains={"development"},
        tools={"read", "write", "bash"},
        max_complexity=0.5,
        avg_duration=30.0,
        success_rate=0.95
    ))

    # Same task, different priorities
    task_description = "Implement user profile update feature"

    priorities = [
        TaskPriority.LOW,
        TaskPriority.NORMAL,
        TaskPriority.HIGH,
        TaskPriority.CRITICAL,
    ]

    print(f"\nTask: {task_description}")
    print("-" * 60)

    for priority in priorities:
        task = Task(
            description=task_description,
            domain="development",
            tools_required=["read", "write"],
            priority=priority
        )

        decision = router.route(task)

        print(f"\nPriority: {priority.value.upper()}")
        print(f"  Strategy: {decision.strategy.value}")
        print(f"  Est. Duration: {decision.estimated_duration:.1f}s")


# ============================================================================
# Example 10: Explicit Strategy Override
# ============================================================================

def example_10_explicit_strategy():
    """
    Example 10: Explicitly specifying execution strategy.

    Demonstrates how to override automatic routing decisions.
    """
    print("\n" + "="*60)
    print("Example 10: Explicit Strategy Override")
    print("="*60)

    router = TaskRouter()

    router.register_agent(AgentCapabilities(
        agent_id="executor-1",
        agent_type=AgentType.EXECUTOR,
        domains={"development"},
        tools={"read", "write", "bash"},
        max_complexity=0.5,
        avg_duration=30.0,
        success_rate=0.95
    ))

    # Task that would normally be multi-agent
    task_auto = Task(
        description="Complex refactoring across multiple modules",
        domain="development",
        tools_required=["read", "write", "bash", "git"],
        requirements=["Refactor module A", "Refactor module B", "Update tests"]
    )

    # Force single-agent execution
    task_single = Task(
        description="Complex refactoring across multiple modules",
        domain="development",
        tools_required=["read", "write", "bash", "git"],
        requirements=["Refactor module A", "Refactor module B", "Update tests"],
        metadata={"strategy": "single_agent"}
    )

    print("\nAutomatic Routing:")
    decision_auto = router.route(task_auto)
    print(f"  Strategy: {decision_auto.strategy.value}")
    print(f"  Reasoning: {decision_auto.reasoning[:100]}...")

    print("\nExplicit Override (single_agent):")
    decision_single = router.route(task_single)
    print(f"  Strategy: {decision_single.strategy.value}")
    print(f"  Reasoning: {decision_single.reasoning[:100]}...")


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Run all examples."""
    print("\n" + "="*60)
    print("BlackBox 5 Task Router Examples")
    print("="*60)

    examples = [
        ("Basic Routing", example_1_basic_routing),
        ("Complexity Analysis", example_2_complexity_analysis),
        ("Single-Agent Routing", example_3_single_agent_routing),
        ("Multi-Agent Routing", example_4_multi_agent_routing),
        ("Custom Thresholds", example_5_custom_thresholds),
        ("Agent Selection", example_6_agent_selection),
        ("Routing Statistics", example_7_routing_statistics),
        ("Domain-Specific Routing", example_8_domain_routing),
        ("Priority-Based Routing", example_9_priority_routing),
        ("Explicit Strategy Override", example_10_explicit_strategy),
    ]

    for name, example_func in examples:
        try:
            example_func()
        except Exception as e:
            print(f"\nError in {name}: {e}")

    print("\n" + "="*60)
    print("All examples completed!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
