import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

# Konfigurasi halaman
st.set_page_config(
    page_title="Analisis Bike Sharing Dataset",
    page_icon="🚲",
    layout="wide"
)

sns.set_theme(style='whitegrid')

# Load dansiapkan data
@st.cache_data
def load_data():
    day_df = pd.read_csv("day.csv")
    hour_df = pd.read_csv("hour.csv")
    
    # Bersihkan kolom yang tidak dipakai
    day_df.drop(columns=['instant'], inplace=True, errors='ignore')
    hour_df.drop(columns=['instant'], inplace=True, errors='ignore')
    
    day_df['dteday'] = pd.to_datetime(day_df['dteday'])
    hour_df['dteday'] = pd.to_datetime(hour_df['dteday'])
    
    # Ubah kode angka jadi keterangan yang jelas
    season_map = {1: 'Spring', 2: 'Summer', 3: 'Fall', 4: 'Winter'}
    yr_map = {0: 2011, 1: 2012}
    weekday_map = {0: 'Minggu', 1: 'Senin', 2: 'Selasa', 3: 'Rabu', 4: 'Kamis', 5: 'Jumat', 6: 'Sabtu'}
    weather_map = {
        1: 'Cerah / Berawan Sebagian',
        2: 'Berkabut / Mendung',
        3: 'Hujan Ringan / Salju Ringan',
        4: 'Hujan Lebat / Badai'
    }
    
    for df in [day_df, hour_df]:
        df['season'] = df['season'].map(season_map)
        df['yr'] = df['yr'].map(yr_map)
        df['weekday'] = df['weekday'].map(weekday_map)
        df['weathersit'] = df['weathersit'].map(weather_map)
        
    rename_cols = {
        'dteday': 'date',
        'yr': 'year',
        'mnth': 'month',
        'hr': 'hour',
        'weathersit': 'weather',
        'hum': 'humidity',
        'cnt': 'total_count'
    }
    day_df.rename(columns=rename_cols, inplace=True)
    hour_df.rename(columns=rename_cols, inplace=True)
    
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    day_df['month_name'] = pd.Categorical(
        day_df['month'].map({i + 1: m for i, m in enumerate(month_names)}),
        categories=month_names,
        ordered=True
    )
    
    hour_df['day_status'] = hour_df['workingday'].map({0: 'Akhir Pekan / Libur', 1: 'Hari Kerja'})
    
    return day_df, hour_df

day_df, hour_df = load_data()

# Bagian Sidebar untuk Filter
st.sidebar.title("Filter Data")
selected_year = st.sidebar.multiselect(
    "Pilih Tahun",
    options=day_df['year'].unique(),
    default=day_df['year'].unique()
)

selected_season = st.sidebar.multiselect(
    "Pilih Musim",
    options=day_df['season'].unique(),
    default=day_df['season'].unique()
)

filtered_day = day_df[
    (day_df['year'].isin(selected_year)) & 
    (day_df['season'].isin(selected_season))
]

filtered_hour = hour_df[
    (hour_df['year'].isin(selected_year)) & 
    (hour_df['season'].isin(selected_season))
]

# Tampilan Utama Dashboard
st.title("Dashboard Analisis Peminjaman Sepeda")
st.write("Aplikasi sederhana buat ngecek pola penyewaan sepeda harian maupun per jam berdasarkan tren waktu dan kondisi cuaca.")
st.markdown("---")

# Ringkasan Angka (Metrics)
total_rentals = filtered_day['total_count'].sum()
avg_daily = filtered_day['total_count'].mean() if not filtered_day.empty else 0
casual_total = filtered_day['casual'].sum()
registered_total = filtered_day['registered'].sum()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Penyewaan", f"{total_rentals:,}")
with col2:
    st.metric("Rata-rata Harian", f"{avg_daily:,.1f}")
with col3:
    st.metric("Pengguna Casual", f"{casual_total:,}")
with col4:
    st.metric("Pengguna Registered", f"{registered_total:,}")

st.markdown("---")

# Visualisasi 1: Tren Bulanan
st.subheader("Tren Rata-rata Penyewaan Sepeda per Bulan")

monthly_eda = (
    filtered_day.groupby(['year', 'month', 'month_name'], observed=True, as_index=False)
    .agg(avg_rentals=('total_count', 'mean'))
    .sort_values(['year', 'month'])
)

fig1, ax1 = plt.subplots(figsize=(10, 4.5))
sns.lineplot(
    data=monthly_eda,
    x='month_name',
    y='avg_rentals',
    hue='year',
    palette=['#5B8FF9', '#E8684A'],
    marker='o',
    linewidth=2.5,
    ax=ax1
)
ax1.set_title('Perbandingan Rata-rata Sewa per Bulan (2011 vs 2012)', pad=12)
ax1.set_xlabel('Bulan')
ax1.set_ylabel('Rata-rata Penyewaan')
ax1.spines[['top', 'right']].set_visible(False)
st.pyplot(fig1)

st.write(
    "**Catatan Analisis:** "
    "Dari grafik di atas, kelihatan banget kalau jumlah peminjaman sepeda polanya mirip tiap tahunnya. "
    "Mulai naik pas masuk pertengahan tahun (musim panas/gugur) dan turun lagi pas akhir tahun. "
    "Selain itu, angka penyewaan di tahun 2012 jauh lebih tinggi dibanding 2011."
)

st.markdown("---")

# Visualisasi 2: Jam & Cuaca
st.subheader("Pengaruh Waktu dan Cuaca terhadap Aktivitas Sewa")

col_a, col_b = st.columns(2)

with col_a:
    st.markdown("##### Pola Jam Sibuk")
    hourly_eda = filtered_hour.groupby(['day_status', 'hour'], as_index=False).agg(
        avg_rentals=('total_count', 'mean')
    )
    
    fig2, ax2 = plt.subplots(figsize=(6, 4))
    sns.lineplot(
        data=hourly_eda,
        x='hour',
        y='avg_rentals',
        hue='day_status',
        palette=['#F6BD16', '#5AD8A6'],
        marker='o',
        linewidth=2,
        ax=ax2
    )
    ax2.set_xlabel('Jam')
    ax2.set_ylabel('Rata-rata Sewa')
    ax2.set_xticks(range(0, 24, 4))
    ax2.spines[['top', 'right']].set_visible(False)
    st.pyplot(fig2)

with col_b:
    st.markdown("##### Pengaruh Kondisi Cuaca")
    weather_eda = (
        filtered_hour.groupby('weather', as_index=False)
        .agg(avg_rentals=('total_count', 'mean'))
        .sort_values('avg_rentals', ascending=False)
    )
    
    fig3, ax3 = plt.subplots(figsize=(6, 4))
    sns.barplot(
        data=weather_eda,
        x='avg_rentals',
        y='weather',
        hue='weather',
        palette='Blues_r',
        legend=False,
        ax3
    )
    ax3.set_xlabel('Rata-rata Sewa per Jam')
    ax3.set_ylabel('')
    ax3.spines[['top', 'right']].set_visible(False)
    st.pyplot(fig3)

st.write(
    "**Catatan Analisis:** "
    "Kalau dilihat dari jamnya, waktu hari kerja orang-orang kelihatan banget pinjam sepeda pas jam berangkat "
    "dan pulang kantor (pagi dan sore). Sementara pas akhir pekan, sewa sepedanya lebih santai di siang hari. "
    "Faktor cuaca juga ngaruh banget: orang jelas lebih malasin sewa pas hujan atau badai dibanding waktu cuaca cerah."
)
```[cite: 7]
