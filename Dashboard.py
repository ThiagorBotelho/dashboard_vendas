import streamlit as st
import requests
import pandas as pd
import plotly.express as px

st.set_page_config(layout = 'wide') # Permite que os gráficos fiquem responsivos ao tamanho da tela
# Após isso, vá ao menu hambúrguer, localizado no canto superior direito, clique em "Settings" 
# e selecionamos a opção "Wide mode", na seção "Appearance", assim alteramos o formato do Streamlit para expansivo.


def formata_numero(valor, prefixo = ''):    # Função para formatar os números
    for unidade in ['', 'mil']:
        if valor < 1000:
            return f'{prefixo} {valor:.2f} {unidade}'
        else:
            valor /= 1000
    return f'{prefixo} {valor:.2f} milhões'

# O streamlit permite criar um dashboard com poucas linhas de código, sem a necessidade de HTML, CSS e JavaScript

# Title
st.title('DASHBOARD DE VENDAS :shopping_trolley:')  # :shopping_trolley: é um emoji

url = 'https://labdados.com/produtos'       # Url da API

# Lista de regiões para o filtro
regioes = ['Brasil', 'Centro-Oeste', 'Nordeste', 'Norte', 'Sudeste', 'Sul']

################ Esses filtros serão passados na url da API, para filtrar os dados antes de eles chegarem aqui no código

# Criando um sidebar para os filtros
st.sidebar.title('Filtros')    # Criando um título para o sidebar

regiao = st.sidebar.selectbox('Região', regioes)    # Criando um selectbox para o filtro de região usando a lista de regiões criada anteriormente

if regiao == 'Brasil':  # Se a região for Brasil, a variável regiao recebe uma string vazia para passar na url
    regiao = ''

todos_anos = st.sidebar.checkbox('Dados de todo o período', value = True) # Criando um checkbox para o filtro de período

if todos_anos:      # Se o checkbox estiver marcado, a variável ano recebe uma string vazia para passar na url
    ano = ''
else:
    ano = st.sidebar.slider('Ano', 2020, 2023) # Criando um slider para o filtro de ano com label, o valor mínimo e máximo

query_string = {'regiao':regiao.lower(), 'ano':ano} # Criando um dicionário com os parâmetros da url armazenando a região e o ano

# Requisição
response = requests.get(url, params= query_string)  # Passando esses filtros para a requisição


################### Tratamento dos dados
dados = pd.DataFrame.from_dict(response.json())     # Transformando o json em um dataframe

# Transformando a coluna 'Data da Compra' em datetime
dados['Data da Compra'] = pd.to_datetime(dados['Data da Compra'], format = '%d/%m/%Y') 

######## Esses filtros são para filtrar os dados após eles chegarem aqui no código

filtro_vendedores = st.sidebar.multiselect('Vendedores', dados['Vendedor'].unique()) # Criando um multiselect para o filtro de vendedores, passando como parametro os nomes de vendedores únicos
# filtro vendedores se torna uma lista de vendedores que foram selecionados

if filtro_vendedores:       # Se tiver alguma opção marcada no filtro de vendedores, a variável dados recebe somente os dados que possuem o nome do vendedor selecionado
    dados = dados[dados['Vendedor'].isin(filtro_vendedores)]    # isin() verifica se o valor está contido na lista



################### Tabelas criadas para especificar os tipos de insights

######## Tabelas de receita ##########

receita_estados = dados.groupby('Local da compra')[['Preço']].sum() # Nova tabela com a receita por estado

# Como perdemos a informação de latitude e longitude, criaremos uma nova tabela com essas informações 
# para cada um dos estados, e depois agruparemos esta tabela com a que tem a receita total.

# Removendo duplicatas do campo 'Local da compra' e selecionando apenas as colunas 'Local da compra', 'lat' e 'lon'
# Depois, fazemos um merge com a tabela de "receita por estado", usando o campo 'Local da compra' como chave
# Por fim, ordenamos a tabela pela receita, em ordem decrescente
receita_estados_completa = dados.drop_duplicates(subset = 'Local da compra')[['Local da compra', 'lat', 'lon']].merge(receita_estados, left_on = 'Local da compra', right_index = True).sort_values('Preço', ascending = False) 

# Criando uma nova coluna com a receita mensal
# O método set_index() transforma a coluna 'Data da Compra' em índice
# O método groupby() agrupa os dados por mês e soma a receita
# O método reset_index() transforma o índice em coluna novamente
receita_mensal = dados.set_index('Data da Compra').groupby(pd.Grouper(freq='M'))['Preço'].sum().reset_index()

# Agora vamos construir duas colunas: uma com a informação do mês e outra com a informação do ano
# Cria coluna "Ano" e chama dt.year que transforma a data somente com a informação do ano.
receita_mensal['Ano'] = receita_mensal['Data da Compra'].dt.year    

