import os
from itertools import count

from locust import HttpUser, constant, task


RUN_ID = int(os.getenv("PERF_RUN_ID", "37"))
TEST_PASSWORD = os.getenv(
    "PERF_TEST_PASSWORD",
    "Performance123!",
)
USER_SEQUENCE = count(1)


class SignupPerformanceUser(HttpUser):
    # 각 사용자는 회원가입 후 다시 실행하지 않도록 충분히 대기
    wait_time = constant(3600)

    def on_start(self):
        self.user_number = next(USER_SEQUENCE)
        self.signup_completed = False

    @task
    def signup(self):
        if self.signup_completed:
            return

        email = (
            f"performance-{RUN_ID}-"
            f"{self.user_number:03d}@example.com"
        )
        phone_number = (
            f"010-{RUN_ID:04d}-"
            f"{self.user_number:04d}"
        )

        with self.client.post(
            "/user_api/v1/users",
            json={
                "email": email,
                "password": TEST_PASSWORD,
                "name": (
                    f"성능테스트{self.user_number:03d}"
                ),
                "department": "DEV",
                "gender": "M",
                "phone_number": phone_number,
            },
            name="/v1/users/signup",
            catch_response=True,
        ) as response:
            if response.status_code != 201:
                response.failure(
                    f"회원가입 실패: "
                    f"{response.status_code}"
                )
                return

            self.signup_completed = True