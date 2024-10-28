import threading
import json


class Handlers:
    def __init__(self, w3, inbox_queue):
        self.w3 = w3
        self.inbox_queue = inbox_queue

        self.stop_event = threading.Event()
        self.threads = []

    def start(self):
        thread = threading.Thread(target=self.process_inbound_msgs)
        thread.daemon = True
        self.threads.append(thread)
        thread.start()
        

    def stop(self):
        print("Stopping Handlers...")
        self.stop_event.set()  # Signal the thread to stop

    def process_inbound_msgs(self):
        try:
            while not self.stop_event.is_set():
                if not self.inbox_queue.empty():
                    item = self.inbox_queue.get()
                else:
                    continue
                self.inbox_queue.task_done()
                req_data = json.loads(item)
                msg_type = req_data.get("type")
                if msg_type == "alphabet":
                    self.run_alphabet_handler(req_data["words"], req_data)
        except Exception as e:
            print("Exception:" + str(e))

    def run_alphabet_handler(self, words, req_data):
        if "hello" in words:
            print("Found hello:"+ json.dumps(req_data))
        if "crypto" in words:
            self.w3.transfer()
