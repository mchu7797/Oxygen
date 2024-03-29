class ChartRankingManager:
    def __init__(self, connection):
        self._connection = connection

    def get_chart_top_records(self, music_id, gauge_difficulty, order_by_date=False):
        cursor = self._connection.cursor()

        if order_by_date:
            order_query = """
                ORDER BY
                    h.PlayedTime DESC,
                    h.Score DESC,
                    h.isClear DESC,
                    h.Cool DESC,
                    s.Clear,
                    h.PlayerCode DESC
            """
        else:
            order_query = """
                ORDER BY
                    h.Score DESC,
                    h.isClear DESC,
                    h.Cool DESC,
                    s.Clear,
                    h.PlayedTime DESC,
                    h.PlayerCode DESC
            """

        cursor.execute(
            f"""
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
                FORMAT(h.PlayedTime, 'yyyy-MM-dd hh:mm tt', 'en-US') AS PlayedTime,
                p.progress_name,
                ROW_NUMBER() OVER ({order_query}) status
            FROM 
                dbo.O2JamHighscore h 
                LEFT OUTER JOIN dbo.T_o2jam_charinfo c on h.PlayerCode = c.USER_INDEX_ID
                LEFT OUTER JOIN dbo.ProgressInfo p ON p.progress_index = h.Progress
                LEFT OUTER JOIN dbo.O2JamStatus s ON h.PlayerCode = s.PlayerCode
            WHERE 
                h.MusicCode = ?
                AND h.Difficulty = ?
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
                    "score": record[7],
                    "is_cleared_record": record[8],
                    "cleared_time": record[9],
                    "progress": record[10],
                    "row_number": record[11],
                }
            )

        if len(records) == 0:
            return None

        return records

    def get_play_count_ranking(self, top=200):
        cursor = self._connection.cursor()

        cursor.execute(
            """
            DECLARE @top int;
            SELECT @top = ?;

            IF @top = 0
            BEGIN
                SELECT @top = (SELECT COUNT(*) FROM dbo.o2jam_music_metadata)
            END

            SELECT
                *
            FROM (
                SELECT
                    m.MusicCode,
                    m.PlayCount,
                    m.NoteLevel,
                    mm.Title,
                    ROW_NUMBER() OVER (
                        ORDER BY m.PlayCount desc, m.NoteLevel desc
                    ) AS Rank
                FROM
                    dbo.o2jam_music_data m
                LEFT OUTER JOIN
                    dbo.o2jam_music_metadata mm
                    ON m.MusicCode = mm.MusicCode
                WHERE
                    m.Difficulty = 2
            ) A
            WHERE Rank <= @top
        """,
            top,
        )

        query_results = cursor.fetchall()

        if query_results is None:
            return []

        response = []

        for rank_info in query_results:
            response.append(
                {
                    "chart_id": rank_info[0],
                    "playcount": rank_info[1],
                    "level": rank_info[2],
                    "chart_title": rank_info[3],
                    "rank_index": rank_info[4],
                }
            )

        return response
