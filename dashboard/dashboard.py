import calendar
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st

# Konfigurasi Halaman
st.set_page_config(page_title='Bike Sharing Dashboard', layout='wide')

# Perkecil ukuran font st.metric agar tidak terpotong (ellipsis)
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


# Load Data
@st.cache_data
def load_data():
  df = pd.read_csv('dashboard.csv')
  df['date'] = pd.to_datetime(df['date'])
  return df


day_df = load_data()

# Mapping nama bulan Indonesia
bulan_id = {
    1: 'Januari',
    2: 'Februari',
    3: 'Maret',
    4: 'April',
    5: 'Mei',
    6: 'Juni',
    7: 'Juli',
    8: 'Agustus',
    9: 'September',
    10: 'Oktober',
    11: 'November',
    12: 'Desember',
}
bulan_abbr = {
    1: 'Jan',
    2: 'Feb',
    3: 'Mar',
    4: 'Apr',
    5: 'Mei',
    6: 'Jun',
    7: 'Jul',
    8: 'Agu',
    9: 'Sep',
    10: 'Okt',
    11: 'Nov',
    12: 'Des',
}

# Header Dashboard
st.title('🚲 Bike Sharing Analytics Dashboard')
st.markdown(
    'Analisis tren penyewaan sepeda (2011–2012) serta perbandingan penyewaan'
    ' berdasarkan kondisi cuaca dan suhu pada tahun 2011.'
)

st.divider()

# ==============================================================================
# BAGIAN 1: TREN PENYEWAAN BULANAN (2011 vs 2012)
# ==============================================================================
st.subheader('1. Tren Rata-rata Penyewaan Sepeda Bulanan (2011 vs 2012)')

selected_years = st.multiselect(
    'Pilih Tahun:', options=[2011, 2012], default=[2011, 2012]
)

if not selected_years:
  st.warning('Silakan pilih minimal satu tahun untuk menampilkan grafik.')
else:
  filtered_df = day_df[day_df['year'].isin(selected_years)]
  monthly_trend = (
      filtered_df.groupby(['year', 'month'])['total_rentals']
      .mean()
      .reset_index()
  )

  # Visualisasi Line Chart
  fig1, ax1 = plt.subplots(figsize=(11, 4.2))
  palette_map = {2011: '#1F77B4', 2012: '#FF7F0E'}

  for yr in sorted(selected_years):
    subset = monthly_trend[monthly_trend['year'] == yr]
    ax1.plot(
        subset['month'],
        subset['total_rentals'],
        marker='o',
        linewidth=2.5,
        label=str(yr),
        color=palette_map[yr],
    )

  ax1.set_xticks(range(1, 13))
  ax1.set_xticklabels([bulan_abbr[m] for m in range(1, 13)])
  ax1.set_ylabel('Rata-rata Penyewaan Harian')
  ax1.set_xlabel('Bulan')
  ax1.set_title('Tren Rata-rata Penyewaan Sepeda per Bulan')
  ax1.legend(title='Tahun')
  ax1.grid(True, linestyle='--', alpha=0.35)
  sns.despine()
  st.pyplot(fig1)

  # KPI Metrics Pertanyaan 1
  max_row = monthly_trend.loc[monthly_trend['total_rentals'].idxmax()]
  min_row = monthly_trend.loc[monthly_trend['total_rentals'].idxmin()]

  col1, col2, col3 = st.columns(3)
  with col1:
    st.metric(
