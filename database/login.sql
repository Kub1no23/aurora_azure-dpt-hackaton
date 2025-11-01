-- Vytvoření loginu na úrovni serveru
CREATE LOGIN app_user WITH PASSWORD = 'TestPasswd123!';
GO

-- Vytvoření uživatele v databázi
USE Hackaton_2_Database;
GO

CREATE USER app_user FOR LOGIN app_user;
GO

-- Přiřazení oprávnění
GRANT SELECT, INSERT, UPDATE, DELETE ON Users TO app_user;
GO