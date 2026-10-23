import pandas as pd

BASE = "/mnt/scratch/olusegu3/geoaquacrop/experiments"

# --------------------------------------------------
# Load summary outputs
# --------------------------------------------------

control_summary = pd.read_pickle(
    f"{BASE}/control/outputs/summary_results.pkl"
)

recovery_summary = pd.read_pickle(
    f"{BASE}/early_recovery/outputs/summary_results.pkl"
)

# --------------------------------------------------
# First grid cell
# --------------------------------------------------

control = control_summary[0]
recovery = recovery_summary[0]

# --------------------------------------------------
# Extract key metrics
# --------------------------------------------------

metrics = [
    "Dry yield (tonne/ha)",
    "Yield potential (tonne/ha)",
    "seasonal_precip_mm",
    "seasonal_et_mm",
    "seasonal_transpiration_mm",
    "wp_et_kg_per_m3",
]

result = pd.DataFrame({
    "Control": control.iloc[0][metrics],
    "Early_Recovery": recovery.iloc[0][metrics]
})

result["Difference"] = (
    result["Early_Recovery"]
    - result["Control"]
)

print("\n========================")
print("CONTROL VS RECOVERY")
print("========================\n")

print(result)

# --------------------------------------------------
# Yield recovery percentage
# --------------------------------------------------

yield_control = control.loc[
    0,
    "Dry yield (tonne/ha)"
]

yield_recovery = recovery.loc[
    0,
    "Dry yield (tonne/ha)"
]

recovery_pct = (
    yield_recovery /
    yield_control
) * 100

print(
    f"\nYield Recovery = {recovery_pct:.1f}% "
    f"of Control Yield"
)
