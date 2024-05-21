import threading
import queue

# Adapted from https://maxhalford.github.io/blog/flask-sse-no-deps/ and https://github.com/MaxHalford/maxhalford.github.io/issues/5#issuecomment-902440289


class SSEQueue:
    def __init__(self):
        self.listeners = []
        self.lock = threading.Lock()

    def listen(self):
        with self.lock:
            q = queue.Queue(maxsize=5)
            self.listeners.append(q)
            return q

    def put(self, message):
        with self.lock:
            for i in reversed(range(len(self.listeners))):
                try:
                    self.listeners[i].put_nowait(message)
                except queue.Full:
                    del self.listeners[i]
