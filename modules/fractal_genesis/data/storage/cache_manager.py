"""Cache manager with file-based and in-memory LRU caching."""

import json
import hashlib
import time
from pathlib import Path
from typing import Any, Optional, Dict, Callable
from functools import wraps
from collections import OrderedDict
import threading


class FileCache:
    """File-based cache with mtime invalidation."""

    def __init__(self, cache_dir: str, ttl_seconds: int = 300):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_seconds = ttl_seconds
        self._lock = threading.Lock()

    def _get_cache_key(self, file_path: str) -> str:
        """Generate cache key from file path."""
        return hashlib.md5(file_path.encode()).hexdigest()

    def _get_cache_path(self, cache_key: str) -> Path:
        """Get cache file path for key."""
        return self.cache_dir / f"{cache_key}.json"

    def _get_meta_path(self, cache_key: str) -> Path:
        """Get metadata file path for key."""
        return self.cache_dir / f"{cache_key}.meta.json"

    def get(self, file_path: str) -> Optional[Any]:
        """Get cached data if valid."""
        with self._lock:
            cache_key = self._get_cache_key(file_path)
            cache_path = self._get_cache_path(cache_key)
            meta_path = self._get_meta_path(cache_key)

            if not cache_path.exists() or not meta_path.exists():
                return None

            # Check metadata
            try:
                with open(meta_path, "r") as f:
                    meta = json.load(f)
            except (json.JSONDecodeError, IOError):
                return None

            file_stat = Path(file_path).stat()
            current_mtime = file_stat.st_mtime
            current_size = file_stat.st_size

            # Validate cache
            if meta.get("mtime") != current_mtime or meta.get("size") != current_size:
                return None

            # Check TTL
            if time.time() - meta.get("cached_at", 0) > self.ttl_seconds:
                return None

            # Load cached data
            try:
                with open(cache_path, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return None

    def set(self, file_path: str, data: Any) -> None:
        """Cache data for file."""
        with self._lock:
            cache_key = self._get_cache_key(file_path)
            cache_path = self._get_cache_path(cache_key)
            meta_path = self._get_meta_path(cache_key)

            file_stat = Path(file_path).stat()

            meta = {
                "mtime": file_stat.st_mtime,
                "size": file_stat.st_size,
                "cached_at": time.time(),
                "path": file_path
            }

            try:
                with open(cache_path, "w") as f:
                    json.dump(data, f)
                with open(meta_path, "w") as f:
                    json.dump(meta, f)
            except IOError:
                pass

    def invalidate(self, file_path: str) -> None:
        """Invalidate cache for file."""
        with self._lock:
            cache_key = self._get_cache_key(file_path)
            cache_path = self._get_cache_path(cache_key)
            meta_path = self._get_meta_path(cache_key)

            if cache_path.exists():
                cache_path.unlink()
            if meta_path.exists():
                meta_path.unlink()

    def clear(self) -> None:
        """Clear all cached data."""
        with self._lock:
            for f in self.cache_dir.glob("*.json"):
                f.unlink()


class MemoryCache:
    """In-memory LRU cache for hot data."""

    def __init__(self, max_entries: int = 1000, ttl_seconds: int = 86400):
        self.max_entries = max_entries
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._lock = threading.Lock()

    def _generate_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments."""
        key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
        return hashlib.md5(key_data.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """Get cached value if valid."""
        with self._lock:
            if key not in self._cache:
                return None

            entry = self._cache[key]

            # Check TTL
            if time.time() - entry.get("cached_at", 0) > self.ttl_seconds:
                del self._cache[key]
                return None

            # Move to end (most recently used)
            self._cache.move_to_end(key)
            return entry.get("data")

    def set(self, key: str, data: Any) -> None:
        """Cache value."""
        with self._lock:
            # Evict oldest if at capacity
            while len(self._cache) >= self.max_entries:
                self._cache.popitem(last=False)

            self._cache[key] = {
                "data": data,
                "cached_at": time.time()
            }
            self._cache.move_to_end(key)

    def invalidate(self, key: str) -> None:
        """Invalidate specific key."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]

    def clear(self) -> None:
        """Clear all cached data."""
        with self._lock:
            self._cache.clear()

    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        with self._lock:
            return {
                "entries": len(self._cache),
                "max_entries": self.max_entries
            }


class CacheManager:
    """Unified cache manager for file and memory caching."""

    def __init__(self, cache_root: str = "~/.blackbox5/.cache"):
        self.cache_root = Path(cache_root).expanduser()
        self.cache_root.mkdir(parents=True, exist_ok=True)

        # Initialize caches
        self.file_cache = FileCache(str(self.cache_root / "files"))
        self.memory_cache = MemoryCache()

        # Statistics
        self._hits = {"file": 0, "memory": 0}
        self._misses = {"file": 0, "memory": 0}

    def get_file_cached(self, file_path: str, loader: Callable[[], Any]) -> Any:
        """Get data with file-based caching."""
        cached = self.file_cache.get(file_path)
        if cached is not None:
            self._hits["file"] += 1
            return cached

        self._misses["file"] += 1
        data = loader()
        self.file_cache.set(file_path, data)
        return data

    def get_memory_cached(self, key: str, loader: Callable[[], Any]) -> Any:
        """Get data with memory-based caching."""
        cached = self.memory_cache.get(key)
        if cached is not None:
            self._hits["memory"] += 1
            return cached

        self._misses["memory"] += 1
        data = loader()
        self.memory_cache.set(key, data)
        return data

    def get_embedding_cached(self, text: str, model_version: str, loader: Callable[[], Any]) -> Any:
        """Get embedding with specialized caching."""
        text_hash = hashlib.md5(text.encode()).hexdigest()
        key = f"embedding:{text_hash}:{model_version}"
        return self.get_memory_cached(key, loader)

    def get_skill_cached(self, file_path: str, loader: Callable[[], Any]) -> Any:
        """Get skill YAML with file-based caching."""
        return self.get_file_cached(file_path, loader)

    def get_queue_cached(self, queue_path: str, loader: Callable[[], Any]) -> Any:
        """Get queue data with file-based caching."""
        return self.get_file_cached(queue_path, loader)

    def get_task_scan_cached(self, tasks_dir: str, loader: Callable[[], Any]) -> Any:
        """Get task directory scan with file-based caching."""
        return self.get_file_cached(tasks_dir, loader)

    def invalidate_file(self, file_path: str) -> None:
        """Invalidate file cache."""
        self.file_cache.invalidate(file_path)

    def invalidate_memory(self, key: str) -> None:
        """Invalidate memory cache."""
        self.memory_cache.invalidate(key)

    def clear_all(self) -> None:
        """Clear all caches."""
        self.file_cache.clear()
        self.memory_cache.clear()
        self._hits = {"file": 0, "memory": 0}
        self._misses = {"file": 0, "memory": 0}

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_file = self._hits["file"] + self._misses["file"]
        total_memory = self._hits["memory"] + self._misses["memory"]

        return {
            "file_cache": {
                "hits": self._hits["file"],
                "misses": self._misses["file"],
                "hit_rate": self._hits["file"] / total_file if total_file > 0 else 0
            },
            "memory_cache": {
                "hits": self._hits["memory"],
                "misses": self._misses["memory"],
                "hit_rate": self._hits["memory"] / total_memory if total_memory > 0 else 0,
                "stats": self.memory_cache.get_stats()
            }
        }


def cached(cache_type: str = "memory", key_func: Optional[Callable] = None):
    """Decorator for caching function results.

    Args:
        cache_type: "memory" or "file"
        key_func: Optional function to generate cache key from args
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get or create cache manager
            cache = getattr(wrapper, "_cache", None)
            if cache is None:
                cache = CacheManager()
                wrapper._cache = cache

            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{hashlib.md5(str(args).encode()).hexdigest()}"

            if cache_type == "memory":
                return cache.get_memory_cached(cache_key, lambda: func(*args, **kwargs))
            else:
                # For file cache, first arg is assumed to be file path
                file_path = args[0] if args else cache_key
                return cache.get_file_cached(file_path, lambda: func(*args, **kwargs))

        return wrapper
    return decorator
