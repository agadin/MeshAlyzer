import time  # for sleep functionality :contentReference[oaicite:0]{index=0}


def inflate_time_seconds(k_cm3_per_psi_min, P_supply_psi, P_internal_psi=0):
    """
    Calculate balloon inflation time in seconds.

    Parameters:
        vol_cm3 (float): Balloon volume in cubic centimeters.
        k_cm3_per_psi_min (float): Flow coefficient in cm³/(psi·min).
        P_supply_psi (float): Supply pressure in psi.
        P_internal_psi (float): Initial internal pressure in psi (default = 0).

    Returns:
        float: Inflation time in seconds, or float('inf') if no driving pressure.
    """
    vol_cm3 = 10051
    # Ensure pressure differential is non-negative
    delta_P = max(P_supply_psi - P_internal_psi, 0)
    if delta_P <= 0:
        return float('inf')
    # Compute time in minutes, then convert to seconds
    time_minutes = vol_cm3 / (k_cm3_per_psi_min * delta_P)
    return time_minutes * 60  # convert to seconds


if __name__ == "__main__":
    while True:  # Loop indefinitely :contentReference[oaicite:1]{index=1}
        try:
            k = float(input("Enter flow coefficient k (cm³/(psi·min)): "))
            P_supply = float(input("Enter supply pressure (psi): "))
            raw = input("Enter initial internal pressure (psi) [default 0]: ")
            P_internal = float(raw) if raw else 0

            t_seconds = inflate_time_seconds( k, P_supply, P_internal)
            if t_seconds == float('inf'):
                print("No driving pressure; balloon will not inflate.")
            else:
                print(f"Estimated inflation time: {t_seconds:.2f} seconds")  # :contentReference[oaicite:3]{index=3}

        except ValueError:
            print("Invalid input. Please enter numeric values.")

        # Wait 5 seconds before next iteration
        time.sleep(5)  # :contentReference[oaicite:4]{index=4}
