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
        label='Puncak Tertinggi',
        value=f"{bulan_id[int(max_row['month'])]} {int(max_row['year'])}",
        delta=f"{max_row['total_rentals']:,.1f} sewa/hari",
    )
  with col2:
    st.metric(
        label='Titik Terendah',
        value=f"{bulan_id[int(min_row['month'])]} {int(min_row['year'])}",
        delta=f"{min_row['total_rentals']:,.1f} sewa/hari",
        delta_color='off',
    )
  with col3:
    if set(selected_years) == {2011, 2012}:
      avg_2011 = day_df[day_df['year'] == 2011]['total_rentals'].mean()
      avg_2012 = day_df[day_df['year'] == 2012]['total_rentals'].mean()
      growth = ((avg_2012 - avg_2011) / avg_2011) * 100
      st.metric(
          label='Pertumbuhan Tahunan (2011 ke 2012)',
          value=f'+{growth:.1f}%',
          delta=f'{avg_2011:,.1f} → {avg_2012:,.1f} unit/hari',
      )
    else:
      yr = selected_years[0]
      avg_yr = filtered_df['total_rentals'].mean()
      st.metric(
          label=f'Rata-rata Harian ({yr})',
          value=f'{avg_yr:,.1f} unit',
          delta=f"Total: {filtered_df['total_rentals'].sum():,} unit",
          delta_color='off',
      )

  with st.expander('Insight Tren Penyewaan (2011 vs 2012)', expanded=True):
    st.markdown("""
        - Rata-rata penyewaan harian meningkat sebesar **64,4%** dari **3.405,8** unit/hari pada tahun 2011 menjadi **5.599,9** unit/hari pada tahun 2012.
        - Pola musiman konsisten di kedua tahun: penyewaan berada di titik terendah pada **Januari–Februari** (cocok untuk jadwal *maintenance* besar unit), meningkat hingga mencapai puncak pada **Juni–September**, lalu menurun kembali pada akhir tahun.
        """)

st.divider()

# ==============================================================================
# BAGIAN 2: CUACA & SUHU (TAHUN 2011)
# ==============================================================================
st.subheader(
    '2. Perbandingan Penyewaan Berdasarkan Kondisi Cuaca & Suhu (Tahun 2011)'
)
day_2011 = day_df[day_df['year'] == 2011].copy()

col_left, col_right = st.columns(2)

# Visualisasi 2A: Kondisi Cuaca
with col_left:
  weather_avg = (
      day_2011.groupby('weather')['total_rentals']
      .mean()
      .sort_values(ascending=False)
      .reset_index()
  )
  fig2, ax2 = plt.subplots(figsize=(6, 4.3))
  colors_w = [
      '#1F618D' if i == 0 else '#A9CCE3' for i in range(len(weather_avg))
  ]
  bars_w = ax2.bar(
      weather_avg['weather'], weather_avg['total_rentals'], color=colors_w
  )

  for bar in bars_w:
    yval = bar.get_height()
    ax2.text(
        bar.get_x() + bar.get_width() / 2,
        yval + 60,
        f'{yval:,.0f}',
        ha='center',
        va='bottom',
        fontsize=10,
        fontweight='bold',
    )

  ax2.set_ylim(0, weather_avg['total_rentals'].max() * 1.18)
  ax2.set_ylabel('Rata-rata Penyewaan Harian')
  ax2.set_title('Rata-rata Penyewaan per Kondisi Cuaca (2011)')
  ax2.tick_params(axis='x', rotation=12)
  sns.despine()
  st.pyplot(fig2)

# Visualisasi 2B: Rentang Suhu
with col_right:
  temp_order = ['< 15°C', '15–20°C', '20–25°C', '25–30°C', '> 30°C']
  day_2011['temp_range'] = pd.Categorical(
      day_2011['temp_range'], categories=temp_order, ordered=True
  )
  temp_avg = (
      day_2011.groupby('temp_range', observed=False)['total_rentals']
      .mean()
      .reset_index()
  )

  fig3, ax3 = plt.subplots(figsize=(6, 4.3))
  max_temp_val = temp_avg['total_rentals'].max()
  colors_t = [
      '#1F618D' if v == max_temp_val else '#A9CCE3'
      for v in temp_avg['total_rentals']
  ]
  bars_t = ax3.bar(
      temp_avg['temp_range'], temp_avg['total_rentals'], color=colors_t
  )

  for bar in bars_t:
    yval = bar.get_height()
    ax3.text(
        bar.get_x() + bar.get_width() / 2,
        yval + 60,
        f'{yval:,.0f}',
        ha='center',
        va='bottom',
        fontsize=10,
        fontweight='bold',
    )

  ax3.set_ylim(0, max_temp_val * 1.18)
  ax3.set_ylabel('Rata-rata Penyewaan Harian')
  ax3.set_title('Rata-rata Penyewaan per Kategori Suhu (2011)')
  sns.despine()
  st.pyplot(fig3)

with st.expander('Insight Kondisi Cuaca & Suhu (2011)', expanded=True):
  st.markdown("""
    - **Kondisi Cuaca:** Rata-rata penyewaan tertinggi terjadi saat cuaca **Clear / Partly Cloudy** (**3.671** unit/hari), menurun pada cuaca **Mist / Cloudy** (**3.026** unit/hari), dan turun drastis saat **Light Snow / Rain** (**1.682** unit/hari).
    - **Rentang Suhu:** Penyewaan terendah berada pada suhu dingin **< 15°C** (**2.049** unit/hari), meningkat hingga mencapai puncak pada rentang **25–30°C** (**4.504** unit/hari), dan sedikit menurun pada suhu ekstrem **> 30°C** (**4.206** unit/hari).
    """)
