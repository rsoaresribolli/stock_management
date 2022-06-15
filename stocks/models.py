from dataclasses import dataclass
from datetime import date
from typing import List, NewType, Optional

Quantity = NewType("Quantity", int)
Sku = NewType("Sku", str)
Reference = NewType("Reference", str)


class OutOfStock(Exception):
    pass


@dataclass(frozen=True)
class OrderLine:
    """
    As the order line has data but no identity (its identity is directly related to the order), we represent it using the Value Object Pattern.
    A value object is uniquely represented by the data it holds and are usually immutable (in this case, frozen=True).
    Compared through value equality.
    """

    orderid: str
    sku: str
    qty: int


class Batch:
    """
    Entity: a domain object that has long-lived (or persistent) identity (its values can change, but its identity doesn't - differently from value objects).
    Compared through identity equality.
    """

    def __eq__(self, other):
        # Defines the behavior of ==
        if not isinstance(other, Batch):
            return False
        return other.reference == self.reference

    def __hash__(self):
        # Method used when we add these objects to sets or use them as dict keys
        return hash(self.reference)

    def __gt__(self, other):
        if self.eta is None:
            return False
        if other.eta is None:
            return True
        return self.eta > other.eta

    def __init__(self, ref: str, sku: str, qty: int, eta: Optional[date]):
        self.reference = ref
        self.sku = sku
        self.eta = eta
        self._purchased_quantity = qty
        self._allocations = set()

    def allocate(self, line: OrderLine):
        if self.can_allocate(line):
            self._allocations.add(line)

    def deallocate(self, line: OrderLine):
        if line in self._allocations:
            self._allocations.remove(line)

    @property
    def allocated_quantity(self) -> int:
        return sum(line.qty for line in self._allocations)

    @property
    def available_quantity(self) -> int:
        return self._purchased_quantity - self.allocated_quantity

    def can_allocate(self, line: OrderLine) -> bool:
        return self.sku == line.sku and self.available_quantity >= line.qty


def allocate(line: OrderLine, batches: List[Batch]) -> str:
    try:
        batch = next(b for b in sorted(batches) if b.can_allocate(line))
        batch.allocate(line)
        return batch.reference
    except StopIteration:
        raise OutOfStock(f"Out of stock for sku {line.sku}")
