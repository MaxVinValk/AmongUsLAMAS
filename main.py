import pygame
import sys
from map import SimpleSkeld
from controller import Controller

from gui.tabmanager import TabManager
from pane import Pane, SimpleSkeldPane, MenuPane, InfoPane, KripkePane
from mlsolver.model import AmongUs as KripkeModel
from util.util import Message


def visual_run(controller, km, num_imp):
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
                if event.button == 1:
                    pos = pygame.mouse.get_pos()
                    tm.handle_click(pos, event.button)
                # Ugly and should be handled by the TM
                elif tm.active_tab == 1:
                    if event.button == 4:
                        kp.receive(Message(None, "zoom", {"direction": "up"}))
                    elif event.button == 5:
                        kp.receive(Message(None, "zoom", {"direction": "down"}))

        # held key events
        keys = pygame.key.get_pressed()

        # Should be handled by the tm
        if tm.active_tab == 1:
            if keys[pygame.K_LEFT]:
                kp.receive(Message(None, "scroll", {"side": "left"}))
            elif keys[pygame.K_RIGHT]:
                kp.receive(Message(None, "scroll", {"side": "right"}))

            if keys[pygame.K_UP]:
                kp.receive(Message(None, "scroll", {"side": "up"}))
            elif keys[pygame.K_DOWN]:
                kp.receive(Message(None, "scroll", {"side": "down"}))

        screen.fill((255, 255, 255))

        tm.draw()

        # To allow the simulation to play itself
        controller.check_continuous_update()

        pygame.display.flip()
        clock.tick(30)

def headless_run(controller, num_steps):

    #TODO: Use TQDM after proper logger implementation
    for i in range(num_steps):
        print(f"\033[1;32m Run: {i}\033[0;37m")
        controller.receive(Message(None, "run_to_end", None))



if __name__ == "__main__":

    num_crew = 8
    num_imp = 2
    num_tasks = 5

    headless = False
    num_steps_headless = 10

    # Can be expanded easily to allow for more customization from a terminal run
    for i, arg in enumerate(sys.argv):
        if arg == "--headless":
            headless = True
        elif arg == "--num_steps":
            num_steps_headless = int(sys.argv[i + 1])

    # The map we want to use
    ss = SimpleSkeld(num_imp + num_crew)

    COOLDOWN = 5
    STATIONARY_THRESHOLD = 0.5

    km = KripkeModel(num_crew + num_imp)

    # TODO: Implement functioning logger instead of passing None

    # The controller controls the simulation flow
    controller = Controller(km, ss, num_crew, num_imp, num_tasks, COOLDOWN, STATIONARY_THRESHOLD, None)

    if not headless:
        visual_run(controller, km, num_imp)
    else:
        headless_run(controller, num_steps_headless)




