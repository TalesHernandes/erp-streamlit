import streamlit as st
import pandas as pd
import sqlite3
import altair as alt


# Interface Streamlit
def main():
    st.title("ERP Financeiro com Streamlit")

    menu = ["Clientes", "Contas a Pagar", "Contas a Receber", "Lançamentos", "Relatórios"]
    choice = st.sidebar.selectbox("Selecione uma opção", menu)
    conn = sqlite3.connect("erp_finance.db", detect_types=sqlite3.PARSE_DECLTYPES)
    cursor = conn.cursor()

    if choice == "Clientes":
        st.subheader("Cadastro de Clientes")
        df = pd.read_sql_query("SELECT * FROM clientes", conn)
        st.dataframe(df)

    elif choice == "Contas a Pagar":
        st.subheader("Contas a Pagar")
        df = pd.read_sql_query("SELECT * FROM contas_pagar", conn)
        st.dataframe(df)

    elif choice == "Contas a Receber":
        st.subheader("Contas a Receber")
        df = pd.read_sql_query("SELECT * FROM contas_receber", conn)
        st.dataframe(df)

    elif choice == "Lançamentos":
        st.subheader("Lançamentos Financeiros")
        df = pd.read_sql_query("SELECT * FROM lancamentos", conn)
        st.dataframe(df)


    elif choice == "Relatórios":

        st.subheader("Relatórios Financeiros")

        report_type = st.selectbox(

            "Selecione o tipo de relatório",

            ["Fluxo de Caixa", "Distribuição de Contas a Pagar", "Top 5 Clientes"]

        )

        if report_type == "Fluxo de Caixa":

            mostrar_fluxo_de_caixa(conn)


        elif report_type == "Distribuição de Contas a Pagar":

            mostrar_distribuicao_contas_pagar(conn)


        elif report_type == "Top 5 Clientes":

            mostrar_top_clientes(conn)

    conn.close()


def mostrar_top_clientes(conn):
    st.subheader("Top 5 Clientes com Maior Receita")


    query = """

    SELECT 

        c.nome as cliente,

        SUM(cr.valor) as receita_total

    FROM 

        contas_receber cr

    JOIN 

        clientes c ON cr.cliente_id = c.id

    WHERE 

        cr.status = 'Recebido'

    GROUP BY 

        cr.cliente_id

    ORDER BY 

        receita_total DESC

    LIMIT 5

    """

    df = pd.read_sql_query(query, conn)

    if df.empty:
        st.warning("Não há dados de receita por cliente para mostrar.")

        return


    df['ranking'] = range(1, len(df) + 1)


    df['receita_formatada'] = df['receita_total'].apply(
        lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

    chart = alt.Chart(df).mark_bar().encode(

        y=alt.Y('cliente:N', sort='-x', title='Cliente'),

        x=alt.X('receita_total:Q', title='Receita Total (R$)'),

        color=alt.Color('receita_total:Q', scale=alt.Scale(scheme='greenblue'), legend=None),

        tooltip=['ranking', 'cliente', 'receita_formatada']

    ).properties(

        title='Top 5 Clientes por Receita Total',

        width=600,

        height=300

    )

    text = chart.mark_text(

        align='left',

        baseline='middle',

        dx=3

    ).encode(

        text='receita_formatada'

    )


    st.altair_chart(chart + text, use_container_width=True)


    st.subheader("Dados dos Top 5 Clientes")


    display_df = df[['ranking', 'cliente', 'receita_formatada']].rename(

        columns={'ranking': 'Posição', 'cliente': 'Cliente', 'receita_formatada': 'Receita Total'}

    )

    st.dataframe(display_df, hide_index=True)


    if len(df) > 0:
        total_receita = df['receita_total'].sum()

        top_cliente = df.iloc[0]['cliente']

        top_receita = df.iloc[0]['receita_total']

        st.subheader("Insights")

        col1, col2 = st.columns(2)

        with col1:
            st.metric("Cliente Principal", top_cliente)

        with col2:
            st.metric("Receita do Top 5",
                      f"R$ {total_receita:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))


        st.caption(
            f"O cliente principal representa {(top_receita / total_receita) * 100:.1f}% da receita total dos top 5 clientes.")


def mostrar_fluxo_de_caixa(conn):
    st.subheader("Fluxo de Caixa por Mês")

    query = """
    SELECT 
        strftime('%Y-%m', data) as mes,
        tipo,
        SUM(valor) as total
    FROM 
        lancamentos
    GROUP BY 
        mes, tipo
    ORDER BY 
        mes
    """

    df = pd.read_sql_query(query, conn)

    if df.empty:
        st.warning("Não há dados de lançamentos para mostrar.")
        return

    chart = alt.Chart(df).mark_bar().encode(
        x='mes:O',
        y='total:Q',
        color=alt.Color('tipo:N', scale=alt.Scale(
            domain=['Receita', 'Despesa'],
            range=['green', 'red']
        )),
        tooltip=['mes', 'tipo', 'total']
    ).properties(
        title='Receitas e Despesas por Mês',
        width=600
    )

    st.altair_chart(chart, use_container_width=True)

    st.subheader("Dados do Fluxo de Caixa")
    st.dataframe(df)


def mostrar_distribuicao_contas_pagar(conn):
    st.subheader("Distribuição das Contas a Pagar por Fornecedor")

    query = """
    SELECT 
        fornecedor,
        SUM(valor) as total
    FROM 
        contas_pagar
    GROUP BY 
        fornecedor
    ORDER BY 
        total DESC
    LIMIT 10
    """

    df = pd.read_sql_query(query, conn)

    if df.empty:
        st.warning("Não há dados de contas a pagar para mostrar.")
        return

    chart = alt.Chart(df).mark_arc().encode(
        theta=alt.Theta(field="total", type="quantitative"),
        color=alt.Color(field="fornecedor", type="nominal"),
        tooltip=['fornecedor', 'total']
    ).properties(
        title='Distribuição de Contas a Pagar por Fornecedor',
        width=400,
        height=400
    )

    st.altair_chart(chart, use_container_width=True)

    bar_chart = alt.Chart(df).mark_bar().encode(
        y=alt.Y('fornecedor:N', sort='-x'),
        x='total:Q',
        tooltip=['fornecedor', 'total']
    ).properties(
        title='Top 10 Fornecedores por Valor a Pagar',
        width=600
    )

    st.altair_chart(bar_chart, use_container_width=True)

    st.subheader("Dados por Fornecedor")
    st.dataframe(df)


if __name__ == "__main__":
    main()
