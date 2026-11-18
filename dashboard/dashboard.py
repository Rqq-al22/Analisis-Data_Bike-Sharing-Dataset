import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

# Set konfigurasi halaman Streamlit
st.set_page_config(
    page_title="E-Commerce Dashboard",
    layout="wide"
)

# Load cleaned data
@st.cache_data
def load_data():
    df = pd.read_csv("all_data.csv")
    df["order_date"] = pd.to_datetime(df["order_date"])
    return df

all_df = load_data()

# --- SIDEBAR (FILTER & IDENTITAS) ---
with st.sidebar:
    st.header("E-Commerce Dashboard")
    
    min_date = all_df["order_date"].min()
    max_date = all_df["order_date"].max()
    
    try:
        start_date, end_date = st.date_input(
            label="Rentang Waktu",
            min_value=min_date,
            max_value=max_date,
            value=[min_date, max_date]
        )
    except:
        start_date, end_date = min_date, max_date

# Filter DataFrame berdasarkan rentang tanggal di sidebar
main_df = all_df[(all_df["order_date"] >= pd.to_datetime(start_date)) & 
                 (all_df["order_date"] <= pd.to_datetime(end_date))]

# --- HELPER FUNCTIONS (PEMBUATAN DATAFRAME) ---
def create_monthly_orders_df(df):
    df_temp = df.set_index("order_date")
    monthly_orders_df = df_temp.resample(rule='M').agg({
        "order_id": "nunique",
        "total_price": "sum"
    })
    monthly_orders_df.index = monthly_orders_df.index.strftime('%Y-%m')
    monthly_orders_df = monthly_orders_df.reset_index()
    monthly_orders_df.rename(columns={
        "order_id": "order_count",
        "total_price": "revenue"
    }, inplace=True)
    return monthly_orders_df

def create_sum_order_items_df(df):
    sum_order_items_df = df.groupby("product_name").quantity_x.sum().sort_values(ascending=False).reset_index()
    return sum_order_items_df

def create_bygender_df(df):
    bygender_df = df.groupby(by="gender").customer_id.nunique().reset_index()
    bygender_df.rename(columns={"customer_id": "customer_count"}, inplace=True)
    return bygender_df

def create_byage_df(df):
    byage_df = df.groupby(by="age_group").customer_id.nunique().reset_index()
    byage_df.rename(columns={"customer_id": "customer_count"}, inplace=True)
    return byage_df

def create_bystate_df(df):
    bystate_df = df.groupby(by="state").customer_id.nunique().reset_index()
    bystate_df.rename(columns={"customer_id": "customer_count"}, inplace=True)
    return bystate_df

def create_rfm_df(df):
    rfm_df = df.groupby(by="customer_id", as_index=False).agg({
        "order_date": "max",
        "order_id": "nunique",
        "total_price": "sum"
    })
    rfm_df.columns = ["customer_id", "max_order_timestamp", "frequency", "monetary"]
    
    rfm_df["max_order_timestamp"] = rfm_df["max_order_timestamp"].dt.date
    recent_date = df["order_date"].dt.date.max()
    rfm_df["recency"] = rfm_df["max_order_timestamp"].apply(lambda x: (recent_date - x).days)
    rfm_df.drop("max_order_timestamp", axis=1, inplace=True)
    return rfm_df

# Eksekusi helper functions
monthly_orders_df = create_monthly_orders_df(main_df)
sum_order_items_df = create_sum_order_items_df(main_df)
bygender_df = create_bygender_df(main_df)
byage_df = create_byage_df(main_df)
bystate_df = create_bystate_df(main_df)
rfm_df = create_rfm_df(main_df)


# --- MAIN PAGE DASHBOARD ---
st.title("E-Commerce Public Dashboard")

# 1. Performa Penjualan & Revenue Bulanan
st.subheader("Performa Penjualan dan Revenue Perusahaan")

col1, col2 = st.columns(2)
with col1:
    total_order = monthly_orders_df["order_count"].sum()
    st.metric("Total Orders", value=f"{total_order:,}")

with col2:
    total_revenue = monthly_orders_df["revenue"].sum()
    st.metric("Total Revenue", value=f"AUD {total_revenue:,.2f}")

fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(
    monthly_orders_df["order_date"],
    monthly_orders_df["order_count"],
    marker='o',
    linewidth=2,
    color="#72BCD4"
)
ax.set_title("Number of Orders per Month", loc="center", fontsize=15)
plt.xticks(rotation=45, fontsize=10)
st.pyplot(fig)


