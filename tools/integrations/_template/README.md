# {SERVICE_NAME} Integration for BlackBox5

> **NOTE:** This is a template directory for creating new integrations.
> Files contain placeholder syntax like `{SERVICE_NAME}`, `{ServiceName}`, etc.
> which should be replaced when creating a new integration from this template.
> These placeholder markers intentionally cause syntax errors - they are not bugs.

{BRIEF_DESCRIPTION_OF_WHAT_THIS_INTEGRATION_DOES}

## Features

- **Feature 1**: Description of primary capability
- **Feature 2**: Description of secondary capability
- **Feature 3**: Description of additional capability

## Architecture

### Components

- **`{ServiceName}Manager`**: Main manager class for all operations
- **`DataType`**: Data class for {specific entity}
- **`EnumType`**: Enum for {options/statuses}

## Requirements

### Authentication

1. **Get API Token**:
   - Navigate to {URL_TO_GET_TOKEN}
   - Create {TOKEN_TYPE} with permissions:
     - Permission 1
     - Permission 2
   - Copy token and set as environment variable:
     ```bash
     export {SERVICE_NAME}_TOKEN="your_token_here"
     ```

2. **Additional Configuration** (if needed):
   - {CONFIG_ITEM_1}
   - {CONFIG_ITEM_2}

### Python Dependencies

```bash
pip install {LIBRARY_NAME}
```

Add to `.blackbox5/engine/requirements.txt`:
```txt
{LIBRARY_NAME}>=1.0.0
```

## Usage

### Basic Usage

```python
import asyncio
from integration.{SERVICE_LOWER} import {ServiceName}Manager

async def main():
    # Initialize manager
    manager = {ServiceName}Manager(
        token="{ENV_VAR_NAME}",
        # additional_params
    )

    # Perform operation
    result = await manager.{operation_name}()

    # Close connection
    await manager.close()

asyncio.run(main())
```

### Advanced Usage

{ADVANCED_EXAMPLE}

## API Reference

### Methods

| Method | Description | Parameters | Returns |
|--------|-------------|------------|---------|
| `method_name` | Description | `param1`, `param2` | `ReturnType` |

### Data Classes

#### `DataType`

| Field | Type | Description |
|-------|------|-------------|
| `field1` | `str` | Description |
| `field2` | `int` | Description |

## Error Handling

```python
from {SERVICE_LOWER}_exceptions import {ServiceName}Error

try:
    result = await manager.operation()
except {ServiceName}Error as e:
    print(f"Error: {e}")
```

## Rate Limits

- **Rate Limit**: {RATE_LIMIT_DETAILS}
- **Best Practices**: {BEST_PRACTICES}

## Testing

```bash
# Run tests
python .blackbox5/integration/{SERVICE_LOWER}/tests/test_integration.py
```

## Troubleshooting

### Common Issues

**Issue**: {COMMON_ISSUE}
- **Solution**: {SOLUTION}

## See Also

- {SERVICE_NAME} Documentation: {DOCS_URL}
- API Reference: {API_REF_URL}
