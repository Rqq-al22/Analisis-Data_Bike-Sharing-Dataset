import os
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="Proyek Analisis Data: Bike Sharing",
    layout="wide",
)

sns.set_theme(style="whitegrid")


# Load and Clean Data
@st.cache_data
def load_data():
  if os.path.exists("dashboard/dashboard.csv"):
    path = "dashboard/dashboard.csv"
  elif os.path.exists("dashboard.csv"):
    path = "dashboard.csv"
  elif os.path.exists("data/day.csv"):
    path = "data/day.csv"
  else:
    path = "day.csv"

  if "day.csv" in path or path.endswith("day.csv"):
    day_df = pd.read_csv(path)
    day_df.drop(columns=["instant"], errors="ignore", inplace=True)
    day_df["dteday"] = pd.to_datetime(day_df["dteday"])

    day_df["season"] = day_df["season"].map(
        {1: "Spring", 2: "Summer", 3: "Fall", 4: "Winter"}
    )
    day_df["year"] = day_df["yr"].map({0: 2011, 1: 2012})
    day_df["month"] = day_df["mnth"]
    day_df["weekday"] = day_df["weekday"].map({
        0: "Minggu",
        1: "Senin",
        2: "Selasa",
        3: "Rabu",
        4: "Kamis",
        5: "Jumat",
        6: "Sabtu",
    })
    day_df["weather"] = day_df["weathersit"].map({
        1: "Cerah / Berawan Sebagian",
        2: "Berkabut / Mendung",
        3: "Hujan Ringan / Salju Ringan",
        4: "Hujan Lebat / Badai",
    })
    day_df.rename(columns={"dteday": "date", "cnt": "total_count"}, inplace=True)
    return day_df, day_df.copy()
  else:
    df = pd.read_csv(path)
    if "dteday" in df.columns:
      df["dteday"] = pd.to_datetime(df["dteday"])
      df["date"] = df["dteday"]
    if "year" not in df.columns and "date" in df.columns:
      df["year"] = df["date"].dt.year
    if "month" not in df.columns and "date" in df.columns:
      df["month"] = df["date"].dt.month
    return df, df


day_df, hour_df = load_data()

# Pastikan kolom penunjang tersedia
if "month_name" not in day_df.columns:
  month_names_dict = {
      1: "Jan",
      2: "Feb",
      3: "Mar",
      4: "Apr",
      5: "May",
      6: "Jun",
      7: "Jul",
      8: "Aug",
      9: "Sep",
      10: "Oct",
      11: "Nov",
      12: "Dec",
  }
  day_df["month_name"] = day_df["month"].map(month_names_dict)
  hour_df["month_name"] = hour_df["month"].map(month_names_dict)

if "day_status" not in hour_df.columns and "workingday" in hour_df.columns:
  hour_df["day_status"] = hour_df["workingday"].map(
      {0: "Akhir Pekan / Libur", 1: "Hari Kerja"}
  )
if "day_status" not in day_df.columns and "workingday" in day_df.columns:
  day_df["day_status"] = day_df["workingday"].map(
      {0: "Akhir Pekan / Libur", 1: "Hari Kerja"}
  )

# --- SIDEBAR: FILTER DATA ---
st.sidebar.title("Parameter Filter")

available_years = (
    sorted(day_df["year"].unique()) if "year" in day_df.columns else [2011, 2012]
)
selected_year = st.sidebar.multiselect(
    "Pilih Tahun",
    options=available_years,
    default=available_years,
    key="unique_year_filter",
)

available_seasons = (
    sorted(day_df["season"].unique())
    if "season" in day_df.columns
    else ["Spring", "Summer", "Fall", "Winter"]
)
selected_season = st.sidebar.multiselect(
    "Pilih Musim",
    options=available_seasons,
    default=available_seasons,
    key="unique_season_filter",
)

# Tambahan Filter Hari Kerja / Libur
available_status = ["Hari Kerja", "Akhir Pekan / Libur"]
selected_status = st.sidebar.multiselect(
    "Pilih Status Hari",
    options=available_status,
    default=available_status,
    key="unique_status_filter",
)

# Terapkan Filter ke DataFrame
filtered_day = day_df[
    (day_df["year"].isin(selected_year))
    & (day_df["season"].isin(selected_season))
    & (day_df["day_status"].isin(selected_status))
]
filtered_hour = hour_df[
    (hour_df["year"].isin(selected_year))
    & (hour_df["season"].isin(selected_season))
    & (hour_df["day_status"].isin(selected_status))
]

# --- HEADER UTAMA DASHBOARD ---
st.title("Dashboard Analisis Bike Sharing Dataset")
st.markdown(
    "Eksplorasi data penyewaan sepeda berdasarkan performa bulanan dan"
    " tren waktu."
)
st.markdown("---")

# --- KARTU METRIK UTAMA (Seperti Contoh Gambar) ---
st.subheader("Ringkasan Performa")
col_m1, col_m2, col_m3 = st.columns(3)

total_orders = filtered_day["total_count"].sum()
total_casual = (
    filtered_day["casual"].sum() if "casual" in filtered_day.columns else 0
)
total_registered = (
    filtered_day["registered"].sum()
    if "registered" in filtered_day.columns
    else 0
)

with col_m1:
  st.metric(label="Total Penyewaan", value=f"{total_orders:,}")
with col_m2:
  st.metric(label="Pengguna Casual", value=f"{total_casual:,}")
with col_m3:
  st.metric(label="Pengguna Registered", value=f"{total_registered:,}")

st.markdown("---")

# --- BAGIAN 1: TREN BULANAN ---
st.subheader("Tren Rata-rata Penyewaan Sepeda Harian per Bulan")

month_order = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]
filtered_day["month_name"] = pd.Categorical(
    filtered_day["month_name"], categories=month_order, ordered=True
)

monthly_eda = (
    filtered_day.groupby(["year", "month_name"], observed=False)
    .agg(avg_rentals=("total_count", "mean"))
    .reset_index()
)

fig, ax = plt.subplots(figsize=(12, 5))
sns.lineplot(
    data=monthly_eda
