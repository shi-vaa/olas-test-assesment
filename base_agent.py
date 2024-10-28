from abc import ABC, abstractmethod

class BaseAgent(ABC):

    @abstractmethod
    def register_behaviour(self,name):
        pass
    
    @abstractmethod
    def register_handler(self,message_type,url):
        pass
    