import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import datetime
from io import StringIO

# Configuração da página
st.set_page_config(
    page_title="Dashboard Papello Embalagens",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configurações seguras usando Streamlit Secrets
try:
    # Tenta carregar das secrets do Streamlit Cloud
    APP_PASSWORD = st.secrets["APP_PASSWORD"]
    PLANILHA_ID = st.secrets["PLANILHA_ID"]
    GOOGLE_CREDENTIALS = st.secrets["GOOGLE_CREDENTIALS"]
except:
    # Fallback para desenvolvimento local (crie um arquivo .streamlit/secrets.toml)
    st.error("❌ Credenciais não encontradas! Configure o arquivo secrets.toml")
    st.stop()

# Função de autenticação
def check_password():
    """Retorna True se o usuário inseriu a senha correta."""
    
    def password_entered():
        """Verifica se a senha inserida pelo usuário está correta."""
        if st.session_state["password"] == APP_PASSWORD:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Não armazena a senha
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # Primeira execução, mostra inputs para senha
        st.markdown("### 🔐 Acesso ao Dashboard")
        st.text_input(
            "Senha", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Senha não bate, mostra input e mensagem de erro
        st.text_input(
            "Senha", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 Senha incorreta")
        return False
    else:
        # Senha correta
        return True

@st.cache_data(ttl=300)  # Cache por 5 minutos
def conectar_google_sheets():
    """Conecta ao Google Sheets e retorna o spreadsheet"""
    try:
        # Carrega as credenciais
        creds_dict = json.loads(GOOGLE_CREDENTIALS)
        scope = ["https://www.googleapis.com/auth/spreadsheets", 
                "https://www.googleapis.com/auth/drive"]
        
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(PLANILHA_ID)
        return spreadsheet
    except Exception as e:
        st.error(f"Erro ao conectar com Google Sheets: {e}")
        return None

@st.cache_data(ttl=300)  # Cache por 5 minutos
def carregar_dados_planilha(sheet_name):
    """Carrega dados de uma aba específica da planilha"""
    try:
        spreadsheet = conectar_google_sheets()
        if spreadsheet is None:
            return pd.DataFrame()
        
        worksheet = spreadsheet.worksheet(sheet_name)
        data = worksheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Erro ao carregar dados da aba '{sheet_name}': {e}")
        return pd.DataFrame()

def formatar_valor_monetario(valor):
    """Formata valores monetários"""
    try:
        valor = float(valor)
        if abs(valor) >= 1_000_000:
            return f"R$ {valor/1_000_000:.1f}M"
        elif abs(valor) >= 1_000:
            return f"R$ {valor/1_000:.1f}K"
        else:
            return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"

def criar_grafico_linha_vendas(df, coluna_x, coluna_y, titulo):
    """Cria gráfico de linha para vendas"""
    fig = px.line(df, x=coluna_x, y=coluna_y, 
                  title=titulo, markers=True)
    fig.update_layout(
        xaxis_title="Período",
        yaxis_title="Valor",
        hovermode='x unified'
    )
    return fig

def criar_grafico_barras_horizontal(df, coluna_x, coluna_y, titulo, cor='steelblue'):
    """Cria gráfico de barras horizontal"""
    fig = px.bar(df, x=coluna_y, y=coluna_x, orientation='h',
                 title=titulo, color_discrete_sequence=[cor])
    fig.update_layout(
        xaxis_title="Valor",
        yaxis_title="",
        height=max(400, len(df) * 30)
    )
    return fig

def criar_grafico_barras_vertical(df, coluna_x, coluna_y, titulo, cor='coral'):
    """Cria gráfico de barras vertical"""
    fig = px.bar(df, x=coluna_x, y=coluna_y,
                 title=titulo, color_discrete_sequence=[cor])
    fig.update_layout(
        xaxis_title="",
        yaxis_title="Valor"
    )
    return fig

def main():
    if not check_password():
        return
    
    # Header do dashboard
    st.title("📊 Dashboard Papello Embalagens")
    st.markdown("---")
    
    # Sidebar para filtros
    st.sidebar.title("⚙️ Controles")
    
    # Botão para atualizar dados
    if st.sidebar.button("🔄 Atualizar Dados"):
        st.cache_data.clear()
        st.rerun()
    
    # Data da última atualização
    st.sidebar.info(f"Última atualização: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}")
    
    # Carregamento dos dados principais
    with st.spinner('Carregando dados...'):
        df_resumo = carregar_dados_planilha("ResumoMensal")
        df_regioes_total = carregar_dados_planilha("Regioes_Total")
        df_clientes_totais = carregar_dados_planilha("Clientes")
        df_vendas_dia_semana = carregar_dados_planilha("Vendas_Dia_Semana")
        df_vendas_hora_dia = carregar_dados_planilha("Vendas_Hora_Dia")
        df_market_basket = carregar_dados_planilha("Market_Basket")
        df_produtos = carregar_dados_planilha("ProdutoResumo")
    
    # Verificar se os dados foram carregados
    if df_resumo.empty:
        st.error("❌ Não foi possível carregar os dados da planilha. Verifique a conexão.")
        return
    
    # === SEÇÃO 1: INDICADORES PRINCIPAIS ===
    st.header("1️⃣ Indicadores Principais")
    
    if not df_resumo.empty:
        col1, col2, col3, col4 = st.columns(4)
        
        # Calcular totais
        total_pedidos = df_resumo['total_pedidos'].sum() if 'total_pedidos' in df_resumo.columns else 0
        total_faturamento = df_resumo['faturamento_bruto'].sum() if 'faturamento_bruto' in df_resumo.columns else 0
        ticket_medio = total_faturamento / total_pedidos if total_pedidos > 0 else 0
        
        with col1:
            st.metric("Total de Pedidos", f"{total_pedidos:,}".replace(",", "."))
        
        with col2:
            st.metric("Faturamento Total", formatar_valor_monetario(total_faturamento))
        
        with col3:
            st.metric("Ticket Médio", formatar_valor_monetario(ticket_medio))
        
        with col4:
            meses_ativos = len(df_resumo) if not df_resumo.empty else 1
            st.metric("Meses Ativos", meses_ativos)
    
    # === SEÇÃO 2: GRÁFICOS DE EVOLUÇÃO ===
    st.header("2️⃣ Evolução de Vendas")
    
    if not df_resumo.empty and 'mes' in df_resumo.columns:
        col1, col2 = st.columns(2)
        
        with col1:
            if 'total_pedidos' in df_resumo.columns:
                fig_pedidos = criar_grafico_linha_vendas(
                    df_resumo, 'mes', 'total_pedidos', 
                    "Evolução do Número de Pedidos"
                )
                st.plotly_chart(fig_pedidos, use_container_width=True)
        
        with col2:
            if 'faturamento_bruto' in df_resumo.columns:
                fig_faturamento = criar_grafico_linha_vendas(
                    df_resumo, 'mes', 'faturamento_bruto', 
                    "Evolução do Faturamento"
                )
                st.plotly_chart(fig_faturamento, use_container_width=True)
    
    # === SEÇÃO 3: ANÁLISE POR REGIÕES ===
    st.header("3️⃣ Análise por Regiões")
    
    if not df_regioes_total.empty:
        # Top 10 Estados por Faturamento
        top_estados = df_regioes_total.head(10)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if 'faturamento_total' in top_estados.columns and 'estado' in top_estados.columns:
                fig_regioes_fat = criar_grafico_barras_horizontal(
                    top_estados, 'estado', 'faturamento_total',
                    "Top 10 Estados por Faturamento", 'coral'
                )
                st.plotly_chart(fig_regioes_fat, use_container_width=True)
        
        with col2:
            if 'pedidos_totais' in top_estados.columns and 'estado' in top_estados.columns:
                fig_regioes_ped = criar_grafico_barras_horizontal(
                    top_estados, 'estado', 'pedidos_totais',
                    "Top 10 Estados por Número de Pedidos", 'seagreen'
                )
                st.plotly_chart(fig_regioes_ped, use_container_width=True)
        
        # Tabela completa de regiões
        st.subheader("📋 Dados Completos por Região")
        
        # Formatar a tabela para exibição
        df_regioes_display = df_regioes_total.copy()
        if 'faturamento_total' in df_regioes_display.columns:
            df_regioes_display['faturamento_total'] = df_regioes_display['faturamento_total'].apply(
                lambda x: formatar_valor_monetario(x)
            )
        
        st.dataframe(df_regioes_display, use_container_width=True)
    
    # === SEÇÃO 4: TOP PRODUTOS ===
    st.header("4️⃣ Produtos Mais Vendidos")
    
    if not df_produtos.empty:
        # Selecionar mês mais recente
        if 'mes' in df_produtos.columns:
            mes_mais_recente = df_produtos['mes'].max()
            df_produtos_recente = df_produtos[df_produtos['mes'] == mes_mais_recente]
            
            if 'total_produtos' in df_produtos_recente.columns and 'nome_universal' in df_produtos_recente.columns:
                top20_produtos = df_produtos_recente.nlargest(20, 'total_produtos')
                
                fig_produtos = criar_grafico_barras_horizontal(
                    top20_produtos, 'nome_universal', 'total_produtos',
                    f"Top 20 Produtos Mais Vendidos ({mes_mais_recente})", 'steelblue'
                )
                st.plotly_chart(fig_produtos, use_container_width=True)
    
    # === SEÇÃO 5: TOP CLIENTES ===
    st.header("5️⃣ Melhores Clientes")
    
    if not df_clientes_totais.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            if 'faturamento_total' in df_clientes_totais.columns and 'nome' in df_clientes_totais.columns:
                top10_clientes_fat = df_clientes_totais.nlargest(10, 'faturamento_total')
                
                fig_clientes_fat = criar_grafico_barras_horizontal(
                    top10_clientes_fat, 'nome', 'faturamento_total',
                    "Top 10 Clientes por Faturamento", 'gold'
                )
                st.plotly_chart(fig_clientes_fat, use_container_width=True)
        
        with col2:
            if 'frequencia' in df_clientes_totais.columns and 'nome' in df_clientes_totais.columns:
                top10_clientes_freq = df_clientes_totais.nlargest(10, 'frequencia')
                
                fig_clientes_freq = criar_grafico_barras_horizontal(
                    top10_clientes_freq, 'nome', 'frequencia',
                    "Top 10 Clientes por Frequência", 'mediumseagreen'
                )
                st.plotly_chart(fig_clientes_freq, use_container_width=True)
    
    # === SEÇÃO 6: ANÁLISE TEMPORAL ===
    st.header("6️⃣ Análise de Padrões de Venda")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if not df_vendas_dia_semana.empty and 'faturamento' in df_vendas_dia_semana.columns:
            fig_dia_semana = criar_grafico_barras_vertical(
                df_vendas_dia_semana, 'dia_da_semana', 'faturamento',
                "Faturamento por Dia da Semana", 'teal'
            )
            st.plotly_chart(fig_dia_semana, use_container_width=True)
    
    with col2:
        if not df_vendas_hora_dia.empty and 'faturamento' in df_vendas_hora_dia.columns:
            fig_hora_dia = criar_grafico_barras_vertical(
                df_vendas_hora_dia, 'hora_do_dia', 'faturamento',
                "Faturamento por Hora do Dia", 'darkorange'
            )
            st.plotly_chart(fig_hora_dia, use_container_width=True)
    
    # === SEÇÃO 7: MARKET BASKET ANALYSIS ===
    st.header("7️⃣ Produtos Comprados Juntos")
    
    if not df_market_basket.empty:
        st.subheader("🛒 Market Basket Analysis")
        
        # Formatar a tabela para melhor visualização
        df_basket_display = df_market_basket.copy()
        if len(df_basket_display) > 0:
            st.dataframe(df_basket_display, use_container_width=True)
        else:
            st.info("Não há dados suficientes para análise de Market Basket")
    
    # === RODAPÉ ===
    st.markdown("---")
    st.markdown("📈 **Dashboard Papello Embalagens** - Dados atualizados automaticamente da planilha")

if __name__ == "__main__":
    main()