class Controller:

    def __init__(self, agents, game_map):
        self.agents = agents
        self.game_map = game_map

        self.phases = ["act", "observe", "discuss", "vote", "check"]
        self.phase = 0

    # Blegh. Ugly. TODO: Fix Up?
    def step(self):

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

            # Let the rest act.
            [a.act() for a in self.agents if not a.is_impostor()]

        elif phase == "observe":
            spotted_corpses = [a.observe() for a in self.agents]
            self.game_map.reset_room_events()

            if True not in spotted_corpses:
                next_phase = 0

            # Update Crewmate Knowledge about what happens in their current room
            [a.update_knowledge_during_game(self.agents) for a in self.agents if not a.is_impostor()]

        elif phase == "discuss":
            # Update Crewmate Knowledge about who died
            [a.update_knowledge_before_discussion(self.agents) for a in self.agents if not a.is_impostor()]
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

            # Update Crewmate Knowledge about who possibly lied
            [a.update_knowledge_after_discussion(self.agents) for a in self.agents if not a.is_impostor()]

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

        # TODO: This could be improved with a dictionary mapping IDs to objects. But we do not need such improvements
        # as the set of agents is small
        for agent in self.agents:
            if agent.agent_id == agent_id:
                dead_agent = agent
                break

        self.game_map.mark_agent_killed(dead_agent)
        self.agents.remove(dead_agent)
