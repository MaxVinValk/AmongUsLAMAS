from agent import Crewmate, Impostor, create_agents
from util.util import Message, LMObject
from collections import Counter
from enum import Enum

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

    # TODO: Fix this hot mess. Currently the controller needs these pieces of info to create a new agentset
    # on reset. Perhaps move to a custom function where we can 'init' agents on their own?
    def __init__(self, km, game_map, num_crew, num_imp, num_tasks, cooldown, stat_thres, logger):
        super().__init__()

        self.km = km
        self.game_map = game_map
        self.num_crew = num_crew
        self.num_imp = num_imp
        self.num_tasks = num_tasks
        self.cooldown = cooldown
        self.stat_thres = stat_thres
        self.logger = logger

        self.agents = []
        self.reset_agents()

        # self.phases = ["act", "observe", "discuss", "vote", "check"]
        self.phase = Phase.ACT

        self.is_game_over = False
        self.run_continuously = False

    def reset_agents(self):
        self.agents = create_agents(self.game_map, self.km, self.num_crew, self.num_imp, self.num_tasks, self.cooldown,
                                    self.stat_thres, self.logger)

    def reset(self):
        """Resets the simulation"""
        self.game_map.map_reset()
        self.reset_agents()
        self.phase = Phase.ACT
        self.is_game_over = False
        self.send(Message(self, "update", None))
        self.send(Message(self, "clear", None))

    def step(self):

        if self.is_game_over:
            return

        print(self.phase)

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

                # Check to see how many crewmates have been killed, and if the impostor already won
                if len(self.agents) <= self.num_imp + 1:
                    self.send(Message(self, "game_over", {"victor": "impostor(s)"}))
                    self.is_game_over = True

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
            # TODO: Consider multi-round announcements? It may be the case that after 1 announcement,
            # another agent will obtain the ability to announce something else. Needs to be investigated further.
            announced = [a.announce() for a in self.agents]
            [a.receive(announced) for a in self.agents]

            # Update Crewmate Knowledge about who possibly lied?
            # [a.update_knowledge_after_discussion(self.agents) for a in self.agents if not a.is_impostor()]

        elif self.phase == Phase.VOTE:
            # Gather all votes
            votes = [a.vote(self.agents) for a in self.agents]

            # Get the ID with most votes
            vote_count = Counter(votes)
            top_votes = vote_count.most_common(2)

            # If there is a tie, do not continue voting
            if top_votes[0][1] == top_votes[1][1] and len(top_votes) > 1:
                print(f"A tie: No agent was voted off.")
            elif top_votes[0][0] == -1:
                # Most agents voted for a tie, do not continue voting
                print(f"Most agents pass: No agent was voted off.")
            else:
                # Remove agent with most votes from the game
                self.__remove_agent_with_id(top_votes[0][0], voted_off=True)
                print(f"Agent {top_votes[0][0]} received the most votes.")

        elif self.phase == Phase.CHECK:
            # Check to see if the impostors win, triggers when a crewmate was voted off with 3 agents left
            if len(self.agents) <= 2:
                self.send(Message(self, "game_over", {"victor": "impostor(s)"}))
                self.is_game_over = True

            # Check if the crewmates win
            imp_found = False

            for a in self.agents:
                if a.is_impostor():
                    imp_found = True

            if not imp_found:
                self.send(Message(self, "game_over", {"victor": "crewmates"}))
                self.is_game_over = True

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

    def __remove_agent_with_id_from_map(self, agent_id, voted_off=False):
        print(f"Removing agent {agent_id} from the map")
        dead_agent = self.get_agent_with_id(agent_id)

        self.game_map.mark_agent_killed(dead_agent, voted_off)

    def __remove_agent_with_id_from_set(self, agent_id):
        print(f"Removing agent {agent_id} from agent update set")
        dead_agent = self.get_agent_with_id(agent_id)
        self.agents.remove(dead_agent);

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
            self.run_continuously = not self.run_continuously
        elif message.name == "run_to_end":
            self.run_to_end()
