import os
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="Proyek Analisis Data: Bike Sharing",
    page_icon="🚲",
    layout="wide",
)

sns.set_theme(style="whitegrid")


# Load and Clean Data
@st.cache_data
def load_data():
  # Deteksi path file data otomatis
  if os.path.exists("dashboard/dashboard.csv"):
    path = "dashboard/dashboard.csv"
  elif os.path.exists("dashboard.csv"):
    path = "dashboard.csv"
  elif os.path.exists("data/day.csv"):
    path = "data/day.csv"
  else:
    path = "day.csv"

  # Cek apakah file berupa day.csv mentah atau dashboard.csv matang
  if "day.csv" in path or path.endswith("day.csv"):
    day_df = pd.read_csv(path)
    day_df.drop(columns=["instant"], errors="ignore", inplace=True)
    day_df["dteday"] = pd.to_datetime(day_df["dteday"])

    # Mapping standar notebook
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

# --- SIDEBAR: FILTER DATA (Dengan Key Unik) ---
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

# Terapkan Filter
filtered_day = day_df[
    (day_df["year"].isin(selected_year))
    & (day_df["season"].isin(selected_season))
]
filtered_hour = hour_df[
    (hour_df["year"].isin(selected_year))
    & (hour_df["season"].isin(selected_season))
]

# --- HEADER UTAMA DASHBOARD ---
st.title("🚲 Dashboard Analisis Bike Sharing Dataset")
st.markdown(
    "Eksplorasi data penyewaan sepeda berdasarkan pertanyaan bisnis proyek"
    " Dicoding."
)
st.markdown("---")

# --- PERTANYAAN 1: TREN RATA-RATA PENYEWAAN BULANAN ---
st.subheader(
    "1. Tren Rata-rata Penyewaan Sepeda Harian per Bulan (2011 vs 2012)"
)

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
    data=monthly_eda,
    x="month_name",
    y="avg_rentals",
    hue="year",
    palette=["#5B8FF9", "#E8684A"],
    marker="o",
    linewidth=2.5,
    ax=ax,
)
ax.set_title("Rata-rata Penyewaan Harian Tiap Bulan", pad=14, fontsize=12)
ax.set_xlabel("Bulan", fontsize=10)
ax.set_ylabel("Rata-rata Penyewaan", fontsize=10)
ax.legend(title="Tahun")
ax.spines[["top", "right"]].set_visible(False)
st.pyplot(fig)

st.markdown("---")

# --- PERTANYAAN 2: POLA JAM & KONDISI CUACA ---
st.subheader(
    "2. Pengaruh Kondisi Cuaca dan Pola Jam Terhadap Penyewaan Sepeda"
)

col1, col2 = st.columns(2)

with col1:
  st.markdown("##### Pola Penyewaan per Jam (Hari Kerja vs Libur)")
  if "hour" in filtered_hour.columns and "day_status" in filtered_hour.columns:
    hourly_eda = (
        filtered_hour.groupby(["day_status", "hour"], observed=False)
        .agg(avg_rentals=("total_count", "mean"))
        .reset_index()
    )

    fig1, ax1 = plt.subplots(figsize=(7, 4.5))
    sns.lineplot(
        data=hourly_eda,
        x="hour",
        y="avg_rentals",
        hue="day_status",
        palette=["#F6BD16", "#5AD8A6"],
        marker="o",
        linewidth=2,
        ax=ax1,
    )
    ax1.set_title("Pola Jam Penyewaan", pad=10, fontsize=11)
    ax1.set_xlabel("Jam", fontsize=9)
    ax1.set_ylabel("Rata-rata Penyewaan", fontsize=9)
    ax1.spines[["top", "right"]].set_visible(False)
    st.pyplot(fig1)
  else:
    st.warning("Kolom jam atau status hari tidak ditemukan.")

with col2:
  st.markdown("##### Rata-rata Penyewaan Berdasarkan Kondisi Cuaca")
  if "weather" in filtered_hour.columns:
    weather_eda = (
        filtered_hour.groupby("weather", observed=False)
        .agg(avg_rentals=("total_count", "mean"))
        .reset_index()
        .sort_values("avg_rentals", ascending=False)
    )

    fig2, ax2 = plt.subplots(figsize=(7, 4.5))
    sns.barplot(
        data=weather_eda,
        x="avg_rentals",
        y="weather",
        hue="weather",
        palette="Blues_r",
        legend=False,
        ax=ax2,
    )
    ax2.set_title("Penyewaan Berdasarkan Cuaca", pad=10, fontsize=11)
    ax2.set_xlabel("Rata-rata Penyewaan", fontsize=9)
    ax2.set_ylabel("")
    ax2.spines[["top", "right"]].set_visible(False)
    st.pyplot(fig2)
  else:
    st.warning("Kolom cuaca tidak ditemukan.")

st.markdown("---")
st.caption(
    "Proyek Analisis Data - Bike Sharing Dataset | Dibuat dengan Streamlit"
)
