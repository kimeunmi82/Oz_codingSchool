from pwdlib import PasswordHash

from starlette.concurrency import run_in_threadpool

password_hash = PasswordHash.recommended()


def hash_password(plain_password: str) -> str:
    return password_hash.hash(plain_password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    return password_hash.verify(
        plain_password,
        hashed_password,
    )

#비동기 함수 추가

async def hash_password_async(
    plain_password: str,
) -> str:
    return await run_in_threadpool(
        hash_password,
        plain_password,
    )


async def verify_password_async(
    plain_password: str,
    hashed_password: str,
) -> bool:
    return await run_in_threadpool(
        verify_password,
        plain_password,
        hashed_password,
    )