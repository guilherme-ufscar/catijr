import streamlit as st
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor


@st.cache_resource
def treina_modelo():
    df_train = pd.read_csv('datasets/train.csv')

    df_train['area_total'] = df_train['TotalBsmtSF'] + df_train['1stFlrSF'] + df_train['2ndFlrSF']

    cols_simulador = ['OverallQual', 'area_total', 'GrLivArea', 'GarageCars',
                      'TotalBsmtSF', 'FullBath', 'YearBuilt', 'Neighborhood']

    df_simulador = df_train[cols_simulador + ['SalePrice']].copy()
    df_simulador['SalePrice_log'] = np.log1p(df_simulador['SalePrice'])

    x_sim = pd.get_dummies(df_simulador[cols_simulador], columns=['Neighborhood'], dtype='int64')
    y_sim = df_simulador['SalePrice_log']

    modelo = RandomForestRegressor(n_estimators=300, random_state=51).fit(x_sim, y_sim)

    return modelo, list(x_sim.columns)


def monta_entrada(overall_qual, area_total, gr_liv_area, garage_cars,
                  total_bsmt_sf, full_bath, year_built, neighborhood, colunas):
    entrada = pd.DataFrame([{
        'OverallQual': overall_qual,
        'area_total': area_total,
        'GrLivArea': gr_liv_area,
        'GarageCars': garage_cars,
        'TotalBsmtSF': total_bsmt_sf,
        'FullBath': full_bath,
        'YearBuilt': year_built,
    }])

    entrada = pd.get_dummies(entrada)
    entrada[f'Neighborhood_{neighborhood}'] = 1

    entrada = entrada.reindex(columns=colunas, fill_value=0)

    return entrada


st.set_page_config(page_title='Simulador de Preço', page_icon=':houses:')

st.html("<h3>Simulador de Preço de Imóvel"
        "<p>House Prices - catijr</p>")

modelo, colunas = treina_modelo()

bairros = ['Blmngtn', 'Blueste', 'BrDale', 'BrkSide', 'ClearCr', 'CollgCr',
           'Crawfor', 'Edwards', 'Gilbert', 'IDOTRR', 'MeadowV', 'Mitchel',
           'NAmes', 'NPkVill', 'NWAmes', 'NoRidge', 'NridgHt', 'OldTown',
           'SWISU', 'Sawyer', 'SawyerW', 'Somerst', 'StoneBr', 'Timber', 'Veenker']

c1, c2 = st.columns(2)

overall_qual = c1.slider('Qualidade Geral (1-10)', min_value=1, max_value=10, value=5)
year_built = c2.number_input('Ano de Construção', min_value=1872, max_value=2026, value=2000)

gr_liv_area = c1.number_input('Área Habitável (pés²)', min_value=0, value=1500)
total_bsmt_sf = c2.number_input('Área do Porão (pés²)', min_value=0, value=0)

garage_cars = c1.slider('Vagas na Garagem', min_value=0, max_value=4, value=1)
full_bath = c2.slider('Banheiros Completos', min_value=0, max_value=3, value=1)

neighborhood = st.selectbox('Bairro', bairros)

area_total = total_bsmt_sf + gr_liv_area

st.markdown(f"**Área Total (Porão + Habitável)**: {area_total} pés²")

entrada = monta_entrada(overall_qual, area_total, gr_liv_area, garage_cars,
                        total_bsmt_sf, full_bath, year_built, neighborhood, colunas)

pred_log = modelo.predict(entrada)[0]
preco_previsto = np.expm1(pred_log)

with st.container(border=True):
    st.markdown(f"### Preço Estimado: $ {preco_previsto:,.2f}")
