from agent import Crewmate, Impostor, create_agents
from util.util import Message, LMObject


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

        self.phases = ["act", "observe", "discuss", "vote", "check"]
        self.phase = 0

        self.is_game_over = False

    def reset_agents(self):
        self.agents = create_agents(self.game_map, self.num_crew, self.num_imp, self.num_tasks, self.cooldown,
                                    self.stat_thres, self.logger)

    def reset(self):
        """Resets the simulation"""
        self.game_map.map_reset()
        self.reset_agents()
        self.phase = 0
        self.is_game_over = False
        self.send(Message(self, "update", None))
        self.send(Message(self, "clear", None))

    def step(self):

        if self.is_game_over:
            return

        phase = self.phases[self.phase]
        print(phase)

        next_phase = (self.phase + 1) % len(self.phases)

        if phase == "act":

            # To allow for more deterministic behaviour, let the impostors go first
            kills = [a.act() for a in self.agents if a.is_impostor()]
            kills = [res for res in kills if res is not None]

            for result in kills:
                # A kill has taken place, of the agent whose ID was returned
                self.__remove_agent_with_id(result)

                # The killed crewmate now knows who the imposter is
                self.km.update_known_impostor(result,self.num_crew)

                # Check to see how many crewmates have been killed, and if the impostor already won
                if len(self.agents) <= 2:
                    self.send(Message(self, "game_over", {"victor": "impostor(s)"}))
                    self.is_game_over = True

            # Let the rest act.
            [a.act() for a in self.agents if not a.is_impostor()]

        elif phase == "observe":
            spotted_corpses = [a.observe(self.km, self.agents) for a in self.agents]
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

        elif phase == "discuss":
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

        elif phase == "vote":
            votes = [a.vote() for a in self.agents]

            # TODO: Actually use voting results

        elif phase == "check":
            imp_found = False

            for a in self.agents:
                if a.is_impostor():
                    imp_found = True

            if not imp_found:
                self.send(Message(self, "game_over", {"victor": "crewmates"}))
                self.is_game_over = True

        self.phase = next_phase
        self.send(Message(self, "update", None))

    def __remove_agent_with_id(self, agent_id):

        print(f"Removing agent {agent_id}")

        dead_agent = None

        # TODO: This could be improved with a dictionary mapping IDs to objects. But we do not need such improvements
        # as the set of agents is small
        for agent in self.agents:
            if agent.agent_id == agent_id:
                dead_agent = agent
                break

        self.game_map.mark_agent_killed(dead_agent)
        self.agents.remove(dead_agent)

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
