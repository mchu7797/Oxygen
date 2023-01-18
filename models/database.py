import pyodbc
from models.information import OxygenInformation
from models.scoreboard import OxygenScoreboard
from models.utils import OxygenUtils


class OxygenDatabase:
    def __init__(self, database_config):
        self.__connection = pyodbc.connect(database_config["connection_string"])
        self.__connection_trade = pyodbc.connect(
            database_config["connection_string_for_trade"]
        )
        self.scoreboard = OxygenScoreboard(self.__connection)
        self.information = OxygenInformation(self.__connection)
        self.utils = OxygenUtils(self.__connection, self.__connection_trade)
