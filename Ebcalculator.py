from dataclasses import dataclass
from typing import Optional
import datetime
 
 
# ─── Tariff Slabs (TNEB Domestic Tariff) ────────────────────────────────────
 
DOMESTIC_SLABS = [
    # (units_up_to, rate_per_unit)
    (100,  0.00),   # First 100 units FREE
    (200,  1.50),   # 101–200 units @ ₹1.50/unit
    (500,  3.00),   # 201–500 units @ ₹3.00/unit
    (float('inf'), 5.00),  # Above 500 units @ ₹5.00/unit
]
 
COMMERCIAL_SLABS = [
    (100,  5.00),
    (300,  6.50),
    (500,  8.00),
    (float('inf'), 9.00),
]
 
AGRICULTURAL_SLABS = [
    (100,  0.00),   # First 100 units FREE (HP < 5)
    (300,  1.50),
    (float('inf'), 3.00),
]
 
FIXED_CHARGES = {
    "domestic":     {1: 20, 2: 40, 3: 50, 4: 60, 5: 80},   # per service per month
    "commercial":   {"<5kw": 120, ">=5kw": 400},
    "agricultural": {"<5hp": 0, ">=5hp": 100},
}
 
METER_RENTAL      = 15.0   # ₹ per month
ELECTRICITY_DUTY  = 0.05   # 5% of energy charges
CONSUMER_SERVICE_CHARGE = 10.0  # ₹ per month
 
 
# ─── Data Classes ────────────────────────────────────────────────────────────
 
@dataclass
class BillResult:
    consumer_name:      str
    consumer_number:    str
    connection_type:    str
    billing_period:     str
    previous_reading:   int
    current_reading:    int
    units_consumed:     int
    energy_charge:      float
    fixed_charge:       float
    meter_rental:       float
    electricity_duty:   float
    consumer_service_charge: float
    gross_amount:       float
    rebate:             float
    net_amount:         float
    due_date:           str
    breakdown:          list
 
 
# ─── Core Calculator ─────────────────────────────────────────────────────────
 
def calculate_energy_charge(units: int, slabs: list) -> tuple[float, list]:
    """
    Calculate energy charge based on slab rates.
    Returns (total_charge, breakdown_list)
    """
    charge = 0.0
    breakdown = []
    prev_limit = 0
 
    for limit, rate in slabs:
        if units <= 0:
            break
 
        slab_max = limit if limit != float('inf') else units + prev_limit
        slab_units = min(units, slab_max - prev_limit)
 
        if slab_units > 0:
            slab_charge = slab_units * rate
            charge += slab_charge
            if rate == 0:
                breakdown.append(f"  {prev_limit+1}–{prev_limit+slab_units} units ({slab_units} units) @ FREE = ₹0.00")
            else:
                breakdown.append(
                    f"  {prev_limit+1}–{prev_limit+slab_units} units "
                    f"({slab_units} units) @ ₹{rate:.2f} = ₹{slab_charge:.2f}"
                )
            units -= slab_units
 
        prev_limit = int(limit) if limit != float('inf') else prev_limit + slab_units
 
    return round(charge, 2), breakdown
 
 
def get_fixed_charge(connection_type: str, sanctioned_load: Optional[int] = None) -> float:
    """Return fixed charge based on connection type and load."""
    if connection_type == "domestic":
        load = sanctioned_load or 1
        load = min(load, 5)
        return FIXED_CHARGES["domestic"].get(load, 80)
    elif connection_type == "commercial":
        if sanctioned_load and sanctioned_load >= 5:
            return FIXED_CHARGES["commercial"][">=5kw"]
        return FIXED_CHARGES["commercial"]["<5kw"]
    elif connection_type == "agricultural":
        if sanctioned_load and sanctioned_load >= 5:
            return FIXED_CHARGES["agricultural"][">=5hp"]
        return FIXED_CHARGES["agricultural"]["<5hp"]
    return 0.0
 
 
