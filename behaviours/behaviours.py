import time
import random
import threading
import logging


from threading import ThreadError

logger = logging.getLogger("App.Behaviour")


class Behaviours:
    def __init__(self, w3, outbox_queue):
        self.outbox_queue = outbox_queue
        self.w3 = w3

        self.existing_behavious = {
            "words_generator": {"is_active": True, "interval": 2},
            "erc20_balance": {"is_active": True, "interval": 10},
        }

        self.alphabet = [
            "hello",
            "sun",
            "world",
            "space",
            "moon",
            "crypto",
            "sky",
            "ocean",
            "universe",
            "human",
        ]

        self.threads = []
        self.stop_event = threading.Event()

    def start(self):
        for behaviour, options in self.existing_behavious.items():
            if options["is_active"]:
                if behaviour == "words_generator":
                    thread = threading.Thread(target=self.run_alphabet_behaviour)
                    thread.daemon = True
                    self.threads.append(thread)
                    thread.start()
                elif behaviour == "erc20_balance":
                    thread = threading.Thread(target=self.run_erc20_balance_behaviour)
                    thread.daemon = True
                    self.threads.append(thread)
                    thread.start()

    def stop(self):
        logger.info("Stopping Behaviours...")
        self.stop_event.set()  # Signal the thread to stop

    def run_erc20_balance_behaviour(self):
        try:
            while not self.stop_event.is_set():
                balance = self.w3.get_balance(self.w3.from_address)
                logger.info(f"Balance is:  {balance}")
                time.sleep(10)
        except ThreadError as e:
            logger.error("Thread Exception inside balance behaviour" + str(e))
        except Exception as e:
            logger.error("Exception:" + str(e))

    def run_alphabet_behaviour(self):
        try:
            while not self.stop_event.is_set():
                selected_words = random.sample(self.alphabet, 2)
                if not self.outbox_queue.full():
                    self.outbox_queue.put(
                        {
                            "method": "Message",
                            "type": "alphabet",
                            "words": selected_words,
                        }
                    )
                time.sleep(2)
        except ThreadError as e:
            logger.error("Thread exception inside alphabet behaviour" + str(e))
        except Exception as e:
            logger.error("Exception:" + str(e))
