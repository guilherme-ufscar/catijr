import streamlit as st
import pandas as pd
import requests
import datetime


@st.cache_data(ttl="1day")
def busca_selic():
    link = "https://www.bcb.gov.br/api/servico/sitebcb/historicotaxasjuros"
    r = requests.get(link)
    tab_selic = pd.DataFrame(r.json()["conteudo"])
    tab_selic["DataInicioVigencia"] = pd.to_datetime(tab_selic["DataInicioVigencia"]).dt.date
    tab_selic["DataFimVigencia"] = pd.to_datetime(tab_selic["DataFimVigencia"]).dt.date
    tab_selic["DataFimVigencia"] = tab_selic["DataFimVigencia"].fillna(datetime.datetime.today().date())
    return tab_selic


def calc_stats(base:pd.DataFrame):
    stats = base.groupby(by="Data")[["Valor"]].sum()
    stats["lag_1"] = stats["Valor"].shift(1)
    stats["Diferença Mensal Abs."] = stats["Valor"] - stats["lag_1"]
    stats["Média 6M Diferença Mensal Abs."] = stats["Diferença Mensal Abs."].rolling(6).mean()
    stats["Média 12M Diferença Mensal Abs."] = stats["Diferença Mensal Abs."].rolling(12).mean()
    stats["Média 24M Diferença Mensal Abs."] = stats["Diferença Mensal Abs."].rolling(24).mean()
    stats["Diferença Mensal Rel."] = stats["Valor"] / stats["lag_1"] - 1
    stats["Evolução 6M Total"] = stats["Valor"].rolling(6).apply(lambda x: x[-1] - x[0], raw=True)
    stats["Evolução 12M Total"] = stats["Valor"].rolling(12).apply(lambda x: x[-1] - x[0], raw=True)
    stats["Evolução 24M Total"] = stats["Valor"].rolling(24).apply(lambda x: x[-1] - x[0], raw=True)
    stats["Evolução 6M Relativa"] = stats["Valor"].rolling(6).apply(lambda x: x[-1] / x[0] - 1, raw=True)
    stats["Evolução 12M Relativa"] = stats["Valor"].rolling(12).apply(lambda x: x[-1] / x[0] - 1, raw=True)
    stats["Evolução 24M Relativa"] = stats["Valor"].rolling(24).apply(lambda x: x[-1] / x[0] - 1, raw=True)

    stats = stats.drop("lag_1", axis=1)

    return stats

def bloco_metas():
    c1, c2 = st.columns(2)

    dt_ini_meta = c1.date_input("Início da Meta", max_value=tab_stats.index.max())
    st.text(dt_ini_meta)
    dt_achada = tab_stats.index[tab_stats.index <= dt_ini_meta][-1]

    fixos = c1.number_input("Custos Fixos", min_value=0., format="%.2f")
    sal_bruto = c2.number_input("Salário Bruto", min_value=0., format="%.2f")
    sal_liq = c2.number_input("Salário Liquido", min_value=0., format="%.2f")

    patrim_ini = tab_stats.loc[dt_achada]["Valor"]
    c1.markdown(f"**Patrimônio no Início da Meta**: R$ {patrim_ini:.2f}")

    selic_bc = busca_selic()
    filtro_dt = (selic_bc["DataInicioVigencia"] < dt_ini_meta) & (selic_bc["DataFimVigencia"] > dt_ini_meta)
    selic_pad = selic_bc[filtro_dt]["MetaSelic"].iloc[0]

    txt_selic = st.number_input("Selic", min_value=0., value=selic_pad, format="%.2f")
    selic_ano = txt_selic / 100
    selic_mes = (selic_ano + 1) ** (1/12) - 1

    rend_ano = patrim_ini * selic_ano
    rend_mes = patrim_ini * selic_mes

    cp1, cp2 = st.columns(2)
    potencial_mes = sal_liq - fixos + rend_mes
    potencial_ano = 12*(sal_liq - fixos) + rend_ano

    with cp1.container(border=True):
        st.markdown(f"""**Potencial Arrecadação Mês**:\n\n R$ {potencial_mes:.2f}""",
                    help = f"{sal_liq:.2f} + (-{fixos:.2f}) + {rend_mes:.2f}")

    with cp2.container(border=True):
        st.markdown(f"""**Potencial Arrecadação Ano**:\n\n R$ {potencial_ano:.2f}""",
                    help=f"12 *({sal_liq:.2f} + (-{fixos:.2f})) + {rend_ano:.2f}")

    with st.container(border=True):
        cm1, cm2 = st.columns(2)
        with cm1:
            meta_final = st.number_input("Meta Estipulada", min_value=-9999999., format="%.2f", value=potencial_ano)

        with cm2:
            patrim_final = meta_final + patrim_ini
            st.markdown(f"Patrimônio Estimado pós meta:\n\n R$ {patrim_final:.2f}")

    return dt_ini_meta, patrim_ini, meta_final, patrim_final

st.set_page_config(page_title='Finanças',page_icon=':moneybag:')

st.html("<h3>App Financeiro"\
        "<p>Streamlit catijr")

upload = st.file_uploader(label="Faça upload dos dados aqui", type=['csv'])

