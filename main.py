import pygame
import sys
from map import SimpleSkeld
from controller import Controller
from logger import Logger
from tqdm import tqdm

from gui.tabmanager import TabManager
from pane import SimpleSkeldPane, MenuPane, InfoPane, KripkePane
from mlsolver.model import AmongUsTwoImp, AmongUsOneImp
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


def headless_run(controller, num_steps, file_name=None):
    logger = Logger.get_instance()
    logger.add_run_info("num_sim_runs", num_steps)

    for i in tqdm(range(num_steps)):
        logger.log(f"Run: {i}", Logger.LOG)
        controller.receive(Message(None, "run_to_end", None))

    logger.save_logs(file_name)


if __name__ == "__main__":

    num_crew = 8
    num_imp = 1  # Currently one and two are accepted values

    num_tasks = 5
    num_visuals = 4

    headless = False
    num_steps_headless = 10
    log_file_name = None

    cooldown = 5
    stationary_threshold = 0.5

    # Can be expanded easily to allow for more customization from a terminal run
    for i, arg in enumerate(sys.argv):
        if arg == "--headless":
            headless = True
        elif arg == "--num_steps":
            num_steps_headless = int(sys.argv[i + 1])
        elif arg == "--log_name":
            log_file_name = sys.argv[i + 1]
        elif arg == "--visuals":
            num_visuals = int(sys.argv[i + 1])
        elif arg == "--num_tasks":
            num_tasks = int(sys.argv[i + 1])
        elif arg == "--num_crew":
            num_crew = int(sys.argv[i + 1])
        elif arg == "--num_imp":
            num_imp = int(sys.argv[i + 1])
        elif arg == "--cooldown":
            cooldown = int(sys.argv[i + 1])
        elif arg == "--stat_thres":
            stationary_threshold = float(sys.argv[i + 1])

    if num_visuals > num_tasks:
        print("Visuals cannot be set higher than the number of tasks available")
        exit(1)

    if not 0 < num_imp < 2:
        print("One or two impostors are supported.")
        exit(1)

    # The map we want to use
    ss = SimpleSkeld(num_crew + num_imp)

    if num_imp == 1:
        km = AmongUsOneImp(num_crew + num_imp)
    else:
        km = AmongUsTwoImp(num_crew + num_imp)

    # The controller controls the simulation flow
    controller = Controller(km, ss, num_crew, num_imp, num_tasks, num_visuals, cooldown, stationary_threshold)

    logger = Logger.get_instance()
    logger.set_headless_mode(headless)

    # Dump run statistics into file so that it is easy to find back later during analysis
    logger.add_run_info("num_crew", num_crew)
    logger.add_run_info("num_imp", num_imp)
    logger.add_run_info("num_tasks", num_tasks)
    logger.add_run_info("num_visuals", num_visuals)
    logger.add_run_info("cooldown", cooldown)
    logger.add_run_info("stat_thres", stationary_threshold)

    if not headless:
        visual_run(controller, km, num_imp)
    else:
        headless_run(controller, num_steps_headless, log_file_name)
