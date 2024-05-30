CREATE TABLE IF NOT EXISTS user (
    user_id VARCHAR NOT NULL PRIMARY KEY,
    user_name VARCHAR,
    language_id INTEGER REFERENCES language,
    start_prompt_id INTEGER REFERENCES prompt
);

CREATE TABLE IF NOT EXISTS language (
    language_id VARCHAR NOT NULL PRIMARY KEY,
    lang_code VARCHAR(2)
);

CREATE TABLE IF NOT EXISTS prompt (
    prompt_id VARCHAR NOT NULL PRIMARY KEY,
    version INTEGER,
    prompt VARCHAR,
    language_id INTEGER REFERENCES language
);