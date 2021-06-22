from datetime import datetime
import pickle
"""
    Singleton logger class for ease of access throughout the program.
"""


class Logger:
    PRINT_VISUAL    = 0b1
    PRINT_HEADLESS  = 0b10
    LOG             = 0b100
    WARN            = 0b1000
    ERR             = 0b10000
    HEADER          = 0b100000

    __instance = None

    @staticmethod
    def get_instance():
        if not Logger.__instance:
            Logger()
        return Logger.__instance

    def __init__(self):

        if Logger.__instance is not None:
            raise Exception("This is a singleton class, access with get_instance instead!")
        else:
            Logger.__instance = self

        self.run_info = {}
        self.messages = []
        self.headless_mode = False

    def set_headless_mode(self, val):
        self.headless_mode = val

    def log(self, msg, log_level):

        if log_level & Logger.LOG:
            self.messages.append(msg)
        if (log_level & Logger.PRINT_VISUAL and not self.headless_mode) or (log_level & Logger.PRINT_HEADLESS and self.headless_mode):
            if log_level & Logger.WARN:
                print(f"\033[93m{msg}\033[0m")
            elif log_level & Logger.ERR:
                print(f"\033[91m{msg}\033[0m")
            elif log_level & Logger.HEADER:
                print(f"\033[1;32m{msg}\033[0m")
            else:
                print(msg)

    def add_run_info(self, key, value):
        self.run_info[key] = value

    def get_logs(self):
        return self.messages

    def save_logs(self, file_name=None):

        if file_name is None:
            file_name = datetime.now().strftime("%y_%m_%d__%H-%M.amongus")
        elif not file_name.endswith(".amongus"):
            file_name = file_name + ".amongus"

        with open(file_name, "wb") as f:
            pickle.dump({"run_info": self.run_info, "logs": self.messages}, f)


