import streamlit as st
import folium
from streamlit_folium import st_folium
import copy
import pandas as pd
from bs4 import BeautifulSoup


from datafunctions import inputvar_complemento,forecast,getinfobarrio,getvalorizacion,getcaracterizacion,getcomparables
from html_scripts import boxkpi
from analysis_by_business import analysis_by_business

st.set_page_config(layout="wide",initial_sidebar_state="expanded")

@st.experimental_memo
def convert_df(df):
   return df.to_csv(index=False).encode('utf-8')

def style_function(feature):
    return {
        'fillColor': '#ffaf00',
        'color': 'blue',
        'weight': 0, 
        #'dashArray': '5, 5'
    }    

def tiempodeconstruido(x):
    result = None
    try:
        if x<=5: result = 'Entre 0 y 5 años'
        elif x>5 and x<=10: result = 'Entre 5 y 10 años'
        elif x>10 and x<=20: result = 'Entre 10 y 20 años'
        elif x>20: result = 'Mayor a 20 años'
    except: pass
    return result

# streamlit run D:\Dropbox\Empresa\Buydepa\PROYECTOS\APPRAISAL\streamlit\Home.py
# https://streamlit.io/
# pipreqs --encoding utf-8 "D:\Dropbox\Empresa\Buydepa\PROYECTOS\APPRAISAL\streamlit\online"


# Ejemplo colombia
# inputvar = {'pais': 'colombia', 'tipoinmueble': 'Apartamento', 'direccion': 'carrera 19a 103a 62, bogota, colombia', 'areaconstruida': 114, 'habitaciones': 2, 'banos': 3, 'garajes': 2, 'estrato': 6, 'tiempodeconstuido': 'Entre 10 y 20 años'}

# Ejemplo chile
# inputvar = {'pais': 'chile', 'tipoinmueble': 'Apartamento', 'direccion': 'Robinson Crusoe 900 - 1200, Las Condes, Chile', 'areaconstruida': 113, 'habitaciones': 4, 'banos': 3,'garajes':1,'tiempodeconstuido': 'Entre 10 y 20 años'}
# inputvar = {'pais': 'chile', 'tipoinmueble': 'Apartamento', 'direccion': 'Inglaterra 1144, Independencia, Chile', 'areaconstruida': 30, 'habitaciones': 1, 'banos': 1,'garajes':0,'tiempodeconstuido': 'Entre 10 y 20 años'}

diccionario = {'chile':{'garajes': 'Estacionamientos', 'comuna': 'Comuna', 'habitaciones': 'Dormitorios', 'currency': 'UF','inmueble':'Departamento'},
               'colombia':{'garajes': 'Garajes', 'comuna': 'Localidad', 'habitaciones': 'Habitaciones', 'currency': 'COP','inmueble':'Inmueble'}
               }


formato = {'inputvar':{},
           'show_results':False, 
           'dataventacomp':pd.DataFrame(),
           'datarriendocomp':pd.DataFrame()
          }

for key,value in formato.items():
    if key not in st.session_state: 
        st.session_state[key] = value



