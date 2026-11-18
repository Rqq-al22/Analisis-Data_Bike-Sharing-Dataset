import streamlit as st  # <-- Pastikan baris ini ada di paling atas!
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Konfigurasi halaman (harus menjadi perintah st pertama)
st.set_page_config(
    page_title="Analisis Bike Sharing Dataset",
    layout="wide"
)

# Load dan persiapan data yang disempurnakan
@st.cache_data
def load_data():
  if os.path.exists("dashboard/dashboard.csv"):
    path = "dashboard/dashboard.csv"
  elif os.path.exists("dashboard.csv"):
    path = "dashboard.csv"
  else:
    path = "data/dashboard.csv"

  df = pd.read_csv(path)

  if "dteday" in df.columns:
    df["dteday"] = pd.to_datetime(df["dteday"])

  # Memastikan kolom tahun, bulan, dan nama bulan tersedia secara otomatis
  if "dteday" in df.columns:
    if "year" not in df.columns:
      df["year"] = df["dteday"].dt.year
    if "month" not in df.columns:
      df["month"] = df["dteday"].dt.month
    if "month_name" not in df.columns:
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

  # Memastikan kolom status hari (day_status) tersedia untuk grafik jam
  if "workingday" in df.columns and "day_status" not in df.columns:
    df["day_status"] = df["workingday"].map(
        {0: "Akhir Pekan / Libur", 1: "Hari Kerja"}
    )

  # Memastikan kolom cuaca (weather) tersedia
  if "weathersit" in df.columns and "weather" not in df.columns:
    weather_map = {
        1: "Cerah / Berawan Sebagian",
        2: "Berkabut / Mendung",
        3: "Hujan Ringan / Salju Ringan",
        4: "Hujan Lebat / Badai",
    }
    df["weather"] = df["weathersit"].map(weather_map)

  return df


df = load_data()

day_df = df.copy()
hour_df = df.copy()

# Sidebar untuk Filter Data
st.sidebar.title("Parameter Filter")
available_years = (
    sorted(day_df["year"].unique()) if "year" in day_df.columns else []
)
selected_year = st.sidebar.multiselect(
    "Pilih Tahun", options=available_years, default=available_years
)

available_seasons = (
    sorted(day_df["season"].unique()) if "season" in day_df.columns else []
)
selected_season = st.sidebar.multiselect(
    "Pilih Musim", options=available_seasons, default=available_seasons
)

# Filter dataframe berdasarkan pilihan sidebar
if "year" in day_df.columns and "season" in day_df.columns:
  filtered_day = day_df[
      (day_df["year"].isin(selected_year))
      & (day_df["season"].isin(selected_season))
  ]
  filtered_hour = hour_df[
      (hour_df["year"].isin(selected_year))
      & (hour_df["season"].isin(selected_season))
  ]
else:
  filtered_day = day_df
  filtered_hour = hour_df

# Sidebar untuk Filter Data
st.sidebar.title("Parameter Filter")
selected_year = st.sidebar.multiselect(
    "Pilih Tahun",
    options=day_df['year'].unique() if 'year' in day_df.columns else [],
    default=day_df['year'].unique() if 'year' in day_df.columns else []
)

selected_season = st.sidebar.multiselect(
    "Pilih Musim",
    options=day_df['season'].unique() if 'season' in day_df.columns else [],
    default=day_df['season'].unique() if 'season' in day_df.columns else []
)

if 'year' in day_df.columns and 'season' in day_df.columns:
    filtered_day = day_df[
        (day_df['year'].isin(selected_year)) & 
        (day_df['season'].isin(selected_season))
    ]
    filtered_hour = hour_df[
        (hour_df['year'].isin(selected_year)) & 
        (hour_df['season'].isin(selected_season))
    ]
else:
    filtered_day = day_df
    filtered_hour = hour_df

# Header Utama Dashboard
st.title("Dashboard Analisis Performa Penyewaan Sepeda")
st.write("Eksplorasi tren historis penyewaan sepeda harian dan per jam berdasarkan dimensi waktu serta kondisi meteorologi.")
st.markdown("---")

# Metrik Utama (KPIs)
total_rentals = filtered_day['total_count'].sum() if 'total_count' in filtered_day.columns else 0
avg_daily = filtered_day['total_count'].mean() if not filtered_day.empty and 'total_count' in filtered_day.columns else 0
casual_total = filtered_day['casual'].sum() if 'casual' in filtered_day.columns else 0
registered_total = filtered_day['registered'].sum() if 'registered' in filtered_day.columns else 0

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Keseluruhan Sewa", f"{total_rentals:,}")
with col2:
    st.metric("Rata-rata Sewa Harian", f"{avg_daily:,.1f}")
with col3:
    st.metric("Pengguna Casual", f"{casual_total:,}")
