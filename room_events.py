from abc import ABC
from enum import Enum


class EventType(Enum):
    CORPSE = 0
    KILL = 1
    TASK = 2
    TASK_VISUAL = 3


class RoomEvent(ABC):

    def __init__(self, type: EventType, agent_id, name):
        self.type = type
        self.agent_id = agent_id
        self.name = name