create table if not exists urls (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name VARCHAR(255) UNIQUE NOT NULL,
    created_at DATE
);

create table if not exists url_checks (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    url_id BIGINT REFERENCES urls (id),
    status_code BIGINT,
    h1 VARCHAR(255),
    title VARCHAR(255),
    description TEXT,
    created_at DATE
);