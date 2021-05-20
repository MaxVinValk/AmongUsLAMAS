import random
from abc import ABC, abstractmethod

class Agent(ABC):

    def __init__(self, agent_id, num_crew, num_imp, game_map, logger):
        self.agent_id = agent_id
        self.game_map = game_map
        self.logger = logger
        self.num_crew = num_crew
        self.num_imp = num_imp

        self.room = game_map.room_start
        self.alive = True

    @abstractmethod
    def move(self):
        pass

    @abstractmethod
    def act(self):
        pass

    @abstractmethod
    def observe(self):
        pass

    @abstractmethod
    def announce(self):
        pass

    @abstractmethod
    def receive(self, announced):
        pass

    @abstractmethod
    def vote(self):
        pass


class Crewmate(Agent):

    def __init__(self, agent_id, num_crew, num_imp, game_map, logger, num_tasks):
        super().__init__(agent_id, num_crew, num_imp, game_map, logger)

        self.tasks = game_map.create_tasks_unique(num_tasks)
        self.goal = None

    # Set a goal if we have none and there are tasks left, and move toward it if we have it
    def move(self):
        if self.goal is None:
            if self.tasks:
                self.goal = self.tasks.pop()
                print(f"Crewmate {self.agent_id} set as goal: {self.goal[1]} in {self.game_map.room_names[self.goal[0]]}")
            else:
                self.room = self.game_map.move_random(self)
                return

        if self.room is not self.goal[0]:
            self.room = self.game_map.next_toward(self, self.goal[0])

    def act(self):
        if self.goal and self.room is self.goal[0]:
            print(f"Crewmate {self.agent_id} completed their goal: {self.goal[1]} in {self.game_map.room_names[self.goal[0]]}")
            self.game_map.add_room_event(self.room, (self.agent_id, self.goal[1]))
            self.goal = None

    def observe(self):
        # TODO: add observations to KM
        obs = self.game_map.get_room_events(self.room)

        for evt in obs:
            if evt[1].startswith("Corpse"):
                return True

    def announce(self):
        pass

    def receive(self, announced):
        pass

    def vote(self):
        pass


class Impostor(Agent):

    def __init__(self, agent_id, num_crew, num_imp, game_map, logger):
        super().__init__(agent_id, num_crew, num_imp, game_map, logger)

    def move(self):
        self.room = self.game_map.move_random(self)

    def act(self):
        current_room = self.game_map.rooms[self.room]

        # TODO: Allow for more than one impostor here.
        # Easiest adjustment: Give each Impostor the ID of each impostor

        num_others = sum(current_room) - 1

        if num_others:
            # TODO: Find a more elegant formula here?
            threshold = 1 - (num_others / len(current_room))

            if random.random() < threshold:
                # Kill!
                # Select the IDs of all others in the room that are present and are not oneself.
                # This is easily changed for multiple known impostor IDs
                present_crewmates = [x for x in range(len(current_room)) if not current_room[x] == 0 and not x == self.agent_id]

                to_kill = random.sample(present_crewmates, 1)[0]

                self.game_map.add_room_event(self.room, (self.agent_id, f"Kill: {to_kill}"))

                print(f"Impostor {self.agent_id} kills {to_kill}!")

                return to_kill

    def observe(self):
        # The impostor tells at random, so it does not need to see
        pass

    def announce(self):
        # TODO: Announce something at random
        pass

    def receive(self, announced):
        # The impostor does not do anything with announced information (for now)
        # But: It does need to know who is dead for voting
        pass

    def vote(self):
        # TODO: Extend to work for multiple impostors
        # TODO: Incorporate deaths in vote
        total = self.num_imp + self.num_crew

        return random.sample([x for x in range(total) if not x == self.agent_id], 1)[0]


