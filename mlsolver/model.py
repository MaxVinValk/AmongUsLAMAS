""" Three wise men puzzle

Module contains data model for three wise men puzzle as Kripke strukture and agents announcements as modal logic
formulas
"""

from mlsolver.kripke import KripkeStructure, World
from mlsolver.formula import Atom, And, Not, Or, Box_a, Box_star


class WiseMenWithHat:
    """
    Class models the Kripke structure of the "Three wise men example.
    """

    knowledge_base = []

    def __init__(self):
        worlds = [
            World('RWW', {'1:R': True, '2:W': True, '3:W': True}),
            World('RRW', {'1:R': True, '2:R': True, '3:W': True}),
            World('RRR', {'1:R': True, '2:R': True, '3:R': True}),
            World('WRR', {'1:W': True, '2:R': True, '3:R': True}),

            World('WWR', {'1:W': True, '2:W': True, '3:R': True}),
            World('RWR', {'1:R': True, '2:W': True, '3:R': True}),
            World('WRW', {'1:W': True, '2:R': True, '3:W': True}),
            World('WWW', {'1:W': True, '2:W': True, '3:W': True}),
        ]

        relations = {
            '1': {('RWW', 'WWW'), ('RRW', 'WRW'), ('RWR', 'WWR'), ('WRR', 'RRR')},
            '2': {('RWR', 'RRR'), ('RWW', 'RRW'), ('WRR', 'WWR'), ('WWW', 'WRW')},
            '3': {('WWR', 'WWW'), ('RRR', 'RRW'), ('RWW', 'RWR'), ('WRW', 'WRR')}
        }

        relations.update(add_reflexive_edges(worlds, relations))
        relations.update(add_symmetric_edges(relations))

        print(relations)

        self.ks = KripkeStructure(worlds, relations)

        # Wise man ONE does not know whether he wears a red hat or not
        self.knowledge_base.append(And(Not(Box_a('1', Atom('1:R'))), Not(Box_a('1', Not(Atom('1:R'))))))

        # This announcement implies that either second or third wise man wears a red hat.
        self.knowledge_base.append(Box_star(Or(Atom('2:R'), Atom('3:R'))))

        # Wise man TWO does not know whether he wears a red hat or not
        self.knowledge_base.append(And(Not(Box_a('2', Atom('2:R'))), Not(Box_a('2', Not(Atom('2:R'))))))

        # This announcement implies that third men has be the one, who wears a red hat
        self.knowledge_base.append(Box_a('3', Atom('3:R')))

def add_reflexive_edges(worlds, relations):
    """Routine adds reflexive edges to Kripke frame
    """
    result = {}
    for agent, agents_relations in relations.items():
        result_agents = agents_relations.copy()
        for world in worlds:
            result_agents.add((world.name, world.name))
            result[agent] = result_agents
    return result


def add_symmetric_edges(relations):
    """Routine adds symmetric edges to Kripke frame
    """
    result = {}
    for agent, agents_relations in relations.items():
        result_agents = agents_relations.copy()
        for r in agents_relations:
            x, y = r[1], r[0]
            result_agents.add((x, y))
        result[agent] = result_agents
    return result


#TODO: does not yet fully support multiple imposters: imposters only know they are imposter
#Also, each world only has one imposter so far
class AmongUs:

    def __init__(self, num_agents, imposters):
        self.worlds = []
        self.relations = {}
        agent_is_imposter = {}

        # Build the same number of worlds as there are agents. Each world has one imposter
        for i in range(num_agents):
            for j in range(num_agents):
                if(i is j):
                    agent_is_imposter[j] = 'True'
                else:
                    agent_is_imposter[j] = 'False'

            self.worlds.append(World(i, agent_is_imposter))

        # Build relations according to the following rules:
        # Each agent knows whether they themselves are imposter or not
        # This leads to crewmates not having accessibility to the worlds where they are imposter
        # This leads to imposters only having a reflexive relation to themselves
        for i in range(num_agents):
            if(i not in imposters):
                self.relations[i] = set((x,y) for x in range(num_agents) for y in range(num_agents) if ((i is not x) and (i is not y)))
            else:
                self.relations[i] = set((x,y) for x in range(num_agents) for y in range(num_agents) if ((x is y) and (i is x)))

        self.relations.update(add_symmetric_edges(self.relations))

        self.kripke_structure = KripkeStructure(self.worlds, self.relations)


    # def update_relations(self):
    #     model = self.kripke_structure.solve(Box_a('1', Atom('2:False')))
    #     model.update_relations()

    #     # pass

if __name__ == "__main__":
    model = AmongUs(5, [4])

    for w in model.worlds:
        print(w.name, w.assignment)
    print(model.relations)

    #TODO hoe kan je nou een formule toepassen op het model?
    model = model.kripke_structure.solve(Box_star(Not(Atom('1'))))

    for w in model.worlds:
        print(w.name, w.assignment)
    print(model.relations)

    # f = Box_a('1',Atom('2:True'))
    # model = model.kripke_structure.solve_a('1', f)
    # print(model.relations)



