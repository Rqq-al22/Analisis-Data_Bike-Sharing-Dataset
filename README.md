# Proyek Analisis Data — Bike Sharing Dataset

Proyek ini dibuat untuk memenuhi kriteria proyek akhir analisis data Dicoding: pertanyaan bisnis SMART, data wrangling, EDA, visualisasi dan explanatory analysis, kesimpulan, serta dashboard interaktif Streamlit. 

## Struktur proyek

```text
Proyek_Analisis_Data_Bike_Sharing/
├── data/
│   ├── hour.csv
│   ├── day.csv
├── dashboard/
│   └── dashboard.py
├── notebook.ipynb
├── requirements.txt
├── README.md
└── url.txt
```

## Dataset

Dataset yang digunakan adalah Bike Sharing Dataset (hour.csv dan day.csv) yang mencakup data penyewaan sepeda harian dan per jam dari tahun 2011 hingga 2012.

## Persiapan environment

Instal dependensi yang diperlukan dengan menjalankan perintah berikut di terminal:

```bash
pip install -r requirements.txt
```

## Menjalankan notebook

Buka `notebook.ipynb` pada Jupyter Notebook atau Google Colab, lalu jalankan seluruh sel secara berurutan untuk melihat proses data wrangling, exploratory data analysis, hingga visualisasi.

## Menjalankan dashboard Streamlit secara lokal

Dari folder utama proyek, jalankan perintah berikut pada terminal:

```bash
streamlit run dashboard/dashboard.py
```
