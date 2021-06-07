import random
from abc import ABC, abstractmethod


def create_agents(game_map, num_crew, num_imp, num_tasks, cooldown, stat_thres, logger):
    """Utility function to create an agent set with tasks, impostors"""
    agents = [Crewmate(x, num_crew, num_imp, game_map, logger, num_tasks) for x in range(num_crew)]
    # TODO: Multiple impostor support here
    # noinspection PyTypeChecker
    agents.append(Impostor(num_crew, num_crew, num_imp, game_map, logger, cooldown, stat_thres))

    return agents


class Agent(ABC):
    """
    An abstract class which contains all functions an agent must have in order to ensure a proper simulation flow
    """
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
    def observe(self, km, agents):
        pass

    @abstractmethod
    def announce(self):
        pass

    @abstractmethod
    def receive(self, announced):
        pass

    @abstractmethod
    def vote(self, km, agents):
        pass

    def round_reset(self):
        """Runs logic associated with resetting this agent for the next round"""
        self.location_history.clear()

        # Keep the current room as the position we have been in for two timeframes for later
        self.location_history.append(self.room)

    @abstractmethod
    def is_impostor(self):
        pass

    def is_alive(self):
        return self.alive

    @abstractmethod
    def get_info(self):
        pass


class Crewmate(Agent):
    """
    This class provides the behaviour of a crewmate in all phases of the simulation
    """

    def __init__(self, agent_id, num_crew, num_imp, game_map, logger, num_tasks):
        super().__init__(agent_id, num_crew, num_imp, game_map, logger)

        self.tasks = game_map.create_tasks_unique(num_tasks)
        self.goal = None
        self.goal_history = []
        self.other_is_imposter = {}

    # TODO
    def update_knowledge_before_discussion(self, km):
        # \item Dead agents must be crewmates: A1 is dead $\rightarrow$ all A know that A1 a crewmate
        pass

    # TODO
    def update_knowledge_after_discussion(self, ):
        # \item Catching the imposter in a lie: (A1 is in the same room X1 as A2 at time Y $\land$ A2 announces
        # they were at room X2 (IS NOT X1) at Y) $\rightarrow$ A1 knows A2 is the imposter
        pass

    def act(self):
        """Try to complete the goal that is currently set, or else move"""
        if self.goal and self.room is self.goal.room_id:
            print(
                f"Crewmate {self.agent_id} completed their goal: {self.goal.name} in {self.game_map.room_names[self.goal.room_id]}")

            # If we perform an action in a room, we can only see the room in which the action is performed.
            self.location_history.append(self.room)
            self.game_map.add_room_event(self.room, (self.agent_id, self.goal.name))
            self.goal = None
        else:
            self.__move()

    # Set a goal if we have none and there are tasks left, and move toward it if we have it
    def __move(self):
        """Move toward the goal if we have one, set one if not, and if no goals are left, move randomly"""
        if self.goal is None:
            if self.tasks:
                self.goal = self.tasks.pop()
                self.goal_history.append(self.goal)
                print(
                    f"Crewmate {self.agent_id} set as goal: {self.goal.name} in {self.game_map.room_names[self.goal.room_id]}")
            else:
                self.room = self.game_map.move_random(self)
                self.location_history.append(self.room)
                return

        if self.room is not self.goal.room_id:
            self.room = self.game_map.next_toward(self, self.goal.room_id)

        # Log the current room we are in: Either the room we moved to, or the room that happens to be the goal room
        self.location_history.append(self.room)


    def observe(self, km, agents):
        """Observe the current room, the previous room, and all events that occurred there"""

        # After acting, it is guaranteed that there are at least 2 rooms in memory.
        origin_room_evts = self.game_map.get_room_events(self.location_history[-2])
        target_room_evts = self.game_map.get_room_events(self.location_history[-1])

        # origin_room_evts now contains events in both rooms
        origin_room_evts.extend(target_room_evts)

        corpse_found = -1
        kill_witnessed = False
        agent_id_task_witnessed = False

        for evt in origin_room_evts:
            if evt[1].startswith("Kill"):
                kill_witnessed = True
        # TODO: Choose which tasks are 'visual' tasks
            elif evt[1].startswith("Wires") or evt[1].startswith("Engine") or evt[1].startswith("Fuel"):
                agent_id_task_witnessed = evt[0] # This is the ID of the agent that performed the task
            elif evt[1].startswith("Corpse"):
                corpse_found = evt[0] # This is the ID of the agent that is found dead

        self.update_knowledge_during_game(km, agents, kill_witnessed, agent_id_task_witnessed)
        return corpse_found

    def update_knowledge_during_game(self, km, agents, kill_witnessed, agent_id_task_witnessed):
        # Check which agents are roommates (and which are not)
        agents_in_same_room = []
        agents_elsewhere = []
        for a in agents:
            if a.agent_id is not self.agent_id:
                if a.location_history[-1] is self.location_history[-1]:
                    agents_in_same_room.append(a)
                else:
                    agents_elsewhere.append(a)

        if agents_in_same_room:
            # Catching the imposter on the body
            if kill_witnessed:
                # One of the people in the room is the imposter, so the others are cleared
                for a in agents_elsewhere:
                    # self.other_is_imposter[a.agent_id] = False
                    km.update_known_crewmate(self.agent_id, a.agent_id)

            # Clearing a crewmate by seeing their task:
            elif agent_id_task_witnessed:
                print(self.agent_id, "witnessed", agent_id_task_witnessed)
                km.update_known_crewmate(self.agent_id, agent_id_task_witnessed)


    def announce(self):
        pass

    def receive(self, announced):
        pass

    def vote(self, km, agents):
        """Crewmates vote for an agent if they're sure they are the imposter. 
        Otherwise, they have a chance of either voting an agent that they still suspect,
        or passing."""

        suspects = []

        # Check which agents the current agent still suspects
        for a in agents:
            if km.suspects(self.agent_id, a.agent_id):
                suspects.append(a.agent_id)
                print(f"Crewmate {self.agent_id} suspects {a.agent_id}")

        # If this is only a single agent, vote for this agent
        if len(suspects) == 1:
            print(f"Crewmate {self.agent_id} votes for {suspects[0]}\n")
            return suspects[0]
        else:  
            # Randomly vote for an agent on the suspect-list
            vote = random.sample(suspects, 1)[0]

            # If you are not yet sure, there is a 50% probability that you will pass vote
            # TODO: Could be improved (e.g. less people on list -> more likely to NOT vote pass)
            threshold = 0.5
            if random.random() > threshold:
                vote = -1

            print(f"Crewmate {self.agent_id} votes for {vote}\n")
            return vote

    def is_impostor(self):
        return False

    def round_reset(self):
        super().round_reset()
        self.goal_history.clear()

    def get_info(self):

        goal_line = ""
        if self.goal == None:
            goal_line = "No current goal"
        else:
            goal_line = f"Current goal: {self.goal[1]} in {self.game_map.room_names[self.goal[0]]}"

        return [
            f"Agent {self.agent_id} (Crewmate)",
            goal_line,
            f"Goals left: {len(self.tasks)}",
            f"Loc. Hist: {self.location_history}"
        ]


