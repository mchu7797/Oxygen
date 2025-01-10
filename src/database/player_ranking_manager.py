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


class PeriodOption(Enum):
    DAY_1 = 0
    DAY_7 = 1
    DAY_30 = 2
    YEAR_HALF = 3
    YEAR_1 = 4


class PlayerRankingManager:
    def __init__(self, connection):
        self._connection = connection

    def get_player_top_records(self, player_id, gauge_difficulty, show_f_rank, page):
        cursor = self._connection.cursor()

        if show_f_rank:
            view_option_query = "h.Score >= 50000"
        else:
            view_option_query = "h.isClear = 1"

        cursor.execute(
            f"""
                    WITH RankedResults AS (
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
                            h.PatternOrder,
                            ROUND(h.PlaySpeedRate, 3) AS PlaySpeedRate,
                            h.PlayTimingRate,
                            h.FLNOption,
                            h.SLNOption,
                            h.isNLN,
                            sr.SongRank AS SongRank,
                            ROW_NUMBER() OVER (
                                ORDER BY d.NoteLevel DESC, h.Score DESC
                            ) AS RowNumber
                        FROM dbo.O2JamHighscore h
                        INNER JOIN dbo.o2jam_music_data d
                            ON d.MusicCode = h.MusicCode
                            AND d.Difficulty = h.Difficulty
                        LEFT JOIN dbo.o2jam_music_metadata md
                            ON md.MusicCode = h.MusicCode
                        LEFT JOIN dbo.ProgressInfo p
                            ON p.progress_index = h.Progress
                        LEFT JOIN (
                            SELECT
                                PlayerCode,
                                MusicCode,
                                Difficulty,
                                RANK() OVER (
                                    PARTITION BY MusicCode, Difficulty
                                    ORDER BY Score DESC
                                ) AS SongRank
                            FROM dbo.O2JamHighscore
                        ) sr ON sr.PlayerCode = h.PlayerCode AND
                                sr.MusicCode = h.MusicCode AND
                                sr.Difficulty = h.Difficulty
                        WHERE h.PlayerCode = ?
                            AND h.Difficulty = ?
                            AND {view_option_query}
                    )
                    SELECT
                        PlayerCode,
                        MusicCode,
                        Title,
                        Difficulty,
                        NoteLevel,
                        Score,
                        progress_name,
                        isClear,
                        FORMAT(PlayedTime, 'yyyy-MM-dd hh:mm tt', 'en-US') AS PlayedTime,
                        SongRank,
                        PatternOrder,
                        PlaySpeedRate,
                        PlayTimingRate,
                        FLNOption,
                        SLNOption,
                        isNLN,
                        RowNumber
                    FROM RankedResults
                    {"WHERE RowNumber BETWEEN ? * 100 + 1 AND (? + 1) * 100" if page is not None else ""}
                    ORDER BY RowNumber;
                """,
            (player_id, gauge_difficulty, page, page) if page is not None else (player_id, gauge_difficulty),
        )

        raw_records = cursor.fetchall()
        response = []

        for record in raw_records:
            response.append(
                {
                    "player_code": record[0],
                    "music_code": record[1],
                    "music_title": record[2],
                    "music_difficulty": record[3],
                    "music_level": record[4],
                    "score": record[5],
                    "progress": record[6],
                    "is_cleared_record": record[7],
                    "cleared_time": record[8],
                    "record_rank": record[9],
                    "pattern_order": record[10],
                    "play_speed_rate": float(record[11]) if record[11] is not None else None,
                    "play_timing_rate": record[12],
                    "fln_option": record[13],
                    "sln_option": record[14],
                    "is_nln": record[15],
                    "row_number": record[16]
                }
            )

        if len(response) == 0:
            return None

        return response

    def get_player_top_records_count(self, player_id, gauge_difficulty, show_f_rank):
        cursor = self._connection.cursor()

        if show_f_rank:
            view_option_query = "Score >= 50000"
        else:
            view_option_query = "isClear = 1"

        cursor.execute(
            f"""
                SELECT COUNT(PlayerCode)
                FROM dbo.O2JamHighscore
                WHERE PlayerCode = ?
                      AND Difficulty = ?
                      AND {view_option_query}
            """,
            (player_id, gauge_difficulty),
        )

        return cursor.fetchval()

    def get_player_ranking(self, sort_option: int):
        cursor = self._connection.cursor()

        sort_option = PlayerRankingOption(sort_option)

        if sort_option == PlayerRankingOption.ORDER_PLAYCOUNT:
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
        elif sort_option == PlayerRankingOption.ORDER_CLEAR:
            cursor.execute(
                f"""
                            SELECT
                                s.PlayerCode, 
                                c.USER_NICKNAME, 
                                s.{self._ranking_option_to_string(sort_option)},
                                t.tier_name,
                                RANK() OVER (
                                    ORDER BY
                                        s.{self._ranking_option_to_string(sort_option)} desc,
                                        s.D desc,
                                        s.C desc,
                                        s.B desc,
                                        s.A desc,
                                        s.S desc,
                                        s.SS desc,
                                        s.P desc,
                                        s.UpdatedTime desc
                                ) RowNum
                            FROM 
                                dbo.O2JamStatus s
                                LEFT OUTER JOIN dbo.T_o2jam_charinfo c on s.PlayerCode = c.USER_INDEX_ID 
                                LEFT OUTER JOIN dbo.TierInfo t on s.Tier = t.tier_index
                        """
            )
        else:
            cursor.execute(
                f"""
                SELECT
                    s.PlayerCode, 
                    c.USER_NICKNAME, 
                    s.{self._ranking_option_to_string(sort_option)},
                    t.tier_name,
                    RANK() OVER (
                        ORDER BY
                            s.{self._ranking_option_to_string(sort_option)} desc,
                            s.UpdatedTime desc
                    ) RowNum
                FROM 
                    dbo.O2JamStatus s
                    LEFT OUTER JOIN dbo.T_o2jam_charinfo c on s.PlayerCode = c.USER_INDEX_ID 
                    LEFT OUTER JOIN dbo.TierInfo t on s.Tier = t.tier_index
            """
            )

        raw_records = cursor.fetchall()
        player_informations = []

        for player_information in raw_records:
            player_informations.append(
                {
                    "player_code": player_information[0],
                    "player_nickname": player_information[1],
                    "rank": player_information[2],
                    "tier": player_information[3],
                    "row_number": player_information[4],
                }
            )

        return {
            "player_infos": player_informations,
            "current_option_name": self._ranking_option_to_string(sort_option),
        }

    @staticmethod
    def _ranking_option_to_string(ranking_option):
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

    def get_record_histories(self, player_id, chart_id, difficulty, order_by_date):
        cursor = self._connection.cursor()

        if order_by_date:
            order_query = "ORDER BY PlayedTime DESC"
        else:
            order_query = "ORDER BY Score DESC"

        cursor.execute(
            f"""
                SELECT TOP 50
                    FORMAT(PlayedTime, 'yyyy-MM-dd hh:mm tt', 'en-US') AS PlayedTime,
                    Score,
                    Progress,
                    isClear,
                    Cool,
                    Good,
                    Bad,
                    Miss,
                    MaxCombo,
                    PatternOrder,
                    ROUND(PlaySpeedRate, 3) AS PlaySpeedRate,
                    PlayTimingRate,
                    FLNOption,
                    SLNOption,
                    isNLN,
                    RowNum
                FROM (
                    SELECT *,
                           ROW_NUMBER() OVER (
                               PARTITION BY isClear
                               ORDER BY 
                                   CASE 
                                       WHEN isClear = 1 THEN Score
                                       ELSE Cool + Good + Bad + Miss
                                   END DESC
                           ) AS RowNum
                    FROM dbo.O2JamPlaylog
                    WHERE PlayerCode = ? AND MusicCode = ? AND Difficulty = ?
                ) RankedScores
                ORDER BY isClear DESC, RowNum
            """,
            (player_id, chart_id, difficulty),
        )

        query_results = cursor.fetchall()

        if query_results is None:
            return []

        response = []

        for rank_info in query_results:
            response.append(
                {
                    "player_code": player_id,
                    "cleared_time": rank_info[0],
                    "score": rank_info[1],
                    "progress": rank_info[2],
                    "is_cleared_record": rank_info[3],
                    "score_cool": rank_info[4],
                    "score_good": rank_info[5],
                    "score_bad": rank_info[6],
                    "score_miss": rank_info[7],
                    "score_max_combo": rank_info[8],
                    "pattern_order": rank_info[9],
                    "play_speed_rate": float(rank_info[10]) if rank_info[10] is not None else None,
                    "play_timing_rate": rank_info[11],
                    "fln_option": rank_info[12],
                    "sln_option": rank_info[13],
                    "is_nln": rank_info[14],
                    "row_number": rank_info[15],
                }
            )

        return response

    def get_recent_records(self, player_id, difficulty, show_f_rank):
        cursor = self._connection.cursor()

        view_option_query = ""

        if not show_f_rank:
            view_option_query = "AND isClear = 1"

        cursor.execute(
            f"""
                SELECT TOP 150
                    p.MusicCode,
                    mt.Title,
                    m.NoteLevel,
                    FORMAT(PlayedTime, 'yyyy-MM-dd hh:mm tt', 'en-US') AS PlayedTime,
                    Score,
                    Progress,
                    isClear,
                    Cool,
                    Good,
                    Bad,
                    Miss,
                    MaxCombo,
                    PatternOrder,
                    ROUND(PlaySpeedRate, 3) AS PlaySpeedRate,
                    PlayTimingRate,
                    FLNOption,
                    SLNOption,
                    isNLN,
                    ROW_NUMBER() OVER (ORDER BY PlayedTime DESC) RowNum
                FROM dbo.O2JamPlaylog AS p
                RIGHT OUTER JOIN
                    dbo.o2jam_music_metadata AS mt ON p.MusicCode = mt.MusicCode
                RIGHT OUTER JOIN
                    dbo.o2jam_music_data AS m ON p.MusicCode = m.MusicCode AND p.Difficulty = m.Difficulty
                WHERE
                    PlayerCode = ?
                    AND p.Difficulty = ?
                    AND PlayedTime > DATEADD(day, -15, GETDATE())
                    {view_option_query}
            """,
            (player_id, difficulty),
        )

        query_results = cursor.fetchall()

        if query_results is None:
            return []

        response = []

        for rank_info in query_results:
            response.append(
                {
                    "music_code": rank_info[0],
                    "music_title": rank_info[1],
                    "music_level": rank_info[2],
                    "cleared_time": rank_info[3],
                    "score": rank_info[4],
                    "progress": rank_info[5],
                    "is_cleared_record": rank_info[6],
                    "score_cool": rank_info[7],
                    "score_good": rank_info[8],
                    "score_bad": rank_info[9],
                    "score_miss": rank_info[10],
                    "score_max_combo": rank_info[11],
                    "pattern_order": rank_info[12],
                    "play_speed_rate": float(rank_info[13]) if rank_info[13] is not None else None,
                    "play_timing_rate": rank_info[14],
                    "fln_option": rank_info[15],
                    "sln_option": rank_info[16],
                    "is_nln": rank_info[17],
                    "row_number": rank_info[18],
                }
            )

        return response

    def get_best_play(self, player_id, sort_option=PlayerRankingOption.ORDER_CLEAR):
        if sort_option == PlayerRankingOption.ORDER_PLAYCOUNT:
            return None

        cursor = self._connection.cursor()

        if sort_option == PlayerRankingOption.ORDER_CLEAR:
            record_count = 8
            option_string = "AND isClear = 1"
        else:
            record_count = 10
            option_string = ""

        cursor.execute(f'''
            SELECT TOP {record_count} mm.Title,
                         m.NoteLevel,
                         m.MusicCode
            FROM dbo.O2JamHighscore AS h
                     LEFT JOIN dbo.o2jam_music_data AS m ON h.MusicCode = m.MusicCode AND h.Difficulty = m.Difficulty
                     LEFT JOIN dbo.o2jam_music_metadata AS mm ON h.MusicCode = mm.MusicCode
            WHERE h.PlayerCode = ?
              AND h.Progress <= ?
              AND h.Difficulty = 2
              {option_string}
            ORDER BY m.NoteLevel DESC
        ''', (player_id, sort_option.value + 1))

        query_results = cursor.fetchall()

        response = []

        for rank_info in query_results:
            response.append(
                {
                    "title": rank_info[0],
                    "level": rank_info[1],
                    "id": rank_info[2],
                }
            )

        return response if len(response) > 0 else None
