import streamlit as st
import subprocess
import re
import os
import io

URL_DA_LOGO = "https://i.postimg.cc/rFLbQtsS/Screenshot-2026-05-27-12-09-42.png"

st.set_page_config(page_title="Vidy Downloader", page_icon=URL_DA_LOGO, layout="centered")

# SENHA FIXA DE SEGURANÇA PARA A NUVEM
SENHA_CORRETA = "441.828.315-4"

if "logado" not in st.session_state:
    st.session_state.logado = False

# TELA DE LOGIN
if not st.session_state.logado:
    st.image(URL_DA_LOGO, use_container_width=True)
    st.markdown("<h2 style='text-align: center; color: #1E90FF;'>🔐 Área Restrita do Vidy</h2>", unsafe_allow_html=True)
    st.write("---")
    
    usuario_input = st.text_input("Nome do Usuário:")
    senha_input = st.text_input("Senha de Acesso:", type="password")
    
    if st.button("🔓 Entrar no Aplicativo", use_container_width=True):
        if usuario_input and senha_input == SENHA_CORRETA:
            st.session_state.logado = True
            st.success("Acesso concedido! Carregando o app...")
            st.rerun()
        else:
            st.error("Usuário ou Senha incorretos!")
    st.stop()

# INTERFACE DO APP COMPLETO
st.warning("🚨 AVISO DE PRIVACIDADE:

           Este é um app privado só para você. NÃO compartilhe este link com ninguém!🔗🚫
           
           JAMAIS baixe vídeos com direitos autorais!🧑‍✈🚧
           
           Siga essas regras e aproveite o seu app!👋👍")
st.image(URL_DA_LOGO, use_container_width=True)
st.markdown("<h1 style='text-align: center; color: #1E90FF;'>🚀 Vidy Downloader</h1>", unsafe_allow_html=True)
st.write("---")

if "processado" not in st.session_state:
    st.session_state.processado = False
if "caminho_arquivo" not in st.session_state:
    st.session_state.caminho_arquivo = ""
if "nome_arquivo" not in st.session_state:
    st.session_state.nome_arquivo = ""

url = st.text_input("Cole a URL do YouTube aqui (Vídeo ou Playlist):", placeholder="https://youtube.com...")

col1, col2 = st.columns(2)
with col1:
    formato = st.selectbox("Formato desejado:", ["Video (MP4)", "Audio (MP3)"])
with col2:
    resolucao = st.selectbox("Resolução máxima (Apenas para Vídeo):", ["Maxima Qualidade (Ate 4K/8K)", "720p (HD)", "480p (Standard)"])

st.write("")

if st.button("🚀 Iniciar Processamento", use_container_width=True):
    if not url:
        st.error("Por favor, insira uma URL válida do YouTube!")
    else:
        st.session_state.processado = False
        st.info("Analisando o link e capturando informações originais...")
        
        try:
            resultado_titulo = subprocess.run(
                ['yt-dlp', '--get-title', url], 
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True
            )
            titulo_original = resultado_titulo.stdout.strip()
            titulo_limpo = re.sub(r'[/\\\\?%*:|"<>.]', '', titulo_original)
        except:
            titulo_limpo = "Vidy_Download"

        extensao = "mp4" if formato == "Video (MP4)" else "mp3"
        nome_final = f"download_temporario.{extensao}"
        
        st.session_state.nome_arquivo = f"{titulo_limpo}.{extensao}"
        st.session_state.caminho_arquivo = nome_final
        
        if os.path.exists(nome_final):
            os.remove(nome_final)
            
        comando = ['yt-dlp', '--newline', '--ignore-errors', '--embed-metadata', '-o', nome_final, url]
        
        if resolucao == "720p (HD)":
            filtro_video = "bv*[height<=720]+ba/b[height<=720]"
        elif resolucao == "480p (Standard)":
            filtro_video = "bv*[height<=480]+ba/b[height<=480]"
        else:
            filtro_video = "bv*+ba/b"

        if formato == "Video (MP4)":
            comando[1:1] = ['-f', filtro_video, '--merge-output-format', 'mp4']
        else:
            comando[1:1] = ['-x', '--audio-format', 'mp3', '--audio-quality', '0', '--embed-thumbnail']

        processo = subprocess.Popen(comando, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        
        status_progresso = st.empty()
        barra_progresso = st.progress(0)
        
        ultimo_valor = 0
        for linha in processo.stdout:
            if "[download]" in linha and "%" in linha:
                try:
                    partes = linha.split()
                    for p in partes:
                        if "%" in p:
                            porcentagem = float(p.replace("%", ""))
                            progresso_int = int(porcentagem)
                            if progresso_int > ultimo_valor:
                                barra_progresso.progress(progresso_int / 100.0)
                                status_progresso.text(f"Progresso atual: {progresso_int}%")
                                ultimo_valor = progresso_int
                            break
                except:
                    pass

        processo.wait()
        
        if os.path.exists(nome_final):
            st.session_state.processado = True
            st.rerun()
        else:
            st.error("Erro ao gerar o arquivo de mídia.")

if st.session_state.processado and os.path.exists(st.session_state.caminho_arquivo):
    st.success(f"✨ Pronto! Pronto para baixar: {st.session_state.nome_arquivo}")
    with open(st.session_state.caminho_arquivo, "rb") as f:
        st.download_button(
            label="💾 CLIQUE AQUI PARA SALVAR NO SEU DISPOSITIVO",
            data=f.read(),
            file_name=st.session_state.nome_arquivo,
            mime="application/octet-stream",
            use_container_width=True
        )
