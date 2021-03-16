class BadSearchStringError(Exception):
    ''' The given search string was not found in the Resource Locker Server! Please check again or talk to any Administrator of the server'''

class BadRequestError(Exception):
    ''' Error from the Resource Locker Server! '''