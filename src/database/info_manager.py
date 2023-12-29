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
                ISNULL(FORMAT(LastAccess, 'yy/MM/dd hh:mm'), 'NONE') as LastAccess
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

        player_ranking = cursor.fetchone()

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

        tie_player_count = int(cursor.fetchone()[0])

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

        clear_count = int(cursor.fetchone()[0])

        if raw_player_info is None:
            return None

        return {
            "nickname": raw_player_info[0],
            "level": raw_player_info[1],
            "play_count": raw_player_info[2],
            "admin_level": raw_player_info[3],
            "player_ranking": player_ranking[0] if player_ranking is not None else 0,
            "current_view_difficulty": int(gauge_difficulty),
            "tie_player_count": tie_player_count,
            "player_code": raw_player_info[4],
            "cleared_charts_count": clear_count,
            "last_access_time": raw_player_info[5],
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
