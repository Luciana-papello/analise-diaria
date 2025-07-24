import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px
import json
import datetime

# Configuração da página
st.set_page_config(
    page_title="Dashboard Papello Embalagens",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Carregando segredos
try:
    APP_PASSWORD = st.secrets["APP_PASSWORD"]
    PLANILHA_ID = st.secrets["PLANILHA_ID"]
    GOOGLE_CREDENTIALS = st.secrets["GOOGLE_CREDENTIALS"]
except:
    st.error("❌ Credenciais não encontradas! Configure os secrets.")
    st.stop()

# Autenticação com senha
def check_password():
    def password_entered():
        if st.session_state["password"] == APP_PASSWORD:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.markdown("### 🔐 Acesso ao Dashboard")
        st.text_input("Senha", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Senha", type="password", on_change=password_entered, key="password")
        st.error("😕 Senha incorreta")
        return False
    else:
        return True

@st.cache_data(ttl=300)
def conectar_google_sheets():
    try:
        creds_dict = json.loads(GOOGLE_CREDENTIALS)
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        return client.open_by_key(PLANILHA_ID)
    except Exception as e:
        st.error(f"Erro ao conectar com Google Sheets: {e}")
        return None

@st.cache_data(ttl=300)
def carregar_aba(sheet_name):
    planilha = conectar_google_sheets()
    if not planilha:
        return pd.DataFrame()
    try:
        dados = planilha.worksheet(sheet_name).get_all_records()
        return pd.DataFrame(dados)
    except Exception as e:
        st.error(f"Erro ao carregar aba '{sheet_name}': {e}")
        return pd.DataFrame()

def formatar_reais(valor):
    try:
        valor = float(valor)
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"

def main():
    if not check_password():
        return

    st.title("📊 Dashboard Papello Embalagens")
    st.sidebar.title("⚙️ Filtros e Controles")

    if st.sidebar.button("🔄 Atualizar dados"):
        st.cache_data.clear()
        st.rerun()

    st.sidebar.info(f"Atualizado em: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}")

    # Carregando dados
    df_resumo = carregar_aba("ResumoMensal")
    df_regioes = carregar_aba("Regioes_Total")
    df_clientes = carregar_aba("Clientes")
    df_produtos = carregar_aba("ProdutoResumo")

    if df_resumo.empty:
        st.error("❌ Não foi possível carregar dados da planilha.")
        return

    # === FILTROS ===
    st.sidebar.markdown("---")
    mes_disp = sorted(df_resumo['mes'].unique(), reverse=True)
    mes_sel = st.sidebar.selectbox("Selecionar mês", mes_disp)
    df_resumo = df_resumo[df_resumo['mes'] == mes_sel]

    if not df_regioes.empty:
        estados = sorted(df_regioes['estado'].unique())
        estados_sel = st.sidebar.multiselect("Filtrar estados", estados, default=estados)
        df_regioes = df_regioes[df_regioes['estado'].isin(estados_sel)]

    # === INDICADORES ===
    st.subheader("🌟 Indicadores Gerais")
    col1, col2, col3 = st.columns(3)
    total_fat = df_resumo['faturamento_bruto'].sum()
    total_ped = df_resumo['total_pedidos'].sum()
    ticket = total_fat / total_ped if total_ped else 0

    col1.metric("Faturamento", formatar_reais(total_fat))
    col2.metric("Pedidos", f"{total_ped:,}".replace(",", "."))
    col3.metric("Ticket Médio", formatar_reais(ticket))

    # === GRÁFICOS ===
    st.subheader("🔢 Evolução de Pedidos e Faturamento")
    if 'mes' in df_resumo.columns:
        col1, col2 = st.columns(2)
        with col1:
            fig1 = px.line(df_resumo, x='mes', y='total_pedidos', title="Pedidos por mês", markers=True)
            st.plotly_chart(fig1, use_container_width=True)
        with col2:
            fig2 = px.line(df_resumo, x='mes', y='faturamento_bruto', title="Faturamento por mês", markers=True)
            st.plotly_chart(fig2, use_container_width=True)

    # === TOP REGIÕES ===
    st.subheader("🌍 Top Estados")
    if not df_regioes.empty:
        top_estados = df_regioes.sort_values("faturamento_total", ascending=False).head(10)
        fig = px.bar(top_estados, x='faturamento_total', y='estado', orientation='h',
                     title="Top 10 Estados por Faturamento", color_discrete_sequence=['coral'])
        st.plotly_chart(fig, use_container_width=True)

    # === TOP PRODUTOS ===
    st.subheader("🍭 Produtos mais vendidos")
    if not df_produtos.empty:
        mes_prod = df_produtos['mes'].max()
        top_prod = df_produtos[df_produtos['mes'] == mes_prod].nlargest(10, 'total_produtos')
        fig = px.bar(top_prod, x='total_produtos', y='nome_universal', orientation='h',
                     title=f"Top 10 Produtos ({mes_prod})", color_discrete_sequence=['steelblue'])
        st.plotly_chart(fig, use_container_width=True)

    # === TOP CLIENTES ===
    st.subheader("👨‍💼 Clientes Destaque")
    if not df_clientes.empty:
        col1, col2 = st.columns(2)
        with col1:
            top_fat = df_clientes.nlargest(10, 'faturamento_total')
            fig = px.bar(top_fat, x='faturamento_total', y='nome', orientation='h',
                         title="Top 10 por Faturamento", color_discrete_sequence=['gold'])
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            top_freq = df_clientes.nlargest(10, 'frequencia')
            fig = px.bar(top_freq, x='frequencia', y='nome', orientation='h',
                         title="Top 10 por Frequência", color_discrete_sequence=['seagreen'])
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.caption("Desenvolvido por Luciana Papello • Dados em tempo real da planilha Google")

if __name__ == "__main__":
    main()