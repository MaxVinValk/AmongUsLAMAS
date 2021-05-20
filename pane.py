import pygame


class Pane:

    def __init__(self, screen, x, y, width, height, color):
        self.screen = screen
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color

    def draw(self):
        pygame.draw.rect(self.screen, self.color, (self.x, self.y, self.width, self.height))


class SimpleSkeldPane(Pane):

    def __init__(self, controller, num_imp, screen, x, y):
        self.game_map = controller.game_map
        self.agents = controller.agents
        self.num_imp = num_imp

        self.bg_img = pygame.image.load("sprites/simpleskeld.png")
        self.imp_img = pygame.image.load("sprites/impostor_small.png")
        self.crew_img = pygame.image.load("sprites/crew_small.png")
        self.corpse_img = pygame.image.load("sprites/corpse_recoloured_small.png")

        size = self.bg_img.get_size()
        super().__init__(screen, x, y, size[0], size[1], (255, 255, 255))

        room_names = ["Cafeteria", "Medbay", "Upper Engine", "Reactor", "Security", "Lower Engine", "Electrical",
                      "Storage", "Admin"]
        self.room_coords = [(444, 124), (312, 216), (120, 136), (28, 267), (234, 262), (124, 424), (336, 366),
                            (474, 440), (624, 340)]
        self.room_width = [5, 2, 2, 3, 2, 3, 3, 4, 3]

    def draw(self):
        self.screen.blit(self.bg_img, (self.x, self.y))

        for room, room_corpses, room_coords, room_width in zip(self.game_map.rooms, self.game_map.corpses, self.room_coords, self.room_width):
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

                    self.screen.blit(img_to_use, (start_x, start_y))
                    start_x += self.crew_img.get_size()[0] + 8
                    width_used += 1

                    if width_used >= room_width:
                        width_used = 0
                        start_x = room_coords[0]
                        start_y += self.crew_img.get_size()[1] + 8




