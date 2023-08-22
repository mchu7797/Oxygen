import pyodbc
from database.info_manager import InfoManager
from database.scoreboard_manager import ScoreboardManager
from database.tools import DatabaseTools


class DatabaseConnection:
    def __init__(self, database_config):
        self._connection = pyodbc.connect(database_config["connection_string"])
        self._connection_trade = pyodbc.connect(
            database_config["connection_string_for_trade"]
        )
        self.scoreboard = ScoreboardManager(self._connection)
        self.info = InfoManager(self._connection)
        self.tools = DatabaseTools(self._connection, self._connection_trade)