with col4:
    st.metric("Pengguna Terdaftar (Registered)", f"{registered_total:,}")

st.markdown("---")

# Layout Sejajar (Side-by-Side) untuk Grafik 1 dan Grafik 2 (Menyerupai referensi teman)
col_top_left, col_top_right = st.columns(2)

with col_top_left:
    st.subheader("Tren Rata-rata Penyewaan per Bulan")
    if 'month_name' in filtered_day.columns and 'year' in filtered_day.columns:
        monthly_eda = (
            filtered_day.groupby(['year', 'month', 'month_name'], observed=True, as_index=False)
            .agg(avg_rentals=('total_count', 'mean'))
            .sort_values(['year', 'month'])
        )

        fig1, ax1 = plt.subplots(figsize=(7, 4.5))
        sns.lineplot(
            data=monthly_eda,
            x='month_name',
            y='avg_rentals',
            hue='year',
            palette=['#1f77b4', '#ff7f0e'],
            marker='o',
            linewidth=2,
            ax=ax1
        )
        ax1.set_title("Fluktuasi Bulanan (2011 vs 2012)", pad=10)
        ax1.set_xlabel("Bulan")
        ax1.set_ylabel("Rata-rata Penyewaan")
        ax1.spines[['top', 'right']].set_visible(False)
        st.pyplot(fig1)

with col_top_right:
    st.subheader("Pola Jam Sibuk Berdasarkan Tipe Hari")
    if 'day_status' in filtered_hour.columns and 'hour' in filtered_hour.columns:
        hourly_eda = filtered_hour.groupby(['day_status', 'hour'], as_index=False).agg(
            avg_rentals=('total_count', 'mean')
        )
        
        fig2, ax2 = plt.subplots(figsize=(7, 4.5))
        sns.lineplot(
            data=hourly_eda,
            x='hour',
            y='avg_rentals',
            hue='day_status',
            palette=['#2ca02c', '#d62728'],
            marker='o',
            linewidth=2,
            ax=ax2
        )
        ax2.set_title("Distribusi Jam Operasional", pad=10)
        ax2.set_xlabel("Jam (0 - 23)")
        ax2.set_ylabel("Rata-rata Penyewaan")
        ax2.set_xticks(range(0, 24, 4))
        ax2.spines[['top', 'right']].set_visible(False)
        st.pyplot(fig2)

st.markdown("---")

# Visualisasi Bawah: Pengaruh Kondisi Cuaca
st.subheader("Analisis Dampak Kondisi Cuaca terhadap Volume Sewa")

if 'weather' in filtered_hour.columns:
    weather_eda = (
        filtered_hour.groupby('weather', as_index=False)
        .agg(avg_rentals=('total_count', 'mean'))
        .sort_values('avg_rentals', ascending=False)
    )
    
    fig3, ax3 = plt.subplots(figsize=(10, 4))
    sns.barplot(
        data=weather_eda,
        x='avg_rentals',
        y='weather',
        hue='weather',
        palette='Blues_r',
        legend=False,
        ax=ax3
    )
    ax3.set_xlabel("Rata-rata Penyewaan per Jam")
    ax3.set_ylabel("Kondisi Cuaca")
    ax3.spines[['top', 'right']].set_visible(False)
    st.pyplot(fig3)

# Insight Bisnis Formal
st.markdown("### Kesimpulan Analisis Bisnis")
st.write(
    "**1. Tren Pertumbuhan Tahunan & Musiman:** "
    "Volume permintaan menunjukkan tren peningkatan yang signifikan pada tahun 2012 dibandingkan tahun 2011. "
    "Secara musiman, tingkat permintaan memuncak pada periode pertengahan tahun (musim panas hingga awal musim gugur) "
    "dan mengalami kontraksi pada awal serta akhir tahun."
)
st.write(
    "**2. Pola Perilaku Pengguna Berdasarkan Waktu:** "
    "Terdapat perbedaan karakteristik yang jelas antara hari kerja dan hari libur. Pada hari kerja, lonjakan volume "
    "terjadi secara tajam pada jam-jam komuter (pukul 08:00 dan 17:00), mengindikasikan dominasi penggunaan untuk keperluan mobilitas kerja atau studi. "
    "Sebaliknya, pada akhir pekan, pola permintaan berbentuk distribusi normal yang melandai di siang hari."
)
st.write(
    "**3. Pengaruh Faktor Meteorologi:** "
    "Kondisi cuaca memberikan pengaruh krusial terhadap tingkat utilitas layanan. Cuaca cerah atau berawan sebagian "
    "mencatatkan tingkat penyewaan tertinggi, sementara kondisi cuaca buruk seperti hujan lebat atau badai menekan angka "
    "permintaan secara drastis, yang perlu diantisipasi dalam manajemen alokasi armada operasional."
)
