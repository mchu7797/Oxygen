from enum import Enum
from tools.encrypt import make_new_password_token


class GameChannelId(Enum):
    SUPER_HARD = 0
    HARD = 1
    NORMAL = 2
    EASY = 3


class DatabaseTools:
    def __init__(self, connection, connection_trade):
        self._connection = connection
        self._connection_trade = connection_trade

    def search_chart(self, search_data):
        cursor = self._connection.cursor()

        level_query = f"data.NoteLevel BETWEEN {search_data['options']['level'][0]} AND {search_data['options']['level'][1]}"
        search_query = []
        keyword = (
            search_data["keywords"]
            .replace("'", "''")
            .replace("%", "[%]")
            .replace("_", "[_]")
        )

        if search_data["options"]["title"]:
            search_query.append("Title LIKE '%{string}%'")
        if search_data["options"]["artist"]:
            search_query.append("Artist LIKE '%{string}%'")
        if search_data["options"]["mapper"]:
            search_query.append("NoteCharter LIKE '%{string}%'")

        cursor.execute(
            f"""
            SELECT
                meta.MusicCode,
                Title,
                Artist,
                NoteCharter,
                BPM,
                data.NoteLevel
            FROM
                dbo.o2jam_music_metadata meta
            RIGHT OUTER JOIN (
                SELECT
                    MusicCode,
                    NoteLevel
                FROM
                    dbo.o2jam_music_data WHERE Difficulty = 2) data
                        ON data.MusicCode = meta.MusicCode
            WHERE
                {level_query}
                AND ({" OR ".join(search_query).format(string = keyword)})
            ORDER BY
                data.NoteLevel DESC
        """
        )

        raw_result = cursor.fetchall()
        chart_list = []

        for chart_info in raw_result:
            chart_list.append(
                {
                    "music_code": chart_info[0],
                    "title": chart_info[1],
                    "artist": chart_info[2],
                    "note_charter": chart_info[3],
                    "bpm": round(float(chart_info[4]), 2),
                    "hard_level": chart_info[5],
                }
            )

        return chart_list

    def get_online_players(self):
        cursor = self._connection.cursor()

        cursor.execute(
            """
            SELECT
              charinfo.USER_NICKNAME,
              charInfo.Level,
              login.SUB_CH
            FROM
              dbo.T_o2jam_login login
              LEFT OUTER JOIN dbo.T_o2jam_charinfo charInfo on charinfo.USER_INDEX_ID = login.USER_INDEX_ID
            ORDER BY
              charInfo.Level desc
        """
        )

        raw_result = cursor.fetchall()
        online_players = {
            "super_hard_channel": [],
            "hard_channel": [],
            "normal_channel": [],
            "easy_channel": [],
            "all_players_count": len(raw_result),
        }

        for player in raw_result:
            packed_data = {"player_nickname": player[0], "player_level": player[1]}

            try:
                match GameChannelId(int(player[2])):
                    case GameChannelId.SUPER_HARD:
                        online_players["super_hard_channel"].append(packed_data)
                    case GameChannelId.HARD:
                        online_players["hard_channel"].append(packed_data)
                    case GameChannelId.NORMAL:
                        online_players["normal_channel"].append(packed_data)
                    case GameChannelId.EASY:
                        online_players["easy_channel"].append(packed_data)
            except ValueError:
                continue

        return online_players

    def clean_login_data(self, player_id, password):
        cursor = self._connection.cursor()

        cursor.execute(
            """
            DELETE FROM
                dbo.T_o2jam_login
            FROM
                dbo.T_o2jam_login login
            LEFT OUTER JOIN
                dbo.member member
            ON 
                member.userid = login.USER_ID
            COLLATE
	            Korean_Wansung_CI_AS
            WHERE
                member.userid = ?
                AND member.passwd = ?
        """,
            (player_id, password),
        )

        cursor.commit()

    def exchange_cash(self, player_id, password, exchange_rate, exchange_direction):
        cursor = self._connection.cursor()
        cursor_trade = self._connection_trade.cursor()

        cursor.execute(
            f"""
            DECLARE @PlayerId int

            SELECT
                @PlayerId = charinfo.USER_INDEX_ID
            FROM 
                dbo.member member
            LEFT OUTER JOIN
                dbo.T_o2jam_charinfo charinfo
            ON
                member.userid = charinfo.USER_ID
            COLLATE
	            Korean_Wansung_CI_AS
            WHERE
                member.userid = '{player_id}'
                AND member.passwd = '{password}'

            SELECT
                @PlayerId = ISNULL(@PlayerId, 0)

            SELECT
                @PlayerId AS PlayerId
        """
        )

        player_origin_id = cursor.fetchone()[0]

        if player_origin_id == 0:
            return 1

        player_wallet = self.get_wallet_info(player_id)

        if exchange_direction == "gem":
            if exchange_rate % 100 != 0:
                return 2
            if player_wallet["mcash"] < exchange_rate / 100:
                return 3

            player_wallet["gem"] += exchange_rate
            player_wallet["mcash"] -= exchange_rate / 100
        elif exchange_direction == "mcash":
            if player_wallet["gem"] < exchange_rate * 100:
                return 3

            player_wallet["mcash"] += exchange_rate
            player_wallet["gem"] -= exchange_rate * 100
        else:
            return 4

        cursor.execute(
            """
            UPDATE
                dbo.T_o2jam_charCash
            SET
                GEM = ?,
                MCASH = ?
            WHERE
                USER_INDEX_ID = ?
        """,
            (player_wallet["gem"], player_wallet["mcash"], player_origin_id),
        )

        cursor_trade.execute(
            "UPDATE dbo.UserMcash SET MCASH=? WHERE id = ?",
            player_wallet["mcash"],
            player_origin_id,
        )

        cursor_trade.commit()
        cursor.commit()

        return 0

    def get_wallet_info(self, player_id):
        cursor = self._connection.cursor()
        cursor.execute(
            """
            SELECT
                info.USER_INDEX_ID,
                cash.GEM,
                cash.MCASH
            FROM
                dbo.T_o2jam_charinfo info
            LEFT OUTER JOIN
                dbo.T_o2jam_charCash cash
            ON
                info.USER_INDEX_ID = cash.USER_INDEX_ID
            WHERE
                info.USER_ID = ?
        """,
            player_id,
        )

        raw_result = cursor.fetchone()

        return {
            "player_code": raw_result[0],
            "gem": raw_result[1],
            "mcash": raw_result[2],
        }

    def nickname_to_usercode(self, nickname):
        cursor = self._connection.cursor()

        cursor.execute(
            """
            SELECT
                USER_INDEX_ID
            FROM
                dbo.T_o2jam_charinfo
            WHERE
                USER_NICKNAME=?
        """,
            nickname,
        )

        raw_result = cursor.fetchone()

        if raw_result[0] == 0:
            return None

        return raw_result[0]

    def generate_login_token(self, username, password):
        if not check_account_is_valid(username, password):
            return False

        new_token = make_new_password_token()
        cursor = self._connection.cursor()

        cursor.execute(
            "UPDATE dbo.member SET login_token_enabled = 1, login_token = ? WHERE username = ? AND password=?",
            (new_token, username, password),
        )

        cursor.commit()

        return new_token
