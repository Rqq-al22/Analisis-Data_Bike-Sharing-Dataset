import streamlit as st
import pandas as pd
import os

# Konfigurasi halaman Streamlit
st.set_page_config(
    page_title="Bike Sharing Dashboard",
    page_icon="🚲",
    layout="wide"
)

# Fungsi untuk memuat data dengan aman
@st.cache_data
def load_data():
    # Mendapatkan direktori tempat file dashboard.py ini berada
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Mencoba membaca file dashboard.csv di folder yang sama dengan dashboard.py
    file_path = os.path.join(current_dir, "dashboard.csv")
    
    # Jika file tidak ditemukan di folder dashboard, coba cari di luar folder (root utama)
    if not os.path.exists(file_path):
        file_path = os.path.join(current_dir, "../dashboard.csv")
        
    df = pd.read_csv(file_path)
    
    # Konversi kolom tanggal jika ada (sesuaikan nama kolomnya jika berbeda)
    if 'dteday' in df.columns:
        df['dteday'] = pd.to_datetime(df['dteday'])
        
    return df

# Memanggil fungsi load data
try:
    all_df = load_data()
except Exception as e:
    st.error(f"Gagal memuat data CSV. Pastikan file 'dashboard.csv' sudah di-upload ke GitHub di dalam folder 'dashboard/'. Detail error: {e}")
    st.stop()

# --- TAMPILAN DASHBOARD ---
st.title("🚲 Bike Sharing Analysis Dashboard")
st.markdown("Selamat datang di dashboard analisis data penyewaan sepeda!")

# Contoh preview data ringkas di dashboard
st.subheader("Preview Data")
st.dataframe(all_df.head())

# (Lanjutkan sisa kode grafik dan visualisasi Alya di bawah sini...)
