from pyodbc import DataError

from src.tools.encrypt import make_email_auth_token


class AccountManager:
    def __init__(self, connection, connection_trade):
        self._connection = connection
        self._connection_trade = connection_trade

    def get_change_nickname_token(self, username, password):
        cursor = self._connection.cursor()

        cursor.execute(
            "SELECT id FROM dbo.member WHERE userid=? AND passwd=?",
            (username, password),
        )
        account_id = cursor.fetchval()

        if account_id is None:
            return None

        cursor.execute(
            "SELECT USER_INDEX_ID FROM dbo.T_o2jam_charinfo WHERE USER_ID=?", username
        )
        player_id = cursor.fetchval()

        if player_id is None:
            return None

        auth_token = make_email_auth_token()

        cursor.execute(
            "DELETE FROM dbo.nickname_exchange_token where member_id=?",
            account_id,
        )

        cursor.execute(
            "INSERT INTO dbo.nickname_exchange_token VALUES (?, ?, ?, DATEADD(MINUTE, 5, GETDATE()))",
            (account_id, player_id, auth_token),
        )

        cursor.commit()

        return auth_token

    def get_nickname_changeable(self, username, password):
        cursor = self._connection.cursor()

        cursor.execute(
            """
            SELECT
                c.USER_INDEX_ID
            FROM
                dbo.member AS m
            LEFT OUTER JOIN
                dbo.T_o2jam_charinfo AS c ON m.userid = c.USER_ID
            WHERE
                m.userid = ? AND m.passwd = ?
            """,
            (username, password),
        )

        player_index_id = cursor.fetchval()

        if player_index_id is None:
            return False

        cursor.execute(
            """
            SELECT
                Gem
            FROM
                dbo.T_o2jam_charCash
            WHERE
                USER_INDEX_ID = ?
            """,
            player_index_id,
        )

        player_gem = cursor.fetchval()

        cursor.execute(
            """
            SELECT exchange_money
            FROM
                dbo.nickname_exchange_info
            WHERE
                nickname_count = COALESCE((
                    SELECT
                        COUNT(nickname)
                    FROM
                        dbo.nickname_history
                    WHERE
                        player_id = ?
                ), 1)
            """,
            player_index_id,
        )

        nickname_exchange_money = cursor.fetchval()

        return (
                player_gem is not None
                and nickname_exchange_money is not None
                and player_gem >= nickname_exchange_money
        )

    def change_nickname(self, token, nickname):
        cursor = self._connection.cursor()

        cursor.execute(
            "SELECT player_id FROM dbo.nickname_exchange_token WHERE token = ? AND token_expiration_period > GETDATE()",
            token,
        )

        player_index_id = cursor.fetchval()

        if player_index_id is None:
            return False

        cursor.execute(
            "SELECT COUNT(nickname) FROM dbo.nickname_history WHERE nickname = ?", nickname
        )

        nickname_history_count = cursor.fetchval()

        if nickname_history_count is not None and nickname_history_count > 0:
            return False

        cursor.execute(
            "SELECT COUNT(USER_NICKNAME) FROM dbo.T_o2jam_charinfo WHERE USER_NICKNAME = ?", nickname
        )

        nickname_count = cursor.fetchval()

        cursor.execute(
            "SELECT USER_NICKNAME FROM dbo.T_o2jam_charinfo WHERE USER_INDEX_ID = ?", player_index_id
        )

        current_nickname = cursor.fetchval()

        if nickname_count is not None and nickname_count > 0:
            return False

        cursor.execute(
            "SELECT COUNT(nickname) FROM dbo.nickname_history WHERE player_id = ?",
            player_index_id,
        )

        player_nickname_count = cursor.fetchval()

        if player_nickname_count is None:
            return False
        elif player_nickname_count > 9:
            player_nickname_count = 9

        cursor.execute(
            "SELECT exchange_money FROM dbo.nickname_exchange_info WHERE nickname_count = ?",
            player_nickname_count,
        )

        nickname_exchange_money = cursor.fetchval()

        cursor.execute(
            "SELECT GEM FROM dbo.T_o2jam_charCash WHERE USER_INDEX_ID = ?",
            player_index_id,
        )

        gem = cursor.fetchval()

        if gem is None or nickname_exchange_money > gem:
            return False

        cursor.execute(
            "UPDATE dbo.T_o2jam_charCash SET gem = ? WHERE USER_INDEX_ID = ?",
            (gem - nickname_exchange_money, player_index_id),
        )

        try:
            cursor.execute(
                "UPDATE dbo.T_o2jam_charinfo SET USER_NICKNAME = ? WHERE USER_INDEX_ID = ?",
                (nickname, player_index_id),
            )
        except DataError:
            self._connection.rollback()
            return False

        cursor.execute(
            "INSERT INTO dbo.nickname_history (player_id, nickname, occur_date) VALUES (?, ?, GETDATE())",
            (player_index_id, current_nickname),
        )

        cursor.execute(
            "DELETE FROM dbo.nickname_exchange_token WHERE player_id = ?",
            player_index_id)

        self._connection.commit()

        return True
