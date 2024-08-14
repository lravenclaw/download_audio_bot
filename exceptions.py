class InputError(Exception):
    default_detail = 'Only link is allowed.'

class LoginError(Exception):
    default_detail = 'Invalid username or password.'

class DownloadError(Exception):
    default_detail = 'Video is unavaialable.'

class DatabaseRegisterError(Exception):
    default_detail = 'User already exist.'

class DatabaseSelectError(Exception):
    default_detail = 'No such user found.'

class SQLiteError(Exception):
    default_detail = 'Can\' read from database file.'