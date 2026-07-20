# API 처리 시간 측정

import logging
from time import perf_counter

from fastapi import Request, Response


performance_logger = logging.getLogger("uvicorn.error")


async def log_api_performance(
    request: Request,
    call_next,
) -> Response:
    path = request.url.path

    # 사용자 및 인증 API만 측정
    is_target_api = (
        "/v1/users" in path
        or "/v1/auth" in path
    )

    if not is_target_api:
        return await call_next(request)

    started_at = perf_counter()
    status_code = 500

    try:
        response = await call_next(request)
        status_code = response.status_code

        return response
    finally:
        duration_ms = (
            perf_counter() - started_at
        ) * 1000

        # 라우팅이 완료된 후 실제 라우트 패턴을 가져옴
        route = request.scope.get("route")
        endpoint = getattr(route, "path", path)

        log_message = (
            "api_performance "
            f"method={request.method} "
            f"endpoint={endpoint} "
            f"status_code={status_code} "
            f"duration_ms={duration_ms:.2f}"
        )

        if duration_ms > 3000:
            performance_logger.warning(log_message)
        else:
            performance_logger.info(log_message)