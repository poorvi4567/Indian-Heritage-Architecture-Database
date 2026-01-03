-- schema.sql

CREATE TABLE location (
    location_id SERIAL PRIMARY KEY,
    city TEXT,
    state TEXT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    UNIQUE(city, state)
);

CREATE TABLE architectural_style (
    style_id SERIAL PRIMARY KEY,
    name TEXT UNIQUE
);

CREATE TABLE period (
    period_id SERIAL PRIMARY KEY,
    year INTEGER UNIQUE
);

CREATE TABLE monument (
    monument_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    location_id INTEGER REFERENCES location(location_id),
    style_id INTEGER REFERENCES architectural_style(style_id),
    period_id INTEGER REFERENCES period(period_id)
);
