import os
import matplotlib.pyplot as plt
import numpy as np
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

  df = pd.read_csv(path)
  df.drop(columns=["instant"], errors="ignore", inplace=True)

  if "dteday" in df.columns:
    df["dteday"] = pd.to_datetime(df["dteday"])
    df["date"] = df["dteday"]
  elif "date" in df.columns:
    df["date"] = pd.to_datetime(df["date"])

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

  if "season" in df.columns and pd.api.types.is_numeric_dtype(df["season"]):
    df["season"] = df["season"].map(
        {1: "Spring", 2: "Summer", 3: "Fall", 4: "Winter"}
    )

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

  if "cnt" in df.columns and "total_count" not in df.columns:
    df.rename(columns={"cnt": "total_count"}, inplace=True)

  if "weather" not in df.columns and "weathersit" in df.columns:
    df["weather"] = df["weathersit"].map({
        1: "Cerah / Berawan Sebagian",
        2: "Berkabut / Mendung",
        3: "Hujan Ringan / Salju Ringan",
        4: "Hujan Lebat / Badai",
    })

  if "day_status" not in df.columns and "workingday" in df.columns:
    df["day_status"] = df["workingday"].map(
        {0: "Akhir Pekan / Libur", 1: "Hari Kerja"}
    )

  # Konversi suhu ternormalisasi ke perkiraan Celsius (sesuai skala dataset Bike Sharing)
  if "temp" in df.columns:
    df["temp_c"] = df["temp"] * 41

  # Jika dataset yang terbaca berupa data per jam (lebih dari 366 baris per tahun),
  # agregasikan dulu ke tingkat harian agar selaras dengan analisis harian di notebook
  if "date" in df.columns and len(df) > 400:
    agg_dict = {"total_count": "sum"}
    for col in ["casual", "registered"]:
      if col in df.columns:
        agg_dict[col] = "sum"
    for col in ["temp_c", "temp", "atemp", "hum", "windspeed"]:
      if col in df.columns:
        agg_dict[col] = "mean"
    for col in ["year", "month", "season", "weekday", "weather", "day_status"]:
      if col in df.columns:
        agg_dict[col] = "first"

    df = df.groupby("date", as_index=False).agg(agg_dict)

  if "month_name" not in df.columns and "month" in df.columns:
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
    df["month_name"] = df["month"].map(month_names_dict)

  return df


day_df = load_data()

# --- SIDEBAR: FILTER DATA ---
st.sidebar.title("Parameter Filter")

available_years = (
    sorted(day_df["year"].dropna().unique())
    if "year" in day_df.columns
    else [2011, 2012]
)
selected_year = st.sidebar.multiselect(
    "Pilih Tahun",
    options=available_years,
    default=available_years,
    key="unique_year_filter",
)

available_seasons = (
    sorted(day_df["season"].dropna().unique())
    if "season" in day_df.columns
    else ["Spring", "Summer", "Fall", "Winter"]
)
selected_season = st.sidebar.multiselect(
    "Pilih Musim",
    options=available_seasons,
    default=available_seasons,
    key="unique_season_filter",
)

available_status = (
    sorted(day_df["day_status"].dropna().unique())
    if "day_status" in day_df.columns
    else ["Hari Kerja", "Akhir Pekan / Libur"]
)
selected_status = st.sidebar.multiselect(
    "Pilih Status Hari",
    options=available_status,
    default=available_status,
    key="unique_status_filter",
)

# Terapkan Filter ke DataFrame
filtered_day = day_df.copy()
if "year" in filtered_day.columns and selected_year:
  filtered_day = filtered_day[filtered_day["year"].isin(selected_year)]
if "season" in filtered_day.columns and selected_season:
  filtered_day = filtered_day[filtered_day["season"].isin(selected_season)]
if "day_status" in filtered_day.columns and selected_status:
  filtered_day = filtered_day[filtered_day["day_status"].isin(selected_status)]

if filtered_day.empty:
  st.warning(
      "Tidak ada data yang sesuai dengan kombinasi filter yang dipilih. Silakan"
      " sesuaikan filter di sidebar."
  )
  st.stop()

# --- HEADER UTAMA DASHBOARD ---
st.markdown("# Dashboard Analisis Bike Sharing Dataset")
st.markdown(
    "Eksplorasi tren penyewaan sepeda harian berdasarkan performa bulanan"
    " serta pengaruh kondisi cuaca dan suhu."
)
st.markdown("---")

# --- KARTU METRIK UTAMA ---
st.subheader("Ringkasan Performa")
col_m1, col_m2, col_m3, col_m4 = st.columns(4)

total_orders = filtered_day["total_count"].sum()
avg_daily_orders = filtered_day["total_count"].mean()
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
  st.metric(label="Rata-rata Harian", value=f"{avg_daily_orders:,.1f}")
with col_m3:
  st.metric(label="Pengguna Casual", value=f"{total_casual:,}")
with col_m4:
  st.metric(label="Pengguna Registered", value=f"{total_registered:,}")

st.markdown("---")

# --- BAGIAN 1 (PERTANYAAN 1): TREN BULANAN & TAHUNAN ---
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
plot_df = filtered_day.copy()
plot_df["month_name"] = pd.Categorical(
    plot_df["month_name"], categories=month_order, ordered=True
)

monthly_eda = (
    plot_df.groupby(["year", "month_name"], observed=False)
    .agg(avg_rentals=("total_count", "mean"))
    .reset_index()
)

