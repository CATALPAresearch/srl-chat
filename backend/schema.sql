CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR NOT NULL,
    client VARCHAR NOT NULL,
    language_id VARCHAR NOT NULL REFERENCES languages,
    PRIMARY KEY (user_id, client)
);

CREATE TABLE IF NOT EXISTS languages (
    language_id VARCHAR NOT NULL PRIMARY KEY,
    lang_code VARCHAR(2)
);

CREATE TABLE IF NOT EXISTS prompts (
    prompt_id VARCHAR NOT NULL PRIMARY KEY,
    version INTEGER,
    prompt VARCHAR,
    language_id INTEGER REFERENCES languages
);