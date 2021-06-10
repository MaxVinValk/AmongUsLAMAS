import pygame
from map import SimpleSkeld
from controller import Controller

from gui.tabmanager import TabManager
from pane import Pane, SimpleSkeldPane, MenuPane, InfoPane, KripkePane
from mlsolver.model import AmongUs as KripkeModel

if __name__ == "__main__":
    num_crew = 8
    num_imp = 2
    num_tasks = 5

    # The map we want to use
    ss = SimpleSkeld(num_imp + num_crew)

    COOLDOWN = 5
    STATIONARY_THRESHOLD = 0.8

    #TODO: Change this function to work with multiple impostors
    km = KripkeModel(num_crew + num_imp, num_crew)

    # TODO: Implement functioning logger instead of passing None

    # The controller controls the simulation flow
    controller = Controller(km, ss, num_crew, num_imp, num_tasks, COOLDOWN, STATIONARY_THRESHOLD, None)

    pygame.init()

    screen = pygame.display.set_mode([1024, 768])
    pygame.display.set_caption("Sus")

    # The tab manager is for drawing utility, and each pane something to be drawn on the screen
    tm = TabManager()

    ssp = SimpleSkeldPane(controller, num_imp, screen, 0, 0)
    mp = MenuPane(km, tm, controller, screen, 768, 0, 256, 1024, (255, 255, 255))
    ip = InfoPane(controller, screen, 0, 600, 1024, 256, (64, 64, 64))

    main_tab = [ssp, mp, ip]

    kp = KripkePane(km, tm, controller, screen, 0, 0, 1024, 768, (255, 255, 255))

    kripke_tab = [kp]

    tm.add_tab(main_tab)
    tm.add_tab(kripke_tab)

    # Registering listeners for message passing
    ssp.register_listener(ip)
    controller.register_listener(ssp)
    controller.register_listener(ip)

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
                tm.handle_click(pos, event.button)

        screen.fill((255, 255, 255))

        tm.draw()

        # To allow the simulation to play itself
        controller.check_continuous_update()

        pygame.display.flip()
        clock.tick(30)
