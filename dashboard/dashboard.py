from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

st.set_page_config(
    page_title="Dashboard Penyewaan Sepeda (2011–2012)",
    page_icon="🚲",
    layout="wide",
)

sns.set_theme(style="whitegrid")


@st.cache_data
def load_data():
    base_dir = Path(__file__).resolve().parent
    candidate_dirs = [
        base_dir / "data",
        base_dir,
        Path("data"),
        Path("."),
    ]

    day_path = None
    hour_path = None
    for folder in candidate_dirs:
        if (folder / "day.csv").exists() and (folder / "hour.csv").exists():
            day_path = folder / "day.csv"
            hour_path = folder / "hour.csv"
            break

    if day_path is None or hour_path is None:
        raise FileNotFoundError(
            "File 'day.csv' dan 'hour.csv' tidak ditemukan. "
            "Pastikan keduanya berada di folder 'data/' atau sejajar dengan dashboard.py."
        )

    day_df = pd.read_csv(day_path)
    hour_df = pd.read_csv(hour_path)

    season_map = {
        1: "Semi (Spring)",
        2: "Panas (Summer)",
        3: "Gugur (Fall)",
        4: "Dingin (Winter)",
    }
    weather_map = {
        1: "Cerah / Berawan Sebagian",
        2: "Berkabut / Berawan",
        3: "Hujan Ringan / Salju Ringan",
        4: "Cuaca Ekstrem",
    }
    month_names = {
        1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr",
        5: "Mei", 6: "Jun", 7: "Jul", 8: "Agu",
        9: "Sep", 10: "Okt", 11: "Nov", 12: "Des",
    }

    for df in (day_df, hour_df):
        df["dteday"] = pd.to_datetime(df["dteday"])
        df["year"] = df["yr"].map({0: 2011, 1: 2012})
        df["month_num"] = df["mnth"]
        df["month_name"] = df["mnth"].map(month_names)
        df["season_name"] = df["season"].map(season_map)
        df["weather_name"] = df["weathersit"].map(weather_map)
        df["day_type"] = df["workingday"].map(
            {1: "Hari Kerja", 0: "Akhir Pekan / Libur"}
        )
        df["temp_c"] = df["temp"] * 41.0

    return day_df, hour_df


try:
    day_df, hour_df = load_data()
except FileNotFoundError as err:
    st.error(str(err))
    st.stop()

# Sidebar Filter
with st.sidebar:
    st.header("Filter Data")

    min_date = day_df["dteday"].min().date()
    max_date = day_df["dteday"].max().date()
    date_range = st.date_input(
        "Rentang Tanggal",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date, end_date = min_date, max_date

    selected_seasons = st.multiselect(
        "Musim",
        options=list(day_df["season_name"].dropna().unique()),
        default=list(day_df["season_name"].dropna().unique()),
    )

    selected_weathers = st.multiselect(
        "Kondisi Cuaca",
        options=list(hour_df["weather_name"].dropna().unique()),
        default=list(hour_df["weather_name"].dropna().unique()),
    )

    selected_day_types = st.multiselect(
        "Tipe Hari",
        options=["Hari Kerja", "Akhir Pekan / Libur"],
        default=["Hari Kerja", "Akhir Pekan / Libur"],
    )

# Terapkan filter
day_filtered = day_df[
    (day_df["dteday"].dt.date >= start_date)
    & (day_df["dteday"].dt.date <= end_date)
    & (day_df["season_name"].isin(selected_seasons))
    & (day_df["day_type"].isin(selected_day_types))
].copy()

hour_filtered = hour_df[
    (hour_df["dteday"].dt.date >= start_date)
    & (hour_df["dteday"].dt.date <= end_date)
    & (hour_df["season_name"].isin(selected_seasons))
    & (hour_df["weather_name"].isin(selected_weathers))
    & (hour_df["day_type"].isin(selected_day_types))
].copy()

st.title("🚲 Dashboard Analisis Penyewaan Sepeda (2011–2012)")
st.caption(
    "Eksplorasi pola permintaan harian, jam sibuk, tipe hari, dan pengaruh cuaca pada Capital Bikeshare."
)

if day_filtered.empty or hour_filtered.empty:
    st.warning("Tidak ada data yang cocok dengan kombinasi filter saat ini.")
    st.stop()

# Ringkasan Metrik (label diperjelas agar nilai tidak terpotong '...')
avg_2011 = day_filtered.loc[day_filtered["year"] == 2011, "cnt"].mean()
avg_2012 = day_filtered.loc[day_filtered["year"] == 2012, "cnt"].mean()
total_rentals = int(day_filtered["cnt"].sum())
avg_hourly = hour_filtered["cnt"].mean()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(
        label="Total Penyewaan",
        value=f"{total_rentals:,} unit",
    )
with col2:
    st.metric(
        label="Rata-rata Harian (2011)",
        value=f"{avg_2011:,.1f} unit" if pd.notna(avg_2011) else "-",
    )
with col3:
    delta_yoy = (
        f"{((avg_2012 - avg_2011) / avg_2011) * 100:+.1f}%"
        if pd.notna(avg_2011) and pd.notna(avg_2012) and avg_2011 > 0
        else None
    )
    st.metric(
        label="Rata-rata Harian (2012)",
        value=f"{avg_2012:,.1f} unit" if pd.notna(avg_2012) else "-",
        delta=delta_yoy,
    )
with col4:
    st.metric(
        label="Rata-rata per Jam",
        value=f"{avg_hourly:,.1f} unit",
    )

st.divider()

# 1. Tren Rata-rata Penyewaan Harian per Bulan (2011 vs 2012)
st.subheader("1.
