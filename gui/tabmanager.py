from util.util import Message, LMObject


class TabManager(LMObject):

    def __init__(self):
        self.tabs = []
        self.active_tab = 0

    def add_tab(self, tab_content):
        self.tabs.append(tab_content)

    def draw(self):
        for pane in self.tabs[self.active_tab]:
            pane.draw()

    def handle_click(self, pos, mouse_button):
        [pane.handle_click(pos, mouse_button) for pane in self.tabs[self.active_tab]]

    def receive(self, message):

        if message.name == "switch":

            selected_tab = message.information["target"]

            if 0 <= selected_tab < len(self.tabs):
                self.active_tab = message.information["target"]
