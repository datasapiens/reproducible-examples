import time

from locust import User, TaskSet, task, between, events
from trino.dbapi import connect

conn = connect(
    host="0.0.0.0",
    port=8889,
    user="exporter"
)

def execute_query():

    cur = conn.cursor()
    cur.execute("select count(*) from tpcds.sf1.store")
    rows = cur.fetchall()
    cur.close()
    
    return rows

class TrinoClient:

    def __getattr__(self, name):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                res = execute_query()
                events.request_success.fire(
                    request_type="trino",
                    name=name,
                    response_time=int((time.time() - start_time) * 1000),
                    response_length=len(res)
                )
            except Exception as e:
                events.request_failure.fire(
                    request_type="trino",
                    name=name,
                    response_time=int((time.time() - start_time) * 1000),
                    exception=e
                )

        return wrapper


class TrinoTaskSet(TaskSet):
    @task
    def execute_query(self):
        self.client.execute_query()


class TrinoUser(User):
    host = "http://0.0.0.0:8889"

    wait_time = between(0.1, 1)

    def __init__(self, environment):
        super(TrinoUser, self).__init__(environment)
        self.client = TrinoClient()

    @task
    def execute_query(self):
        self.client.execute_query()