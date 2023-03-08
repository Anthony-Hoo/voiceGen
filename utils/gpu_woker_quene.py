import threading
from queue import Queue
import time

class GPUWorkerQuene(object):
    def __init__(self):
        self.task_queue = Queue()

    def add_task(self, task):
        self.task_queue.put(task)

    def start(self):
        thread = threading.Thread(target=self.main_thread)
        thread.start()

    def main_thread(self):
        while True:
            task, args = self.task_queue.get()
            task(args)
            time.sleep(0.1)
