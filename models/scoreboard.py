from enum import Enum


class PlayerRankingOption(Enum):
    ORDER_P = 0
    ORDER_SS = 1
    ORDER_S = 2
    ORDER_A = 3
    ORDER_B = 4
    ORDER_C = 5
    ORDER_D = 6
    ORDER_CLEAR = 7
    ORDER_PLAYCOUNT = 8


class OxygenScoreboard:
    def __init__(self, connection):
        self.__connection = connection

    def get_player_scoreboard(self, player_id, gauge_difficulty, show_f_rank):
        cursor = self.__connection.cursor()

        if show_f_rank:
            option_query = "h.Progress <= 7"
        else:
            option_query = "h.Progress <= 8 AND h.Score / 10000 >= 10"

        cursor.execute(
            f"""
            SELECT
                h.PlayerCode,
                h.MusicCode,
                md.Title,
                h.Difficulty,
                d.NoteLevel,
                h.Score,
                p.progress_name,
                h.isClear,
                h.PlayedTime,
                sr.SongRank,
                ROW_NUMBER() OVER (
                ORDER BY
                    d.NoteLevel DESC,
                    h.Score DESC
                ) RowNumber
            FROM
                dbo.O2JamHighscore h
                LEFT OUTER JOIN
                    dbo.o2jam_music_metadata md ON md.MusicCode = h.MusicCode
                LEFT OUTER JOIN
                    dbo.o2jam_music_data d
                        ON d.MusicCode = h.MusicCode AND d.Difficulty = h.Difficulty
                LEFT OUTER JOIN
                    dbo.ProgressInfo p ON p.progress_index = h.Progress
                LEFT OUTER JOIN (
                    SELECT
                        PlayerCode,
                        MusicCode,
                        Difficulty,
                        RANK() OVER (
                        PARTITION BY MusicCode,
                        Difficulty
                        ORDER BY
                            Score DESC
                        ) SongRank
                    FROM
                        dbo.O2JamHighscore
                    ) sr on sr.PlayerCode = h.PlayerCode
                AND sr.MusicCode = h.MusicCode
                AND sr.Difficulty = h.Difficulty
            WHERE
                h.PlayerCode = {player_id}
                AND h.Difficulty = {gauge_difficulty}
                AND {option_query}
        """
        )

        raw_result = cursor.fetchall()
        records = []

        for record in raw_result:
            records.append(
                {
                    "player_code": record[0],
                    "music_code": record[1],
                    "music_title": record[2],
                    "music_difficulty": record[3],
                    "music_level": record[4],
                    "score": round(int(record[5]) / 10000, 2),
                    "progress": record[6],
                    "is_cleared_record": record[7],
                    "cleared_time": record[8],
                    "record_rank": record[9],
                    "row_number": record[10],
                }
            )

        if len(records) == 0:
            return None

        return records

    def get_music_scoreboard(self, music_id, gauge_difficulty):
        cursor = self.__connection.cursor()

        cursor.execute(
            """
            SELECT 
                h.PlayerCode, 
                c.USER_NICKNAME, 
                h.Cool, 
                h.Good, 
                h.Bad, 
                h.Miss, 
                h.MaxCombo, 
                h.Score,
                h.isClear,
                h.PlayedTime,
                p.progress_name,
                ROW_NUMBER() OVER (ORDER BY h.Score DESC, h.isClear DESC) status
            FROM 
                dbo.O2JamHighscore h 
                LEFT OUTER JOIN dbo.T_o2jam_charinfo c on h.PlayerCode = c.USER_INDEX_ID
                LEFT OUTER JOIN dbo.ProgressInfo p ON p.progress_index = h.Progress
            WHERE 
                h.MusicCode = ?
                AND h.Difficulty = ?
            ORDER BY
                h.Score desc
        """,
            (music_id, gauge_difficulty),
        )

        raw_result = cursor.fetchall()
        records = []

        for record in raw_result:
            records.append(
                {
                    "player_code": record[0],
                    "player_nickname": record[1],
                    "score_cool": record[2],
                    "score_good": record[3],
                    "score_bad": record[4],
                    "score_miss": record[5],
                    "score_max_combo": record[6],
                    "score": round(int(record[7]) / 10000, 2),
                    "is_cleared_record": record[8],
                    "cleared_time": record[9],
                    "progress": record[10],
                    "row_number": record[11],
                }
            )

        if len(records) == 0:
            return None

        return records

    def get_player_ranking(self, sort_option):
        cursor = self.__connection.cursor()

        if PlayerRankingOption(sort_option) == PlayerRankingOption.ORDER_PLAYCOUNT:
            cursor.execute(
                """
                SELECT 
                    c.USER_INDEX_ID, 
                    c.USER_NICKNAME, 
                    c.Battle, 
                    t.tier_name,
                    RANK() OVER (ORDER BY battle desc) RowNum
                FROM 
                    dbo.T_o2jam_charinfo c 
                    LEFT OUTER JOIN dbo.O2JamStatus s on s.PlayerCode = c.USER_INDEX_ID 
                    LEFT OUTER JOIN dbo.TierInfo t on s.Tier = t.tier_index
            """
            )
        else:
            cursor.execute(
                f"""
                SELECT
                    s.PlayerCode, 
                    c.USER_NICKNAME, 
                    s.{self.__ranking_option_to_string(sort_option)}, 
                    t.tier_name,
                    c.LastAccess,
                    RANK() OVER (ORDER BY s.{self.__ranking_option_to_string(sort_option)} desc, s.Tier ASC) RowNum
                FROM 
                    dbo.O2JamStatus s
                    LEFT OUTER JOIN dbo.T_o2jam_charinfo c on s.PlayerCode = c.USER_INDEX_ID 
                    LEFT OUTER JOIN dbo.TierInfo t on s.Tier = t.tier_index
            """
            )

        raw_result = cursor.fetchall()
        player_infos = []

        for player_info in raw_result:
            player_infos.append(
                {
                    "player_code": player_info[0],
                    "player_nickname": player_info[1],
                    "rank": player_info[2],
                    "tier": player_info[3],
                    "last_access_time": player_info[4].strftime("%Y-%m-%d, %H:%M:%S")
                    if player_info[4] is not None
                    else "None",
                    "row_number": player_info[5],
                }
            )

        return {
            "player_infos": player_infos,
            "current_option_name": self.__ranking_option_to_string(sort_option),
        }

    def __ranking_option_to_string(self, ranking_option):
        match PlayerRankingOption(ranking_option):
            case PlayerRankingOption.ORDER_P:
                return "P"
            case PlayerRankingOption.ORDER_SS:
                return "SS"
            case PlayerRankingOption.ORDER_S:
                return "S"
            case PlayerRankingOption.ORDER_A:
                return "A"
            case PlayerRankingOption.ORDER_B:
                return "B"
            case PlayerRankingOption.ORDER_C:
                return "C"
            case PlayerRankingOption.ORDER_D:
                return "D"
            case PlayerRankingOption.ORDER_CLEAR:
                return "Clear"
            case PlayerRankingOption.ORDER_PLAYCOUNT:
                return "PlayCount"
            case _:
                return "Unknown"
