class BadRequestError(Exception):
    """Error from the Resource Locker Server!"""


class TimeoutReachedForLockingResource(Exception):
    """In the given timeout range, there were no lockable resources that got free"""