def calculate_bill(
    consumer_name:    str,
    consumer_number:  str,
    connection_type:  str,
    previous_reading: int,
    current_reading:  int,
    sanctioned_load:  int = 1,
    months:           int = 2,   # TNEB bills bimonthly by default
) -> BillResult:
    """
    Calculate the complete EB bill.
 
    Args:
        consumer_name:    Name of the consumer
        consumer_number:  EB consumer number
        connection_type:  'domestic', 'commercial', or 'agricultural'
        previous_reading: Previous meter reading (units)
        current_reading:  Current meter reading (units)
        sanctioned_load:  Sanctioned load in kW or HP
        months:           Billing period in months
 
    Returns:
        BillResult with full bill breakdown
    """
    if current_reading < previous_reading:
        raise ValueError("Current reading cannot be less than previous reading.")
 
    units_consumed = current_reading - previous_reading
 
    # Select slab based on connection type
    slab_map = {
        "domestic":     DOMESTIC_SLABS,
        "commercial":   COMMERCIAL_SLABS,
        "agricultural": AGRICULTURAL_SLABS,
    }
    slabs = slab_map.get(connection_type.lower(), DOMESTIC_SLABS)
 
    # Energy charge
    energy_charge, breakdown = calculate_energy_charge(units_consumed, slabs)
 
    # Fixed charge (per month × months)
    fixed_charge = get_fixed_charge(connection_type.lower(), sanctioned_load) * months
 
    # Other charges
    meter_rental_total       = METER_RENTAL * months
    electricity_duty_total   = round(energy_charge * ELECTRICITY_DUTY, 2)
    consumer_service_total   = CONSUMER_SERVICE_CHARGE * months
 
    # Gross amount
    gross = round(
        energy_charge + fixed_charge + meter_rental_total +
        electricity_duty_total + consumer_service_total, 2
    )
 
    # Rebate: 5% if units < 50 and domestic
    rebate = 0.0
    if connection_type.lower() == "domestic" and units_consumed < 50:
        rebate = round(gross * 0.05, 2)
 
    net_amount = round(gross - rebate, 2)
 
    # Billing period
    today = datetime.date.today()
    start = today - datetime.timedelta(days=months * 30)
    billing_period = f"{start.strftime('%d %b %Y')} – {today.strftime('%d %b %Y')}"
    due_date = (today + datetime.timedelta(days=15)).strftime('%d %b %Y')
 
    return BillResult(
        consumer_name=consumer_name,
        consumer_number=consumer_number,
        connection_type=connection_type.capitalize(),
        billing_period=billing_period,
        previous_reading=previous_reading,
        current_reading=current_reading,
        units_consumed=units_consumed,
        energy_charge=energy_charge,
        fixed_charge=fixed_charge,
        meter_rental=meter_rental_total,
        electricity_duty=electricity_duty_total,
        consumer_service_charge=consumer_service_total,
        gross_amount=gross,
        rebate=rebate,
        net_amount=net_amount,
        due_date=due_date,
        breakdown=breakdown,
    )
 
 
# ─── Bill Formatter ───────────────────────────────────────────────────────────
 
def format_bill(result: BillResult) -> str:
    """Render the bill as a formatted string."""
    sep  = "═" * 52
    thin = "─" * 52
 
    lines = [
        sep,
        "   TAMIL NADU ELECTRICITY BOARD (TNEB)".center(52),
        "         ELECTRICITY BILL".center(52),
        sep,
        f"  Consumer Name  : {result.consumer_name}",
        f"  Consumer No.   : {result.consumer_number}",
        f"  Connection     : {result.connection_type}",
        f"  Billing Period : {result.billing_period}",
        thin,
        f"  Previous Reading : {result.previous_reading:>8} units",
        f"  Current Reading  : {result.current_reading:>8} units",
        f"  Units Consumed   : {result.units_consumed:>8} units",
        thin,
        "  ENERGY CHARGE BREAKDOWN:",
        *[f"   {line}" for line in result.breakdown],
        thin,
        f"  {'Energy Charge':<30} ₹{result.energy_charge:>8.2f}",
        f"  {'Fixed Charge':<30} ₹{result.fixed_charge:>8.2f}",
        f"  {'Meter Rental':<30} ₹{result.meter_rental:>8.2f}",
        f"  {'Electricity Duty (5%)':<30} ₹{result.electricity_duty:>8.2f}",
        f"  {'Consumer Service Charge':<30} ₹{result.consumer_service_charge:>8.2f}",
        thin,
        f"  {'GROSS AMOUNT':<30} ₹{result.gross_amount:>8.2f}",
    ]
 
    if result.rebate > 0:
        lines.append(f"  {'Rebate (5% for < 50 units)':<30} -₹{result.rebate:>7.2f}")
 
    lines += [
        sep,
        f"  {'NET AMOUNT PAYABLE':<30} ₹{result.net_amount:>8.2f}",
        sep,
        f"  Due Date : {result.due_date}",
        f"  {'Pay on time to avoid 2% surcharge.':^50}",
        sep,
    ]
 
    return "\n".join(lines)
