CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL
);

-- Initial test user (plain text for now as per simple auth-service pattern)
INSERT INTO users (email, password) VALUES ('user@example.com', 'password123');
