"""
Base service class providing common functionality for all services.
"""

import logging


class ServiceBase:
    """Base class for all services, providing standard logging and repository handling."""

    def __init__(self, logger_name=None):
        """
        Initialize the service with a logger.

        Args:
            logger_name: Name for the logger. Defaults to class name.
        """
        if logger_name is None:
            logger_name = self.__class__.__name__

        self.logger = logging.getLogger(logger_name)
