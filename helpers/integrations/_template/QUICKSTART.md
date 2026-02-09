# {SERVICE_NAME} Integration - Quick Start

Get started with the {SERVICE_NAME} integration in 5 minutes.

## 1. Get Your API Token

{TOKEN_ACQUISITION_STEPS}

## 2. Configure Environment Variables

```bash
# Add to your .env or shell profile
export {SERVICE_UPPER}_TOKEN="your_token_here"
# Optional: additional config
export {SERVICE_UPPER}_CONFIG="value"
```

## 3. Install Dependencies

```bash
pip install {LIBRARY_NAME}
```

## 4. Basic Usage

### Initialize Manager

```python
from integration.{SERVICE_LOWER} import {ServiceName}Manager

manager = {ServiceName}Manager()
```

### Common Operations

#### Operation 1

```python
result = await manager.operation1()
print(result)
```

#### Operation 2

```python
result = await manager.operation2(param="value")
```

#### Operation 3

```python
result = await manager.operation3(id="123")
```

## 5. Full Example

```python
import asyncio
from integration.{SERVICE_LOWER} import {ServiceName}Manager

async def main():
    async with {ServiceName}Manager() as manager:
        # Do something
        result = await manager.some_operation()
        print(f"Success: {result}")

asyncio.run(main())
```

## Next Steps

- Read the [full documentation](README.md)
- Check out [examples](demo.py)
- Review the [API reference](README.md#api-reference)
