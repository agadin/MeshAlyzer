import pandas as pd
from pathlib import Path

ATM_PSI = 14.696  # standard atmospheric pressure (psi)

def compute_q_for_folder():
    balloon_volume_cm3 = 10_051          # balloon volume in cm³
    folder_path = Path(
        "/Users/colehanan/Desktop/WashuClasses/MeshAlyzer/getting_Q"
    )

    # verify directory exists
    if not folder_path.is_dir():
        raise FileNotFoundError(f"{folder_path} is not a valid directory")

    rows = []
    for csv_file in folder_path.glob("*.csv"):
        df = pd.read_csv(csv_file)
        for _, r in df.iterrows():
            delta_p = r["avg_post"] - r["avg_pre"]          # psi
            delta_v = balloon_volume_cm3 * (delta_p / ATM_PSI)  # cm³
            q = delta_v                                     # cm³ /s (pulse = 1 s)
            rows.append({
                "file": csv_file.name,
                "trial": int(r["trial"]),
                "delta_P_psi": round(delta_p, 3),
                "Q_cm3_per_s": round(q, 3),
            })

    result_df = pd.DataFrame(rows)
    out_path = folder_path / "Q_results.csv"
    result_df.to_csv(out_path, index=False)
    print(f"Saved results to {out_path}")

if __name__ == "__main__":
    compute_q_for_folder()