#-----------------------------------------------------------------------------#
# Formulario
#-----------------------------------------------------------------------------#
with st.sidebar:
    pais      = st.selectbox('País', options=['Chile','Colombia'])
    paislower = pais.lower()
    
    if pais.lower()=='chile':
        ciudad = st.selectbox('Ciudad', options=['Área metropolitana de Santiago'])
    elif pais.lower()=='colombia':
        ciudad = st.selectbox('Ciudad', options=['Bogotá'])    

    direccion = st.text_input('Dirección',value='')
    
    if pais.lower()=='chile':
        comuna = st.selectbox(diccionario[paislower]['comuna'], options=['','Cerrillos', 'Cerro Navia', 'Conchalí', 'El Bosque', 'Estación Central', 'Huechuraba', 'Independencia', 'La Cisterna', 'La Florida', 'La Granja', 'La Pintana', 'La Reina', 'Las Condes', 'Lo Barnechea', 'Lo Espejo', 'Lo Prado', 'Macul', 'Maipú', 'Ñuñoa', 'Pedro Aguirre Cerda', 'Peñalolén', 'Providencia', 'Pudahuel', 'Quilicura', 'Quinta Normal', 'Recoleta', 'Renca', 'San Joaquín', 'San Miguel', 'San Ramón', 'Santiago', 'Vitacura'])
    elif pais.lower()=='colombia':
        comuna = ''
    
    if pais.lower()=='chile':
        tipoinmueble        = st.selectbox('Tipo de inmueble',options=['Departamento','Casa'])
        tipoinmuebleinicial = copy.deepcopy(tipoinmueble)
        if tipoinmueble=='Departamento': tipoinmueble = 'Apartamento'
    elif pais.lower()=='colombia':
        tipoinmueble        = st.selectbox('Tipo de inmueble',options=['Apartamento','Casa']) 
        tipoinmuebleinicial = copy.deepcopy(tipoinmueble)
        
    areaconstruida = st.number_input('Área construida',min_value=20,max_value=500,value=60)
    habitaciones   = st.selectbox(diccionario[paislower]['habitaciones'], options=[1,2,3,4,5,6],index=1)
    banos          = st.selectbox('Baños', options=[1,2,3,4,5,6],index=1)
    if pais.lower()=='chile':
        garajes = st.selectbox(diccionario[paislower]['garajes'], options=[0,1,2,3,4],index=0)
    elif pais.lower()=='colombia':
        garajes = st.selectbox(diccionario[paislower]['garajes'], options=[0,1,2,3,4],index=0)
        
    antiguedad = st.number_input('Antiguedad',min_value=0,max_value=100,value=8)
    estrato    = None
    
    if pais.lower()=='colombia':
        estrato = st.selectbox('Estrato', options=[2,3,4,5,6],index=2)    
        
    if st.button(f'Valorar este {diccionario[paislower]["inmueble"].lower()}'):
        with st.spinner():
            if pais.lower()=='chile':
                direccionformato = f'{direccion.strip()},{comuna},chile'
            elif pais.lower()=='colombia':
                direccionformato = f'{direccion.strip()},{ciudad},colombia'
                
            st.session_state.inputvar = { 'pais': pais,
                         'tipoinmueble': tipoinmueble,
                         'direccion': direccionformato,
                         'areaconstruida': areaconstruida,
                         'habitaciones': habitaciones,
                         'banos': banos,
                         'garajes': garajes,
                         'antiguedad':antiguedad,
                         'tiempoconstruido': tiempodeconstruido(antiguedad)}
            if estrato is not None:
                st.session_state.inputvar.update({'estrato':estrato})
            
            st.session_state.inputvar = inputvar_complemento(st.session_state.inputvar)
            st.session_state.inputvar = forecast(st.session_state.inputvar)
            
            pais           = st.session_state.inputvar['pais']
            tipoinmueble   = st.session_state.inputvar['tipoinmueble']
            codigo         = st.session_state.inputvar['codigo']
            areaconstruida = st.session_state.inputvar['areaconstruida']
            habitaciones   = st.session_state.inputvar['habitaciones']
            banos          = st.session_state.inputvar['banos']
            garajes        = st.session_state.inputvar['garajes']
            st.session_state.inputvar['barrio']       = getinfobarrio(pais,tipoinmueble,codigo,areaconstruida,habitaciones,banos,garajes)
            st.session_state.inputvar['valorizacion'] = getvalorizacion(pais,tipoinmueble,codigo,habitaciones,banos,garajes)
            st.session_state.inputvar['caracterizacion'] = getcaracterizacion(pais,tipoinmueble,codigo)
            
            forecast_venta    = st.session_state.inputvar['forecast_venta']
            forecast_arriendo = st.session_state.inputvar['forecast_arriendo']
            st.session_state.dataventacomp, st.session_state.datarriendocomp = getcomparables(pais,tipoinmueble,codigo,areaconstruida,forecast_venta,forecast_arriendo,habitaciones,banos,garajes)
        
            st.session_state.show_results = True
        
        
