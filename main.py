from eb_calculator import calculate_bill, format_bill
 
 
def get_int(prompt: str, min_val: int = 0, max_val: int = 999999) -> int:
    while True:
        try:
            val = int(input(prompt).strip())
            if min_val <= val <= max_val:
                return val
            print(f"  ⚠  Please enter a value between {min_val} and {max_val}.")
        except ValueError:
            print("  ⚠  Invalid input. Please enter a whole number.")
 
 
def get_choice(prompt: str, choices: dict) -> str:
    print(prompt)
    for key, label in choices.items():
        print(f"  [{key}] {label}")
    while True:
        choice = input("  Enter choice: ").strip().lower()
        if choice in choices:
            return choice
        print(f"  ⚠  Invalid choice. Please enter one of: {', '.join(choices.keys())}")
 
 
def main():
    banner = """
╔══════════════════════════════════════════════╗
║   TNEB  ELECTRICITY BILL CALCULATOR  ⚡       ║
╚══════════════════════════════════════════════╝
"""
    print(banner)
 
    # Consumer details
    name   = input("  Consumer Name   : ").strip() or "Consumer"
    number = input("  Consumer Number : ").strip() or "TN-000000"
 
    # Connection type
    conn_type = get_choice(
        "\n  Select Connection Type:",
        {"1": "Domestic", "2": "Commercial", "3": "Agricultural"}
    )
    conn_map = {"1": "domestic", "2": "commercial", "3": "agricultural"}
    connection = conn_map[conn_type]
 
    # Meter readings
    print()
    prev = get_int("  Previous Meter Reading (units) : ")
    curr = get_int("  Current Meter Reading  (units) : ", min_val=prev)
 
    # Sanctioned load
    load_label = "kW" if connection in ("domestic", "commercial") else "HP"
    load = get_int(f"  Sanctioned Load ({load_label})           : ", min_val=1, max_val=100)
 
    # Billing months
    months = get_choice(
        "\n  Billing Period:",
        {"1": "Monthly (1 month)", "2": "Bimonthly (2 months — TNEB default)"}
    )
    billing_months = int(months)
 
    # Calculate
    try:
        result = calculate_bill(
            consumer_name=name,
            consumer_number=number,
            connection_type=connection,
            previous_reading=prev,
            current_reading=curr,
            sanctioned_load=load,
            months=billing_months,
        )
        print("\n")
        print(format_bill(result))
    except ValueError as e:
        print(f"\n  ❌ Error: {e}")
 
    # Save option
    save = input("\n  Save bill to file? (y/n): ").strip().lower()
    if save == "y":
        filename = f"bill_{result.consumer_number.replace('/', '-')}_{result.billing_period[:7]}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(format_bill(result))
        print(f"  ✅ Bill saved to: {filename}")
 
    print("\n  Thank you for using TNEB Bill Calculator!\n")
 
 
if __name__ == "__main__":
    main()

