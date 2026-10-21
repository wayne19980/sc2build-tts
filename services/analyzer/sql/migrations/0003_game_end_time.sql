-- Replays often keep running after the game ends (GG). Player stats stop at
-- the real game end, so use the last stats tick as the replay duration.
UPDATE {{schema}}.games AS g
SET duration_sec = stats.end_t
FROM (
    SELECT game_id, max(t_sec) AS end_t
    FROM {{schema}}.stats_timeline
    GROUP BY game_id
) AS stats
WHERE g.id = stats.game_id
  AND stats.end_t IS NOT NULL
  AND stats.end_t > 0
  AND (g.duration_sec IS NULL OR stats.end_t < g.duration_sec);
