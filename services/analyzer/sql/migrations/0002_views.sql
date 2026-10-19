CREATE OR REPLACE VIEW {{schema}}.v_game_summary AS
SELECT
    g.id AS game_id,
    g.folder_id,
    f.name AS folder_name,
    f.path AS folder_path,
    g.file_name,
    g.map_name,
    g.duration_sec,
    g.played_at,
    g.game_version,
    g.region,
    g.game_type,
    string_agg(
        gp.name || ' (' || COALESCE(gp.race, '?') || ')',
        ' vs ' ORDER BY gp.team NULLS LAST, gp.pid
    ) AS players,
    max(gp.name) FILTER (WHERE gp.is_winner) AS winner
FROM {{schema}}.games g
JOIN {{schema}}.folders f ON f.id = g.folder_id
LEFT JOIN {{schema}}.game_players gp ON gp.game_id = g.id
GROUP BY g.id, f.id;

CREATE OR REPLACE VIEW {{schema}}.v_player_events AS
SELECT
    e.game_id,
    gp.id AS player_id,
    gp.name AS player_name,
    gp.race,
    e.frame,
    e.t_sec,
    e.kind,
    e.name,
    e.display_name,
    e.supply,
    e.is_worker,
    e.payload
FROM {{schema}}.events e
JOIN {{schema}}.game_players gp ON gp.id = e.player_id;

CREATE OR REPLACE VIEW {{schema}}.v_player_build_events AS
SELECT *
FROM {{schema}}.v_player_events
WHERE kind IN ('order', 'build_start', 'build_done', 'unit_training_start', 'upgrade_done');

CREATE OR REPLACE VIEW {{schema}}.v_player_tech_timings AS
SELECT
    game_id,
    player_id,
    player_name,
    race,
    t_sec,
    frame,
    name AS tech,
    payload
FROM {{schema}}.v_player_events
WHERE kind = 'upgrade_done';

CREATE OR REPLACE VIEW {{schema}}.v_player_unit_births AS
SELECT
    game_id,
    player_id,
    player_name,
    race,
    t_sec,
    frame,
    name AS unit,
    COALESCE((payload->>'is_worker')::boolean, false) AS is_worker,
    COALESCE((payload->>'is_army')::boolean, false) AS is_army,
    COALESCE((payload->>'is_building')::boolean, false) AS is_building,
    payload
FROM {{schema}}.v_player_events
WHERE kind = 'unit_born';

CREATE OR REPLACE VIEW {{schema}}.v_player_unit_deaths AS
SELECT
    game_id,
    player_id,
    player_name,
    race,
    t_sec,
    frame,
    name AS unit,
    COALESCE((payload->>'is_worker')::boolean, false) AS is_worker,
    COALESCE((payload->>'is_army')::boolean, false) AS is_army,
    COALESCE((payload->>'is_building')::boolean, false) AS is_building,
    payload
FROM {{schema}}.v_player_events
WHERE kind = 'unit_died';

CREATE OR REPLACE VIEW {{schema}}.v_player_unit_production AS
SELECT
    game_id,
    player_id,
    player_name,
    race,
    unit,
    is_worker,
    is_army,
    is_building,
    count(*) AS produced
FROM {{schema}}.v_player_unit_births
WHERE NOT is_building
GROUP BY game_id, player_id, player_name, race, unit, is_worker, is_army, is_building;

CREATE OR REPLACE VIEW {{schema}}.v_player_units AS
SELECT
    u.game_id,
    u.player_id,
    gp.name AS player_name,
    gp.race,
    u.unit_id,
    u.first_type,
    u.unit_type,
    u.born_t_sec,
    u.died_t_sec,
    u.is_worker,
    u.is_army,
    u.is_building,
    u.morphs,
    u.payload
FROM {{schema}}.units u
JOIN {{schema}}.game_players gp ON gp.id = u.player_id;

CREATE OR REPLACE VIEW {{schema}}.v_player_stats AS
SELECT
    st.game_id,
    st.player_id,
    gp.name AS player_name,
    gp.race,
    st.frame,
    st.t_sec,
    st.minerals,
    st.vespene,
    st.workers,
    st.supply_used,
    st.supply_made,
    st.army_value,
    st.minerals_collection_rate,
    st.vespene_collection_rate,
    st.resources_lost,
    st.resources_killed,
    st.payload
FROM {{schema}}.stats_timeline st
JOIN {{schema}}.game_players gp ON gp.id = st.player_id;

CREATE OR REPLACE VIEW {{schema}}.v_game_features AS
SELECT
    g.id AS game_id,
    g.map_name,
    g.duration_sec,
    g.played_at,
    jsonb_agg(
        jsonb_build_object(
            'pid', gp.pid,
            'name', gp.name,
            'race', gp.race,
            'result', gp.result,
            'is_winner', gp.is_winner
        ) ORDER BY gp.pid
    ) AS players,
    (
        SELECT jsonb_agg(
            jsonb_build_object(
                'player', p.player_name,
                't_sec', p.t_sec,
                'kind', p.kind,
                'name', p.name
            ) ORDER BY p.player_name, p.t_sec, p.rn
        )
        FROM (
            SELECT
                v.player_name,
                v.t_sec,
                v.kind,
                v.name,
                row_number() OVER (
                    PARTITION BY v.game_id, v.player_id
                    ORDER BY v.t_sec, v.frame
                ) AS rn
            FROM {{schema}}.v_player_build_events v
            WHERE v.game_id = g.id
        ) p
        WHERE p.rn <= 30
    ) AS opening_events,
    (
        SELECT jsonb_agg(
            jsonb_build_object(
                'player', p.player_name,
                'unit', p.unit,
                'produced', p.produced,
                'is_worker', p.is_worker,
                'is_army', p.is_army,
                'is_building', p.is_building
            ) ORDER BY p.player_name, p.produced DESC
        )
        FROM {{schema}}.v_player_unit_production p
        WHERE p.game_id = g.id
    ) AS unit_production,
    (
        SELECT jsonb_agg(
            jsonb_build_object(
                'player', t.player_name,
                't_sec', t.t_sec,
                'tech', t.tech
            ) ORDER BY t.t_sec
        )
        FROM {{schema}}.v_player_tech_timings t
        WHERE t.game_id = g.id
    ) AS tech_timings
FROM {{schema}}.games g
LEFT JOIN {{schema}}.game_players gp ON gp.game_id = g.id
GROUP BY g.id;