# Cria coluna "Mês" e chama dt.month_name() que transforma a data somente com a informação do mês.
receita_mensal['Mês'] = receita_mensal['Data da Compra'].dt.month_name()

# Ordenamos a tabela pela receita, em ordem decrescente
receita_categorias = dados.groupby('Categoria do Produto')[['Preço']].sum().sort_values('Preço', ascending = False)


######## Tabelas de quantidade de vendas ##########

vendas_estados = dados.groupby('Local da compra')[['Preço']].count()
vendas_estados_completa = dados.drop_duplicates(subset = 'Local da compra')[['Local da compra', 'lat', 'lon']].merge(vendas_estados, left_on = 'Local da compra', right_index = True).sort_values('Preço', ascending = False) 
vendas_estados_completa = vendas_estados_completa.rename(columns = {'Preço': 'Quantidade de Vendas'})

vendas_mensal = dados.set_index('Data da Compra').groupby(pd.Grouper(freq='M'))['Preço'].sum().reset_index()
vendas_mensal['Ano'] = vendas_mensal['Data da Compra'].dt.year    
vendas_mensal['Mês'] = vendas_mensal['Data da Compra'].dt.month_name()
vendas_mensal = vendas_mensal.rename(columns = {'Preço': 'Quantidade de Vendas'})

vendas_categoria = dados.groupby('Categoria do Produto')[['Preço']].count().sort_values('Preço', ascending = False)


######## Tabelas de vendedores ##########
vendedores = pd.DataFrame(dados.groupby('Vendedor')['Preço'].agg(['sum', 'count'])) # agg permite agregar mais de uma função ao mesmo tempo (Soma e contagem)



################### Criação dos gráficos ###################

######## Gráficos de receita ########

## Gráfico de mapa, com a receita por estado no formato de bolhas
fig_mapa_receita = px.scatter_geo(receita_estados_completa,  
                                   lat = 'lat',                             # Latitude
                                   lon = 'lon',                             # Longitude
                                   scope = 'south america',                 # Localização do mapa
                                   size = 'Preço',                          # Tamanho da bolha baseado na receita
                                   template = 'seaborn',                    # Template do gráfico
                                   hover_name = 'Local da compra',          # Nome que aparece ao passar o mouse
                                   hover_data = {'lat':False,'lon':False},  # Não mostra a latitude e longitude ao passar o mouse
                                   title = 'Receita por Estado')            # Título do gráfico


## Gráfico de linha, com a receita mensal
fig_receita_mensal = px.line(receita_mensal,
                                x = 'Mês',                                  # Eixo X
                                y = 'Preço',                                # Eixo Y
                                markers = True,                             # Mostra os pontos nos meses
                                range_y = (0, receita_mensal.max()),        # Define o intervalo do eixo Y, começando em 0 e indo até o valor máximo da receita
                                color='Ano',                                # Define que a cor será alterada com base na informação do ano
                                line_dash = 'Ano',                          # Define que a linha será tracejada com base na informação do ano
                                title = 'Receita mensal')                   # Título do gráfico
# Alterando Título do eixo Y
fig_receita_mensal.update_layout(yaxis_title = 'Receita')             


## Gráfico de barras, com a receita por estado
fig_receita_estados = px.bar(receita_estados_completa.head(),
                                x = 'Local da compra',                      # Eixo X
                                y = 'Preço',                                # Eixo Y
                                text_auto = True,                           # Mostra o valor da receita acima de cada barra
                                title = 'Top estados')                      # Título do gráfico
# Alterando Título do eixo Y
fig_receita_estados.update_layout(yaxis_title = 'Receita')        


## Gráfico de barras, com a receita por categoria
fig_receita_categorias = px.bar(receita_categorias,                         # Como a tabela só possui duas colunas, não precisamos definir o eixo X e y
                                    text_auto = True,
                                    title = 'Receita por categoria')
# Alterando Título do eixo Y
fig_receita_categorias.update_layout(yaxis_title = 'Receita')


######## Gráficos de Vendas ########

## Gráfico de mapa, com as vendas por estado no formato de bolhas
fig_mapa_vendas = px.scatter_geo(vendas_estados_completa,  
                                    lat = 'lat',                          
                                    lon = 'lon',                              
                                    scope = 'south america',                 
                                    size = 'Quantidade de Vendas',             
                                    template = 'seaborn',                       
                                    hover_name = 'Local da compra',             
                                    hover_data = {'lat':False,'lon':False},     
                                    title = 'Qtd Vendas por Estado')            


## Gráfico de linha, com a venda mensal
fig_receita_mensal = px.line(vendas_mensal,
                                x = 'Mês',                                
                                y = 'Quantidade de Vendas',                         
                                markers = True,                             
                                range_y = (0, vendas_mensal.max()),       
                                color='Ano',                               
                                line_dash = 'Ano',                         
                                title = 'Qtd de Vendas mensal')                 
