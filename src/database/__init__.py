import pyodbc

from src.database.chart_ranking_manager import ChartRankingManager
from src.database.info_manager import InfoManager
from src.database.player_ranking_manager import PlayerRankingManager
from src.database.utils import DatabaseUtils
from src.database.account import AccountManager


class DatabaseConnection:
    def __init__(self, database_config):
        self._connection = pyodbc.connect(database_config["connection_string"])
        self._trade_connection = pyodbc.connect(
            database_config["trade_connection_string"]
        )

        self.player_ranking = PlayerRankingManager(self._connection)
        self.chart_ranking = ChartRankingManager(self._connection)
        self.info = InfoManager(self._connection)
        self.utils = DatabaseUtils(self._connection, self._trade_connection)
        self.account_manager = AccountManager(self._connection, self._trade_connection)

    def close(self):
        try:
            self._connection.close()
            self._trade_connection.close()
        except pyodbc.ProgrammingError:
            return

    def __del__(self):
        self.close()
