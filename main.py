import os
import logging
import logging.handlers

from customDiscordClient import customDiscordClient
import sys

# Logging config

def init_logger(debug=False):

    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
    
    consoleHandler = logging.StreamHandler(sys.stdout)
    consoleHandler.setFormatter(formatter)
        
    handlers = [consoleHandler]
    if not os.environ.get("AM_I_IN_A_DOCKER_CONTAINER"):
        if not os.path.isdir("logs"):
            os.mkdir("logs")
        script_name = os.path.basename(__file__)
        logpath = f"logs/{script_name}.log"
        rotatingFileHandler = logging.handlers.TimedRotatingFileHandler(filename=logpath, when='midnight', backupCount=30)
        rotatingFileHandler.suffix = "%Y%m%d"
        rotatingFileHandler.setFormatter(formatter)
        handlers.append(rotatingFileHandler)
    
    if debug:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO
    logging.basicConfig(format='%(asctime)s | %(levelname)s | %(message)s', level=log_level, handlers=handlers)

    class NoRunningFilter(logging.Filter):
        def filter(self, record):
            if "change_client_presence" in record.getMessage():
                return False
            else:
                return True

    my_filter = NoRunningFilter()
    logging.getLogger("apscheduler.executors.default").addFilter(my_filter)

init_logger()
logger = logging.getLogger(__name__)
API_KEY = os.environ.get("API_KEY")
cogs_dir = "cogs"
command_prefix = "!!!"

def handle_exception(exc_type, exc_value, exc_traceback):
    logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = handle_exception

if __name__ == "__main__":
    bot = customDiscordClient(command_prefix=command_prefix, case_insensitive=True, logger=logger, cogs_dir=cogs_dir)
    bot.run(API_KEY)
