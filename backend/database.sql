USE [master]
GO
/****** Object:  Database [SecureNodeControlTest]    Script Date: 15.09.2024 19:43:59 ******/
CREATE DATABASE [SecureNodeControlTest]
 CONTAINMENT = NONE
 ON  PRIMARY
( NAME = N'SecureNodeControlTest', FILENAME = N'/var/opt/mssql/data/SecureNodeControlTest.mdf' , SIZE = 8192KB , MAXSIZE = UNLIMITED, FILEGROWTH = 65536KB )
 LOG ON
( NAME = N'SecureNodeControlTest_log', FILENAME = N'/var/opt/mssql/data/SecureNodeControlTest_log.ldf' , SIZE = 8192KB , MAXSIZE = 2048GB , FILEGROWTH = 65536KB )
 WITH CATALOG_COLLATION = DATABASE_DEFAULT, LEDGER = OFF
GO
ALTER DATABASE [SecureNodeControlTest] SET COMPATIBILITY_LEVEL = 160
GO
IF (1 = FULLTEXTSERVICEPROPERTY('IsFullTextInstalled'))
begin
EXEC [SecureNodeControlTest].[dbo].[sp_fulltext_database] @action = 'enable'
end
GO
ALTER DATABASE [SecureNodeControlTest] SET ANSI_NULL_DEFAULT OFF
GO
ALTER DATABASE [SecureNodeControlTest] SET ANSI_NULLS OFF
GO
ALTER DATABASE [SecureNodeControlTest] SET ANSI_PADDING OFF
GO
ALTER DATABASE [SecureNodeControlTest] SET ANSI_WARNINGS OFF
GO
ALTER DATABASE [SecureNodeControlTest] SET ARITHABORT OFF
GO
ALTER DATABASE [SecureNodeControlTest] SET AUTO_CLOSE OFF
GO
ALTER DATABASE [SecureNodeControlTest] SET AUTO_SHRINK OFF
GO
ALTER DATABASE [SecureNodeControlTest] SET AUTO_UPDATE_STATISTICS ON
GO
ALTER DATABASE [SecureNodeControlTest] SET CURSOR_CLOSE_ON_COMMIT OFF
GO
ALTER DATABASE [SecureNodeControlTest] SET CURSOR_DEFAULT  GLOBAL
GO
ALTER DATABASE [SecureNodeControlTest] SET CONCAT_NULL_YIELDS_NULL OFF
GO
ALTER DATABASE [SecureNodeControlTest] SET NUMERIC_ROUNDABORT OFF
GO
ALTER DATABASE [SecureNodeControlTest] SET QUOTED_IDENTIFIER OFF
GO
ALTER DATABASE [SecureNodeControlTest] SET RECURSIVE_TRIGGERS OFF
GO
ALTER DATABASE [SecureNodeControlTest] SET  DISABLE_BROKER
GO
ALTER DATABASE [SecureNodeControlTest] SET AUTO_UPDATE_STATISTICS_ASYNC OFF
GO
ALTER DATABASE [SecureNodeControlTest] SET DATE_CORRELATION_OPTIMIZATION OFF
GO
ALTER DATABASE [SecureNodeControlTest] SET TRUSTWORTHY OFF
GO
ALTER DATABASE [SecureNodeControlTest] SET ALLOW_SNAPSHOT_ISOLATION OFF
GO
ALTER DATABASE [SecureNodeControlTest] SET PARAMETERIZATION SIMPLE
GO
ALTER DATABASE [SecureNodeControlTest] SET READ_COMMITTED_SNAPSHOT OFF
GO
ALTER DATABASE [SecureNodeControlTest] SET HONOR_BROKER_PRIORITY OFF
GO
ALTER DATABASE [SecureNodeControlTest] SET RECOVERY FULL
GO
ALTER DATABASE [SecureNodeControlTest] SET  MULTI_USER
GO
ALTER DATABASE [SecureNodeControlTest] SET PAGE_VERIFY CHECKSUM
GO
ALTER DATABASE [SecureNodeControlTest] SET DB_CHAINING OFF
GO
ALTER DATABASE [SecureNodeControlTest] SET FILESTREAM( NON_TRANSACTED_ACCESS = OFF )
GO
ALTER DATABASE [SecureNodeControlTest] SET TARGET_RECOVERY_TIME = 60 SECONDS
GO
ALTER DATABASE [SecureNodeControlTest] SET DELAYED_DURABILITY = DISABLED
GO
ALTER DATABASE [SecureNodeControlTest] SET ACCELERATED_DATABASE_RECOVERY = OFF
GO
EXEC sys.sp_db_vardecimal_storage_format N'SecureNodeControlTest', N'ON'
GO
ALTER DATABASE [SecureNodeControlTest] SET QUERY_STORE = ON
GO
ALTER DATABASE [SecureNodeControlTest] SET QUERY_STORE (OPERATION_MODE = READ_WRITE, CLEANUP_POLICY = (STALE_QUERY_THRESHOLD_DAYS = 30), DATA_FLUSH_INTERVAL_SECONDS = 900, INTERVAL_LENGTH_MINUTES = 60, MAX_STORAGE_SIZE_MB = 1000, QUERY_CAPTURE_MODE = AUTO, SIZE_BASED_CLEANUP_MODE = AUTO, MAX_PLANS_PER_QUERY = 200, WAIT_STATS_CAPTURE_MODE = ON)
GO
USE [SecureNodeControlTest]
GO
/****** Object:  Table [dbo].[AuditLog]    Script Date: 15.09.2024 19:43:59 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[AuditLog](
	[AuditLog_Id] [int] IDENTITY(1,1) NOT NULL,
	[AuditLog_TableName] [nvarchar](50) NOT NULL,
	[AuditLog_ColumnName] [nvarchar](50) NOT NULL,
	[AuditLog_RowId] [int] NOT NULL,
	[AuditLog_OldValue] [nvarchar](max) NULL,
	[AuditLog_NewValue] [nvarchar](max) NULL,
	[AuditLog_Action] [nvarchar](10) NOT NULL,
	[AuditLog_Timestamp] [datetime2](7) NULL,
	[AuditLog_UserId] [int] NULL,
	[AuditLog_IPAddress] [nvarchar](45) NULL,
PRIMARY KEY CLUSTERED
(
	[AuditLog_Id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO
/****** Object:  Table [dbo].[Projectdata]    Script Date: 15.09.2024 19:43:59 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[Projectdata](
	[Project_IdKey] [int] IDENTITY(1,1) NOT NULL,
	[Project_Name] [nvarchar](64) NOT NULL,
	[Project_Image] [nvarchar](255) NULL,
	[Project_Version] [nvarchar](32) NULL,
	[Project_Network] [nvarchar](32) NULL,
	[Project_InstanceType] [nvarchar](4) NULL,
	[Project_CreationDate] [datetime2](7) NULL,
	[Project_LastModifiedDate] [datetime2](7) NULL,
 CONSTRAINT [PK__Projectd__90C13B3A300984B9] PRIMARY KEY CLUSTERED
(
	[Project_IdKey] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[User_Projects]    Script Date: 15.09.2024 19:43:59 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[User_Projects](
	[UserProject_IdKey] [int] IDENTITY(1,1) NOT NULL,
	[UserProject_UserIdKey] [int] NOT NULL,
	[UserProject_Network] [nvarchar](32) NULL,
	[UserProject_ProjectIdKey] [int] NOT NULL,
	[UserProject_InstanceId] [nvarchar](50) NULL,
	[UserProject_Version] [nvarchar](32) NULL,
	[UserProject_CreationDate] [datetime2](7) NULL,
	[UserProject_LastModifiedDate] [datetime2](7) NULL,
 CONSTRAINT [PK__User_Pro__0E1D271ED5D435A0] PRIMARY KEY CLUSTERED
(
	[UserProject_IdKey] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[Userdata]    Script Date: 15.09.2024 19:43:59 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[Userdata](
	[User_IdKey] [int] IDENTITY(1,1) NOT NULL,
	[User_Name] [nvarchar](64) NOT NULL,
	[User_Mail] [nvarchar](255) NOT NULL,
	[User_PasswordHash] [nvarchar](255) NOT NULL,
	[User_PasswordSalt] [nvarchar](255) NOT NULL,
	[User_CreationDate] [datetime2](7) NULL,
	[User_LastModifiedDate] [datetime2](7) NULL,
	[User_Status] [nvarchar](20) NULL,
	[User_FailedLoginAttempts] [int] NOT NULL,
	[User_LockoutTime] [datetime2](7) NULL,
	[User_LastLoginDate] [datetime2](7) NULL,
	[User_TwoFactorEnabled] [bit] NOT NULL,
	[User_TwoFactorSecret] [nvarchar](32) NULL,
	[User_EmailVerified] [bit] NOT NULL,
	[User_ResetToken] [nvarchar](255) NULL,
	[User_ResetTokenExpires] [datetime2](7) NULL,
	[User_VerificationToken] [nvarchar](255) NULL,
PRIMARY KEY CLUSTERED
(
	[User_IdKey] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
UNIQUE NONCLUSTERED
(
	[User_Mail] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[UserKeys]    Script Date: 15.09.2024 19:43:59 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[UserKeys](
	[UserKey_IdKey] [int] IDENTITY(1,1) NOT NULL,
	[UserKey_UserProjectIdKey] [int] NULL,
	[UserKey_EncryptedPubKey] [nvarchar](max) NULL,
	[UserKey_EncryptedPrivKey] [nvarchar](max) NULL,
	[UserKey_EncryptedPassword] [nvarchar](max) NULL,
	[UserKey_IPAddress] [nvarchar](15) NULL,
	[UserKey_IV] [varchar](44) NULL,
	[UserKey_CreationDate] [datetime2](7) NULL,
	[UserKey_LastModifiedDate] [datetime2](7) NULL,
 CONSTRAINT [PK__UserKeys__12AA5BCD6AE7A678] PRIMARY KEY CLUSTERED
(
	[UserKey_IdKey] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
 CONSTRAINT [UQ__UserKeys__46A897DA15A366AF] UNIQUE NONCLUSTERED
(
	[UserKey_UserProjectIdKey] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [IX_AuditLog_TableName_RowId]    Script Date: 15.09.2024 19:43:59 ******/
