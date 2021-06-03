import pygame
from abc import ABC, abstractmethod


'''
    The reason for this construction is that before pygame is initialized, you cannot create a font with pygame.font,
    so we cannot set the default value right away without initializing first. As code here will also run when the code
    is imported, then this results in a crash. Therefore, we use a little wrapper function to initialize it when we need
    it for the first time, which is after the init
'''
DEFAULT_GUI_FONT = None


def get_default_gui_font():
    global DEFAULT_GUI_FONT

    if DEFAULT_GUI_FONT is None:
        DEFAULT_GUI_FONT = pygame.font.SysFont(None, 20)
    return DEFAULT_GUI_FONT


class GUIElement(ABC):

    def __init__(self, screen, x, y, w, h):
        self.screen = screen
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    @abstractmethod
    def draw(self):
        pass

    def handle_click(self, pos, mouse_button):
        pass

    def in_bounds(self, pos):
        if pos[0] < self.x or pos[0] > (self.x + self.w):
            return False
        if pos[1] < self.y or pos[1] > (self.y + self.h):
            return False

        return True


class Button(GUIElement):

    def __init__(self, screen, x, y, w, h, text, on_click):
        super().__init__(screen, x, y, w, h)
        self.text = text
        self.text_img = get_default_gui_font().render(text, True, (255, 255, 255))
        self.on_click = on_click

    def update_text(self, new_text, font=None):

        if font is None:
            font = get_default_gui_font()

        self.text = new_text
        self.text_img = font.render(new_text, True, (255, 255, 255))

    def draw(self):
        pygame.draw.rect(self.screen, (50, 128, 128), (self.x, self.y, self.w, self.h))
        self.screen.blit(self.text_img, (self.x + 4, self.y + 10))

    def handle_click(self, pos, mouse_button):
        if self.in_bounds(pos):
            self.on_click()


class MultiLine(GUIElement):

    def __init__(self, screen, x, y, w, h, num_lines, line_spacing, font, color):
        super().__init__(screen, x, y, w, h)
        self.num_lines = num_lines
        self.spacing = line_spacing
        self.font = font
        self.color = color

        self.text = ["" for _ in range(num_lines)]
        self.text_images = [self.font.render(self.text[i], True, color) for i in range(num_lines)]

    def set_line(self, line_no, text):
        self.text[line_no] = text
        self.text_images[line_no] = self.font.render(text, True, self.color)

    def set_lines(self, lines):
        assert(len(lines) <= self.num_lines)

        for i in range(len(lines)):
            self.set_line(i, lines[i])

        for i in range(len(lines), self.num_lines):
            self.set_line(i, "")

    def draw(self):

        for i, text_img in enumerate(self.text_images):
            self.screen.blit(text_img, (self.x + 16, self.y + 16 + i * self.spacing))
