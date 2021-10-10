CREATE USER doka WITH password 'doka_admin';

CREATE DATABASE doka_project;
GRANT ALL PRIVILEGES ON DATABASE doka_project TO doka;