from datetime import date

import pytest
from django_project.stocks import models as django_models
from stocks.adapters import repository
from stocks.domain import models


@pytest.mark.django_db
def test_repository_can_save_batch():
    batch = models.Batch("batch1", "RUSTY-SOAPDISH", 100, eta=date(2023, 12, 25))

    repo = repository.DjangoRepository()
    repo.add(batch)

    [saved_batch] = django_models.Batch.objects.all()
    assert saved_batch.reference == batch.reference
    assert saved_batch.sku == batch.sku
    assert saved_batch.qty == batch._purchased_quantity
    assert saved_batch.eta == batch.eta


@pytest.mark.django_db
def test_repository_can_retrieve_a_batch_with_allocations():
    sku = "PONY-STATUE"
    d_line = django_models.OrderLine.objects.create(orderid="order1", sku=sku, qty=12)
    d_batch1 = django_models.Batch.objects.create(
        reference="batch1", sku=sku, qty=100, eta=None
    )
    d_batch2 = django_models.Batch.objects.create(
        reference="batch2", sku=sku, qty=100, eta=None
    )

    django_models.Allocation.objects.create(line=d_line, batch=d_batch1)

    repo = repository.DjangoRepository()
    retrieved = repo.get("batch1")

    expected = models.Batch("batch1", sku, 100, eta=None)
    assert retrieved == expected
    assert retrieved.sku == expected.sku
    assert retrieved._purchased_quantity == expected._purchased_quantity
    assert retrieved._allocations == {models.OrderLine("order1", sku, 12)}
