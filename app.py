import streamlit as st
import pandas as pd
from io import StringIO
import altair as alt

st.set_page_config(layout="wide")

def clean_csv(dataframe):
    dataframe = dataframe.drop(['Person ID', 'Department', 'Attendance Status', 'Custom Name', 'Data Source', 'Handling Type', 'Temperature', 'Abnormal'], axis=1)
    dataframe = dataframe.rename(columns={'Attendance Check Point' : 'Sala', 'Name' : 'Nome', 'Time' : 'Data'})    
    dataframe['Sala'] = dataframe['Sala'].apply(lambda x: 'ADM' if x == 'SALA ADM_Door1_Entrance Card Reader1' else x)
    dataframe['Sala'] = dataframe['Sala'].apply(lambda x: 'CCOP' if x == 'SALA CCOP_Door1_Entrance Card Reader1' else x)
    dataframe['Sala'] = dataframe['Sala'].apply(lambda x: 'SERVIÇO' if x == 'SALA SERVICE_Door1_Entrance Card Reader1' else x)
    
    return dataframe

def group_by_user(dataframe):
    dataframe['Data'] = pd.to_datetime(dataframe['Data'])
    
    grouped = dataframe.groupby('Nome').agg(
        Datas=('Data', lambda x: x.dt.strftime('%d/%m/%Y').unique().tolist()),
        **{'Total dias': ('Data', lambda x: x.dt.date.nunique())}
    ).reset_index()
    
    return grouped

st.title('Altave Facial')
st.text('Análise detalhada dos acessos e presenças dos colaboradores.')

st.sidebar.image("https://altave.com.br/wp-content/webp-express/webp-images/uploads/2021/11/Novo_logo_ALTAVE-1024x683.png.webp", width=300)

uploaded_file = st.sidebar.file_uploader("Selecione o arquivo CSV", type=["csv"])

if 'sort_ascending' not in st.session_state:
    st.session_state.sort_ascending = True

def toggle_sort():
    st.session_state.sort_ascending = not st.session_state.sort_ascending

if uploaded_file is not None:
    dataframe = pd.read_csv(uploaded_file, encoding='ISO-8859-1')
    dataframe_clean = clean_csv(dataframe)
    data = group_by_user(dataframe_clean)
    
    options = ['Todos'] + data['Nome'].tolist()
    
    selected_user = st.sidebar.selectbox(
        "Selecione uma pessoa (ou digite para buscar):",
        options=options,
        index=0
    )
    
    if selected_user == 'Todos':
        filtered_data = data
    else:
        filtered_data = data[data['Nome'] == selected_user]
    
    text = "Análise Geral" if selected_user == 'Todos' else f'Análise detalhada do usuário: {selected_user}'
    st.subheader(text)
    st.dataframe(filtered_data, use_container_width=True, hide_index=True)
    
    if selected_user == 'Todos':
        st.write(f"Quantidade de dias por pessoa:")
        st.button("Ordenar gráfico pela quantidade de dias", on_click=toggle_sort)
        
        sort_order = alt.SortField(field='Total dias', order='ascending' if st.session_state.sort_ascending else 'descending')
        num_users = len(filtered_data)
        height_graph = max(300, num_users * 30)
        chart = alt.Chart(filtered_data).mark_bar().encode(
            y=alt.Y('Nome', sort=sort_order),
            x=alt.X('Total dias', scale=alt.Scale(round=True, domain=[0, filtered_data['Total dias'].max()], nice=False), axis=alt.Axis(tickCount=filtered_data['Total dias'].max())),
            tooltip=['Nome', 'Total dias']
        ).properties(
            height=height_graph,
            width='container'
        )
        st.altair_chart(chart, use_container_width=True)
    
    else:   
        data_user = dataframe_clean[dataframe_clean['Nome'] == selected_user].copy()
        data_user['Total dias'] = data_user['Data'].dt.strftime('%d/%m/%Y')
        
        unique_days = data_user['Total dias'].unique().tolist()
        
        selected_day = st.selectbox(
            "Selecione o dia para ver os horários de acesso:",
            options=unique_days,
        )
        
        access_day = data_user[data_user['Total dias'] == selected_day]
        
        st.write(f"Horários de acesso em {selected_day}:")
        st.dataframe(
            access_day[['Data', 'Sala']].sort_values('Data'),
            use_container_width=True,
            column_config={
                "Data": st.column_config.DatetimeColumn("Horario de acesso", format="HH:mm:ss"),
                "Sala": "Sala"
            },
            hide_index=True
        )