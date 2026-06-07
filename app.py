import streamlit as st
import yt_dlp
import re
import os
import tempfile
import zipfile

URL_DA_LOGO = "https://i.postimg.cc/dt63gCnc/Vidy-Logo.png"

st.set_page_config(page_title="Vidy Downloader v2", page_icon=URL_DA_LOGO, layout="centered")

# BUSCA A SENHA NOS SECRETS DO STREAMLIT (NUVEM OU LOCAL)
SENHA_CORRETA = st.secrets["MINHA_SENHA_SECRETA"]

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
st.warning("""🚨 AVISO DE SEGURANÇA E PRIVACIDADE:

Este é um app privado só para você. NÃO compartilhe este link com ninguém!🔗🚫

JAMAIS baixe vídeos com direitos autorais! 🚧

Saiba mais sobre direitos autorias 👉 https://vimeo.com/1199219472?share=copy&fl=sv&fe=ci""")

st.image(URL_DA_LOGO, use_container_width=True)
st.markdown("<h1 style='text-align: center; color: #1E90FF;'>🚀 Vidy Downloader v2</h1>", unsafe_allow_html=True)
st.write("---")

if "processado" not in st.session_state:
    st.session_state.processado = False
if "caminho_arquivo" not in st.session_state:
    st.session_state.caminho_arquivo = ""
if "nome_arquivo" not in st.session_state:
    st.session_state.nome_arquivo = ""

url = st.text_input("Cole a URL do YouTube aqui:", placeholder="https://youtube.com...")

# CONFIGURAÇÕES DE FORMATO E QUALIDADE
col1, col2 = st.columns(2)
with col1:
    formato = st.selectbox("Formato desejado:", ["Video (MP4)", "Audio (MP3)"])
with col2:
    resolucao = st.selectbox("Resolução máxima (Apenas Vídeo):", ["Maxima Qualidade (Ate 4K/8K)", "720p (HD)", "480p (Standard)"])

# 🎶 CONFIGURAÇÃO DE PLAYLIST
st.markdown("### 🎶 Configuração de Playlist")
eh_playlist = st.checkbox("Baixar a PLAYLIST INTEIRA (Se o link contiver uma)", value=False)

st.write("")

if st.button("🚀 Iniciar Processamento", use_container_width=True):
    if not url:
        st.error("Por favor, insira uma URL válida do YouTube!")
    elif not re.match(r"^(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+", url.strip()):
        st.error("🚨 Link inválido! Por segurança, este aplicativo aceita apenas URLs oficiais do YouTube.")
    else:
        st.session_state.processado = False
        status_info = st.info("Processando o download direto nos servidores... Aguarde.")
        
        # Criação estável de diretório temporário
        if "temp_dir" not in st.session_state or not os.path.exists(st.session_state.temp_dir):
            st.session_state.temp_dir = tempfile.mkdtemp()
            
        extensao = "mp4" if formato == "Video (MP4)" else "mp3"
        
        # Filtros de qualidade
        filtro_video = "bv*+ba/b"
        if resolucao == "720p (HD)":
            filtro_video = "bv*[height<=720]+ba/b[height<=720]"
        elif resolucao == "480p (Standard)":
            filtro_video = "bv*[height<=480]+ba/b[height<=480]"

        # Opções nativas do yt-dlp totalmente reformuladas
        ydl_opts = {
            'outtmpl': os.path.join(st.session_state.temp_dir, '%(title)s.%(ext)s'),
            'ignoreerrors': True,
            'noplaylist': not eh_playlist,
            'quiet': True,
            'no_warnings': True,
        }
        
        if formato == "Video (MP4)":
            ydl_opts['format'] = filtro_video
            ydl_opts['merge_output_format'] = 'mp4'
        else:
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '0',
            }, {
                'key': 'FFmpegEmbedThumbnail',
            }]

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url.strip(), download=True)
                
                # 📦 TRATAMENTO DE PLAYLIST (ZIP)
                if eh_playlist:
                    titulo_playlist = info_dict.get('title', 'Playlist_Vidy') if info_dict else 'Playlist_Vidy'
                    titulo_limpo = re.sub(r'[/\\\\?%*:|"<>.]', '', titulo_playlist)
                    
                    st.session_state.nome_arquivo = f"Playlist_{titulo_limpo}.zip"
                    st.session_state.caminho_arquivo = os.path.join(st.session_state.temp_dir, st.session_state.nome_arquivo)
                    
                    arquivos_baixados = [os.path.join(st.session_state.temp_dir, f) for f in os.listdir(st.session_state.temp_dir) if f.endswith(extensao)]
                    if arquivos_baixados:
                        with zipfile.ZipFile(st.session_state.caminho_arquivo, 'w') as zipf:
                            for arq in arquivos_baixados:
                                zipf.write(arq, os.path.basename(arq))
                                os.remove(arq)
                
                # 🎥 TRATAMENTO DE VÍDEO/ÁUDIO ÚNICO
                else:
                    arquivos_na_pasta = os.listdir(st.session_state.temp_dir)
                    arquivo_encontrado = None
                    
                    # Procura o arquivo gerado na pasta temporária de forma dinâmica
                    for f in arquivos_na_pasta:
                        if f.endswith(extensao) and not f.endswith('.zip'):
                            arquivo_encontrado = f
                            break
                    
                    if arquivo_encontrado:
                        st.session_state.caminho_arquivo = os.path.join(st.session_state.temp_dir, arquivo_encontrado)
                        st.session_state.nome_arquivo = arquivo_encontrado
                    else:
                        # Fallback seguro caso o nome falhe
                        titulo_video = info_dict.get('title', 'Vidy_Download') if info_dict else 'Vidy_Download'
                        titulo_limpo = re.sub(r'[/\\\\?%*:|"<>.]', '', titulo_video)
                        st.session_state.nome_arquivo = f"{titulo_limpo}.{extensao}"

            if os.path.exists(st.session_state.caminho_arquivo):
                st.session_state.processado = True
                st.rerun()
            else:
                st.error("O arquivo foi baixado, mas não pôde ser movido. Tente novamente.")
        except Exception as e:
            st.error(f"Erro de processamento nos servidores: {str(e)}")

# BOTÃO DE DOWNLOAD FINAL
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
