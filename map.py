import random

from abc import ABC, abstractmethod
from collections import deque


class Map(ABC):

    def __init__(self, room_nums, room_names, room_adjacent, room_start, room_meeting, tasks, num_agents):
        self.room_nums = room_nums
        self.room_names = room_names
        self.room_adjacent = room_adjacent
        self.room_start = room_start
        self.room_meeting = room_meeting
        self.tasks = tasks
        self.num_agents = num_agents

        # Keeps track of room occupancy
        self.rooms = [[0] * num_agents for _ in range(self.room_nums)]
        self.rooms[0] = [1] * num_agents

        # Keeps track of what events have happened in a room
        self.room_events = [[] for _ in range(self.room_nums)]

        # Used for navigation
        self.nav = self.create_nav()

    def next_toward(self, agent, target):
        self.rooms[agent.room][agent.agent_id] = 0
        next_room = self.nav[agent.room][target]
        self.rooms[next_room][agent.agent_id] = 1

        return next_room

    # Not terribly efficient.
    def move_random(self, agent):
        picked_room = random.randint(0, self.room_nums - 1)

        # Grr. I want Do-while
        while self.room_adjacent[agent.room][picked_room] == 0:
            picked_room = random.randint(0, self.room_nums - 1)

        self.rooms[agent.room][agent.agent_id] = 0
        self.rooms[picked_room][agent.agent_id] = 1
        return picked_room

    def remove_agent(self, agent):
        self.rooms[agent.room][agent.agent_id] = 0

    def reset_room_events(self):
        self.room_events = [[] for _ in range(self.room_nums)]

    def add_room_event(self, room, event):
        self.room_events[room].append(event)

    def get_room_events(self, room):
        return self.room_events[room]

    def create_tasks_unique(self, num_tasks):
        if num_tasks > len(self.tasks):
            print(f"Asked for {num_tasks} unique tasks, but there are only {len(num_tasks)} available")
            exit(1)

        return random.sample(self.tasks, num_tasks)

    # No need for a terribly efficient algorithm: Maps are small
    # so a simple BFS works
    def create_nav(self):
        nav = []
        # For each starting point, for each goal room, we find the first room in the shortest path to the goal room
        for starting_room in range(self.room_nums):

            reached = [-1] * self.room_nums

            # Queue of els: First element is the current location, second the origin/first move in path
            to_visit = deque()

            # We add every room we can enter from the start
            for j in range(self.room_nums):
                if not self.room_adjacent[starting_room][j] == 0:
                    to_visit.append((j, j))

            while to_visit:
                check = to_visit.popleft()
                room = check[0]
                origin = check[1]
                if not room == starting_room and reached[room] == -1:
                    reached[room] = origin
                    for j in range(self.room_nums):
                        if self.room_adjacent[room][j]:
                            to_visit.append((j, origin))

            nav.append(reached)

        return nav


'''
    A simplified version of the Skeld, with the right side fo the map entirely removed
'''


class SimpleSkeld(Map):
    def __init__(self, num_agents):
        room_nums = 9
        room_names = ["Cafeteria", "Medbay", "Upper Engine", "Reactor", "Security", "Lower Engine", "Electrical",
                      "Storage", "Admin"]

        rooms_adjacent = [[0, 1, 1, 0, 0, 0, 0, 1, 1],
                          [1, 0, 1, 0, 0, 0, 0, 0, 0],
                          [1, 1, 0, 1, 1, 1, 0, 0, 0],
                          [0, 0, 1, 0, 1, 1, 0, 0, 0],
                          [0, 0, 1, 1, 0, 1, 0, 0, 0],
                          [0, 0, 1, 1, 1, 0, 1, 1, 0],
                          [0, 0, 0, 0, 0, 1, 0, 1, 0],
                          [1, 0, 0, 0, 0, 1, 1, 0, 1],
                          [1, 0, 0, 0, 0, 0, 0, 1, 0]]

        room_start = 0
        room_meeting = 0

        # Defined separately for each room/task to allow extending with additional
        # information such as visual y/n, duration of task, precondition, etc.
        # As possible extensions for later
        tasks = [[0, "Wires"], [0, "Trash"],
                 [1, "Scan"], [1, "Vials"],
                 [2, "Engine"], [2, "Fuel"],
                 [3, "Manifolds"], [3, "Start reactor"],
                 [5, "Engine"], [5, "Fuel"],
                 [6, "Wires"], [6, "Align"], [6, "Divert power"],
                 [7, "Fuel"],
                 [8, "Swipe"]]

        super().__init__(room_nums, room_names, rooms_adjacent, room_start, room_meeting, tasks, num_agents)


'''
    
    Need: Matrix such that it gives the next room to go to. Row: Starting point
                                                            Col: next room

'''
