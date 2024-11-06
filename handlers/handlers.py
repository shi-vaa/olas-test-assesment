import threading
import json
import logging
import queue

from threading import ThreadError
from web3.exceptions import Web3Exception

logger = logging.getLogger("App.Handler")


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
        logger.info("Stopping Handlers...")
        self.stop_event.set()  # Signal the thread to stop

    def process_inbound_msgs(self):
        try:
            while not self.stop_event.is_set():
                if not self.inbox_queue.empty():
                    req_data = self.inbox_queue.get()
                else:
                    continue
                self.inbox_queue.task_done()
                msg_type = req_data.get("type")
                if msg_type == "alphabet":
                    self.run_alphabet_handler(req_data["words"], req_data)
        except Web3Exception as e:
            logger.error("Web3 exception occured" + str(e))
        except ThreadError as e:
            logger.error("Thread exception while processing inbox messages" + str(e))
        except Exception as e:
            logger.error("Exception:" + str(e))

    def run_alphabet_handler(self, words, req_data):

        if "hello" in words:
            logger.info("Found hello:" + json.dumps(req_data))
        if "crypto" in words:
            logger.info("Found crypto initiating transfer:" + json.dumps(req_data))
            self.w3.transfer(self.w3.from_address, self.w3.to_address)
