Dashboard Papello Embalagens
Dashboard interativo em Streamlit que exibe os principais indicadores de vendas da Papello Embalagens, consumindo dados diretamente do Google Sheets.
🚀 Funcionalidades

Autenticação: Acesso protegido por senha
Indicadores Principais: Métricas de pedidos, faturamento e ticket médio
Evolução de Vendas: Gráficos de linha mostrando tendências
Análise por Regiões: Top estados por faturamento e número de pedidos
Top Produtos: Produtos mais vendidos por período
Melhores Clientes: Ranking por faturamento e frequência
Análise Temporal: Padrões de venda por dia da semana e hora
Market Basket: Produtos mais comprados juntos
Atualização Automática: Cache com TTL de 5 minutos

📋 Pré-requisitos

Python 3.8+
Conta no GitHub
Conta no Streamlit Cloud

🛠️ Instalação Local

Clone o repositório:

bashgit clone <seu-repositorio>
cd dashboard-papello

Instale as dependências:

bashpip install -r requirements.txt

Execute o aplicativo:

bashstreamlit run app.py
🌐 Deploy no Streamlit Cloud

Faça upload dos arquivos para o GitHub:

app.py
requirements.txt
README.md


Configure no Streamlit Cloud:

Acesse share.streamlit.io
Conecte sua conta GitHub
Selecione o repositório
O arquivo principal deve ser app.py


Configuração de Secrets (se necessário):

No Streamlit Cloud, vá em Settings > Secrets
Adicione as credenciais se quiser externalizar:

toml[credentials]
google_credentials = """{"type": "service_account", ...}"""
planilha_id = "1cERMKGnnCH0y_C29QNfT__7zeB4bHVHaxdA3fTDcaxs"
app_password = "dash123"


🔐 Acesso

Senha padrão: dash123
Para alterar a senha, modifique a variável APP_PASSWORD no código

📊 Dados Consumidos
O dashboard consome as seguintes abas da planilha Google Sheets:

ResumoMensal: Indicadores mensais agregados
Regioes_Total: Dados por estado/região
Clientes: Informações dos clientes
Vendas_Dia_Semana: Vendas por dia da semana
Vendas_Hora_Dia: Vendas por hora do dia
Market_Basket: Análise de produtos comprados juntos
ProdutoResumo: Resumo de produtos vendidos

🔄 Cache e Performance

Cache de 5 minutos (300 segundos) para dados da planilha
Botão "Atualizar Dados" na sidebar para forçar refresh
Carregamento otimizado com spinners de progresso

📱 Interface

Layout Responsivo: Adapta-se a diferentes tamanhos de tela
Sidebar: Controles e informações de atualização
Seções Organizadas: 7 seções principais com visualizações específicas
Gráficos Interativos: Plotly para visualizações avançadas

🛡️ Segurança

Autenticação por senha na entrada
Credenciais do Google embeddadas no código (para maior facilidade)
Session state para gerenciar autenticação

🆘 Suporte
Em caso de problemas:

Verifique se a planilha está acessível
Confirme se as credenciais do Google estão corretas
Verifique se as abas mencionadas existem na planilha
Consulte os logs do Streamlit Cloud em caso de deploy

📈 Próximas Melhorias

Filtros por período
Export de dados em PDF/Excel
Alertas automáticos
Comparativos ano a ano
Dashboards personalizáveis por usuário