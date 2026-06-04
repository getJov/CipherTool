-- CipherTool Microsoft SQL Server equivalent migration.
-- Runtime target remains Supabase PostgreSQL; this is maintained for plan
-- parity only.

IF OBJECT_ID(N'dbo.users', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.users (
        id int IDENTITY(1,1) NOT NULL,
        username varchar(255) NOT NULL,
        password varchar(255) NOT NULL,
        login_attempts int NOT NULL CONSTRAINT DF_users_login_attempts DEFAULT 0,
        blocked bit NOT NULL CONSTRAINT DF_users_blocked DEFAULT 0,
        CONSTRAINT PK_users PRIMARY KEY (id)
    );
END;