class Impostor(Agent):

    def __init__(self, agent_id, num_crew, num_imp, game_map, logger, cooldown, stat_threshold):
        self.cooldown = cooldown
        self.cooldown_ctr = self.cooldown

        # Stationary threshold: Threshold for standing still instead of moving during move function
        self.stat_threshold = stat_threshold

        super().__init__(agent_id, num_crew, num_imp, game_map, logger)

    def act(self):
        """Try to kill if possible, otherwise, move about randomly"""

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

    def observe(self, km, agents):
        # The impostor tells at random, so it does not need to see
        return -1

    def announce(self):
        # TODO: Announce something at random
        pass

    def receive(self, announced):
        # The impostor does not do anything with announced information (for now)
        # But: It does need to know who is dead for voting
        pass

    def vote(self, km, agents):
        """The imposter votes for a random living agent."""
        # TODO: Extend to work for multiple impostors
        # TODO: Extend with HOL (e.g. Imposter votes for most sus crewmate)
        
        vote = random.sample([a.agent_id for a in agents if not a.agent_id == self.agent_id and a.alive], 1)[0]
        print(f"Imposter {self.agent_id} votes for {vote}")
        return vote

    def round_reset(self):
        super().round_reset()
        self.reset_cooldown()

    def is_impostor(self):
        return True

    def reset_cooldown(self):
        self.cooldown_ctr = self.cooldown

    def get_info(self):
        return [
            f"Agent {self.agent_id} (Impostor)",
            f"Loc. His: {self.location_history}"
        ]
