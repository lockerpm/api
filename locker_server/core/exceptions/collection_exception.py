from locker_server.core.exceptions.app import CoreException


class CollectionException(CoreException):
    """
    Base exception
    """


class CollectionDoesNotExistException(CollectionException):
    """
    The Collection does not exist
    """
    def __init__(self, collection_id=None, message=None):
        if collection_id:
            message = message or f"The team collection {collection_id} does not exist"
        super().__init__(message)
        self._collection_id = collection_id

    @property
    def collection_id(self):
        return self._collection_id


class CollectionCannotRemoveException(CollectionDoesNotExistException):
    def __init__(self, collection_id=None, message=None):
        if collection_id:
            message = message or f"You can not remove collection {collection_id}"
        super().__init__(message)
        self._collection_id = collection_id


class CollectionCannotAddException(CollectionDoesNotExistException):
    def __init__(self, collection_id=None, message=None):
        if collection_id:
            message = message or f"You can not add collection {collection_id}"
        super().__init__(message)
        self._collection_id = collection_id
