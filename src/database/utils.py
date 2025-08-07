import re
from enum import Enum

from src.tools.encrypt import make_new_password_token, make_email_auth_token
from src.tools.input_validator import InputValidator


class GameChannelId(Enum):
    SUPER_HARD = 0
    HARD = 1
    NORMAL = 2
    EASY = 3


class DatabaseUtils:
    def __init__(self, connection, trade_connection):
        self._connection = connection
        self._trade_connection = trade_connection

    def search_chart(self, search_data):
        def escape_like(s):
            def escape_brackets(match):
                return '[' + ''.join(f'[{c}]' for c in match.group(1)) + ']'

            s = re.sub(r'\[([^\]]+)\]', escape_brackets, s)
            return s.replace('%', '[%]').replace('_', '[_]')

        query = """
                SELECT meta.MusicCode,
                       Title,
                       Artist,
                       NoteCharter,
                       BPM,
                       data.NoteLevel
                FROM dbo.o2jam_music_metadata meta
                         RIGHT OUTER JOIN (SELECT MusicCode, NoteLevel
                                           FROM dbo.o2jam_music_data
                                           WHERE Difficulty = 2) data ON data.MusicCode = meta.MusicCode
                WHERE data.NoteLevel BETWEEN ? AND ? \
                """

        params = [
            search_data['options']['level'][0],
            search_data['options']['level'][1]
        ]

        search_fields = ['Title', 'Artist', 'NoteCharter']
        search_conditions = [f"{field} LIKE ?" for field, enabled in
                             zip(search_fields, [search_data["options"]["title"],
                                                 search_data["options"]["artist"],
                                                 search_data["options"]["mapper"]])
                             if enabled]

        if search_conditions:
            query += " AND (" + " OR ".join(search_conditions) + ")"
            escaped_keyword = escape_like(search_data['keywords'])
            params.extend([f"%{escaped_keyword}%"] * len(search_conditions))

        query += " ORDER BY data.NoteLevel DESC"

        with self._connection.cursor() as cursor:
            cursor.execute(query, params)
            return [
                {
                    "music_code": code,
                    "title": title,
                    "artist": artist,
                    "note_charter": charter,
                    "bpm": round(float(bpm), 2),
                    "hard_level": level,
                }
                for code, title, artist, charter, bpm, level in cursor.fetchall()
            ]

    def get_online_players(self):
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT charinfo.USER_NICKNAME,
                       charInfo.Level,
                       login.SUB_CH
                FROM dbo.T_o2jam_login login
                         LEFT OUTER JOIN dbo.T_o2jam_charinfo charInfo on charinfo.USER_INDEX_ID = login.USER_INDEX_ID
                ORDER BY charInfo.Level desc
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
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                DELETE
                FROM dbo.T_o2jam_login
                FROM dbo.T_o2jam_login login
                         LEFT OUTER JOIN
                     dbo.member member
                     ON
                         member.userid = login.USER_ID
                             COLLATE
                                 Korean_Wansung_CI_AS
                WHERE member.userid = ?
                  AND member.passwd = ?
                """,
                (player_id, password),
            )

            cursor.commit()

    def exchange_cash(self, player_id, password, exchange_rate, exchange_direction):
        with self._connection.cursor() as cursor:
            with self._trade_connection.cursor() as trade_cursor:
                cursor.execute(
                    """
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
                        member.userid = ?
                        AND member.passwd = ?

                    SELECT
                        @PlayerId = ISNULL(@PlayerId, 0)

                    SELECT
                        @PlayerId AS PlayerId
                """,
                    (player_id, password, )
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
                    SET GEM   = ?,
                        MCASH = ?
                    WHERE USER_INDEX_ID = ?
                    """,
                    (player_wallet["gem"], player_wallet["mcash"], player_origin_id),
                )

                trade_cursor.execute(
                    "UPDATE dbo.UserMcash SET MCASH=? WHERE id = ?",
                    player_wallet["mcash"],
                    player_origin_id,
                )

                trade_cursor.commit()
                cursor.commit()

                return 0

    def get_wallet_info(self, player_id):
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT info.USER_INDEX_ID,
                       cash.GEM,
                       cash.MCASH
                FROM dbo.T_o2jam_charinfo info
                         LEFT OUTER JOIN
                     dbo.T_o2jam_charCash cash
                     ON
                         info.USER_INDEX_ID = cash.USER_INDEX_ID
                WHERE info.USER_ID = ?
                """,
                player_id,
            )

            raw_result = cursor.fetchone()

            if raw_result is None:
                return None

            return {
                "player_code": raw_result[0],
                "gem": raw_result[1],
                "mcash": raw_result[2],
            }

    def nickname_to_usercode(self, nickname):
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT USER_INDEX_ID
                FROM dbo.T_o2jam_charinfo
                WHERE USER_NICKNAME = ?
                """,
                nickname,
            )

            player_id = cursor.fetchval()

            if player_id is None:
                return -1

            return player_id

    def generate_login_token(self, username, password):
        with self._connection.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM dbo.member WHERE userid = ? AND passwd = ?",
                (username, password),
            )

            if cursor.fetchone() is None:
                return None

            cursor.execute(
                """
                SELECT COUNT(member_index_id)
                FROM dbo.banishment
                WHERE member_id = ?
                  AND (DATEADD(DAY, banishment_period, occur_date) > GETDATE() OR banishment_period IS NULL)
                """,
                username
            )

            banishment_flag = cursor.fetchval()

            if banishment_flag is not None and banishment_flag > 0:
                return None

            new_token = make_new_password_token()

            cursor.execute(
                "UPDATE dbo.member SET login_token_enabled = 1, login_token = ? WHERE userid = ?",
                (new_token, username),
            )

            cursor.commit()

            return new_token

    def get_player_email(self, username):
        with self._connection.cursor() as cursor:
            cursor.execute("SELECT email FROM dbo.member WHERE userid=?", username)
            account_email = cursor.fetchval()

            if account_email is None:
                return None

            return account_email

    def get_password_reset_token(self, username):
        with self._connection.cursor() as cursor:
            cursor.execute("SELECT id FROM dbo.member WHERE userid=?", username)
            account_id = cursor.fetchval()

            if account_id is None:
                return None

            auth_token = make_email_auth_token()

            cursor.execute(
                "DELETE FROM dbo.password_reset_token where member_id=?",
                account_id,
            )

            cursor.execute(
                "INSERT INTO dbo.password_reset_token VALUES (?, ?, DATEADD(MINUTE, 5, GETDATE()))",
                (account_id, auth_token),
            )

            cursor.commit()

            return auth_token

    def reset_password(self, token, password):
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT member_id
                FROM dbo.password_reset_token
                WHERE password_reset_token = ?
                  AND GETDATE() < token_expiration_period""",
                token,
            )

            member_id = cursor.fetchval()

            if member_id is None:
                return False

            cursor.execute("SELECT password_reset_blocked FROM dbo.member WHERE id = ?", member_id)

            password_reset_blocked = cursor.fetchval()

            if password_reset_blocked is not None and password_reset_blocked == 1:
                return False

            cursor.execute(
                "UPDATE dbo.member SET passwd=? WHERE id=?", (password, member_id)
            )
            cursor.execute("DELETE FROM dbo.password_reset_token WHERE password_reset_token = ?", token)

            cursor.commit()

            return True

    def check_password_strength(self, token, password):
        # 기본 패스워드 강도 검증
        password_valid, message = InputValidator.validate_password(password)
        if not password_valid:
            return False

        with self._connection.cursor() as cursor:
            cursor.execute("""
                           SELECT m.userid
                           FROM dbo.member AS m
                                    RIGHT OUTER JOIN dbo.password_reset_token AS t ON m.id = t.member_id
                           WHERE t.password_reset_token = ?""", token)

            username = cursor.fetchval()

            if username is None:
                return False

            cursor.execute("SELECT email FROM dbo.member WHERE userid=?", username)
            email = cursor.fetchval()

            if email is not None:
                email = email[:email.index('@')]
                if email in password:
                    return False

            cursor.execute("SELECT USER_NICKNAME FROM dbo.T_o2jam_charinfo WHERE USER_ID=?", username)
            nickname = cursor.fetchval()

            if nickname is not None and nickname in password:
                return False

            cursor.execute("SELECT COUNT(1) FROM dbo.bad_password WHERE password=?", password)

            is_bad_password = cursor.fetchval()

            if is_bad_password > 0:
                return False

            return True

    def find_user_by_email(self, email):
        with self._connection.cursor() as cursor:
            cursor.execute("SELECT userid FROM dbo.member WHERE email=?", email)

            account_id = cursor.fetchval()

            if account_id is None:
                return None

            return account_id

    def convert_member_id_to_player_id(self, member_id):
        query = f"""
            SELECT c.USER_INDEX_ID
                FROM T_o2jam_charinfo AS c
                         RIGHT OUTER JOIN dbo.member AS m ON m.userid = c.USER_ID
                WHERE m.id = ?
        """

        with self._connection.cursor() as cursor:
            cursor.execute(query, (member_id,))

            return cursor.fetchval()
