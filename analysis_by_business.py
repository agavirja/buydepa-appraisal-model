import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import numpy as np
import plotly.express as px
from bs4 import BeautifulSoup
from shapely.geometry import Polygon,mapping

from datafunctions import getpolygon
from html_scripts import boxkpisecond

@st.experimental_memo
def convert_df(df):
   return df.to_csv(index=False).encode('utf-8')

@st.experimental_memo
def circle_polygon(metros,lat,lng):
    grados   = np.arange(-180, 190, 10)
    Clat     = ((metros/1000.0)/6371.0)*180/np.pi
    Clng     = Clat/np.cos(lat*np.pi/180.0)
    theta    = np.pi*grados/180.0
    longitud = lng + Clng*np.cos(theta)
    latitud  = lat + Clat*np.sin(theta)
    return Polygon([[x, y] for x,y in zip(longitud,latitud)])

def style_function(feature):
    return {
        'fillColor': '#ffaf00',
        'color': 'blue',
        'weight': 0, 
        #'dashArray': '5, 5'
    }    

def analysis_by_business(inputvar,tiponegocio,tipoinmueble,pais,datacomparables,diccionario,metros):
    
    paislower = pais.lower()
    if tiponegocio.lower()=='venta':
        vardep = 'valorventa'
    if tiponegocio.lower()=='arriendo':
        vardep = 'valorarriendo'
        
    
    #-------------------------------------------------------------------------#
    # Mapa comparables 
    st.markdown(f'<div style="background-color: #f2f2f2; border: 1px solid #fff; padding: 0px; margin-bottom: 20px;"><h1 style="margin: 0; font-size: 18px; text-align: center; color: #3A5AFF;">Comparación con inmuebles en <b>{tiponegocio.upper()}</b> en el mismo sector</h1></div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([2,1,1])
    with col1:
        #geojson_data = mapping(getpolygon(inputvar["latitud"], inputvar["longitud"]))
        geojson_data = circle_polygon(metros,inputvar["latitud"], inputvar["longitud"])
        m            = folium.Map(location=[inputvar["latitud"], inputvar["longitud"]], zoom_start=15,tiles="cartodbpositron")
        folium.GeoJson(geojson_data, style_function=style_function).add_to(m)

        img_style = '''
                <style>               
                    .property-image{
                      flex: 1;
                    }
                    img{
                        width:200px;
                        height:120px;
                        object-fit: cover;
                        margin-bottom: 2px; 
                    }
                </style>
                '''
        for i, inmueble in datacomparables.iterrows():
            if isinstance(inmueble['img1'], str) and len(inmueble['img1'])>20: imagen_principal =  inmueble['img1']
            else: imagen_principal = "https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/sin_imagen.png"
            url_export   = f"https://agavirja-buydepa-appraisal-ficha-ficha-1m2ib5.streamlit.app?code={inmueble['id']}&pais={pais.lower()}&tiponegocio={tiponegocio.lower()}&tipoinmueble={tipoinmueble.lower()}" 
            #url_export = ""
            try:    garajes_inmueble = int(inmueble['garajes'])
            except: garajes_inmueble = ""
            
            string_popup = f'''
            <!DOCTYPE html>
            <html>
              <head>
                {img_style}
              </head>
              <body>
                  <div>
                  <a href="{url_export}" target="_blank">
                  <div class="property-image">
                      <img src="{imagen_principal}"  alt="property image" onerror="this.src='https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/sin_imagen.png';">
                  </div>
                  </a>
                  <b> Direccion: {inmueble['direccion']}</b><br>
                  <b> Precio: ${inmueble[vardep]:,.0f}</b><br>
                  <b> Área: {inmueble['areaconstruida']}</b><br>
                  <b> Habitaciones: {int(inmueble['habitaciones'])}</b><br>
                  <b> Baños: {int(inmueble['banos'])}</b><br>
                  <b> Garajes: {garajes_inmueble}</b><br>
                  </div>
              </body>
            </html>
            '''
            folium.Marker(location=[inmueble["latitud"], inmueble["longitud"]], popup=string_popup).add_to(m)
        folium.Marker(location=[inputvar["latitud"], inputvar["longitud"]], icon=folium.Icon(color='green', icon='fa-circle', prefix='fa')).add_to(m)
        st_map = st_folium(m,width=800,height=450)
    
    
    #-------------------------------------------------------------------------#
    # Analisis de barrio
    with col2:
        barrio = pd.DataFrame(inputvar['barrio'])
        
        datapaso = barrio[(barrio['tiponegocio']==tiponegocio.lower()) & (barrio['tipo']=='barrio')]
        if datapaso.empty is False:
            valor  = datapaso['valor'].iloc[0]
            obs    = int(datapaso['obs'].iloc[0])
            if pais.lower()=='colombia': valor = round(valor/ 100000) * 100000
            valor  = f"${valor:,.0f} {diccionario[paislower]['currency']}"
            label  = f"""
            <p>
              Metodo de comparación de mercado<br>
              Muestra: {obs}
            </p>
            """
            html        = boxkpisecond(valor,label)
            html_struct = BeautifulSoup(html, 'html.parser')
            st.markdown(html_struct, unsafe_allow_html=True)
            
        valorizacion = pd.DataFrame(inputvar['valorizacion'])
        datapaso     = valorizacion[(valorizacion['tiponegocio']==tiponegocio.lower()) & (valorizacion['tipo']=='barrio')]
        if datapaso.empty is False:
            valor       = datapaso['valorizacion'].iloc[0]
            valor       = "{:.1%}".format(valor)
            label       = """
            <p>
              Valorización anual<br>
              sector
            </p>
            """            
            html        = boxkpisecond(valor,label)
            html_struct = BeautifulSoup(html, 'html.parser')
            st.markdown(html_struct, unsafe_allow_html=True)        
        
    with col3:
        datapaso = barrio[(barrio['tiponegocio']==tiponegocio.lower()) & (barrio['tipo']=='complemento')]
        if datapaso.empty is False:
            habcomp     = int(datapaso['habitaciones'].iloc[0])
            bancomp     = int(datapaso['banos'].iloc[0])
            obs         = int(datapaso['obs'].iloc[0])
            valor       = datapaso['valor'].iloc[0]
            if pais.lower()=='colombia': valor = round(valor/ 100000) * 100000
            valor       = f"${valor:,.0f} {diccionario[paislower]['currency']}"
            label       = f"""
            <p>
              {habcomp} habitaciones | {bancomp} baños<br>
              Muestra: {obs}
            </p>
            """
            html        = boxkpisecond(valor,label)
            html_struct = BeautifulSoup(html, 'html.parser')
            st.markdown(html_struct, unsafe_allow_html=True)
            
        datapaso = barrio[(barrio['tiponegocio']==tiponegocio.lower()) & (barrio['tipo']=='complemento_garaje')]
        if datapaso.empty is False:
            habcomp     = int(datapaso['habitaciones'].iloc[0])
            bancomp     = int(datapaso['banos'].iloc[0])
            garcomp     = int(datapaso['garajes'].iloc[0])
            obs         = int(datapaso['obs'].iloc[0])
            valor       = datapaso['valor'].iloc[0]
            if pais.lower()=='colombia': valor = round(valor/ 100000) * 100000
            valor       = f"${valor:,.0f} {diccionario[paislower]['currency']}"
            label       = f"""
            <p>
              {habcomp} habitaciones | {bancomp} baños | {garcomp} {diccionario[paislower]['garajes']}<br>
              Muestra: {obs}
            </p>
            """
            html        = boxkpisecond(valor,label)
            html_struct = BeautifulSoup(html, 'html.parser')
            st.markdown(html_struct, unsafe_allow_html=True)            
            
    #-------------------------------------------------------------------------#
    # Carrusel de imagenes
    filtro = st.selectbox('Filtro por:',key=f'filtrar_{tiponegocio}', options=['Sin filtrar','Menor precio','Mayor precio','Menor área','Mayor área','Menor habitaciones','Mayor habitaciones'])
    if filtro=='Menor precio':
        datacomparables = datacomparables.sort_values(by=[vardep],ascending=True)
    if filtro=='Mayor precio':
        datacomparables = datacomparables.sort_values(by=[vardep],ascending=False)
    if filtro=='Menor área':
        datacomparables = datacomparables.sort_values(by=['areaconstruida'],ascending=True)
    if filtro=='Mayor área':
        datacomparables = datacomparables.sort_values(by=['areaconstruida'],ascending=False)

    imagenes = ''
    for i, inmueble in datacomparables.iterrows():
        if isinstance(inmueble['img1'], str) and len(inmueble['img1'])>20: imagen_principal =  inmueble['img1']
        else: imagen_principal = "https://personal-data-bucket-online.s3.us-east-2.amazonaws.com/sin_imagen.png"
        
        try:    garajes_inmueble = f' | <strong>{int(inmueble["garajes"])}</strong> pq'
        except: garajes_inmueble = ""
            
        propertyinfo = f'<strong>{inmueble["areaconstruida"]}</strong> mt<sup>2</sup> | <strong>{int(inmueble["habitaciones"])}</strong> hab | <strong>{int(inmueble["banos"])}</strong> baños {garajes_inmueble}'
        url_export   = f"https://agavirja-buydepa-appraisal-ficha-ficha-1m2ib5.streamlit.app?code={inmueble['id']}&pais={pais.lower()}&tiponegocio={tiponegocio.lower()}&tipoinmueble={tipoinmueble.lower()}" 
        #url_export = ""
        if isinstance(inmueble['direccion'], str): direccion = inmueble['direccion'][0:35]
        else: direccion = '&nbsp'
        imagenes += f'''    
          <div class="propiedad">
            <a href="{url_export}" target="_blank">
            <div class="imagen">
              <img src="{imagen_principal}">
            </div>
            </a>
            <div class="caracteristicas">
              <h3>${inmueble[vardep]:,.0f} {diccionario[paislower]['currency']}</h3>
              <p>{direccion}</p>
              <p>{propertyinfo}</p>
            </div>
          </div>
          '''
        
    style = """
        <style>
          .contenedor-propiedades {
            overflow-x: scroll;
            white-space: nowrap;
            margin-bottom: 40px;
            margin-top: 30px;
          }
          
          .propiedad {
            display: inline-block;
            vertical-align: top;
            margin-right: 20px;
            text-align: center;
            width: 300px;
          }
          
          .imagen {
            height: 200px;
            margin-bottom: 10px;
            overflow: hidden;
          }
          
          .imagen img {
            display: block;
            height: 100%;
            width: 100%;
            object-fit: cover;
          }
          
          .caracteristicas {
            background-color: #f2f2f2;
            padding: 4px;
            text-align: left;
          }
          
          .caracteristicas h3 {
            font-size: 18px;
            margin-top: 0;
          }
          .caracteristicas p {
            font-size: 14px;
            margin-top: 0;
          }
          .caracteristicas p1 {
            font-size: 12px;
            text-align: left;
            width:40%;
            padding: 8px;
            background-color: #294c67;
            color: #ffffff;
            margin-top: 0;
          }
          .caracteristicas p2 {
            font-size: 12px;
            text-align: left;
            width:40%;
            padding: 8px;
            background-color: #008f39;
            color: #ffffff;
            margin-top: 0;
          } 
        </style>
    """
    
    html = f"""
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="UTF-8">
        {style}
      </head>
      <body>
        <div class="contenedor-propiedades">
        {imagenes}
        </div>
      </body>
    </html>
    """
    texto = BeautifulSoup(html, 'html.parser')
    st.markdown(texto, unsafe_allow_html=True)
        
    csv = convert_df(datacomparables)
    st.download_button(
       "Descargar Data",
       csv,
       "data_inmuebles_venta.csv",
       "text/csv",
       key=f'data_inmuebles_{tiponegocio}'
    )
    #-------------------------------------------------------------------------#
    # Graficas
    dataC = pd.DataFrame(inputvar['caracterizacion'])
    
    if dataC.empty is False:
        
        col1, col2 = st.columns(2)
        with col1:
            # Area construida
            st.markdown('<div style="background-color: #f2f2f2; border: 1px solid #fff; padding: 0px; margin-bottom: 20px;"><h1 style="margin: 0; font-size: 18px; text-align: center; color: #3A5AFF;">Área construida</h1></div>', unsafe_allow_html=True)

            df  = dataC[(dataC['tipo']=='areaconstruida') & (dataC['tiponegocio']==tiponegocio.title())]
            df  = df[['valor','variable']]
            if df.empty is False:
                fig = px.bar(df, x='variable', y='valor')
                fig.update_traces(textposition='outside')
                fig.update_layout(
                    plot_bgcolor='rgba(0, 0, 0, 0)',
                    paper_bgcolor='rgba(0, 0, 0, 0)',
                    xaxis_title='',
                    yaxis_title='',
                    legend_title_text=None,
                    showlegend=False,
                    coloraxis_showscale=False,
                    #width=800, 
                    #height=500
                )            
                st.plotly_chart(fig, theme="streamlit",use_container_width=True)
                        
        with col2:
            # Habitaciones
            st.markdown('<div style="background-color: #f2f2f2; border: 1px solid #fff; padding: 0px; margin-bottom: 20px;"><h1 style="margin: 0; font-size: 18px; text-align: center; color: #3A5AFF;">Habitaciones</h1></div>', unsafe_allow_html=True)

            df  = dataC[(dataC['tipo']=='habitaciones') & (dataC['tiponegocio']==tiponegocio.title())]
            df  = df[['valor','variable']]
            df['variable'] = pd.to_numeric(df['variable'],errors='coerce')
            df['variable'] = df['variable'].astype(int)
            if df.empty is False:
                fig = px.bar(df, x='variable', y='valor')
                fig.update_traces(textposition='outside')
                fig.update_layout(
                    plot_bgcolor='rgba(0, 0, 0, 0)',
                    paper_bgcolor='rgba(0, 0, 0, 0)',
                    xaxis_title='',
                    yaxis_title='',
                    legend_title_text=None,
                    showlegend=False,
                    coloraxis_showscale=False,
                    #width=800, 
                    #height=500
                )            
                st.plotly_chart(fig, theme="streamlit",use_container_width=True)
                
        col1, col2 = st.columns(2)
        with col1:
            # Banos
            st.markdown('<div style="background-color: #f2f2f2; border: 1px solid #fff; padding: 0px; margin-bottom: 20px;"><h1 style="margin: 0; font-size: 18px; text-align: center; color: #3A5AFF;">Baños</h1></div>', unsafe_allow_html=True)

            df  = dataC[(dataC['tipo']=='banos') & (dataC['tiponegocio']==tiponegocio.title())]
            df  = df[['valor','variable']]
            df['variable'] = pd.to_numeric(df['variable'],errors='coerce')
            df['variable'] = df['variable'].astype(int)
            if df.empty is False:
                fig = px.bar(df, x='variable', y='valor')
                fig.update_traces(textposition='outside')
                fig.update_layout(
                    plot_bgcolor='rgba(0, 0, 0, 0)',
                    paper_bgcolor='rgba(0, 0, 0, 0)',
                    xaxis_title='',
                    yaxis_title='',
                    legend_title_text=None,
                    showlegend=False,
                    coloraxis_showscale=False,
                    #width=800, 
                    #height=500
                )            
                st.plotly_chart(fig, theme="streamlit",use_container_width=True)

        with col2:
            # Garajes
            st.markdown(f'<div style="background-color: #f2f2f2; border: 1px solid #fff; padding: 0px; margin-bottom: 20px;"><h1 style="margin: 0; font-size: 18px; text-align: center; color: #3A5AFF;">{diccionario[paislower]["garajes"]}</h1></div>', unsafe_allow_html=True)

            df  = dataC[(dataC['tipo']=='garajes') & (dataC['tiponegocio']==tiponegocio.title())]
            df  = df[['valor','variable']]
            df['variable'] = pd.to_numeric(df['variable'],errors='coerce')
            df['variable'] = df['variable'].astype(int)
            if df.empty is False:
                fig = px.bar(df, x='variable', y='valor')
                fig.update_traces(textposition='outside')
                fig.update_layout(
                    plot_bgcolor='rgba(0, 0, 0, 0)',
                    paper_bgcolor='rgba(0, 0, 0, 0)',
                    xaxis_title='',
                    yaxis_title='',
                    legend_title_text=None,
                    showlegend=False,
                    coloraxis_showscale=False,
                    #width=800, 
                    #height=500
                )            
                st.plotly_chart(fig, theme="streamlit",use_container_width=True)
                