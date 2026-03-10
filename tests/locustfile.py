from locust import HttpUser, task, between

class StudyBotUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def reply(self):
        self.client.post("/reply", json={
            "client": "discord",
            "userid": "test_user",
            "message": "Hello, how are you?"
        })