CREATE NONCLUSTERED INDEX [IX_AuditLog_TableName_RowId] ON [dbo].[AuditLog]
(
	[AuditLog_TableName] ASC,
	[AuditLog_RowId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [IX_Projectdata_Name]    Script Date: 15.09.2024 19:43:59 ******/
CREATE NONCLUSTERED INDEX [IX_Projectdata_Name] ON [dbo].[Projectdata]
(
	[Project_Name] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
/****** Object:  Index [IX_UserProjects_ProjectIdKey]    Script Date: 15.09.2024 19:43:59 ******/
CREATE NONCLUSTERED INDEX [IX_UserProjects_ProjectIdKey] ON [dbo].[User_Projects]
(
	[UserProject_ProjectIdKey] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
/****** Object:  Index [IX_UserProjects_UserIdKey]    Script Date: 15.09.2024 19:43:59 ******/
CREATE NONCLUSTERED INDEX [IX_UserProjects_UserIdKey] ON [dbo].[User_Projects]
(
	[UserProject_UserIdKey] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [IX_Userdata_Email]    Script Date: 15.09.2024 19:43:59 ******/
CREATE NONCLUSTERED INDEX [IX_Userdata_Email] ON [dbo].[Userdata]
(
	[User_Mail] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
ALTER TABLE [dbo].[AuditLog] ADD  DEFAULT (getdate()) FOR [AuditLog_Timestamp]
GO
ALTER TABLE [dbo].[Projectdata] ADD  CONSTRAINT [DF__Projectda__Proje__3F466844]  DEFAULT (getdate()) FOR [Project_CreationDate]
GO
ALTER TABLE [dbo].[Projectdata] ADD  CONSTRAINT [DF__Projectda__Proje__403A8C7D]  DEFAULT (getdate()) FOR [Project_LastModifiedDate]
GO
ALTER TABLE [dbo].[User_Projects] ADD  CONSTRAINT [DF__User_Proj__UserP__440B1D61]  DEFAULT (getdate()) FOR [UserProject_CreationDate]
GO
ALTER TABLE [dbo].[User_Projects] ADD  CONSTRAINT [DF__User_Proj__UserP__44FF419A]  DEFAULT (getdate()) FOR [UserProject_LastModifiedDate]
GO
ALTER TABLE [dbo].[Userdata] ADD  DEFAULT (getdate()) FOR [User_CreationDate]
GO
ALTER TABLE [dbo].[Userdata] ADD  DEFAULT (getdate()) FOR [User_LastModifiedDate]
GO
ALTER TABLE [dbo].[Userdata] ADD  DEFAULT ('Active') FOR [User_Status]
GO
ALTER TABLE [dbo].[Userdata] ADD  DEFAULT ((0)) FOR [User_FailedLoginAttempts]
GO
ALTER TABLE [dbo].[Userdata] ADD  DEFAULT ((0)) FOR [User_TwoFactorEnabled]
GO
ALTER TABLE [dbo].[Userdata] ADD  DEFAULT ((0)) FOR [User_EmailVerified]
GO
ALTER TABLE [dbo].[UserKeys] ADD  CONSTRAINT [DF__UserKeys__UserKe__4AB81AF0]  DEFAULT (getdate()) FOR [UserKey_CreationDate]
GO
ALTER TABLE [dbo].[UserKeys] ADD  CONSTRAINT [DF__UserKeys__UserKe__4BAC3F29]  DEFAULT (getdate()) FOR [UserKey_LastModifiedDate]
GO
ALTER TABLE [dbo].[User_Projects]  WITH NOCHECK ADD  CONSTRAINT [FK_UserProjects_Projectdata] FOREIGN KEY([UserProject_ProjectIdKey])
REFERENCES [dbo].[Projectdata] ([Project_IdKey])
GO
ALTER TABLE [dbo].[User_Projects] CHECK CONSTRAINT [FK_UserProjects_Projectdata]
GO
ALTER TABLE [dbo].[User_Projects]  WITH NOCHECK ADD  CONSTRAINT [FK_UserProjects_Userdata] FOREIGN KEY([UserProject_UserIdKey])
REFERENCES [dbo].[Userdata] ([User_IdKey])
GO
ALTER TABLE [dbo].[User_Projects] CHECK CONSTRAINT [FK_UserProjects_Userdata]
GO
ALTER TABLE [dbo].[UserKeys]  WITH NOCHECK ADD  CONSTRAINT [FK_UserKeys_UserProjects] FOREIGN KEY([UserKey_UserProjectIdKey])
REFERENCES [dbo].[User_Projects] ([UserProject_IdKey])
GO
ALTER TABLE [dbo].[UserKeys] CHECK CONSTRAINT [FK_UserKeys_UserProjects]
GO
/****** Object:  StoredProcedure [dbo].[sp_CompletePasswordReset]    Script Date: 15.09.2024 19:43:59 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

-- Create sp_CompletePasswordReset procedure
CREATE PROCEDURE [dbo].[sp_CompletePasswordReset]
    @ResetToken NVARCHAR(255),
    @NewPasswordHash NVARCHAR(255),
    @NewPasswordSalt NVARCHAR(255),
    @Result INT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @UserId INT;

    SELECT @UserId = User_IdKey
    FROM Userdata
    WHERE User_ResetToken = @ResetToken
      AND User_ResetTokenExpires > GETDATE();

    IF @UserId IS NULL
        SET @Result = -1; -- Invalid or expired token
    ELSE
    BEGIN
        UPDATE Userdata
        SET User_PasswordHash = @NewPasswordHash,
            User_PasswordSalt = @NewPasswordSalt,
            User_ResetToken = NULL,
            User_ResetTokenExpires = NULL
        WHERE User_IdKey = @UserId;

        SET @Result = 0; -- Success
    END
END
GO
/****** Object:  StoredProcedure [dbo].[sp_InitiatePasswordReset]    Script Date: 15.09.2024 19:43:59 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

-- Create sp_InitiatePasswordReset procedure
CREATE PROCEDURE [dbo].[sp_InitiatePasswordReset]
    @UserMail NVARCHAR(255),
    @ResetToken NVARCHAR(255),
    @ExpirationTime DATETIME2,
    @Result INT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;

    UPDATE Userdata
    SET User_ResetToken = @ResetToken,
        User_ResetTokenExpires = @ExpirationTime
    WHERE User_Mail = @UserMail;

    IF @@ROWCOUNT = 0
        SET @Result = -1; -- User not found
    ELSE
        SET @Result = 0; -- Success
END
GO
/****** Object:  StoredProcedure [dbo].[sp_RegisterUser]    Script Date: 15.09.2024 19:43:59 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE PROCEDURE [dbo].[sp_RegisterUser]
    @UserName NVARCHAR(64),
    @UserMail NVARCHAR(255),
    @PasswordHash NVARCHAR(255),
    @PasswordSalt NVARCHAR(255),
    @VerificationToken NVARCHAR(255)
AS
BEGIN
    SET NOCOUNT ON;

    -- Check if username already exists
    IF EXISTS (SELECT 1 FROM Userdata WHERE User_Name = @UserName)
    BEGIN
        RAISERROR('Username already exists', 16, 1);
        RETURN;
    END

    -- Check if email already exists
    IF EXISTS (SELECT 1 FROM Userdata WHERE User_Mail = @UserMail)
    BEGIN
        RAISERROR('Email already exists', 16, 1);
        RETURN;
    END

    -- Insert new user
    INSERT INTO Userdata (User_Name, User_Mail, User_PasswordHash, User_PasswordSalt, User_EmailVerified, User_VerificationToken, User_CreationDate, User_LastModifiedDate)
    VALUES (@UserName, @UserMail, @PasswordHash, @PasswordSalt, 0, @VerificationToken, GETDATE(), GETDATE());

    -- Return the new user's ID
    SELECT SCOPE_IDENTITY() AS User_IdKey;
END
GO
/****** Object:  StoredProcedure [dbo].[sp_UpdateFailedLoginAttempts]    Script Date: 15.09.2024 19:43:59 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

-- sp_UpdateFailedLoginAttempts
CREATE PROCEDURE [dbo].[sp_UpdateFailedLoginAttempts]
    @UserId INT,
    @Increment BIT = 1
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @FailedAttempts INT;

    IF @Increment = 1
    BEGIN
        UPDATE Userdata
        SET @FailedAttempts = User_FailedLoginAttempts = User_FailedLoginAttempts + 1
        WHERE User_IdKey = @UserId;
    END
    ELSE
    BEGIN
        UPDATE Userdata
        SET User_FailedLoginAttempts = 0, User_LockoutTime = NULL, User_LastLoginDate = GETDATE()
        WHERE User_IdKey = @UserId;
        RETURN;
    END

    -- Lock account if failed attempts reach 5
    IF @FailedAttempts >= 5
    BEGIN
        UPDATE Userdata
        SET User_LockoutTime = DATEADD(MINUTE, 15, GETDATE())
        WHERE User_IdKey = @UserId;
    END
END
GO
/****** Object:  StoredProcedure [dbo].[sp_UserLogin]    Script Date: 15.09.2024 19:43:59 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

CREATE PROCEDURE [dbo].[sp_UserLogin]
    @UserMail NVARCHAR(255),
    @IPAddress NVARCHAR(45)
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @Result INT;
    DECLARE @UserId INT, @FailedAttempts INT, @LockoutTime DATETIME2, @EmailVerified BIT;

    SELECT @UserId = User_IdKey,
           @FailedAttempts = User_FailedLoginAttempts,
           @LockoutTime = User_LockoutTime,
           @EmailVerified = User_EmailVerified
    FROM Userdata
    WHERE User_Mail = @UserMail;

    IF @UserId IS NULL
        SET @Result = -1; -- User not found
    ELSE IF @EmailVerified = 0
        SET @Result = -2; -- Email not verified
    ELSE IF @LockoutTime IS NOT NULL AND @LockoutTime > GETDATE()
        SET @Result = -3; -- Account is locked
    ELSE
    BEGIN
        -- Existing logic...
        SET @Result = 0; -- Success
    END

    -- Return the result as a SELECT statement
    SELECT @Result AS Result;
END
GO
/****** Object:  StoredProcedure [dbo].[sp_VerifyEmail]    Script Date: 15.09.2024 19:43:59 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

-- Create sp_VerifyEmail procedure
CREATE PROCEDURE [dbo].[sp_VerifyEmail]
    @UserMail NVARCHAR(255),
	@VerificationToken NVARCHAR(255),
    @Result INT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;

    UPDATE Userdata
    SET User_EmailVerified = 1,
        User_VerificationToken = NULL
    WHERE User_Mail = @UserMail
      AND User_VerificationToken = @VerificationToken
      AND User_EmailVerified = 0;

    IF @@ROWCOUNT = 0
        SET @Result = -1; -- User not found or already verified
    ELSE
        SET @Result = 0; -- Success

		-- Return the result
    SELECT @Result AS Result;
END
GO
USE [master]
GO
ALTER DATABASE [SecureNodeControlTest] SET  READ_WRITE
GO
