CREATE TABLE Users (
    user_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    username NVARCHAR(100) NOT NULL,
    email NVARCHAR(255) NOT NULL,
    passwd_hash NVARCHAR(255) NOT NULL,
    last_login DATETIME,
    language NVARCHAR(50),
    login_location NVARCHAR(255)
);
GO

CREATE TABLE Files (
    file_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    user_id UNIQUEIDENTIFIER NOT NULL,  
    file_name NVARCHAR(255) NOT NULL,
    file_type NVARCHAR(50),
    blob_url NVARCHAR(MAX),
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);
GO

CREATE TABLE Conversations (
    convo_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    user_id UNIQUEIDENTIFIER NOT NULL,
    is_persistent BIT NOT NULL,
    started_at DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);
GO

CREATE TABLE Messages (
    message_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    convo_id UNIQUEIDENTIFIER NOT NULL,
    sender NVARCHAR(100),
    content NVARCHAR(MAX),
    time DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (convo_id) REFERENCES Conversations(convo_id)
);
GO

CREATE TABLE User_Settings (
    settings_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    user_id UNIQUEIDENTIFIER NOT NULL,
    key NVARCHAR(100) NOT NULL,
    value NVARCHAR(MAX),
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);
GO

CREATE TABLE RAG_Answering (
    chunk_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    file_id UNIQUEIDENTIFIER NOT NULL,
    user_id UNIQUEIDENTIFIER NOT NULL,
    content NVARCHAR(MAX),
    embedding_vector NVARCHAR(MAX),
    FOREIGN KEY (file_id) REFERENCES Files(file_id),
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);
GO