import logging

# Set up module-level logger
logger = logging.getLogger(__name__)

# Add a NullHandler to avoid "No handler found" warnings when the library is used
# Users can configure their own handlers as needed
logger.addHandler(logging.NullHandler())

__all__ = [
    "resourcelocker",
    "exceptions",
    "utils",
]
