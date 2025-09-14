import streamlit as st
import pandas as pd

st.title('Recommendations Dashboard')

features = pd.read_csv('results/features.csv')
recs = pd.read_csv('results/recommendations.csv')

client = st.selectbox('Выберите клиента', sorted(features['client_code'].tolist()))
f = features[features['client_code'] == client].iloc[0]
r = recs[recs['client_code'] == client].iloc[0]

st.subheader('Доли расходов по категориям')
pct_cols = [c for c in features.columns if c.startswith('pct_')]
st.bar_chart({c.replace('pct_',''): f[c] for c in pct_cols})

st.subheader('Рекомендация')
st.write(f"Топ-1 продукт: {r['top1']}, выгода ≈{int(r['top1_benefit'])} KZT")
st.write(r['push_top1'])
