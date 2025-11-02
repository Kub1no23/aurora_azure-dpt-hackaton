USE Hackaton_2_Database;
GO

INSERT INTO Users (Username, Email, PasswordHash, LastLogin, Language, LoginLocation, EmailVerified)
VALUES 
('admin', 'admin@example.com', 'hashed_password_1', NULL, 'en', 'USA', 1),
('testuser', 'test@example.com', 'hashed_password_2', NULL, 'en', 'USA', 0);
GO