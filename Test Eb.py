import unittest
from eb_calculator import calculate_bill, calculate_energy_charge, DOMESTIC_SLABS
 
 
class TestEnergyCharge(unittest.TestCase):
 
    def test_zero_units(self):
        charge, _ = calculate_energy_charge(0, DOMESTIC_SLABS)
        self.assertEqual(charge, 0.0)
 
    def test_free_slab_exact(self):
        """First 100 units should be free for domestic."""
        charge, _ = calculate_energy_charge(100, DOMESTIC_SLABS)
        self.assertEqual(charge, 0.0)
 
    def test_second_slab(self):
        """101–200 units @ ₹1.50: 100 free + 50 @ 1.50 = ₹75"""
        charge, _ = calculate_energy_charge(150, DOMESTIC_SLABS)
        self.assertAlmostEqual(charge, 75.0)
 
    def test_third_slab(self):
        """200 units: 100 free + 100 @ 1.50 = ₹150"""
        charge, _ = calculate_energy_charge(200, DOMESTIC_SLABS)
        self.assertAlmostEqual(charge, 150.0)
 
    def test_above_500(self):
        """600 units: 100 free + 100@1.50 + 300@3.00 + 100@5.00 = ₹1200"""
        charge, _ = calculate_energy_charge(600, DOMESTIC_SLABS)
        expected = 0 + (100 * 1.50) + (300 * 3.00) + (100 * 5.00)
        self.assertAlmostEqual(charge, expected)
 
 
class TestCalculateBill(unittest.TestCase):
 
    def _make_bill(self, prev, curr, conn="domestic", load=1, months=2):
        return calculate_bill(
            consumer_name="Test User",
            consumer_number="TN-TEST-001",
            connection_type=conn,
            previous_reading=prev,
            current_reading=curr,
            sanctioned_load=load,
            months=months,
        )
 
    def test_units_consumed(self):
        bill = self._make_bill(1000, 1150)
        self.assertEqual(bill.units_consumed, 150)
 
    def test_invalid_reading(self):
        with self.assertRaises(ValueError):
            self._make_bill(500, 400)
 
    def test_gross_is_sum_of_components(self):
        bill = self._make_bill(0, 300)
        expected = (
            bill.energy_charge
            + bill.fixed_charge
            + bill.meter_rental
            + bill.electricity_duty
            + bill.consumer_service_charge
        )
        self.assertAlmostEqual(bill.gross_amount, round(expected, 2), places=2)
 
    def test_rebate_applied_for_low_usage(self):
        """Units < 50 domestic → 5% rebate."""
        bill = self._make_bill(0, 30)
        self.assertGreater(bill.rebate, 0)
        self.assertAlmostEqual(bill.rebate, round(bill.gross_amount * 0.05, 2))
 
    def test_no_rebate_high_usage(self):
        bill = self._make_bill(0, 200)
        self.assertEqual(bill.rebate, 0.0)
 
    def test_net_amount(self):
        bill = self._make_bill(0, 200)
        self.assertAlmostEqual(bill.net_amount, bill.gross_amount - bill.rebate, places=2)
 
    def test_commercial_billing(self):
        bill = self._make_bill(0, 200, conn="commercial", load=3)
        self.assertEqual(bill.connection_type, "Commercial")
        self.assertGreater(bill.energy_charge, 0)
 
    def test_agricultural_free_first_100(self):
        bill = self._make_bill(0, 100, conn="agricultural", load=3)
        self.assertEqual(bill.energy_charge, 0.0)
 
 
if __name__ == "__main__":
    unittest.main(verbosity=2)