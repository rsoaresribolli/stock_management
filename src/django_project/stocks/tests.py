from datetime import date, timedelta

from django.test import TestCase

from .models import Batch, OrderLine, OutOfStock, allocate

# from model import ...

today = date.today()
tomorrow = today + timedelta(days=1)
later = tomorrow + timedelta(days=10)


class AllocationTest(TestCase):
    def make_batch_and_line(self, sku, batch_qty, line_qty):
        return (
            Batch("batch-001", sku, batch_qty, eta=date.today()),
            OrderLine("order-ref", sku, line_qty),
        )

    def test_allocating_to_a_batch_reduces_the_available_quantity(self):
        batch, line = self.make_batch_and_line("SMALL-TABLE", 20, 2)
        batch.allocate(line)
        self.assertEqual(batch.available_quantity, 18)

    def test_can_allocate_if_available_greater_than_required(self):
        large_batch, small_line = self.make_batch_and_line("ELEGANT-LAMP", 20, 2)
        self.assertTrue(large_batch.can_allocate(small_line))

    def test_cannot_allocate_if_available_smaller_than_required(self):
        small_batch, large_line = self.make_batch_and_line("ELEGANT-LAMP", 2, 20)
        self.assertFalse(small_batch.can_allocate(large_line))

    def test_can_allocate_if_available_equal_to_required(self):
        batch, line = self.make_batch_and_line("ELEGANT-LAMP", 2, 2)
        self.assertTrue(batch.can_allocate(line))

    def test_cannot_allocate_if_skus_do_not_match(self):
        batch = Batch("batch-001", "UNCOMFORTABLE-CHAIR", 100, eta=None)
        different_sku_line = OrderLine("order-123", "EXPENSIVE-TOASTER", 10)
        self.assertFalse(batch.can_allocate(different_sku_line))

    def test_can_only_deallocate_allocated_lines(self):
        batch, unallocated_line = self.make_batch_and_line("DECORATIVE-TRINKET", 20, 2)
        batch.deallocate(unallocated_line)
        self.assertEqual(batch.available_quantity, 20)

    def test_allocation_is_idempotent(self):
        batch, line = self.make_batch_and_line("ANGULAR-DESK", 20, 2)
        batch.allocate(line)
        batch.allocate(line)
        self.assertEqual(batch.available_quantity, 18)

    def test_prefers_current_stock_batches_to_shipments(self):
        in_stock_batch = Batch("in-stock-batch", "RETRO-CLOCK", 100, eta=None)
        shipment_batch = Batch("shipment-batch", "RETRO-CLOCK", 100, eta=tomorrow)
        line = OrderLine("oref", "RETRO-CLOCK", 10)

        allocate(line, [in_stock_batch, shipment_batch])

        self.assertEqual(in_stock_batch.available_quantity, 90)
        self.assertEqual(shipment_batch.available_quantity, 100)

    def test_prefers_earlier_batches(self):
        earliest = Batch("speedy-batch", "MINIMALIST-SPOON", 100, eta=today)
        medium = Batch("normal-batch", "MINIMALIST-SPOON", 100, eta=tomorrow)
        latest = Batch("slow-batch", "MINIMALIST-SPOON", 100, eta=later)
        line = OrderLine("order1", "MINIMALIST-SPOON", 10)

        allocate(line, [earliest, medium, latest])

        self.assertEqual(earliest.available_quantity, 90)
        self.assertEqual(medium.available_quantity, 100)
        self.assertEqual(latest.available_quantity, 100)

    def test_returns_allocated_batch_ref(self):
        in_stock_batch = Batch("in-stock-batch-ref", "HIGHBROW-POSTER", 100, eta=None)
        shipment_batch = Batch(
            "shipment-batch-ref", "HIGHBROW-POSTER", 100, eta=tomorrow
        )
        line = OrderLine("oref", "HIGHBROW-POSTER", 10)

        allocation = allocate(line, [in_stock_batch, shipment_batch])

        self.assertEqual(allocation, in_stock_batch.reference)

    def test_raiser_out_of_stock_exception_if_cannot_allocate(self):
        batch = Batch("batch1", "SMALL-FORK", 10, eta=today)
        allocate(OrderLine("order1", "SMALL-FORK", 10), [batch])

        with self.assertRaisesRegexp(OutOfStock, "SMALL-FORK"):
            allocate(OrderLine("order2", "SMALL-FORK", 1), [batch])