fig1, ax1 = plt.subplots(figsize=(12, 4.8))
sns.lineplot(
    data=monthly_eda,
    x="month_name",
    y="avg_rentals",
    hue="year",
    palette=["#5B8FF9", "#E8684A"],
    marker="o",
    linewidth=2.5,
    ax=ax1,
)
ax1.set_title(
    "Rata-rata Penyewaan Sepeda Harian per Bulan", pad=14, fontsize=12
)
ax1.set_xlabel("Bulan", fontsize=10)
ax1.set_ylabel("Rata-rata Penyewaan Harian", fontsize=10)
ax1.legend(title="Tahun")
ax1.spines[["top", "right"]].set_visible(False)
st.pyplot(fig1)

st.markdown("""
**Insight:**
* Penyewaan harian cenderung meningkat dari awal tahun menuju pertengahan hingga akhir pertengahan tahun (musim panas/gugur), lalu melandai pada musim dingin.
* Apabila kedua tahun ditampilkan (2011 dan 2012), rata-rata penyewaan harian meningkat tajam dari **3.405,8** (2011) menjadi **5.599,9** (2012), atau tumbuh sekitar **+64,4%**.
""")

st.markdown("---")

# --- BAGIAN 2 (PERTANYAAN 2): PENGARUH CUACA & SUHU (FOKUS TAHUN 2011) ---
st.subheader("Pengaruh Kondisi Cuaca dan Suhu Terhadap Penyewaan (Tahun 2011)")
st.caption(
    "Catatan: Visualisasi pada bagian ini difokuskan khusus pada data tahun"
    " 2011 sesuai cakupan Pertanyaan 2; pilihan tahun 2012 di sidebar tetap"
    " memengaruhi Ringkasan Performa dan Tren Bulanan di atas."
)

df_2011 = filtered_day[filtered_day["year"] == 2011].copy()

if df_2011.empty:
  st.info(
      "Tahun **2011** tidak terpilih pada filter saat ini. Pilih **2011** di"
      " sidebar untuk melihat analisis cuaca dan suhu tahun 2011."
  )
else:
  m2011_1, m2011_2, m2011_3 = st.columns(3)
  with m2011_1:
    st.metric(
        label="Rata-rata Penyewaan Harian (2011)",
        value=f"{df_2011['total_count'].mean():,.1f}",
    )
  with m2011_2:
    if "temp_c" in df_2011.columns:
      st.metric(
          label="Rata-rata Suhu (2011)",
          value=f"{df_2011['temp_c'].mean():.1f} °C",
      )
  with m2011_3:
    if "temp_c" in df_2011.columns:
      corr_val = df_2011["temp_c"].corr(df_2011["total_count"])
      st.metric(
          label="Korelasi Suhu vs Penyewaan (2011)",
          value=f"{corr_val:.2f}",
      )

  col_c1, col_c2 = st.columns(2)

  with col_c1:
    st.markdown("##### Rata-rata Penyewaan per Kondisi Cuaca (2011)")
    if "weather" in df_2011.columns:
      weather_2011 = (
          df_2011.groupby("weather", observed=False)
          .agg(avg_rentals=("total_count", "mean"))
          .reset_index()
          .sort_values("avg_rentals", ascending=False)
      )

      fig2, ax2 = plt.subplots(figsize=(7, 4.5))
      sns.barplot(
          data=weather_2011,
          x="avg_rentals",
          y="weather",
          hue="weather",
          palette="Blues_r",
          legend=False,
          ax=ax2,
      )
      ax2.set_title(
          "Rata-rata Penyewaan per Kondisi Cuaca (2011)", pad=10, fontsize=11
      )
      ax2.set_xlabel("Rata-rata Penyewaan Harian", fontsize=9)
      ax2.set_ylabel("")
      ax2.spines[["top", "right"]].set_visible(False)
      st.pyplot(fig2)

  with col_c2:
    st.markdown("##### Pengaruh Suhu Terhadap Penyewaan Harian (2011)")
    if "temp_c" in df_2011.columns:
      corr_val = df_2011["temp_c"].corr(df_2011["total_count"])
      fig3, ax3 = plt.subplots(figsize=(7, 4.5))
      sns.regplot(
          data=df_2011,
          x="temp_c",
          y="total_count",
          scatter_kws={"alpha": 0.65, "s": 35, "color": "#4C78A8"},
          line_kws={"color": "#E45756", "linewidth": 2},
          ax=ax3,
      )
      ax3.set_title(
          f"Pengaruh Suhu terhadap Penyewaan Harian (2011) | r = {corr_val:.2f}",
          pad=10,
          fontsize=11,
      )
      ax3.set_xlabel("Suhu (°C)", fontsize=9)
      ax3.set_ylabel("Total Penyewaan per Hari", fontsize=9)
      ax3.spines[["top", "right"]].set_visible(False)
      st.pyplot(fig3)

  st.markdown("""
**Insight:**
* Pada tahun **2011**, kondisi cuaca **Cerah / Berawan Sebagian** menghasilkan rata-rata penyewaan harian tertinggi, sedangkan cuaca berkabut/mendung dan hujan ringan menurunkan volume penyewaan.
* Suhu (`temp_c`) pada tahun **2011** menunjukkan korelasi positif dengan jumlah penyewaan harian—penyewaan cenderung meningkat seiring naiknya suhu hingga rentang hangat, sebelum melandai pada suhu ekstrem.
""")

st.markdown("---")
st.caption("Submission Fundamental Analisis Data - Bike Sharing Dataset")
