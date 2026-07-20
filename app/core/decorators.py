import asyncio
import inspect
import time
from functools import wraps

from fastapi import HTTPException


def enforce_timeout(seconds: float = 3.0):
    def decorator(func):
        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start = time.perf_counter()
                try:
                    return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
                except asyncio.TimeoutError:
                    raise HTTPException(
                        status_code=504,
                        detail=f"요청 처리 시간이 {seconds}초를 초과했습니다.",
                    )
                finally:
                    elapsed = time.perf_counter() - start
                    print(f"[TIMEOUT CHECK] {func.__name__}: {elapsed:.3f}s")

            return async_wrapper

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.perf_counter()
            result = func(*args, **kwargs)
            elapsed = time.perf_counter() - start

            print(f"[TIMEOUT CHECK] {func.__name__}: {elapsed:.3f}s")

            if elapsed > seconds:
                raise HTTPException(
                    status_code=504,
                    detail=f"요청 처리 시간이 {seconds}초를 초과했습니다.",
                )

            return result

        return sync_wrapper

    return decorator