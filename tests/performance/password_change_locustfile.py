import os
from itertools import count

from locust import HttpUser, between, task
from locust.exception import StopUser


RUN_ID = int(os.getenv("PERF_RUN_ID", "37"))

PASSWORD_A = os.getenv(
    "PERF_TEST_PASSWORD",
    "Performance123!",
)
PASSWORD_B = os.getenv(
    "PERF_TEST_PASSWORD_B",
    "Performance456!",
)

USER_SEQUENCE = count(1)


class PasswordChangePerformanceUser(HttpUser):
    # 비밀번호 변경은 낮은 빈도로 실행
    wait_time = between(20, 30)

    def on_start(self):
        sequence = next(USER_SEQUENCE)

        self.user_number = (
            (sequence - 1) % 100
        ) + 1

        self.email = (
            f"performance-{RUN_ID}-"
            f"{self.user_number:03d}@example.com"
        )

        # 생성된 테스트 계정의 초기 비밀번호
        self.current_password = PASSWORD_A

        with self.client.post(
            "/auth_api/v1/auth/login/",
            json={
                "email": self.email,
                "password": self.current_password,
            },
            name="/v1/auth/login/",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(
                    f"로그인 실패: "
                    f"{response.status_code}"
                )
                raise StopUser()

            try:
                response_data = response.json()
            except ValueError:
                response.failure(
                    "로그인 응답이 JSON이 아닙니다."
                )
                raise StopUser()

            access_token = response_data.get(
                "access_token"
            )

            if not access_token:
                response.failure(
                    "응답에 access_token이 없습니다."
                )
                raise StopUser()

            self.client.headers.update(
                {
                    "Authorization": (
                        f"Bearer {access_token}"
                    )
                }
            )

    @task
    def change_password(self):
        new_password = (
            PASSWORD_B
            if self.current_password == PASSWORD_A
            else PASSWORD_A
        )

        with self.client.patch(
            "/mypage_api/v1/users/me/password/",
            json={
                "current_password": (
                    self.current_password
                ),
                "new_password": new_password,
            },
            name="/v1/users/me/password/",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(
                    f"비밀번호 변경 실패: "
                    f"{response.status_code}"
                )
                return

            try:
                response_data = response.json()
            except ValueError:
                response.failure(
                    "비밀번호 변경 응답이 JSON이 아닙니다."
                )
                return

            if (
                response_data.get("message")
                != "비밀번호가 변경되었습니다."
            ):
                response.failure(
                    "비밀번호 변경 성공 메시지가 올바르지 않습니다."
                )
                return

            # 성공한 경우에만 다음 요청의 현재 비밀번호 변경
            self.current_password = new_password