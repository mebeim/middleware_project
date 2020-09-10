DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS images;
DROP TABLE IF EXISTS clients;
DROP TABLE IF EXISTS oauth_tokens;

CREATE TABLE users (
	id VARCHAR(255) PRIMARY KEY,
	name VARCHAR(255) NOT NULL,
	password_salt CHAR(16) NOT NULL,
	password_hash CHAR(128) NOT NULL
);

CREATE TABLE images (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	title TEXT NOT NULL,
	owner_id TEXT NOT NULL,
	FOREIGN KEY (owner_id) REFERENCES users (id)
);

CREATE TABLE clients (
	id CHAR(65) PRIMARY KEY,
	name VARCHAR(255) NOT NULL,
	redirect_uri TEXT NOT NULL,
	secret CHAR(128) NOT NULL
);

CREATE TABLE oauth_tokens (
	token CHAR(128) PRIMARY KEY,
	user_id VARCHAR(255) NOT NULL,
	client_id CHAR(65) NOT NULL,
	scopes TEXT NOT NULL,
	FOREIGN KEY (user_id) REFERENCES users (id)
	FOREIGN KEY (client_id) REFERENCES clients (id)
);
