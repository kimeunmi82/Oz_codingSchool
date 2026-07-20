import os
from itertools import count

from locust import HttpUser, between, task
from locust.exception import StopUser


RUN_ID = int(os.getenv("PERF_RUN_ID", "37"))
TEST_PASSWORD = os.getenv(
    "PERF_TEST_PASSWORD",
    "Performance123!",
)
USER_SEQUENCE = count(1)


class ProfileUpdatePerformanceUser(HttpUser):
    wait_time = between(1, 2)

    def on_start(self):
        sequence = next(USER_SEQUENCE)

        # 1~100번 테스트 계정을 순서대로 할당
        self.user_number = (
            (sequence - 1) % 100
        ) + 1

        self.email = (
            f"performance-{RUN_ID}-"
            f"{self.user_number:03d}@example.com"
        )

        self.department = "DEV"

        with self.client.post(
            "/auth_api/v1/auth/login/",
            json={
                "email": self.email,
                "password": TEST_PASSWORD,
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
    def update_my_profile(self):
        # 매 요청마다 값을 바꿔 실제 UPDATE가 발생하게 함
        self.department = (
            "RESEARCH"
            if self.department == "DEV"
            else "DEV"
        )

        with self.client.patch(
            "/mypage_api/v1/users/me",
            json={
                "department": self.department,
            },
            name="/v1/users/me",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(
                    f"회원 정보 수정 실패: "
                    f"{response.status_code}"
                )
                return

            try:
                response_data = response.json()
            except ValueError:
                response.failure(
                    "회원 정보 수정 응답이 JSON이 아닙니다."
                )
                return

            if (
                response_data.get("department")
                != self.department
            ):
                response.failure(
                    "변경된 부서가 응답과 일치하지 않습니다."
                )