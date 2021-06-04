""" AmongUs Kripke model

Module contains a simple Kripke model for Among Us and 
"""

from mlsolver.kripke import KripkeStructure, World
from mlsolver.formula import Atom, And, Not, Or, Box_a, Box_star
import numpy as np
import pygame
import os
from graphviz import Digraph
import tempfile

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

def kripke_structure_solve_a(self, agent, formula):
    """ This function is a small change to mlsolver taken from the code of The Ship at 
    https://github.com/JohnRoyale/MAS2018/blob/master/mlsolver/kripke.py#L36
    it is necessary to be able to execute updates for only one agent in multi-agent Kripke structures
    """
    nodes_to_remove = self.nodes_not_follow_formula(formula)
    print("Removing nodes: {}".format(nodes_to_remove))
    if len(nodes_to_remove) == 0:
        return self

    relations_to_remove = []

    for relation in self.relations[str(agent)]:
        for node in nodes_to_remove: 
            if node in relation:
                relations_to_remove.append(relation)
                break

    self.relations[str(agent)] = self.relations[str(agent)].difference(set(relations_to_remove))
    return self

def fixed_layout_graphviz(worlds, point, connectivity, r = 2, label_pos = 0.25):
    """ The graphviz layout engines don't always work well for our Kripke structures, 
    so we manually position the nodes.
    worlds: list of strings of world names
    point: index of the real world
    connectivity: (start, end, label)
    """
    dot = Digraph(engine="neato")
    angle = np.linspace(0, 2 * np.pi, len(worlds), endpoint=False)
    world_x = np.cos(angle) * r
    world_y = np.sin(angle) * r
    # Worlds are placed in a circle
    for i, (w, x, y) in enumerate(zip(worlds, world_x, world_y)):
        # peripheries sets double line around the pointed state
        dot.node(w, w, pos ="{},{}!".format(x, y), shape='box', peripheries = str(1 + (i == point)))

    # Labels are placed in "virtual" nodes between the worlds
    for start, end, label in connectivity:
        edge_label_pos = label_pos
        if (abs(start - end) <= 1) or (max(start, end) == len(worlds) - 1) and (min(start,end) == 0):
            edge_label_pos = 0.5
        label_x = world_x[start] * edge_label_pos + world_x[end] * (1 - edge_label_pos)
        label_y = world_y[start] * edge_label_pos + world_y[end] * (1 - edge_label_pos)
        edgename = str((start,end))
        dot.node(str((start,end)), label, pos ="{},{}!".format(label_x, label_y), shape='plaintext')
        dot.edge(edgename, worlds[start])
        dot.edge(edgename, worlds[end])
    return dot

class AmongUs(object):
    def __init__(self, num_agents, imposter):
        self.worlds = []
        self.relations = {}
        

        # Build the same number of worlds as there are agents. Each world has one imposter
        for i in range(num_agents):
            agent_is_imposter = {}
            for j in range(num_agents):
                if i == j:
                    agent_is_imposter["IsImp:{}".format(j)] = True
                else:
                    agent_is_imposter["IsImp:{}".format(j)] = False

            self.worlds.append(World("Imp{}".format(i), agent_is_imposter))

        # Build relations according to the following rules:
        # Each agent knows whether they themselves are imposter or not
        # This leads to crewmates not having accessibility to the worlds where they are imposter
        # This leads to imposters only having a reflexive relation to themselves
        for i in range(num_agents):
            self.relations[str(i)] = set(("Imp{}".format(x),"Imp{}".format(y)) for x in range(num_agents) for y in range(num_agents) if ((i != x) and (i != y)))
        #print(self.relations)
        self.relations.update(add_symmetric_edges(self.relations))
        self.relations.update(add_reflexive_edges(self.worlds, self.relations))
        self.kripke_structure = KripkeStructure(self.worlds, self.relations)
        self.real_world = "Imp{}".format(imposter)
    def suspects(self, observer, other):
        """ Check if agent i suspects agent j of being the impostor
        We do this by evaluating the sentence "i knows not "IsImp:j" 
        """
        sentence = Not(Box_a(str(observer), Not(Atom("IsImp:{}".format(other)))))
        return sentence.semantic(self.kripke_structure, self.real_world)
    def update_known_impostor(self, observer, impostor):
        """Update the model to register that a crewmate has caught the impostor
        """
        sentence = Atom("IsImp:{}".format(impostor))
        self.kripke_structure = kripke_structure_solve_a(self.kripke_structure, str(observer), sentence)
    def update_known_crewmate(self, observer, crewmate):
        """Update the model to register that a crewmate no longer suspects another crewmate
        (e.g. because of a visual task)
        """
        sentence = Not(Atom("IsImp:{}".format(crewmate)))
        self.kripke_structure = kripke_structure_solve_a(self.kripke_structure, str(observer), sentence)
    def plot_fixed(self, size = 2, label_pos = 0.25, render = True):
        """ Plot the kripke structure using the `fixed_layout_kripke` function
        """
        worlds = list()
        world_id = dict()
        for i,w in enumerate(self.kripke_structure.worlds):
            world_id[w.name] = i
            worlds.append(w.name)
        connectivity = {}
        for agent, relations in model.kripke_structure.relations.items():
            for (start, end) in relations:
                (start, end) = (min(start, end), max(start, end))
                if start == end:
                    continue
                if (start, end) in connectivity:
                    connectivity[(start, end)].add(agent)
                else:
                    connectivity[(start, end)] = set([agent])
                    
        edges = []
        for (start, end), labels in connectivity.items():
            edges.append((world_id[start], world_id[end], "," .join(sorted(labels))))
        dot = fixed_layout_graphviz(worlds,world_id[self.real_world],edges, r = size, label_pos = label_pos)
        if render:
            with tempfile.TemporaryDirectory() as tmpdirname:
                dot.render('kripke', format='png', directory=tmpdirname)
                img = pygame.image.load(os.path.join(tmpdirname, 'kripke.png'))
                return img
        else:
            return dot
if __name__ == "__main__":
    model = AmongUs(5, 4)
    import pygame
    pygame.init()
    display_width = 800
    display_height = 600
    gameDisplay = pygame.display.set_mode((display_width,display_height))
    pygame.display.set_caption('Kripke')
    black = (0,0,0)
    white = (255,255,255)
    clock = pygame.time.Clock()
    kripke_img = model.plot_fixed()
    def show_kripke():
        gameDisplay.blit(kripke_img, (0,0))
        
    while True:
        gameDisplay.fill(white)
        show_kripke()
        pygame.display.update()
        clock.tick(60)
