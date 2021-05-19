class Controller:

    def __init__(self, agents, game_map):
        self.agents = agents
        self.game_map = game_map

        self.phases = ["move", "act", "observe", "discuss", "vote", "check"]
        self.phase = 0

    # Blegh. Ugly. TODO: Fix Up?
    def step(self):

        phase = self.phases[self.phase]

        print(phase)

        next_phase = (self.phase + 1) % len(self.phases)

        if phase == "move":
            [a.move() for a in self.agents]

        elif phase == "act":
            act_results = [a.act() for a in self.agents]
            kills = [result for result in act_results if result is not None]

            for result in kills:
                # A kill has taken place, of the agent whose ID was returned
                self.__remove_agent_with_id(result)

        elif phase == "observe":
            spotted_kills = [a.observe() for a in self.agents]
            self.game_map.reset_room_events()

            if True not in spotted_kills:
                next_phase = 0

        elif phase == "discuss":
            # Discussing takes two phases
            announced = [a.announce() for a in self.agents]
            [a.receive(announced) for a in self.agents]

        elif phase == "vote":
            votes = [a.vote() for a in self.agents]

            # TODO: Actually use voting results

        elif phase == "check":
            # TODO: Actually check if the game is over
            pass

        self.phase = next_phase

    def __remove_agent_with_id(self, agent_id):

        print(f"Removing agent {agent_id}")

        dead_agent = None

        for agent in self.agents:
            if agent.agent_id == agent_id:
                dead_agent = agent
                break

        self.game_map.remove_agent(dead_agent)
        self.agents.remove(dead_agent)
