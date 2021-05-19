import pygame

from controller import Controller
from agent import Crewmate, Impostor
from map import SimpleSkeld
from pane import Pane, SimpleSkeldPane


def default_controller(num_crew, num_imp, num_tasks):
    ss = SimpleSkeld(num_imp + num_crew)

    agents = [Crewmate(x, num_crew, num_imp, ss, None, num_tasks) for x in range(num_crew)]

    # TODO: Multiple impostor support here
    agents.append(Impostor(num_crew, num_crew, num_imp, ss, None))

    controller = Controller(agents, ss)

    return controller


if __name__ == "__main__":
    num_crew = 4
    num_imp = 1
    num_tasks = 5

    controller = default_controller(num_crew, num_imp, num_tasks)

    print(controller.game_map.nav)

    pygame.init()

    screen = pygame.display.set_mode([1024, 768])
    pygame.display.set_caption("Sus")

    panes = []
    panes.append(SimpleSkeldPane(controller, num_imp, screen, 0, 0))
    panes.append(Pane(screen, 768, 0, 256, 1024, (255, 255, 255)))
    panes.append(Pane(screen, 0, 512, 1024, 256, (64, 64, 64)))

    clock = pygame.time.Clock()

    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    controller.step()

        screen.fill((255, 255, 255))

        [pane.draw() for pane in panes]

        pygame.display.flip()

        clock.tick(60)
