import logging
import logging.config

from shared.log.config import logging_config


logging.config.dictConfig(logging_config)


class CyLog:
    @classmethod
    def create(cls, data):
        output = data.get("output", ["slack", "stdout"])
        severity = data["severity"]
        message = data["message"]
        for output_type in output:
            if output_type == "slack":
                cls.log_to_slack(message, severity)
            elif output_type == "stdout":
                cls.log_to_screen(message, severity)

    # Log to Slack
    @staticmethod
    def log_to_slack(message, severity):
        logger = logging.getLogger('slack_service')
        if severity == "debug":
            logger.debug(message)
        elif severity == "info":
            logger.info(message)
        elif severity == "warning":
            logger.warning(message)
        elif severity == "error":
            logger.error(message)
        elif severity == "critical":
            logger.critical(message)

    # Log to Screen
    @staticmethod
    def log_to_screen(message, severity):
        logger = logging.getLogger('stdout_service')
        if severity == "debug":
            logger.debug(message)
        elif severity == "info":
            logger.info(message)
        elif severity == "warning":
            logger.warning(message)
        elif severity == "error":
            logger.error(message)
        elif severity == "critical":
            logger.critical(message)

    @classmethod
    def debug(cls, **kwargs):
        kwargs.update({"severity": "debug"})
        return cls.create(kwargs)

    @classmethod
    def info(cls, **kwargs):
        kwargs.update({"severity": "info"})
        return cls.create(kwargs)

    @classmethod
    def warning(cls, **kwargs):
        kwargs.update({"severity": "warning"})
        return cls.create(kwargs)

    @classmethod
    def error(cls, **kwargs):
        kwargs.update({"severity": "error"})
        return cls.create(kwargs)

    @classmethod
    def critical(cls, **kwargs):
        kwargs.update({"severity": "critical"})
        return cls.create(kwargs)