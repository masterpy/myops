import os

class Log_Record():
    def __init__(self,log_file):
        self.log_dir = os.path.dirname(log_file)
        self.log_file = os.path.basename(log_file)
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

    def record_log(self,stdout):
        pass

