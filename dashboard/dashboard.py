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
        st.error("File dataset tidak ditemukan. Pastikan 'main_data.csv' berada di dalam folder 'dashboard/'.")
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
        df["weather"] = df["weather"].replace({"Berkabut / Mendung": "Berkabut / Berawan"})

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
st.sidebar.caption("Filter di bawah ini berlaku untuk seluruh ringkasan dan visualisasi pada dashboard.")

season_order = ["Musim Semi", "Musim Panas", "Musim Gugur", "Musim Dingin"]
available_seasons = [s for s in season_order if s in day_clean["season"].unique()] if "season" in day_clean.columns else []
if not available_seasons and "season" in day_clean.columns:
    available_seasons = sorted(day_clean["season"].dropna().unique())

selected_season = st.sidebar.multiselect(
    "Pilih Musim",
    options=available_seasons,
    default=available_seasons,
)

available_status = (
    sorted(day_clean["day_status"].dropna().unique())
    if "day_status" in day_clean.columns
    else []
)
selected_status = st.sidebar.multiselect(
    "Pilih Status Hari",
    options=available_status,
    default=available_status,
)

# Terapkan filter global
filtered_df = day_clean.copy()
if selected_season:
    filtered_df = filtered_df[filtered_df["season"].isin(selected_season)]
if selected_status:
    filtered_df = filtered_df[filtered_df["day_status"].isin(selected_status)]

if filtered_df.empty:
    st.warning("Tidak ada data yang sesuai dengan kombinasi filter yang dipilih. Silakan sesuaikan filter di sidebar.")
    st.stop()

# --- HEADER UTAMA ---
st.title("Dashboard Analisis Data: Bike Sharing Dataset")
st.markdown(
    "Dashboard interaktif untuk mengeksplorasi tren penyewaan sepeda harian per bulan (2011–2012) "
    "serta pengaruh kondisi cuaca dan tingkat suhu sepanjang tahun 2011."
)
st.markdown("---")

# --- RINGKASAN PERFORMA UTAMA ---
st.subheader("Ringkasan Performa Penyewaan (2011–2012)")
col1, col2, col3, col4 = st.columns(4)

total_rentals = int(filtered_df["total_rentals"].sum())
avg_daily_rentals = filtered_df["total_rentals"].mean()
total_casual = int(filtered_df["casual"].sum()) if "casual" in filtered_df.columns else 0
total_registered = int(filtered_df["registered"].sum()) if "registered" in filtered_df.columns else 0

col1.metric("Total Penyewaan", f"{total_rentals:,}")
col2.metric("Rata-rata Harian", f"{avg_daily_rentals:,.1f} unit")
col3.metric("Pengguna Casual", f"{total_casual:,}")
col4.metric("Pengguna Registered", f"{total_registered:,}")

st.markdown("---")

# --- PERTANYAAN 1: TREN BULANAN & TAHUNAN ---
st.subheader("1. Tren Rata-rata Penyewaan Sepeda Harian per Bulan (2011–2012)")

col_filter, _ = st.columns([1.5, 2.5])
with col_filter:
    year_view = st.radio(
        "Tampilkan Data Tahun:",
        options=["Perbandingan 2011 & 2012", "2011", "2012"],
        horizontal=True,
    )

monthly_trend = (
    filtered_df.groupby(["year", "month"], as_index=False)["total_rentals"]
    .mean()
)

if year_view == "2011":
    plot_monthly = monthly_trend[monthly_trend["year"] == 2011]
    palette_map = {2011: "#1f77b4"}
elif year_view == "2012":
    plot_monthly = monthly_trend[monthly_trend["year"] == 2012]
    palette_map = {2012: "#ff7f0e"}
else:
    plot_monthly = monthly_trend
    palette_map = {2011: "#1f77b4", 2012: "#ff7f0e"}

month_labels = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
month_full_names = {
    1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
    5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
    9: "September", 10: "Oktober", 11: "November", 12: "Desember",
}

