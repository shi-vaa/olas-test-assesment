import threading
import json
import logging
import queue


from dotenv import load_dotenv

from .base_agent import BaseAgent
from behaviours import Behaviours
from handlers import Handlers
from w3 import W3

load_dotenv()

logger = logging.getLogger("App.Agent")


class Agent(BaseAgent):
    def __init__(self, inbox_queue, outbox_queue):
        self.inbox_queue = inbox_queue
        self.outbox_queue = outbox_queue

        self.w3 = W3()
        self.handlers = Handlers(self.w3, self.inbox_queue)
        self.behaviours = Behaviours(self.w3, self.outbox_queue)

        self.stop_event = threading.Event()
        self.threads = []

    def start(self):
        logger.info("...Starting background behaviours & handlers...")
        self.behaviours.start()
        self.handlers.start()

    def stop(self):
        logger.info("...Stopping background behaviours & handlers...")
        self.behaviours.stop()  # Signal the behavious to stop

    def handle_request(self, request):
        """
        Simple Generic Router to handle JSON RPC requests
        If a request of type message is received it will be pushed
        to inbox queue
        """
        try:
            req_data = json.loads(request)
            method = req_data.get("method")
            params = req_data.get("params", [])
            if method == "register_handler":
                return self.register_handler(*params)
            elif method == "register_behaviour":
                return self.register_behaviour(*params)
            if method == "Message":
                self.inbox_queue.put(req_data)
                logger.info(f"Received: {request}")
                return {"result": "Message delivered to inbox"}
            else:
                return {"error": "Method not found"}
        except queue.Full as e:
            logger.error("inbox queue full" + str(e))
            return {"error": "unknown error"}
        except json.JSONDecodeError as e:
            logger.error("Json Decode error" + str(e))
            return {"error": "Invalid JSON"}
        except Exception as e:
            logger.error("Unknown Exception" + str(e))
            return {"error": str(e)}

    def register_handler(self, message_type, url):
        self.allowed_handlers[message_type] = url
        return {"result": "handler Registered"}

    def register_behaviour(self, name):
        if name in self.existing_behavious.keys():
            if self.existing_behavious[name]["is_active"]:
                return {"result": "Behaviour already active"}
            else:
                self.existing_behavious[name]["is_active"] = True
                return {"result": "Behaviour activated"}
        else:
            return {"result": "No such existing behaviour"}
