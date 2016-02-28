from locust import HttpLocust, TaskSet, task
import random


class UserBehavior(TaskSet):
    def on_start(self):
        """ on_start is called when a L ocust start before any task is scheduled """
        self.login()

    def login(self):
        self.client.post("/test", json={'name':'Ananth','email':'weed@hemp.org','mlh_id':random.randint(1,200000000)})

    @task(2)
    def index(self):
        self.client.get("/")

    @task(1)
    def dashboard(self):
        self.client.get("/dashboard")

    @task(1)
    def confirm_status(self):
        self.client.get("/confirmstatus")

    @task(1)
    def confirmed(self):
        self.client.get("/confirmed")

    @task(1)
    def not_attending(self):
        self.client.get("/notattending")

    @task(1)
    def account(self):
        self.client.get("/account")

    @task(1)
    def register(self):
        self.client.get("/register")

    @task(1)
    def post_register_no_file(self):
        self.client.post("/account", json={'github': 'sakib', 'comments': 'alksdfandf'})

    @task(1)
    def post_account_no_file(self):
        self.client.post("/account", json={'github': 'sakib', 'comments': 'alksdfandf'})

class WebsiteUser(HttpLocust):
    task_set = UserBehavior
    min_wait=500
    max_wait=100000
