from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="Proyek Analisis Data: Bike Sharing Dataset",
    layout="wide",
)

# Penyesuaian ukuran font st.metric agar teks seperti "September 2012" tidak terpotong
st.markdown(
    """
    <style>
    [data-testid="stMetricValue"] {
        font-size: 1.65rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

sns.set_theme(style="whitegrid")


@st.cache_data
def load_data():
  base_dir = Path(__file__).parent
  possible_paths = [
      base_dir / "main_data.csv",
      base_dir / "dashboard.csv",
      base_dir.parent / "data" / "day.csv",
      base_dir / "day.csv",
  ]

  data_path = next((p for p in possible_paths if p.exists()), None)
  if data_path is None:
    st.error(
        "File dataset tidak ditemukan. Pastikan 'main_data.csv' atau"
        " 'dashboard.csv' berada di dalam folder 'dashboard/'."
    )
    st.stop()

  df = pd.read_csv(data_path)
  df.drop(columns=["instant", "atemp"], errors="ignore", inplace=True)

  # Standarisasi kolom tanggal
  if "dteday" in df.columns:
    df["date"] = pd.to_datetime(df["dteday"])
  elif "date" in df.columns:
    df["date"] = pd.to_datetime(df["date"])

  # Standarisasi kolom tahun & bulan
  if "year" not in df.columns:
    if "yr" in df.columns:
      df["year"] = df["yr"].map({0: 2011, 1: 2012})
    elif "date" in df.columns:
      df["year"] = df["date"].dt.year

  if "month" not in df.columns:
    if "mnth" in df.columns:
      df["month"] = df["mnth"]
    elif "date" in df.columns:
      df["month"] = df["date"].dt.month

  # Standarisasi nama kolom target penyewaan
  if "total_rentals" not in df.columns:
    if "cnt" in df.columns:
      df.rename(columns={"cnt": "total_rentals"}, inplace=True)
    elif "total_count" in df.columns:
      df.rename(columns={"total_count": "total_rentals"}, inplace=True)

  # Mapping kategori ke Bahasa Indonesia
  if "season" in df.columns and pd.api.types.is_numeric_dtype(df["season"]):
    df["season"] = df["season"].map({
        1: "Musim Semi",
        2: "Musim Panas",
        3: "Musim Gugur",
        4: "Musim Dingin",
    })

  if "weekday" in df.columns and pd.api.types.is_numeric_dtype(df["weekday"]):
    df["weekday"] = df["weekday"].map({
        0: "Minggu",
        1: "Senin",
        2: "Selasa",
        3: "Rabu",
        4: "Kamis",
        5: "Jumat",
        6: "Sabtu",
    })

  if "day_status" not in df.columns and "workingday" in df.columns:
    df["day_status"] = df["workingday"].map({
        0: "Akhir Pekan / Libur",
        1: "Hari Kerja",
    })

  if "weather" not in df.columns and "weathersit" in df.columns:
    df["weather"] = df["weathersit"].map({
        1: "Cerah / Berawan Sebagian",
        2: "Berkabut / Berawan",
        3: "Hujan Ringan / Salju Ringan",
        4: "Hujan Lebat / Badai",
    })
  elif "weather" in df.columns:
    df["weather"] = df["weather"].replace(
        {"Berkabut / Mendung": "Berkabut / Berawan"}
    )

  # Agregasi ke tingkat harian jika dataset yang dimuat adalah data per jam
  if "date" in df.columns and len(df) > 800:
    agg_dict = {"total_rentals": "sum"}
    for col in ["casual", "registered"]:
      if col in df.columns:
        agg_dict[col] = "sum"
    for col in ["temp", "hum", "windspeed"]:
      if col in df.columns:
        agg_dict[col] = "mean"
    for col in ["year", "month", "season", "weekday", "weather", "day_status"]:
      if col in df.columns:
        agg_dict[col] = "first"
    df = df.groupby("date", as_index=False).agg(agg_dict)

  # Konversi suhu ternormalisasi ke skala Celsius
  if "temp" in df.columns:
    df["temp_c"] = df["temp"] * 41

  return df


day_clean = load_data()

# --- SIDEBAR: FILTER GLOBAL ---
st.sidebar.title("Filter Data")
st.sidebar.caption(
    "Filter di bawah ini berlaku untuk seluruh ringkasan dan visualisasi pada"
    " dashboard."
)

season_order = ["Musim Semi", "Musim Panas", "Musim Gugur", "Musim Dingin"]
available_seasons = (
    [s for s in season_order if s in day_clean["season"].unique()]
    if "season" in day_clean.columns
    else []
)
if not available_seasons and "season" in day_clean.columns:
  available_seasons =
