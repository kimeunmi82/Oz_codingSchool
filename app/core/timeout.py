import asyncio

from fastapi import HTTPException
from fastapi.routing import APIRoute


class TimeoutRoute(APIRoute):
    timeout_seconds = 3.0

    def get_route_handler(self):
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request):
            try:
                return await asyncio.wait_for(
                    original_route_handler(request),
                    timeout=self.timeout_seconds,
                )
            except asyncio.TimeoutError:
                raise HTTPException(
                    status_code=504,
                    detail=f"요청 처리 시간이 {self.timeout_seconds}초를 초과했습니다.",
                )

        return custom_route_handler