class InfoManager:
    def __init__(self, connection):
        self.__connection = connection

    def get_player_info(self, player_id, gauge_difficulty):
        cursor = self.__connection.cursor()

        cursor.execute(
            """
            SELECT
                USER_NICKNAME,
                Level, 
                Battle,
                AdminLevel,
                USER_INDEX_ID,
                ISNULL(FORMAT(LastAccess, 'yy/MM/dd hh:mm tt', 'en-US'), 'NONE') as LastAccess
            FROM
                dbo.T_o2jam_charinfo
            WHERE
                USER_INDEX_ID = ?
        """,
            player_id,
        )

        raw_player_info = cursor.fetchone()

        cursor.execute(
            """
            WITH Status AS (
                SELECT
                    PlayerCode,
                    RANK() OVER (
                        ORDER BY
                            Clear desc
                    ) Ranking
                FROM
                    dbo.O2JamStatus
            )
            SELECT
                Ranking
            FROM
                Status
            WHERE
                PlayerCode = ?
        """,
            player_id,
        )

        player_ranking = cursor.fetchval()

        if player_ranking is None:
            player_ranking = 0

        cursor.execute(
            """
            SELECT
                COUNT(*)
            FROM
                dbo.O2JamStatus
            WHERE
                Clear=(SELECT Clear FROM dbo.O2JamStatus WHERE PlayerCode=?)
        """,
            player_id,
        )

        tie_player_count = cursor.fetchval()

        cursor.execute(
            """
            SELECT
                COUNT(*)
            FROM
                dbo.O2JamHighscore
            WHERE
                PlayerCode = ? AND isClear=1 AND Difficulty=2
        """,
            player_id,
        )

        clear_count = cursor.fetchval()

        if raw_player_info is None:
            return None

        cursor.execute(
            """
            SELECT
                Nickname
            FROM
                dbo.nickname_history
            WHERE
                player_id = ?
            """,
            player_id,
        )

        raw_nickname_history = cursor.fetchall()
        nickname_history = []

        for nickname in raw_nickname_history:
            nickname_history.append(nickname[0])

        cursor.execute(
            """
            SELECT
                b.badge_name,
                b.badge_css_tag,
                h.MusicCode
            FROM 
                dbo.player_badge AS b
            INNER JOIN
                dbo.O2JamHighscore AS h ON b.chart_id = h.MusicCode
            INNER JOIN
                dbo.o2jam_music_data AS m ON h.MusicCode = m.MusicCode AND h.Difficulty = m.Difficulty
            WHERE
                h.isClear = 1 AND h.Difficulty = 2 AND h.PlayerCode = ?
            ORDER BY
                b.badge_priority
        """,
            player_id,
        )

        raw_badge_info = cursor.fetchone()

        if raw_badge_info is not None:
            badge_info = {
                "badge_name": raw_badge_info[0],
                "badge_css_tag": raw_badge_info[1],
                "badge_chart_id": raw_badge_info[2],
            }
        else:
            badge_info = None

        cursor.execute(
            """
            SELECT
                CONVERT(char(10), date, 23), level
            FROM
                status_clear_history
            WHERE
                date >= CAST(DATEADD(day, -60, GETDATE()) AS DATE)
                AND player_id = ?
            ORDER BY
                date
            """,
            player_id,
        )

        raw_clear_history = cursor.fetchall()
        clear_history = {"date": [], "level": []}

        for clear in raw_clear_history:
            clear_history["date"].append(clear[0])
            clear_history["level"].append(clear[1])

        return {
            "nickname": raw_player_info[0],
            "level": raw_player_info[1],
            "play_count": raw_player_info[2],
            "admin_level": raw_player_info[3],
            "player_ranking": player_ranking,
            "current_view_difficulty": int(gauge_difficulty),
            "tie_player_count": tie_player_count,
            "player_code": raw_player_info[4],
            "cleared_charts_count": clear_count,
            "last_access_time": raw_player_info[5],
            "nickname_history": nickname_history,
            "badge_info": badge_info,
            "clear_history": clear_history,
        }

    def get_tier_info(self, player_id):
        cursor = self.__connection.cursor()

        cursor.execute(
            f"""
            SELECT
                s.P,
                s.SS,
                s.S,
                s.A,
                s.B,
                s.C,
                s.D,
                s.Clear,
                t.tier_name
            FROM
                dbo.O2JamStatus s
                LEFT OUTER JOIN dbo.TierInfo t ON s.Tier = t.tier_index
            WHERE
                PlayerCode = {player_id}
        """
        )

        raw_result = cursor.fetchone()

        if raw_result is None:
            return None

        return {
            "p_rank": raw_result[0],
            "ss_rank": raw_result[1],
            "s_rank": raw_result[2],
            "a_rank": raw_result[3],
            "b_rank": raw_result[4],
            "c_rank": raw_result[5],
            "d_rank": raw_result[6],
            "cleared": raw_result[7],
            "tier": raw_result[8],
        }

    def get_music_info(self, music_id, gauge_difficulty):
        cursor = self.__connection.cursor()

        cursor.execute(
            """
            SELECT
                d.MusicCode,
                m.Title,
                d.NoteLevel,
                d.NoteCount,
                d.PlayCount,
                m.Artist,
                m.NoteCharter,
                m.BPM
            FROM
                dbo.o2jam_music_data d
                LEFT OUTER JOIN dbo.o2jam_music_metadata m ON m.MusicCode = d.MusicCode
            WHERE
                d.MusicCode = ?
                AND d.Difficulty = ?
        """,
            (music_id, gauge_difficulty),
        )

        raw_result = cursor.fetchone()

        if raw_result is None:
            return None

        return {
            "music_code": raw_result[0],
            "title": raw_result[1],
            "difficulty": int(gauge_difficulty),
            "level": raw_result[2],
            "note_count": raw_result[3],
            "play_count": raw_result[4],
            "artist": raw_result[5],
            "note_charter": raw_result[6],
            "bpm": round(float(raw_result[7])),
        }

    def get_score_status(self, player_id, chart_id, gauge_difficulty):
        # TODO: 데이터 가져오는 부분 구현
        pass
