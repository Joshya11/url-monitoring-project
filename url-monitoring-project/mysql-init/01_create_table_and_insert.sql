CREATE DATABASE IF NOT EXISTS monitor;
USE monitor;
CREATE TABLE IF NOT EXISTS targets (
  id INT AUTO_INCREMENT PRIMARY KEY,
  target VARCHAR(256) NOT NULL
);

INSERT INTO targets (target) VALUES
('google.com'),
('amazon.com'),
('127.0.0.1:8080'),
('localhost:80'),
('example.com'),
('github.com'),
('stackoverflow.com'),
('wikipedia.org'),
('bing.com'),
('yahoo.com'),
('microsoft.com'),
('apple.com'),
('npmjs.com'),
('docker.com'),
('redis.io'),
('postgresql.org'),
('medium.com'),
('mozilla.org'),
('bbc.co.uk'),
('nyt.com');
