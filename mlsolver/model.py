""" AmongUs Kripke model

Module contains a simple Kripke model for Among Us and 
"""

from mlsolver.kripke import KripkeStructure, World
from mlsolver.formula import Atom, And, Not, Or, Box_a, Box_star
from logger import Logger
from graphviz import Digraph
from abc import abstractmethod
import pygame

import os
import tempfile
import numpy as np


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


def kripke_structure_solve_a(self, agent, formula, print_statement=False):
    """ This function is a small change to mlsolver taken from the code of The Ship at 
    https://github.com/JohnRoyale/MAS2018/blob/master/mlsolver/kripke.py#L36
    it is necessary to be able to execute updates for only one agent in multi-agent Kripke structures
    """

    logger = Logger.get_instance()

    nodes_to_remove = self.nodes_not_follow_formula(formula)
    if print_statement and len(nodes_to_remove) != 0:
        logger.log("Removing nodes: {}".format(nodes_to_remove), Logger.PRINT_VISUAL | Logger.LOG)
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


def fixed_layout_graphviz(worlds, point, connectivity, r=2, label_pos=0.25):
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
        dot.node(w, w, pos="{},{}!".format(x, y), shape='box', peripheries=str(1 + (i == point)))

    # Labels are placed in "virtual" nodes between the worlds
    for start, end, label in connectivity:
        edge_label_pos = label_pos
        if (abs(start - end) <= 1) or (max(start, end) == len(worlds) - 1) and (min(start, end) == 0):
            edge_label_pos = 0.5
        label_x = world_x[start] * edge_label_pos + world_x[end] * (1 - edge_label_pos)
        label_y = world_y[start] * edge_label_pos + world_y[end] * (1 - edge_label_pos)
        edgename = str((start, end))
        dot.node(str((start, end)), label, pos="{},{}!".format(label_x, label_y), shape='plaintext')
        dot.edge(edgename, worlds[start])
        dot.edge(edgename, worlds[end])
    return dot


class AmongUsKripke:
    def __init__(self, num_agents):
        self.num_agents = num_agents
        self.worlds = []
        self.relations = {}
        self.kripke_structure = None
        self.real_world = ""

        self.has_received_update = True
        self.buffered_img = None

    @abstractmethod
    def setup(self):
        pass

    @abstractmethod
    def plot_fixed(self, size=15, label_pos=0.25, render=True):
        pass

    def suspects(self, observer, other):
        """ Check if agent i suspects agent j of being the impostor
        We do this by evaluating the sentence "i knows not "IsImp:j"
        """
        sentence = Not(Box_a(str(observer), Not(Atom("IsImp:{}".format(other)))))
        return sentence.semantic(self.kripke_structure, self.real_world)

    # If it holds that: other is an impostor and knows that the observer knows that the other is an impostor
    def knows_knows_imp(self, observer, other):
        sentence = Box_a(str(other), Box_a(str(observer), Atom(f"IsImp:{other}")))
        return sentence.semantic(self.kripke_structure, self.real_world)

    def knows_imp(self, observer, other):
        sentence = Box_a(str(observer), Atom(f"IsImp:{other}"))
        return sentence.semantic(self.kripke_structure, self.real_world)

    def knows_crew(self, observer, other):
        sentence = Box_a(str(observer), Not(Atom(f"IsImp:{other}")))
        return sentence.semantic(self.kripke_structure, self.real_world)

    def update_known_impostor(self, observer, impostor):
        """Update the model to register that a crewmate has caught the impostor
        """
        sentence = Atom("IsImp:{}".format(impostor))
        self.kripke_structure = kripke_structure_solve_a(self.kripke_structure, str(observer), sentence)
        self.has_received_update = True

    def update_known_crewmate(self, observer, crewmate):
        """Update the model to register that a crewmate no longer suspects another crewmate
        (e.g. because of a visual task)
        """
        sentence = Not(Atom("IsImp:{}".format(crewmate)))
        self.kripke_structure = kripke_structure_solve_a(self.kripke_structure, str(observer), sentence)
        self.has_received_update = True

    def update(self, observer, sentence):
        if sentence is not None:
            self.kripke_structure = kripke_structure_solve_a(self.kripke_structure, str(observer), sentence, True)

    def retrieve_knowledge(self, observer):
        conjunction = Not(Atom(f"IsImp:{observer}"))

        for i in range(self.num_agents):
            if i == observer:
                continue

            if self.knows_crew(observer, i):
                conjunction = And(conjunction, Not(Atom(f"IsImp:{i}")))
            elif self.knows_imp(observer, i):
                conjunction = And(conjunction, Atom(f"IsImp:{i}"))
            else:
                conjunction = And(conjunction, Or(Atom(f"IsImp:{i}"), Not(Atom(f"IsImp:{i}"))))

        return Box_a(str(observer), conjunction)

    def plot_fixed(self, size=15, label_pos=0.25, render=True):
        """ Plot the kripke structure using the `fixed_layout_kripke` function
        """
        if not self.has_received_update:
            return self.buffered_img
        else:
            self.has_received_update = False

            worlds = list()
            world_id = dict()
            for i, w in enumerate(self.kripke_structure.worlds):
                world_id[w.name] = i
                worlds.append(w.name)
            connectivity = {}

            for agent, relations in self.kripke_structure.relations.items():
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
                edges.append((world_id[start], world_id[end], ",".join(sorted(labels))))

            dot = fixed_layout_graphviz(worlds, world_id[self.real_world], edges, r=size, label_pos=label_pos)
            if render:
                with tempfile.TemporaryDirectory() as tmpdirname:
                    dot.render('kripke', format='png', directory=tmpdirname)
                    img = pygame.image.load(os.path.join(tmpdirname, 'kripke.png'))
                    self.buffered_img = img
                    return img
            else:
                return dot

    def reset(self):
        self.setup()