# 2. Produk Terbaik dan Terburuk
st.subheader("Produk Paling Banyak dan Paling Sedikit Terjual")

fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(24, 6))
colors = ["#72BCD4", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]

sns.barplot(x="quantity_x", y="product_name", data=sum_order_items_df.head(5), palette=colors, ax=ax[0])
ax[0].set_ylabel(None)
ax[0].set_xlabel(None)
ax[0].set_title("Best Performing Product", loc="center", fontsize=15)
ax[0].tick_params(axis='y', labelsize=12)

sns.barplot(x="quantity_x", y="product_name", data=sum_order_items_df.sort_values(by="quantity_x", ascending=True).head(5), palette=colors, ax=ax[1])
ax[1].set_ylabel(None)
ax[1].set_xlabel(None)
ax[1].invert_xaxis()
ax[1].yaxis.set_label_position("right")
ax[1].yaxis.tick_right()
ax[1].set_title("Worst Performing Product", loc="center", fontsize=15)
ax[1].tick_params(axis='y', labelsize=12)

plt.suptitle("Best and Worst Performing Product by Number of Sales", fontsize=20)
st.pyplot(fig)


# 3. Demografi Pelanggan
st.subheader("Demografi Pelanggan")

col1, col2 = st.columns(2)
with col1:
    st.markdown("##### Berdasarkan Gender")
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.barplot(
        y="customer_count", 
        x="gender",
        data=bygender_df.sort_values(by="customer_count", ascending=False),
        palette=colors,
        ax=ax
    )
    ax.set_ylabel(None)
    ax.set_xlabel(None)
    st.pyplot(fig)

with col2:
    st.markdown("##### Berdasarkan Kelompok Usia")
    if "age_group" in byage_df.columns:
        byage_df['age_group'] = pd.Categorical(byage_df['age_group'], ["Youth", "Adults", "Seniors"])
    fig, ax = plt.subplots(figsize=(8, 5))
    colors_age = ["#D3D3D3", "#72BCD4", "#D3D3D3"]
    sns.barplot(
        y="customer_count", 
        x="age_group",
        data=byage_df.sort_values(by="age_group", ascending=False),
        palette=colors_age,
        ax=ax
    )
    ax.set_ylabel(None)
    ax.set_xlabel(None)
    st.pyplot(fig)

st.markdown("##### Berdasarkan Negara Bagian (State)")
fig, ax = plt.subplots(figsize=(12, 6))
colors_state = ["#72BCD4"] + ["#D3D3D3"] * (len(bystate_df) - 1)
sns.barplot(
    x="customer_count", 
    y="state",
    data=bystate_df.sort_values(by="customer_count", ascending=False),
    palette=colors_state,
    ax=ax
)
ax.set_ylabel(None)
ax.set_xlabel(None)
st.pyplot(fig)


# 4. RFM Analysis
st.subheader("Best Customer Based on RFM Parameters")

col1, col2, col3 = st.columns(3)

with col1:
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.barplot(y="recency", x="customer_id", data=rfm_df.sort_values(by="recency", ascending=True).head(5), palette=colors, ax=ax)
    ax.set_ylabel(None)
    ax.set_xlabel(None)
    ax.set_title("By Recency (days)", loc="center", fontsize=15)
    ax.tick_params(axis='x', rotation=45, labelsize=10)
    st.pyplot(fig)

with col2:
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.barplot(y="frequency", x="customer_id", data=rfm_df.sort_values(by="frequency", ascending=False).head(5), palette=colors, ax=ax)
    ax.set_ylabel(None)
    ax.set_xlabel(None)
    ax.set_title("By Frequency", loc="center", fontsize=15)
    ax.tick_params(axis='x', rotation=45, labelsize=10)
    st.pyplot(fig)

with col3:
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.barplot(y="monetary", x="customer_id", data=rfm_df.sort_values(by="monetary", ascending=False).head(5), palette=colors, ax=ax)
    ax.set_ylabel(None)
    ax.set_xlabel(None)
    ax.set_title("By Monetary", loc="center", fontsize=15)
    ax.tick_params(axis='x', rotation=45, labelsize=10)
    st.pyplot(fig)

st.caption("Copyright (c) E-Commerce Analytics 2026")