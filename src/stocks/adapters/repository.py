import abc

from stocks.domain import models


class AbstractRepository(abc.ABC):
    @abc.abstractmethod
    def add(self, batch: models.Batch):
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, reference) -> models.Batch:
        raise NotImplementedError
