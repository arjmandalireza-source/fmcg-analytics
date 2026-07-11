import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

st.set_page_config(page_title="FMCG ChatBI", page_icon="📊", layout="wide")

st.title("📊 FMCG ChatBI")
st.caption("Conversational Analytics Platform")

# داده نمونه
@st.cache_data
def load_data():
    dates = pd.date_range(start='2026-01-01', periods=30, freq='D')
    return pd.DataFrame({
        'date': dates,
        'sales': np.random.randint(10, 100, 30),
        'product': ['محصول A', 'محصول B', 'محصول C']*10
    })

df = load_data()

# آمار
col1, col2, col3 = st.columns(3)
col1.metric("📦 فروش کل", f"{df['sales'].sum():,}")
col2.metric("📊 میانگین فروش", f"{df['sales'].mean():.0f}")
col3.metric("📈 تعداد رکوردها", len(df))

# نمودار
fig = px.line(df, x='date', y='sales', title="روند فروش")
st.plotly_chart(fig, use_container_width=True)

st.dataframe(df)