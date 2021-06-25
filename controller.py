from agent import create_agents
from util.util import Message, LMObject
from collections import Counter
from enum import Enum
from logger import Logger


class Phase(Enum):
    ACT = 0
    OBSERVE = 1
    DISCUSS = 2
    VOTE = 3
    CHECK = 4


class Controller(LMObject):
    """
        Handles the simulation flow. The simulation occurs in steps, and the flow of the simulation is handled
        by the controller. It is also responsible for checking whether or not the game is over
    """

    # on reset. Perhaps move to a custom function where we can 'init' agents on their own?
    def __init__(self, km, game_map, num_crew, num_imp, num_tasks, num_visuals, cooldown, stat_thres):
        super().__init__()

        self.km = km
        self.game_map = game_map
        self.num_crew = num_crew
        self.num_imp = num_imp
        self.num_tasks = num_tasks
        self.num_visuals = num_visuals
        self.cooldown = cooldown
        self.stat_thres = stat_thres
        self.count_crewmate_wins = 0

        self.logger = Logger.get_instance()

        self.agents = []
        self.reset_agents()

        # self.phases = ["act", "observe", "discuss", "vote", "check"]
        self.phase = Phase.ACT

        self.is_game_over = False
        self.run_continuously = False

    def reset_agents(self):
        self.agents = create_agents(self.game_map, self.km, self.num_crew, self.num_imp, self.num_tasks, self.num_visuals,
                                    self.cooldown, self.stat_thres)

    def reset(self):
        """Resets the simulation"""
        self.km.reset()
        self.game_map.map_reset()
        self.reset_agents()
        self.phase = Phase.ACT
        self.is_game_over = False
        self.send(Message(self, "update", None))
        self.send(Message(self, "clear", None))

    def step(self):

        if self.is_game_over:
            return

        self.logger.log(f"{self.phase}", Logger.LOG | Logger.PRINT_VISUAL)

        next_phase = (self.phase.value + 1) % len(Phase)

        if self.phase == Phase.ACT:

            # To allow for more deterministic behaviour, let the impostors go first
            # Removal of dead agents happens in 2 steps: From the map, and from the agent set of agents
            # that will receive an update. This is kind of an ugly construction, but it prevents from two
            # Impostors attempting to kill the same crewmate, which results in a crash.

            kills = []

            for a in self.agents:
                if not a.is_impostor():
                    continue

                kill = a.act()
                if kill is not None:
                    self.__remove_agent_with_id_from_map(kill)
                    kills.append(kill)

            for kill in kills:
                self.__remove_agent_with_id_from_set(kill)
                # The killed crewmate now knows who the impostor is
                self.km.update_known_impostor(kill, self.num_crew)
                self.check_game_over()

            # Let the rest act.
            [a.act() for a in self.agents if not a.is_impostor()]

        elif self.phase == Phase.OBSERVE:
            spotted_corpses = [a.observe(self.agents) for a in self.agents]
            self.game_map.reset_room_events()

            corpse_has_been_found = False

            for return_val in spotted_corpses:
                if return_val != -1:
                    corpse_has_been_found = True
                    for a in self.agents:
                        if not a.is_impostor():
                            self.km.update_known_crewmate(a.agent_id, return_val)

            if not corpse_has_been_found:
                next_phase = 0

        elif self.phase == Phase.DISCUSS:
            # If we have reached this phase, it is because at least 1 corpse has been found. Thus, we clear all corpses
            self.game_map.clear_corpses()

            # Everyone is moved to the discussion room
            [self.game_map.move_to_meeting_room(a) for a in self.agents]

            # Furthermore, we ask the agents to reset internal variables to start-of-round values, for instance,
            # the kill cooldown for impostors
            [a.round_reset() for a in self.agents]

            # Discussing takes two phases
            # IDEA: Consider multi-round announcements? It may be the case that after 1 announcement
            # another agent will obtain the ability to announce something else. Needs to be investigated further.
            announced = [None for _ in range(self.num_imp + self.num_crew)]
            for a in self.agents:
                announced[a.agent_id] = a.announce()

            [a.receive(announced) for a in self.agents]

            # Update Crewmate Knowledge about who possibly lied?
            # [a.update_knowledge_after_discussion(self.agents) for a in self.agents if not a.is_impostor()]

        elif self.phase == Phase.VOTE:
            # Let the impostors choose a new target: The one who suspects least agents
            [a.choose_target(self.agents) for a in self.agents if a.is_impostor()]

            # Gather all votes
            votes = [a.vote(self.agents) for a in self.agents]

            # Get the ID with most votes
            vote_count = Counter(votes)
            top_votes = vote_count.most_common(2)


            # If there is a tie, do not continue voting
            if top_votes[0][1] == top_votes[1][1] and len(top_votes) > 1:
                self.logger.log("A tie: No agent was voted off.", Logger.LOG | Logger.PRINT_VISUAL)
            elif top_votes[0][0] == -1:
                # Most agents voted for a tie, do not continue voting
                self.logger.log("Most agents pass: No agent was voted off.", Logger.LOG | Logger.PRINT_VISUAL)
            else:
                # Remove agent with most votes from the game
                self.__remove_agent_with_id(top_votes[0][0], voted_off=True)
                self.logger.log(f"Agent {top_votes[0][0]} received the most votes and is voted off.",
                                Logger.LOG | Logger.PRINT_VISUAL)


        elif self.phase == Phase.CHECK:
            self.check_game_over()

        self.phase = Phase(next_phase)
        self.send(Message(self, "update", None))

    def check_continuous_update(self):
        if self.run_continuously:
            if self.is_game_over:
                self.run_continuously = False

            self.step()

    def run_to_end(self):
        while not self.is_game_over:
            self.step()

    def run_hundred_times(self):
        epochs = 100
        self.count_crewmate_wins = 0
        for i in range(epochs):
            self.run_to_end()
            self.reset()
        print(f'Crewmates won {self.count_crewmate_wins} times out of {epochs}.')
        print(f'Impostors won {epochs - self.count_crewmate_wins} times out of {epochs}.')
        self.count_crewmate_wins = 0

    def check_game_over(self):
        if not self.is_game_over:
            num_imps = 0
            for a in self.agents:
                if a.is_impostor():
                    num_imps = num_imps + 1

            num_crew = len(self.agents) - num_imps

            if num_imps == 0:
                self.send(Message(self, "game_over", {"victor": "crewmates"}))
                self.logger.log("Crewmates win!", Logger.LOG | Logger.PRINT_VISUAL)
                self.is_game_over = True
                self.count_crewmate_wins = self.count_crewmate_wins + 1
                return
            elif num_imps >= num_crew:
                self.send(Message(self, "game_over", {"victor": "impostor(s)"}))
                self.logger.log("Impostors win!", Logger.LOG | Logger.PRINT_VISUAL)
                self.is_game_over = True
                return

            # Tasks
            for a in self.agents:
                if not a.is_impostor():
                    if a.has_tasks_left():
                        return

            # If we reach this, no agents have tasks left
            self.send(Message(self, "game_over", {"victor": "crewmates"}))
            self.logger.log("Crewmates win! (tasks)", Logger.LOG | Logger.PRINT_VISUAL)
            self.is_game_over = True
            self.count_crewmate_wins += 1

    def __remove_agent_with_id_from_map(self, agent_id, voted_off=False):
        dead_agent = self.get_agent_with_id(agent_id)

        self.game_map.mark_agent_killed(dead_agent, voted_off)

    def __remove_agent_with_id_from_set(self, agent_id):
        dead_agent = self.get_agent_with_id(agent_id)
        self.agents.remove(dead_agent)

    def __remove_agent_with_id(self, agent_id, voted_off=False):
        self.__remove_agent_with_id_from_map(agent_id, voted_off)
        self.__remove_agent_with_id_from_set(agent_id)

    def get_phase(self):
        return self.phase

    def get_agent_with_id(self, agent_id):
        for a in self.agents:
            if a.agent_id is agent_id:
                return a
        return None

    def receive(self, message):
        if message.name == "step":
            self.step()
        elif message.name == "reset":
            self.reset()
        elif message.name == "toggle_continuous":
            self.reset()
            self.run_continuously = not self.run_continuously
        elif message.name == "run_to_end":
            self.reset()
            self.run_to_end()
        elif message.name == "run_hundred_times":
            self.reset()
            self.run_hundred_times()
        elif message.name == "save_run":
            self.logger.save_logs()
