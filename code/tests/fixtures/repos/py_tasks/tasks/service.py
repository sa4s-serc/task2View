import threading

from tasks.models import Task
from tasks import store


class TaskService:
    def create(self, title):
        task = Task(title=title)
        store.save(task)
        threading.Thread(target=store.flush).start()
        return task
