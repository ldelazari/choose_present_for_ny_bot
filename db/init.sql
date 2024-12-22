CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    price TEXT NOT NULL,
    link TEXT NOT NULL,
    category_slug TEXT NOT NULL,
    UNIQUE(name, category_slug)
);

CREATE TABLE IF NOT EXISTS parsing_status (
    category_slug TEXT PRIMARY KEY,
    status BOOLEAN NOT NULL DEFAULT FALSE
);
