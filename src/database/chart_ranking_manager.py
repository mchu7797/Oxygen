from dateutil.parser import parse as date_parse
import datetime

class ChartRankingManager:
    def __init__(self, connection):
        self._connection = connection

    def get_chart_top_records(self, music_id, gauge_difficulty):
        cursor = self._connection.cursor()

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
                h.PatternOrder,
                ROUND(h.PlaySpeedRate, 3) AS PlaySpeedRate,
                h.PlayTimingRate,
                h.FLNOption,
                h.SLNOption,
                h.isNLN,
                ROW_NUMBER() OVER (ORDER BY
                    h.Score DESC,
                    h.isClear DESC,
                    h.Cool DESC,
                    s.Clear,
                    h.PlayedTime DESC,
                    h.PlayerCode DESC) status
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
                    "pattern_order": record[11],
                    "play_speed_rate": record[12],
                    "play_timing_rate": record[13],
                    "fln_option": record[14],
                    "sln_option": record[15],
                    "is_nln": record[16],
                    "row_number": record[17],
                }
            )

        if len(records) == 0:
            return None

        return records

    def get_play_count_ranking(self, top=200, day_start=None, day_end=None):
        difficulty_column_name = ["level_easy", "level_normal", "level_hard"]

        def validate_date(date_str):
            if date_str is None:
                return None
            try:
                return datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                raise ValueError(f"Invalid date format: {date_str}. Use YYYY-MM-DD format.")

        try:
            top = int(top)
            if top < 1:
                top = abs(top)
        except ValueError:
            top = 200

        start_date = validate_date(day_start)
        end_date = validate_date(day_end)

        # 날짜 범위 설정 로직
        if start_date and end_date:
            if start_date > end_date:
                raise ValueError("start_date must be earlier than or equal to end_date")
        elif start_date:
            end_date = start_date + datetime.timedelta(days=60)
        elif end_date:
            start_date = end_date - datetime.timedelta(days=60)
        else:
            end_date = datetime.date.today()
            start_date = end_date - datetime.timedelta(days=60)

        # 지정된 날짜의 23시 59분 59초까지 집계하기 위함.
        end_date += datetime.timedelta(days=1)

        query = f"""
        WITH RankedPlaycounts AS (
            SELECT
                chart_id_tmp,
                playcount,
                timestamp,
                ROW_NUMBER() OVER (PARTITION BY chart_id, chart_difficulty ORDER BY timestamp ASC) AS rn_asc,
                ROW_NUMBER() OVER (PARTITION BY chart_id, chart_difficulty ORDER BY timestamp DESC) AS rn_desc
            FROM dbo.O2JamPlaycounts
            WHERE timestamp BETWEEN '{start_date.strftime("%Y-%m-%d %H:%M:%S")}' AND '{end_date.strftime("%Y-%m-%d %H:%M:%S")}'
        ),
        PlaycountDifference AS (
            SELECT
                chart_id_tmp,
                MAX(CASE WHEN rn_desc = 1 THEN playcount END) -
                MAX(CASE WHEN rn_asc = 1 THEN playcount END) AS playcount_diff
            FROM RankedPlaycounts
            GROUP BY chart_id_tmp, chart_difficulty
        )
        SELECT {'TOP {}'.format(top) if top else ''}
            p.chart_id_tmp,
            p.playcount_diff AS total_playcount,
            mi.level_hard,
            mi.title,
            ROW_NUMBER() OVER (ORDER BY p.playcount_diff DESC, mi.level_hard DESC) AS Rank
        FROM PlaycountDifference AS p
        JOIN dbo.music_info AS mi ON mi.id = p.chart_id_tmp
        WHERE p.playcount_diff > 0
        """

        cursor = self._connection.cursor()

        cursor.execute(query)

        query_results = cursor.fetchall()

        if query_results is None:
            return []

        response = []

        for rank_info in query_results:
            response.append({
                "chart_id": rank_info[0],
                "playcount": rank_info[1],
                "level": rank_info[2],
                "chart_title": rank_info[3],
                "rank_index": rank_info[4],
            })

        return response