class AmongUsTwoImp(AmongUsKripke):
    def __init__(self, num_agents):
        super().__init__(num_agents)
        self.setup()

    def setup(self):
        self.worlds = []
        self.relations = {}

        # Build the same number of worlds as there are agents. Each world has one impostor
        for i in range(self.num_agents):
            for k in range(i + 1, self.num_agents):

                agent_is_impostor = {}
                for j in range(self.num_agents):
                    if i == j or k == j:
                        agent_is_impostor[f"IsImp:{j}"] = True
                    else:
                        agent_is_impostor[f"IsImp:{j}"] = False

                self.worlds.append(World(f"Imp{i}_{k}", agent_is_impostor))

        # Build relations according to the following rules:
        # Each agent knows whether they themselves are impostor or not
        # This leads to crewmates not having accessibility to the worlds where they are impostor

        # Relationships for each agent
        for i in range(self.num_agents - 2):
            rels = []
            # 2 for loops for each possible world
            for x1 in range(self.num_agents):
                for y1 in range(x1 + 1, self.num_agents):
                    for x2 in range(self.num_agents):
                        for y2 in range(x2 + 1, self.num_agents):
                            if x1 == x2 and y1 == y2:
                                continue

                            if i != x1 and i != y1 and i != x2 and i != y2:
                                rels.append((f"Imp{x1}_{y1}", f"Imp{x2}_{y2}"))
            self.relations[f"{i}"] = set(rels)

        self.relations.update(add_symmetric_edges(self.relations))
        self.relations.update(add_reflexive_edges(self.worlds, self.relations))
        self.kripke_structure = KripkeStructure(self.worlds, self.relations)

        self.real_world = f"Imp{self.num_agents - 2}_{self.num_agents - 1}"
        self.has_received_update = True

    def plot_fixed(self):
        return super().plot_fixed()


class AmongUsOneImp(AmongUsKripke):
    def __init__(self, num_agents):
        super().__init__(num_agents)

        # Last index is always the impostor
        self.impostor = num_agents - 1

        self.setup()

    def setup(self):
        self.worlds = []
        self.relations = {}

        # Build the same number of worlds as there are agents. Each world has one impostor
        for i in range(self.num_agents):
            agent_is_impostor = {}
            for j in range(self.num_agents):
                if i == j:
                    agent_is_impostor["IsImp:{}".format(j)] = True
                else:
                    agent_is_impostor["IsImp:{}".format(j)] = False

            self.worlds.append(World("Imp{}".format(i), agent_is_impostor))

        # Build relations according to the following rules:
        # Each agent knows whether they themselves are impostor or not
        # This leads to crewmates not having accessibility to the worlds where they are impostor
        for i in range(self.num_agents):
            if i is not self.impostor:
                self.relations[str(i)] = set(
                    ("Imp{}".format(x), "Imp{}".format(y)) for x in range(self.num_agents) for y in
                    range(self.num_agents) if
                    ((i != x) and (i != y)))

        self.relations.update(add_symmetric_edges(self.relations))
        self.relations.update(add_reflexive_edges(self.worlds, self.relations))
        self.kripke_structure = KripkeStructure(self.worlds, self.relations)
        self.real_world = "Imp{}".format(self.impostor)

    def plot_fixed(self):
        return super().plot_fixed(size=4)