# Alterando Título do eixo Y
fig_receita_mensal.update_layout(yaxis_title = 'Vendas')


## Gráfico de barras, com o top 5 vendas por estado
fig_vendas_estados = px.bar(vendas_estados_completa.head(),
                                x = 'Local da compra',                     
                                y = 'Quantidade de Vendas',                            
                                text_auto = True,                           
                                title = 'Top estados')                     
# Alterando Título do eixo Y
fig_vendas_estados.update_layout(yaxis_title = 'Vendas')


## Gráfico de barras, com as vendas por categoria
fig_vendas_categorias = px.bar(vendas_categoria,                        
                                    text_auto = True,
                                    title = 'Vendas por categoria')
# Alterando Título do eixo Y
fig_vendas_categorias.update_layout(yaxis_title = 'Vendas')


############ Visualização no Streamlit

# criação das abas para separar os tipos de insights
aba1, aba2, aba3 = st.tabs(['Receita', 'Quantidade de vendas', 'Vendedores'])

# A cláusula with permite acessar as colunas e colocar elementos dentro delas
with aba1: # Receita
    # Criação das 'colunas' para colocar as métricas uma do lado da outra
    coluna1, coluna2 = st.columns(2)

    # A cláusula with permite acessar as colunas e colocar elementos dentro delas
    with coluna1:
        st.metric('Receita', formata_numero(dados['Preço'].sum()), 'R$')        # Gráfico de métricas individuais
        st.plotly_chart(fig_mapa_receita, use_container_width = True)           # # o use_container_width = True faz com que o gráfico ocupe toda a largura da coluna
        st.plotly_chart(fig_receita_estados, use_container_width = True)

    with coluna2:
        st.metric('Quantidade de Vendas', formata_numero(dados.shape[0]))       # Gráfico de métricas individuais
        st.plotly_chart(fig_receita_mensal, use_container_width = True)         # o use_container_width = True faz com que o gráfico ocupe toda a largura da coluna
        st.plotly_chart(fig_receita_categorias, use_container_width = True)
    


with aba2: # Quantidade de vendas
    coluna1, coluna2 = st.columns(2)

    with coluna1:
        st.metric('Receita', formata_numero(dados['Preço'].sum()), 'R$')  
        st.plotly_chart(fig_mapa_vendas, use_container_width = True)     
        st.plotly_chart(fig_vendas_estados, use_container_width = True)

    with coluna2:
        st.metric('Quantidade de Vendas', formata_numero(dados.shape[0]))    
        st.plotly_chart(fig_receita_mensal, use_container_width = True)   
        st.plotly_chart(fig_vendas_categorias, use_container_width = True)
    
    #st.dataframe(vendas_estados_completa)
    #st.dataframe(vendas_categoria)

with aba3: # Vendedores
    qtd_vendedores = st.number_input('Quantidade de vendedores', 2, 10, 5)  # (label, valor mínimo, valor máximo, valor padrão)

    coluna1, coluna2 = st.columns(2)

    with coluna1:
        st.metric('Receita', formata_numero(dados['Preço'].sum()), 'R$')

        # Estou criando o gráfico aqui dentro para que ele seja atualizado de acordo com o input da quantidade de vendedores    
        fig_receita_vendedores = px.bar(vendedores[['sum']].sort_values('sum', ascending=False).head(qtd_vendedores),               # Pegando somente os 5 primeiros vendedores que mais venderam
                                            x='sum',
                                            y=vendedores[['sum']].sort_values(['sum'], ascending=False).head(qtd_vendedores).index, # Pegando o nome dos vendedores
                                            text_auto=True,
                                            title=f'Top {qtd_vendedores} vendedores (receita)')                                      # Título do gráfico personalizado com base no input
        st.plotly_chart(fig_receita_vendedores, use_container_width=True)

    with coluna2:
        st.metric('Quantidade de Vendas', formata_numero(dados.shape[0]))  

        fig_vendas_vendedores = px.bar(vendedores[['count']].sort_values('count', ascending=False).head(qtd_vendedores),               # Pegando somente os 5 primeiros vendedores que mais venderam
                                            x='count',
                                            y=vendedores[['count']].sort_values(['count'], ascending=False).head(qtd_vendedores).index, # Pegando o nome dos vendedores
                                            text_auto=True,
                                            title=f'Top {qtd_vendedores} vendedores (quantidade de vendas)')                                      # Título do gráfico personalizado com base no input
        st.plotly_chart(fig_vendas_vendedores, use_container_width=True)   

    st.dataframe(vendedores)


# Tabela dos dados
st.dataframe(dados)
#st.dataframe(receita_estados)

