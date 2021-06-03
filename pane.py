import pygame
from gui.gui_element import Button, MultiLine, get_default_gui_font
from util.util import LMObject, Message


class Pane(LMObject):

    def __init__(self, controller, screen, x, y, w, h, color):
        super().__init__()
        self.controller = controller
        self.screen = screen
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.color = color
        self.gui_elements = []

    def draw(self):
        pygame.draw.rect(self.screen, self.color, (self.x, self.y, self.w, self.h))
        [g.draw() for g in self.gui_elements]

    def add_gui_element(self, gui_element):
        self.gui_elements.append(gui_element)

    def handle_click(self, pos, mouse_button):
        if pos[0] < self.x or pos[0] > (self.x + self.w):
            return False
        if pos[1] < self.y or pos[1] > (self.y + self.h):
            return False

        [g.handle_click(pos, mouse_button) for g in self.gui_elements]

        return True

    def receive(self, message):
        pass


class SimpleSkeldPane(Pane):
    class Agent_Sprite:
        def __init__(self, x, y, w, h, agent_id, img):
            self.x, self.y = x, y
            self.w, self.h = w, h
            self.agent_id = agent_id
            self.img = img

        def draw(self, screen):
            screen.blit(self.img, (self.x, self.y))
            screen.blit(get_default_gui_font().render(f"{self.agent_id}", True, (255, 255, 255)),
                        (self.x + 4, self.y + 4))

    def __init__(self, controller, num_imp, screen, x, y):
        self.game_map = controller.game_map
        self.agents = controller.agents
        self.num_imp = num_imp

        self.bg_img = pygame.image.load("sprites/simpleskeld.png")
        self.imp_img = pygame.image.load("sprites/impostor_small.png")
        self.crew_img = pygame.image.load("sprites/crew_small.png")
        self.corpse_img = pygame.image.load("sprites/corpse_recoloured_small.png")

        size = self.bg_img.get_size()
        super().__init__(controller, screen, x, y, size[0], size[1], (255, 255, 255))

        self.room_coords = [(444, 124), (312, 216), (120, 136), (28, 267), (234, 262), (124, 424), (336, 366),
                            (474, 440), (624, 340), (258, 130), (524, 286), (130, 228), (266, 482)]
        self.room_width = [5, 2, 2, 3, 2, 3, 3, 4, 3, 5, 2, 2, 4]

        self.sprites_to_draw = []
        self.draw_update()

    def draw(self):
        self.screen.blit(self.bg_img, (self.x, self.y))

        [s.draw(self.screen) for s in self.sprites_to_draw]

    def draw_update(self):
        self.sprites_to_draw = []
        for room, room_corpses, room_coords, room_width in zip(self.game_map.rooms, self.game_map.corpses,
                                                               self.room_coords, self.room_width):
            start_x = room_coords[0]
            start_y = room_coords[1]
            width_used = 0

            # We only care about the IDs in the room.
            # TODO: This is messy... Perhaps we can turn it into events when observed?
            corpses_ids_in_room = [c[0] for c in room_corpses]

            for i, occupant in enumerate(room):
                if occupant or i in corpses_ids_in_room:

                    img_to_use = None
                    if i in corpses_ids_in_room:
                        img_to_use = self.corpse_img
                    elif len(room) - i > self.num_imp:
                        img_to_use = self.crew_img
                    else:
                        img_to_use = self.imp_img

                    size = img_to_use.get_size()
                    self.sprites_to_draw.append(self.Agent_Sprite(start_x, start_y, size[0], size[1], i, img_to_use))

                    start_x += self.crew_img.get_size()[0] + 8
                    width_used += 1

                    if width_used >= room_width:
                        width_used = 0
                        start_x = room_coords[0]
                        start_y += self.crew_img.get_size()[1] + 8

    def handle_click(self, pos, mouse_button):
        if super().handle_click(pos, mouse_button):
            for a in self.sprites_to_draw:
                if a.x <= pos[0] < (a.x + a.w):
                    if a.y <= pos[1] < (a.y + a.h):
                        print(f"You just clicked on agent: {a.agent_id}")
                        self.send(Message(self, "agent_clicked", {"agent_id" : a.agent_id}))

    def receive(self, message):
        if message.name == "update":
            self.draw_update()


class MenuPane(Pane):

    def __init__(self, controller, screen, x, y, w, h, color):
        super().__init__(controller, screen, x, y, w, h, color)

        self.add_gui_element(Button(screen, x + 8, y + 32, 128, 32, "Reset", self.controller.reset))
        self.add_gui_element(Button(screen, x + 8, y + 72, 128, 32, "Step", self.controller.step))


class InfoPane(Pane):

    def __init__(self, controller, screen, x, y, w, h, color):
        super().__init__(controller, screen, x, y, w, h, color)
        self.font = pygame.font.SysFont("arial", 20)

        self.multi_line = MultiLine(screen, x, y, w, h, 5, 28, get_default_gui_font(), (255, 255, 255))
        self.add_gui_element(self.multi_line)

        self.last_selected = -1

    def set_agent_info(self, agent_id):
        agent = self.controller.get_agent_with_id(agent_id)

        # If the agent has been murdered, then we get nothing back
        if agent is None:
            self.last_selected = -1
            self.multi_line.set_lines(["An ex-crewmate", "Its metabolic processes are now history!", "He kicked the bucket",
                                       "Run down the curtain,", "and joined the bleedin' choir invisible!"])
        else:
            info = agent.get_info()
            self.multi_line.set_lines(info)

    def receive(self, message):
        if message.name == "agent_clicked":
            self.last_selected = message.information["agent_id"]
            self.set_agent_info(self.last_selected)
        elif message.name == "update":
            if self.last_selected != -1:
                self.set_agent_info(self.last_selected)

