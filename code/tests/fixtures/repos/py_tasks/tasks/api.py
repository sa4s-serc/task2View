from flask import Flask

from tasks.service import TaskService

app = Flask(__name__)


@app.post("/tasks")
def create_task():
    return TaskService().create("x")


if __name__ == "__main__":
    app.run()
