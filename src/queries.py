CREATE_MESSAGE_TABLE = "CREATE TABLE IF NOT EXISTS Messages(ID INTEGER PRIMARY KEY AUTOINCREMENT, ProfileId, MessageHistory, ExperimentId, CreationDateTime)"
CREATE_USER_TABLE = "CREATE TABLE IF NOT EXISTS Users(UserId type UNIQUE)"
CREATE_USER_PROFILES_TABLE = "CREATE TABLE IF NOT EXISTS UserProfiles(UserId, Profile)"
CREATE_SHARED_PROFILES_TABLE = (
    "CREATE TABLE IF NOT EXISTS SharedProfiles(UserId, Profile)"
)
GET_PROFILES_FOR_USER = "SELECT Profile FROM UserProfiles WHERE UserProfiles.UserId = ?"
GET_SHARED_PROFILES_FOR_USER = (
    "SELECT Profile FROM SharedProfiles WHERE SharedProfiles.UserId = ?"
)
UPDATE_MESSAGES_FOR_INSTANCE = "UPDATE Messages SET MessageHistory = ? WHERE ID = ?"
GET_USER_IDS = "SELECT UserId FROM Users"
GET_INSTANCE_BY_ID = "SELECT ID, ProfileId, MessageHistory, ExperimentId, CreationDateTime FROM Messages AS mh WHERE mh.ID == ?"
GET_INSTANCES_FOR_USER_AND_EXPERIMENT = """
SELECT ID, ProfileId, MessageHistory, ExperimentId, CreationDateTime
FROM Messages AS mh
    LEFT JOIN UserProfiles AS up ON mh.ID = up.Profile
WHERE up.UserId = ?
AND mh.ExperimentId = ?
"""
INSERT_NEW_USER = "INSERT INTO Users(UserId) VALUES (?)"
INSERT_NEW_INSTANCE = """INSERT INTO Messages(ProfileId, MessageHistory, ExperimentId, CreationDateTime) VALUES ( ?, ?, ?, ? )"""
INSERT_INSTANCE_ID_FOR_USER = "INSERT INTO UserProfiles(UserId, Profile) VALUES (?, ?)"

GET_ALL_CHATS_WITH_USERS = """
SELECT ID, ProfileId, MessageHistory, ExperimentId, CreationDateTime, UserId
FROM Messages AS mh
    LEFT JOIN UserProfiles AS up ON mh.ID = up.Profile
"""

INSERT_SHARED_INSTANCE_ID_FOR_USER = (
    "INSERT INTO SharedProfiles(UserId, Profile) VALUES (?, ?)"
)

GET_SHARED_INSTANCES_FOR_USER = """
SELECT ID, ProfileId, MessageHistory, ExperimentId, CreationDateTime
FROM Messages AS mh
    LEFT JOIN SharedProfiles AS up ON mh.ID = up.Profile
WHERE up.UserId = ?
AND mh.ExperimentId = ?
"""
