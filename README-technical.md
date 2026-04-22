

-- Nach dem Start: alle Ereignistypen sehen
SELECT action, count(*) FROM activity_log GROUP BY action ORDER BY count DESC;

-- Vollständige Chat-Nachrichten
SELECT action, value->>'message', turn, step
FROM activity_log
WHERE action IN ('reply_user', 'reply_llm')
ORDER BY timestamp;

-- Seitennavigation
SELECT value->>'path', value->>'userid', timestamp
FROM activity_log WHERE action = 'page_view' ORDER BY timestamp DESC LIMIT 20;

-- Mouse-Traces (eigene Tabelle)
SELECT user_id, session_id, count(*) FROM mouse_traces GROUP BY user_id, session_id;