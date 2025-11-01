USE Hackaton_2_Database;
GO

INSERT INTO Users (Username, Email, PasswordHash)
VALUES 
('admin', 'admin@example.com', 'hashed_password_1'),
('testuser', 'test@example.com', 'hashed_password_2');
GO