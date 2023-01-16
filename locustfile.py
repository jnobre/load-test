import time
import random
import gevent
import base64
from locust import HttpUser, task, between, TaskSet, events
from locust.runners import STATE_STOPPING, STATE_STOPPED, STATE_CLEANUP, WorkerRunner


class ProcessNumberTask(TaskSet):
    @task(1)
    def load(self):
        """request_body = {'username': 'janobre', 'password': 'user1'}
        self.client.post('/square-me', json=request_body, headers={'login-token': self.user.login_token})"""
        
        catalogue = self.client.get("/catalogue").json()
        category_item = random.choice(catalogue)
        item_id = category_item["id"]
        
        self.client.get("/")
        self.client.get("/category.html")
        self.client.get("/detail.html?id={}".format(item_id))
        self.client.delete("/cart")
        self.client.post("/cart", json={"id": item_id, "quantity": 1})
        self.client.get("/basket.html")
        self.client.post("/orders")

 
class TestUser(HttpUser):
    wait_time = between(0.5, 2.5)
    tasks = [ProcessNumberTask]
    login_token = ''
    is_login = False

    def on_start(self):
        with self.client.post('/login', json={'username': 'janobre', 'password': 'user1'}) as response:
            if response.status_code == 200:
                self.login_token = response.json()['token']
                self.is_login = True

    def on_stop(self):
        with self.client.get('/logout') as response:
            if response.status_code == 200:
                self.login_token = ''
                self.is_login = False

    @events.init.add_listener
    def on_locust_init(environment, **_kwargs):
        def checker(environment):
            while environment.runner.state not in [STATE_STOPPING, STATE_STOPPED, STATE_CLEANUP]:
                time.sleep(1)
                if environment.runner.stats.total.num_requests > 5000:
                    environment.runner.quit()
                    return

        if not isinstance(environment.runner, WorkerRunner):
            gevent.spawn(checker, environment)

    @events.test_start.add_listener
    def on_test_start(environment, **kwargs):
        print('Starting test')

    @events.test_stop.add_listener
    def on_test_stop(environment, **kwargs):
        print('Stopping test')
