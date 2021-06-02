import pygame
from map import SimpleSkeld
from controller import Controller

from pane import Pane, SimpleSkeldPane, MenuPane


if __name__ == "__main__":
    num_crew = 4
    num_imp = 1
    num_tasks = 5

    ss = SimpleSkeld(num_imp + num_crew)

    COOLDOWN = 5
    STATIONARY_THRESHOLD = 0.8

    # TODO: Implement functioning logger instead of passing None
    controller = Controller(ss, num_crew, num_imp, num_tasks, COOLDOWN, STATIONARY_THRESHOLD, None)

    pygame.init()

    screen = pygame.display.set_mode([1024, 768])
    pygame.display.set_caption("Sus")

    panes = [SimpleSkeldPane(controller, num_imp, screen, 0, 0),
             MenuPane(controller, screen, 768, 0, 256, 1024, (255, 255, 255)),
             Pane(controller, screen, 0, 600, 1024, 256, (64, 64, 64))
             ]

    clock = pygame.time.Clock()

    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    controller.step()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                [pane.handle_click(pos, event.button) for pane in panes]

        screen.fill((255, 255, 255))

        [pane.draw() for pane in panes]

        pygame.display.flip()

        clock.tick(60)