#-----------------------------------------------------------------------------#
# Resultados
#-----------------------------------------------------------------------------#
if st.session_state.show_results:

    #-------------------------------------------------------------------------#
    # Caracteristicas del inmueble
    formato = [{"name":diccionario[paislower]['comuna'],"value":st.session_state.inputvar['zona3']},
               {"name":"Barrio","value":st.session_state.inputvar['zona4']},
               {"name":"Dirección","value":st.session_state.inputvar['direccion']},   
               {"name":"Tipo de inmueble","value":tipoinmuebleinicial},
               {"name":"Área construida","value":st.session_state.inputvar['areaconstruida']},
               {"name":f"{diccionario[paislower]['habitaciones']}","value":st.session_state.inputvar['habitaciones']},
               {"name":"Baños","value":st.session_state.inputvar['banos']},
               {"name":f"{diccionario[paislower]['garajes']}","value":st.session_state.inputvar['garajes']},
               {"name":"Antiguedad","value":st.session_state.inputvar['antiguedad']}
               ]

    if estrato is not None: 
        formato.append({"name":"Estrato","value":estrato})
        
    col1, col2 = st.columns([1,2])
    with col1:
        html = ""
        for i in formato:
            if i["value"] is not None and i["value"]!='':
                html += f"""
                    <tr>
                        <td><b>{i["name"]}</b></td>
                        <td><b>{i["value"]}</b></td>
                    </tr>
                """
        
        style = """
        <style>
                #tblStocks {
                  font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;
                  border-collapse: collapse;
                  width: 100%;
                }
                #tblStocks td, #tblStocks th {
                  border: 1px solid #ddd;
                  padding: 8px;
                }
                #tblStocks tr:nth-child(even){background-color: #f2f2f2;}
                #tblStocks tr:hover {background-color: #ddd;}
                #tblStocks th {
                    padding-top: 12px;
                    padding-bottom: 12px;
                    text-align: center;
                    background-color: #294c67;
                    color: white;
                  }
                .tabla {
                  margin-bottom: 50px;
                }  
        </style>
        """
        texto = f"""
        <html>
        {style}
        <body>
            <table id="tblStocks" cellpadding="0" cellspacing="50" class="tabla">
            <tr>
                <th colspan="2">Caracteristicas del inmueble</th>
            </tr>
            {html}
            </table>
        </body>
        </html>
        """
        texto = BeautifulSoup(texto, 'html.parser')
        st.markdown(texto, unsafe_allow_html=True)
                    
        
    #-------------------------------------------------------------------------#
    # Mapa inicial
    with col2:
        initialmap = folium.Map(location=[st.session_state.inputvar["latitud"], st.session_state.inputvar["longitud"]], zoom_start=16,tiles="cartodbpositron")
        folium.Marker(location=[st.session_state.inputvar["latitud"], st.session_state.inputvar["longitud"]], icon=folium.Icon(color='green', icon='fa-circle', prefix='fa')).add_to(initialmap)
        st_map = st_folium(initialmap,width=1000,height=480)
        
    #-------------------------------------------------------------------------#
    # Forecast 
    col1, col2 = st.columns(2)      
    with col1:
        if pais.lower()=='chile':
            forecastventa    = st.session_state.inputvar['forecast_venta']
            forecastarriendo = st.session_state.inputvar['forecast_arriendo']
        elif pais.lower()=='colombia':
            forecastventa    = round(st.session_state.inputvar['forecast_venta']/ 100000) * 100000
            forecastarriendo = round(st.session_state.inputvar['forecast_arriendo']/ 1000) * 1000

        forecastventa = f"${forecastventa:,.0f} {diccionario[paislower]['currency']}"
        label         = 'Valor estimado'
        html          = boxkpi(forecastventa,label)
        html_struct   = BeautifulSoup(html, 'html.parser')
        st.markdown(html_struct, unsafe_allow_html=True)
        
    with col2:
        forecastventa = f"${forecastarriendo:,.0f} {diccionario[paislower]['currency']}"
        label         = 'Renta estimada mensual'
        html          = boxkpi(forecastventa,label)
        html_struct   = BeautifulSoup(html, 'html.parser')
        st.markdown(html_struct, unsafe_allow_html=True)
        
    #-------------------------------------------------------------------------#
    # Analisis de inmuebles en venta
    analysis_by_business(st.session_state.inputvar,'Venta',tipoinmueble,pais,st.session_state.dataventacomp,diccionario)

    #-------------------------------------------------------------------------#
    # Analisis de inmuebles en arriendo
    analysis_by_business(st.session_state.inputvar,'Arriendo',tipoinmueble,pais,st.session_state.datarriendocomp,diccionario)
