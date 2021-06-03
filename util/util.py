from abc import ABC, abstractmethod


class Message:

    def __init__(self, sender, name, information: dict):
        self.sender = sender
        self.name = name
        self.information = information


class LMObject(ABC):
    def __init__(self):
        self.listeners = []

    @abstractmethod
    def receive(self, message):
        pass

    def send(self, message):
        for listener in self.listeners:
            listener.receive(message)

    def register_listener(self, listener):
        assert (isinstance(listener, LMObject))

        self.listeners.append(listener)
