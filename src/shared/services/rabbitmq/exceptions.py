class RabbitMQException(BaseException):
    """
    The Base RabbitMQ Exception
    """


class RabbitConnectionError(RabbitMQException):
    """
    Connect to RabbitMQ Error
    """


class RabbitMQSendError(RabbitMQException):
    """
    Sending message to RabbitMQ Error
    """


class QueueNotSetError(RabbitMQSendError):
    """

    """
