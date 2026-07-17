import os
from itertools import count

from locust import HttpUser, between, task
from locust.exception import StopUser


RUN_ID = int(os.getenv("PERF_RUN_ID", "41"))
TEST_PASSWORD = os.getenv(
    "PERF_TEST_PASSWORD",
    "Performance123!",
)
USER_SEQUENCE = count(1)


class RoleLogoutPerformanceUser(HttpUser):
    wait_time = between(1, 2)

    def on_start(self):
        sequence = next(USER_SEQUENCE)

        self.user_number = (
            (sequence - 1) % 100
        ) + 1

        self.email = (
            f"performance-{RUN_ID}-"
            f"{self.user_number:03d}@example.com"
        )

        self.current_role = "PENDING"

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
            user_data = response_data.get("user", {})
            user_id = user_data.get("id")

            if not access_token or not user_id:
                response.failure(
                    "로그인 응답에 토큰 또는 사용자 ID가 없습니다."
                )
                raise StopUser()

            self.user_id = user_id

            self.client.headers.update(
                {
                    "Authorization": (
                        f"Bearer {access_token}"
                    )
                }
            )

    @task(5)
    def update_role(self):
        new_role = (
            "STAFF"
            if self.current_role == "PENDING"
            else "PENDING"
        )

        with self.client.patch(
            (
                f"/user_api/v1/users/"
                f"{self.user_id}/role"
            ),
            json={
                "role": new_role,
            },
            name="/v1/users/{user_id}/role",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(
                    f"권한 변경 실패: "
                    f"{response.status_code}"
                )
                return

            try:
                response_data = response.json()
            except ValueError:
                response.failure(
                    "권한 변경 응답이 JSON이 아닙니다."
                )
                return

            expected_message = (
                "사용자 권한이 성공적으로 변경되었습니다."
            )

            if (
                response_data.get("message")
                != expected_message
            ):
                response.failure(
                    "권한 변경 성공 메시지가 올바르지 않습니다."
                )
                return

            self.current_role = new_role

    @task(1)
    def logout(self):
        with self.client.post(
            "/auth_api/v1/auth/logout/",
            name="/v1/auth/logout/",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(
                    f"로그아웃 실패: "
                    f"{response.status_code}"
                )
                return

            try:
                response_data = response.json()
            except ValueError:
                response.failure(
                    "로그아웃 응답이 JSON이 아닙니다."
                )
                return

            if (
                response_data.get("detail")
                != "로그아웃이 완료되었습니다."
            ):
                response.failure(
                    "로그아웃 성공 메시지가 올바르지 않습니다."
                )