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

        self.location_history = [self.room]

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

    # Meant to run any logic associated with resetting a round.
    def round_reset(self):
        self.location_history.clear()

        # Keep the current room as the position we have been in for two timeframes for later
        self.location_history.append(self.room)

    @abstractmethod
    def is_impostor(self):
        pass

    def is_alive(self):
        return self.alive


class Crewmate(Agent):

    def __init__(self, agent_id, num_crew, num_imp, game_map, logger, num_tasks):
        super().__init__(agent_id, num_crew, num_imp, game_map, logger)

        self.tasks = game_map.create_tasks_unique(num_tasks)
        self.goal = None
        self.goal_history = []

    def act(self):
        if self.goal and self.room is self.goal[0]:
            print(
                f"Crewmate {self.agent_id} completed their goal: {self.goal[1]} in {self.game_map.room_names[self.goal[0]]}")

            # If we perform an action in a room, we can only see the room in which the action is performed.
            self.location_history.append(self.room)
            self.game_map.add_room_event(self.room, (self.agent_id, self.goal[1]))
            self.goal = None
        else:
            self.__move()

    # Set a goal if we have none and there are tasks left, and move toward it if we have it
    def __move(self):
        if self.goal is None:
            if self.tasks:
                self.goal = self.tasks.pop()
                self.goal_history.append(self.goal)
                print(
                    f"Crewmate {self.agent_id} set as goal: {self.goal[1]} in {self.game_map.room_names[self.goal[0]]}")
            else:
                self.room = self.game_map.move_random(self)
                self.location_history.append(self.room)
                return

        if self.room is not self.goal[0]:
            self.room = self.game_map.next_toward(self, self.goal[0])

        # Log the current room we are in: Either the room we moved to, or the room that happens to be the goal room
        self.location_history.append(self.room)


    def observe(self):
        # TODO: add observations to KM

        # After acting, it is guaranteed that there are at least 2 rooms in memory.
        origin_room_evts = self.game_map.get_room_events(self.location_history[-2])
        target_room_evts = self.game_map.get_room_events(self.location_history[-1])

        # origin_room_evts now contains events in both rooms
        origin_room_evts.extend(target_room_evts)

        for evt in origin_room_evts:
            if evt[1].startswith("Corpse"):
                return True

    def announce(self):
        pass

    def receive(self, announced):
        pass

    def vote(self):
        pass

    def is_impostor(self):
        return False

    def round_reset(self):
        super().round_reset()
        self.goal_history.clear()


class Impostor(Agent):

    def __init__(self, agent_id, num_crew, num_imp, game_map, logger, cooldown, stat_threshold):
        self.cooldown = cooldown
        self.cooldown_ctr = self.cooldown

        # Stationary threshold: Threshold for standing still instead of moving during move function
        self.stat_threshold = stat_threshold

        super().__init__(agent_id, num_crew, num_imp, game_map, logger)

    def act(self):

        current_room = self.game_map.rooms[self.room]

        # TODO: Allow for more than one impostor here.
        # Easiest adjustment: Give each Impostor the ID of each impostor

        if self.cooldown_ctr == 0:
            num_others = sum(current_room) - 1

            if num_others:
                # TODO: Find a more elegant formula here?
                threshold = 1 - (num_others / len(current_room))

                if random.random() < threshold:
                    # Kill!
                    # Select the IDs of all others in the room that are present and are not oneself.
                    # This is easily changed for multiple known impostor IDs
                    present_crewmates = [x for x in range(len(current_room)) if
                                         not current_room[x] == 0 and not x == self.agent_id]

                    to_kill = random.sample(present_crewmates, 1)[0]

                    self.game_map.add_room_event(self.room, (self.agent_id, f"Kill: {to_kill}"))

                    print(f"Impostor {self.agent_id} kills {to_kill}!")

                    self.reset_cooldown()

                    return to_kill
        else:
            self.cooldown_ctr -= 1

        # Only is called when no kill has occurred.
        self.__move()

    def __move(self):
        if random.random() > self.stat_threshold:
            self.room = self.game_map.move_random(self)

        self.location_history.append(self.room)


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

    def round_reset(self):
        super().round_reset()
        self.reset_cooldown()

    def is_impostor(self):
        return True

    def reset_cooldown(self):
        self.cooldown_ctr = self.cooldown
