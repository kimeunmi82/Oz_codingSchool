import os

from locust import HttpUser, between, task
from locust.exception import StopUser


TEST_EMAIL = os.getenv("PERF_TEST_EMAIL")
TEST_PASSWORD = os.getenv("PERF_TEST_PASSWORD")


class UserApiPerformanceUser(HttpUser):
    wait_time = between(1, 2)

    def on_start(self):
        if not TEST_EMAIL or not TEST_PASSWORD:
            raise RuntimeError(
                "PERF_TEST_EMAIL과 PERF_TEST_PASSWORD가 필요합니다."
            )

        with self.client.post(
            "/auth_api/v1/auth/login/",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
            },
            name="/v1/auth/login/",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(
                    f"로그인 실패: {response.status_code}"
                )
                raise StopUser()

            response_data = response.json()
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
    # 마이페이지 조회
    @task(8)
    def get_my_page(self):
        with self.client.get(
            "/mypage_api/v1/users/me",
            name="/v1/users/me",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(
                    f"마이페이지 조회 실패: "
                    f"{response.status_code}"
                )
    # 사용자 목록 조회
    @task(3)
    def get_user_list(self):
        with self.client.get(
            "/user_api/v1/users",
            params={
                "page": 1,
                "page_size": 20,
            },
            name="/v1/users",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(
                    f"사용자 목록 조회 실패: "
                    f"{response.status_code}"
                )
                return

            try:
                response_data = response.json()
            except ValueError:
                response.failure(
                    "사용자 목록 응답이 JSON이 아닙니다."
                )
                return

            if not isinstance(response_data, list):
                response.failure(
                    "사용자 목록 응답이 배열이 아닙니다."
                )
    # Access Token 갱신            
    @task(1)
    def refresh_access_token(self):
        with self.client.post(
            "/auth_api/v1/auth/refresh/",
            name="/v1/auth/refresh/",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(
                    f"토큰 갱신 실패: "
                    f"{response.status_code}"
                )
                return

            try:
                response_data = response.json()
            except ValueError:
                response.failure(
                    "토큰 갱신 응답이 JSON이 아닙니다."
                )
                return

            new_access_token = response_data.get(
                "access_token"
            )

            if not new_access_token:
                response.failure(
                    "갱신 응답에 access_token이 없습니다."
                )
                return

            self.client.headers.update(
                {
                    "Authorization": (
                        f"Bearer {new_access_token}"
                    )
                }
            )