if upload:
    df = pd.read_csv(upload)
    df['Data'] = pd.to_datetime(df['Data'],format='%d/%m/%Y').dt.date

    # dados brutos
    exp1 = st.expander('Dados brutos')

    df["Valor"] = df["Valor"].astype(str).str.replace("R$", "", regex=False).str.replace(".", "", regex=False).str.replace(",", ".", regex=False).astype(float)

    colums_fmt = st.column_config.NumberColumn("Valor",format="R$%d")
    exp1.dataframe(df,hide_index=True,column_config={"Valor": colums_fmt})

    # visão por instituição
    exp2 = st.expander('Instituições')
    df_instituicao = df.pivot_table(index="Data",columns="Instituição",values="Valor")

    tab_data, tab_history, tab_share = exp2.tabs(["Dados", "Histórico", "Distribuição"])

    with tab_data:
        st.dataframe(df_instituicao)
    with tab_history:
        st.line_chart(df_instituicao)
    with tab_share:
        date = st.date_input("Data para distribuição", min_value=df_instituicao.index.min(),max_value=df_instituicao.index.max())

        if date not in df_instituicao.index:
            st.warning("Entre com uma data válida")
        else:
            dt_selected = df_instituicao.loc[date]
            st.bar_chart(dt_selected)

    # estatisticas gerais
    exp3 = st.expander("Estatísticas Gerais")

    tab_stats = calc_stats(df)

    cfg_cols = {
        "Valor": st.column_config.NumberColumn("Valor", format='R$ %.2f'),
        "Diferença Mensal Abs.": st.column_config.NumberColumn("Diferença Mensal Abs.", format='R$ %.2f'),
        "Média 6M Diferença Mensal Abs.": st.column_config.NumberColumn("Média 6M Diferença Mensal Abs.", format='R$ %.2f'),
        "Média 12M Diferença Mensal Abs.": st.column_config.NumberColumn("Média 12M Diferença Mensal Abs.", format='R$ %.2f'),
        "Média 24M Diferença Mensal Abs.": st.column_config.NumberColumn("Média 24M Diferença Mensal Abs.", format='R$ %.2f'),
        "Evolução 6M Total": st.column_config.NumberColumn("Evolução 6M Total", format='R$ %.2f'),
        "Evolução 12M Total": st.column_config.NumberColumn("Evolução 12M Total", format='R$ %.2f'),
        "Evolução 24M Total": st.column_config.NumberColumn("Evolução 24M Total", format='R$ %.2f'),
        "Diferença Mensal Rel.": st.column_config.NumberColumn("Diferença Mensal Rel.", format='percent'),
        "Evolução 6M Relativa": st.column_config.NumberColumn("Evolução 6M Relativa", format='percent'),
        "Evolução 12M Relativa": st.column_config.NumberColumn("Evolução 12M Relativa", format='percent'),
        "Evolução 24M Relativa": st.column_config.NumberColumn("Evolução 24M Relativa", format='percent'),
    }

    tab_g1, tab_g2, tab_g3 = exp3.tabs(tabs=["Dados", "Histórico de Evolução", "Crescimento Relativo"])

    with tab_g1:
        st.dataframe(tab_stats, column_config=cfg_cols)

    with tab_g2:
        cols_abs = [
            "Diferença Mensal Abs.",
            "Média 6M Diferença Mensal Abs.",
            "Média 12M Diferença Mensal Abs.",
            "Média 24M Diferença Mensal Abs.",
        ]
        st.line_chart(tab_stats[cols_abs])

    with tab_g3:
        cols_rel = [
            "Diferença Mensal Rel.",
            "Evolução 6M Relativa",
            "Evolução 12M Relativa",
            "Evolução 24M Relativa",
        ]
        st.line_chart(data=tab_stats[cols_rel])

    with st.expander("Metas"):

        tab_conf, tab_meta_dados, tab_meta_graf = st.tabs(tabs=["Configuração", "Dados", "Gráficos"])

        with tab_conf:
            dt_ini_meta, patrim_ini, meta_final, patrim_final = bloco_metas()

        with tab_meta_dados:
            tab_meses = pd.DataFrame({
                "Data Referência":[(dt_ini_meta + pd.DateOffset(months=i)) for i in range(1,13)],
                "Meta Mensal": [patrim_ini + round(meta_final/12,2) * i for i in range(1,13)],
                })

            tab_meses["Data Referência"] = tab_meses["Data Referência"].dt.strftime("%Y-%m")
            df_patrim = tab_stats.reset_index()[["Data", "Valor"]]
            df_patrim["Data Referência"] = pd.to_datetime(df_patrim["Data"]).dt.strftime("%Y-%m")
            tab_meses = tab_meses.merge(df_patrim, how='left', on="Data Referência")

            tab_meses = tab_meses[['Data Referência', "Meta Mensal", "Valor"]]
            tab_meses["Atingimento (%)"] = tab_meses["Valor"] / tab_meses["Meta Mensal"]
            tab_meses["Atingimento Ano"] = tab_meses["Valor"] / patrim_final
            tab_meses["Atingimento Esperado"] = tab_meses["Meta Mensal"] / patrim_final
            tab_meses = tab_meses.set_index("Data Referência")

            cfg_meses = {
                "Meta Mensal": st.column_config.NumberColumn("Meta Mensal", format='R$ %.2f'),
                "Valor": st.column_config.NumberColumn("Valor Atingido", format='R$ %.2f'),
                "Atingimento (%)": st.column_config.NumberColumn("Atingimento (%)", format='percent'),
                "Atingimento Ano": st.column_config.NumberColumn("Atingimento ano", format='percent'),
                "Atingimento Esperado": st.column_config.NumberColumn("Atingimento Esperado", format='percent'),
            }

            st.dataframe(tab_meses, column_config=cfg_meses)

        with tab_meta_graf:
            st.line_chart(tab_meses[["Atingimento Ano", "Atingimento Esperado"]])

else:
    st.html("<h5>Não tem arquivo</h5>")