class Logger:

    def __init__(self):
        self.messages = [[]]
        self.current_step = 0

    def end_step(self):
        self.current_step += 1
        self.messages.append([])

    def log(self, msg):
        self.messages[self.current_step].append(msg)

    def get_logs(self):
        return self.messages
