import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import time


@st.cache_data
def converte_csv(df):
    return df.to_csv(index = False).encode('utf-8')     # index = False para não salvar o index do dataframe no csv

def mensagem_sucesso():
    sucesso = st.success('Arquivo baixado com sucesso!', icon = '🎉')   # Mostra o sucesso na tela
    time.sleep(5)
    sucesso.empty()    # Apaga a mensagem de sucesso da tela


st.title('DADOS BRUTOS') 

url = 'https://labdados.com/produtos'

response = requests.get(url)

dados = pd.DataFrame.from_dict(response.json())

dados['Data da Compra'] = pd.to_datetime(dados['Data da Compra'], format = '%d/%m/%Y')


with st.expander('Colunas'):
    colunas = st.multiselect('Selecione as colunas', list(dados.columns), list(dados.columns))   # (label, opções, padrão (no caso está selecionando todas as colunas como padrão))

st.sidebar.title('Filtros')

###### Criando elementos expansivos para não poluir a tela

with st.sidebar.expander('Nome do produto'):    # (label)
    produtos = st.multiselect('Selecione os produtos', dados['Produto'].unique(), dados['Produto'].unique())   # (label, opções, padrão (no caso está selecionando todas as colunas como padrão))

with st.sidebar.expander('Categoria do Produto'):    # (label)
    categoria = st.multiselect('Selecione os produtos', dados['Categoria do Produto'].unique(), dados['Categoria do Produto'].unique())

with st.sidebar.expander('Preço do produto'):    # 
    preco = st.slider('Selecione o preço', 0, 5000, (0, 5000))   # (label, min, max, padrão (no caso está selecionando todo o intervalo como padrão))

with st.sidebar.expander('Preço do frete'):    # 
    frete = st.slider('Selecione o preço', 0, 250, (0, 250))	

with st.sidebar.expander('Data da Compra'):
    data_compra = st.date_input('Selecione a data da compra', (dados['Data da Compra'].min(), dados['Data da Compra'].max()))   # (label, (data mín, data max))

with st.sidebar.expander('Vendedor'):    # (label)
    vendedores = st.multiselect('Selecione os produtos', dados['Vendedor'].unique(), dados['Vendedor'].unique())

with st.sidebar.expander('Local da Compra'):    # (label)
    local_compra = st.multiselect('Selecione os produtos', dados['Local da compra'].unique(), dados['Local da compra'].unique())

with st.sidebar.expander('Avaliação da Compra'):   
    avaliacao = st.slider('Selecione o preço', 1, 5, (1, 5))	

with st.sidebar.expander('Tipo de Pagamento'):    # (label)
    tipo_pagamento = st.multiselect('Selecione os produtos', dados['Tipo de pagamento'].unique(), dados['Tipo de pagamento'].unique())

with st.sidebar.expander('Quantidade de parcelas'):   
    qtd_parcelas = st.slider('Selecione o preço', 1, 24, (1, 24))	


###### Criando a query para filtrar os dados

# O que tiver com o @ na frente é uma variável que criamos no with acima, sem o @ é uma coluna do dataframe
# O and no final é para concatenar com a próxima linha
# O \ no final é para quebrar a linha e não ficar tudo na mesma linha
# O @preco[0] é o valor mínimo do slider e o @preco[1] é o valor máximo do slider
# Quando o nome da coluna possui espaço, é necessário colocar o nome entre crases

query = '''
Produto in @produtos and \
`Categoria do Produto` in @categoria and \
@preco[0] <= Preço <= @preco[1] and \
@frete[0] <= Frete <= @frete[1] and \
@data_compra[0] <= `Data da Compra` <= @data_compra[1] and \
Vendedor in @vendedores and \
`Local da compra` in @local_compra and \
@avaliacao[0] <= `Avaliação da compra` <= @avaliacao[1] and \
`Tipo de pagamento` in @tipo_pagamento and \
@qtd_parcelas[0] <= `Quantidade de parcelas` <= @qtd_parcelas[1]
'''

dados_filtrados = dados.query(query)    # Filtrando os dados
dados_filtrados = dados_filtrados[colunas]    # Filtrando as colunas selecionadas

st.dataframe(dados_filtrados) 

# Escrevendo um texto para conferir o tamanho da tabela
# O :blue é para deixar o texto azul
st.markdown(f'A tabela possui :blue[{dados_filtrados.shape[0]}] linhas e :blue[{dados_filtrados.shape[1]}] colunas')


###### Criando o botão para fazer o download da tabela filtrada

st.markdown('Escreva um nome para o arquivo')
coluna1, coluna2 = st.columns(2)    # Criando duas colunas

with coluna1:
    nome_arquivo = st.text_input('', label_visibility = 'collapsed', value = 'dados')    # (label, tirar a label vazia do campo de digitação ,valor padrão (se não digitar nada))
    nome_arquivo += '.csv'    # Adicionando a extensão .csv ao nome do arquivo

with coluna2:
    st.download_button('Fazer o downloado da tabela em csv', data = converte_csv(dados_filtrados), file_name = nome_arquivo, mime = 'text/csv', on_click = mensagem_sucesso)   # (label, arquivo, nome do arquivo, tipo do arquivo, função que será executada ao clicar no botão)