fig1, ax1 = plt.subplots(figsize=(12, 4.8))
sns.lineplot(
    data=plot_monthly,
    x="month",
    y="total_rentals",
    hue="year",
    palette=palette_map,
    marker="o",
    linewidth=2.2,
    ax=ax1,
)
ax1.set_title("Rata-rata Penyewaan Sepeda per Hari menurut Bulan", pad=12, fontweight="bold")
ax1.set_xlabel("Bulan")
ax1.set_ylabel("Rata-rata penyewaan per hari")
ax1.set_xticks(range(1, 13))
ax1.set_xticklabels(month_labels)
ax1.legend(title="Tahun")
sns.despine(ax=ax1)
plt.tight_layout()
st.pyplot(fig1)

if not plot_monthly.empty:
    max_row = plot_monthly.loc[plot_monthly["total_rentals"].idxmax()]
    min_row = plot_monthly.loc[plot_monthly["total_rentals"].idxmin()]

    m_col1, m_col2, m_col3 = st.columns(3)
    m_col1.metric(
        "Puncak Tertinggi",
        f"{month_full_names[int(max_row['month'])]} {int(max_row['year'])}",
        f"{max_row['total_rentals']:,.1f} sewa/hari",
    )
    m_col2.metric(
        "Titik Terendah",
        f"{month_full_names[int(min_row['month'])]} {int(min_row['year'])}",
        f"{min_row['total_rentals']:,.1f} sewa/hari",
        delta_color="off",
    )

    yearly_avg = filtered_df.groupby("year")["total_rentals"].mean()
    if 2011 in yearly_avg.index and 2012 in yearly_avg.index:
        pct_yoy = ((yearly_avg[2012] - yearly_avg[2011]) / yearly_avg[2011]) * 100
        m_col3.metric(
            "Pertumbuhan Tahunan (2011 ke 2012)",
            f"+{pct_yoy:.1f}%",
            f"{yearly_avg[2011]:,.1f} → {yearly_avg[2012]:,.1f} unit/hari",
        )

st.markdown("""
**Insight:**
* Sepanjang tahun **2012**, rata-rata penyewaan sepeda harian selalu jauh lebih tinggi dibandingkan tahun **2011** (naik sekitar **+64,4%** secara keseluruhan dari 3.405,8 menjadi 5.599,9 sepeda per hari).
* Pola musiman serupa di kedua tahun: penyewaan paling sepi pada awal tahun (**Januari 2011** sebagai titik terendah) lalu terus menanjak hingga mencapai puncaknya pada pertengahan hingga akhir musim panas (**September 2012** sebagai puncak tertinggi).
* **Rekomendasi Bisnis:** Jadwalkan perawatan besar unit sepeda pada bulan **Januari–Februari** saat permintaan rendah, dan siagakan kapasitas unit penuh menjelang pertengahan tahun.
""")

st.markdown("---")

# --- PERTANYAAN 2: PENGARUH CUACA & RENTANG SUHU (TAHUN 2011) ---
st.subheader("2. Perbandingan Rata-rata Penyewaan Harian Berdasarkan Cuaca dan Suhu (Tahun 2011)")

day_2011 = filtered_df[filtered_df["year"] == 2011].copy()

if day_2011.empty:
    st.info("Tidak ada data tahun 2011 pada kombinasi filter musim/status hari yang dipilih.")
