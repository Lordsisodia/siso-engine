# Integration Template - Implementation Guide

## Template Structure

```
_template/
├── README.md              # Full documentation template
├── QUICKSTART.md          # Quick start guide template
├── __init__.py           # Package initialization
├── manager.py            # Main manager class template
├── types.py              # Data classes and enums
├── config.py             # Configuration helpers
├── demo.py               # Usage examples
└── tests/
    └── test_integration.py  # Test template
```

## Standard File Patterns

### 1. README.md (Required)
Must include:
- Brief description of integration
- Features list
- Authentication setup
- Usage examples
- API reference table
- Rate limits
- Troubleshooting section

### 2. QUICKSTART.md (Required)
Must include:
- Token acquisition steps
- Environment variable setup
- Installation commands
- 3-5 common operations with code examples
- Full working example

### 3. __init__.py (Required)
Must:
- Import main manager class
- Define `__all__` exports
- Include `__version__`
- Have module docstring

### 4. manager.py (Required)
Must include:
- `@dataclass` enums for statuses/types
- `@dataclass` data classes for entities
- `@dataclass` spec classes for operations
- Main `Manager` class with:
  - `API_BASE` and `API_VERSION` class constants
  - `__init__` with token from env var
  - `__aenter__` and `__aexit__` for async context
  - `close()` method
  - CRUD methods: create, get, update, delete, list
  - `check_connection()` helper

### 5. types.py (Optional)
Recommended for complex integrations with:
- Enums for options/statuses
- Data classes for entities
- Spec classes for operations
- Result classes

### 6. config.py (Optional)
For integrations with complex configuration:
- `Config` dataclass
- `from_env()` classmethod
- `from_file()` classmethod
- `get_default_config()` function

### 7. demo.py (Required)
Must:
- Load dotenv
- Check for required env vars
- Demonstrate 3-5 core operations
- Have clear output with emojis
- Be runnable directly

### 8. tests/test_integration.py (Required)
Must include tests for:
- Connection check
- Basic operations
- Entity CRUD
- Error handling

## Naming Conventions

| Type | Pattern | Example |
|------|---------|---------|
| Service | `ServiceName` | `GitHubActionsManager` |
| Manager | `{Service}Manager` | `NotionManager` |
| Enum | PascalCase | `CardStatus`, `EntityType` |
| Data Class | PascalCase | `CardData`, `WorkflowRun` |
| Spec Class | `{Entity}Spec` | `CardSpec`, `DeploymentSpec` |
| Methods | snake_case | `create_entity()`, `list_workflows()` |

## Code Standards

### All managers must:
1. Use `httpx.AsyncClient` for HTTP (sync for Obsidian)
2. Implement async context manager (`__aenter__`, `__aexit__`)
3. Use type hints everywhere
4. Use `logging.Logger` for logging
5. Handle `httpx.HTTPStatusError` with 404 checks
6. Return typed data classes, not raw dicts
7. Log operations with `✅` and `❌` emojis
8. Validate required parameters in `__init__`

### Environment Variables
Use this pattern:
- `{SERVICE}_TOKEN` - Required auth token
- `{SERVICE}_BASE_URL` - Optional API base URL
- `{SERVICE}_TIMEOUT` - Optional timeout
- `{SERVICE}_CONFIG` - Optional config file path

### Logging Levels
- `INFO`: Operations, successes, failures
- `DEBUG`: API calls, responses
- `WARNING`: Missing entities, retries
- `ERROR`: API errors, exceptions

## Implementation Checklist

For each new integration:

- [ ] Copy `_template/` to `{service}/`
- [ ] Replace all placeholders (`{SERVICE_NAME}`, etc.)
- [ ] Implement manager class with all CRUD methods
- [ ] Create enums and data classes in types.py
- [ ] Implement config helper if needed
- [ ] Write demo.py with 3-5 examples
- [ ] Write tests for core operations
- [ ] Update README.md with actual API docs
- [ ] Update QUICKSTART.md with actual steps
- [ ] Add service-specific notes to IMPLEMENTATION-GUIDE.md
- [ ] Test demo.py with real API
- [ ] Run tests and ensure they pass

## Existing Integrations to Update

1. **github/** - Reorganize to match template
2. **vibe/** - Reorganize to match template

## New Integrations to Create

1. **github-actions/** - Workflow automation
2. **notion/** - Documentation sync
3. **obsidian/** - Markdown export
4. **vercel/** - Deployment management
5. **supabase/** - Database/storage
6. **cloudflare/** - DNS/Workers/storage