else:
    weather_2011_vis = (
        day_2011.groupby("weather", as_index=False)["total_rentals"]
        .mean()
        .sort_values("total_rentals", ascending=False)
    )

    bins = [-10, 15, 20, 25, 30, 45]
    labels = ["< 15°C", "15–20°C", "20–25°C", "25–30°C", "> 30°C"]
    day_2011["temp_range"] = pd.cut(day_2011["temp_c"], bins=bins, labels=labels, right=False)

    temp_2011_vis = (
        day_2011.groupby("temp_range", observed=True, as_index=False)
        .agg(total_days=("total_rentals", "count"), avg_rentals=("total_rentals", "mean"))
    )

    c2011_1, c2011_2, c2011_3 = st.columns(3)
    c2011_1.metric("Rata-rata Harian (2011)", f"{day_2011['total_rentals'].mean():,.1f} unit")
    c2011_2.metric("Rata-rata Suhu (2011)", f"{day_2011['temp_c'].mean():.1f} °C")
    if len(day_2011) > 1:
        corr_temp = day_2011["temp"].corr(day_2011["total_rentals"])
        c2011_3.metric("Korelasi Suhu vs Penyewaan (2011)", f"{corr_temp:.2f}")

    fig2, axes = plt.subplots(1, 2, figsize=(15, 5.2))

    # Grafik 1: Kondisi Cuaca
    sns.barplot(
        data=weather_2011_vis,
        x="total_rentals",
        y="weather",
        hue="weather",
        palette="Blues_r",
        legend=False,
        ax=axes[0],
    )
    axes[0].set_title("Rata-rata Penyewaan Harian per Kondisi Cuaca (2011)", pad=12, fontweight="bold")
    axes[0].set_xlabel("Rata-rata Penyewaan per Hari (Unit)")
    axes[0].set_ylabel("Kondisi Cuaca")
    axes[0].set_xlim(0, weather_2011_vis["total_rentals"].max() * 1.18)
    axes[0].spines[["top", "right"]].set_visible(False)
    for container in axes[0].containers:
        axes[0].bar_label(container, fmt="%.1f", padding=4)

    # Grafik 2: Rentang Suhu (°C)
    max_temp_avg = temp_2011_vis["avg_rentals"].max()
    colors_temp = [
        "#A6CEE3" if x < max_temp_avg else "#1F78B4"
        for x in temp_2011_vis["avg_rentals"]
    ]
    sns.barplot(
        data=temp_2011_vis,
        x="temp_range",
        y="avg_rentals",
        hue="temp_range",
        palette=colors_temp,
        legend=False,
        ax=axes[1],
    )
    xtick_labels = [
        f"{row['temp_range']}\n({row['total_days']} hari)"
        for _, row in temp_2011_vis.iterrows()
    ]
    axes[1].set_xticks(range(len(temp_2011_vis)))
    axes[1].set_xticklabels(xtick_labels)
    axes[1].set_title("Rata-rata Penyewaan Harian per Rentang Suhu (2011)", pad=12, fontweight="bold")
    axes[1].set_xlabel("Rentang Suhu (°C)")
    axes[1].set_ylabel("Rata-rata Penyewaan per Hari (Unit)")
    axes[1].set_ylim(0, max_temp_avg * 1.15)
    axes[1].spines[["top", "right"]].set_visible(False)
    for container in axes[1].containers:
        axes[1].bar_label(container, fmt="%.1f", padding=4)

    plt.tight_layout()
    st.pyplot(fig2)

    st.markdown("""
**Insight:**
* **Pengaruh Cuaca:** Penyewaan tertinggi terjadi saat cuaca **Cerah / Berawan Sebagian** (rata-rata **3.695,0 unit/hari**), disusul **Berkabut / Berawan** (**3.088,1 unit/hari**), dan turun drastis saat **Hujan Ringan / Salju Ringan** (**1.674,1 unit/hari**).
* **Pengaruh Suhu:** Suhu memiliki korelasi positif kuat (**r = 0,77**) dengan jumlah penyewaan. Permintaan meningkat seiring menghangatnya suhu dan mencapai titik optimal pada rentang **25–30°C**, lalu sedikit melandai pada suhu di atas **30°C**.
* **Rekomendasi Bisnis:** Alokasikan unit secara maksimal pada hari cerah bersuhu hangat (20–30°C), serta kurangi penempatan unit di lapangan dan berikan promo khusus saat prakiraan cuaca hujan atau suhu dingin (< 15°C).
""")

st.markdown("---")
st.caption("Proyek Analisis Data: Bike Sharing Dataset — Rezki Alya Pasrun")
