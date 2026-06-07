import streamlit as st
import subprocess
import re
import os
import io
import tempfile
import zipfile  # Nova biblioteca para compactar playlists

URL_DA_LOGO = "https://i.postimg.cc/dt63gCnc/Vidy-Logo.png"

st.set_page_config(page_title="Vidy Downloader", page_icon=URL_DA_LOGO, layout="centered")

# BUSCA A SENHA NOS SECRETS DA NUVEM
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

JAMAIS baixe vídeos com direitos autorais!🧑‍✈🚧""")

st.warning("""Saiba mais sobre direitos autorais aqui 👉 https://vimeo.com/1199219472?share=copy&fl=sv&fe=ci""")
st.image(URL_DA_LOGO, use_container_width=True)
st.markdown("<h1 style='text-align: center; color: #1E90FF;'>🚀 Vidy Downloader</h1>", unsafe_allow_html=True)
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

# ✂️ RECURSO 2: RECORTE DE TRECHOS
st.markdown("### ✂️ Cortar um Pedaço (Opcional)")
col_tempo1, col_tempo2 = st.columns(2)
with col_tempo1:
    tempo_inicio = st.text_input("Início (Ex: 00:01:20)", placeholder="Deixe vazio para o início")
with col_tempo2:
    tempo_fim = st.text_input("Fim (Ex: 00:01:35)", placeholder="Deixe vazio para o final")

# 🎶 RECURSO 1: CONFIGURAÇÃO DE PLAYLIST
st.markdown("### 🎶 Configuração de Playlist")
eh_playlist = st.checkbox("Baixar a PLAYLIST INTEIRA (Se o link contiver uma)", value=False)

st.write("")

if st.button("🚀 Iniciar Processamento", use_container_width=True):
    if not url:
        st.error("Por favor, insira uma URL válida do YouTube!")
    elif not url.strip().startswith(("https://youtube.com", "https://youtube.com", "https://youtu.be", "http://youtube.com", "http://youtube.com", "http://youtu.be")):
        st.error("🚨 Link inválido! Por segurança, este aplicativo aceita apenas URLs oficiais do YouTube.")
    else:
        st.session_state.processado = False
        st.info("Analisando o link e capturando informações...")
        
        # Define se vai capturar título individual ou da playlist
                # Define se vai capturar título individual ou da playlist
        try:
            flag_titulo = '--get-filename' if eh_playlist else '--get-title'
            resultado_titulo = subprocess.run(
                ['yt-dlp', flag_titulo, url], 
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True
            )
            # Pegamos o primeiro item da lista gerada pelo split e removemos os espaços
            titulo_original = resultado_titulo.stdout.split('\n')[0].strip()
            titulo_limpo = re.sub(r'[/\\\\?%*:|"<>.]', '', titulo_original)
        except:
            titulo_limpo = "Vidy_Download"


        extensao = "mp4" if formato == "Video (MP4)" else "mp3"
        
        if "temp_dir" not in st.session_state:
            st.session_state.temp_dir = tempfile.mkdtemp()
            
        # Parâmetros base do comando yt-dlp
        comando = ['yt-dlp', '--newline', '--ignore-errors', '--embed-metadata', url]
        
        # Aplica regra de Playlist ou Vídeo Único
        if not eh_playlist:
            comando.append('--no-playlist')
            nome_final = os.path.join(st.session_state.temp_dir, f"download_{int(os.getpid())}.{extensao}")
            comando.extend(['-o', nome_final])
            st.session_state.nome_arquivo = f"{titulo_limpo}.{extensao}"
            st.session_state.caminho_arquivo = nome_final
        else:
            comando.append('--yes-playlist')
            # Para playlist, salvamos com o título original de cada vídeo mapeado temporariamente
            nome_final_template = os.path.join(st.session_state.temp_dir, "%(title)s.%(ext)s")
            comando.extend(['-o', nome_final_template])
            st.session_state.nome_arquivo = f"Playlist_{titulo_limpo}.zip"
            st.session_state.caminho_arquivo = os.path.join(st.session_state.temp_dir, st.session_state.nome_arquivo)

        # Filtros de qualidade
        filtro_video = "bv*+ba/b"
        if resolucao == "720p (HD)":
            filtro_video = "bv*[height<=720]+ba/b[height<=720]"
        elif resolucao == "480p (Standard)":
            filtro_video = "bv*[height<=480]+ba/b[height<=480]"

        if formato == "Video (MP4)":
            comando.extend(['-f', filtro_video, '--merge-output-format', 'mp4'])
        else:
            comando.extend(['-x', '--audio-format', 'mp3', '--audio-quality', '0', '--embed-thumbnail'])

        # Aplica o Recorte de Pedaço (Apenas se o usuário preencheu e NÃO for playlist inteira)
        if (tempo_inicio or tempo_fim) and not eh_playlist:
            t_inicio = tempo_inicio if tempo_inicio else "00:00:00"
            t_fim = tempo_fim if tempo_fim else "inf"
            comando.extend(['--download-sections', f"*{t_inicio}-{t_fim}"])

        # Executa o download
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
        
        # Se for playlist, junta todos os arquivos gerados na pasta em um único ZIP
        if eh_playlist:
            arquivos_baixados = [os.path.join(st.session_state.temp_dir, f) for f in os.listdir(st.session_state.temp_dir) if f.endswith(extensao)]
            if arquivos_baixados:
                with zipfile.ZipFile(st.session_state.caminho_arquivo, 'w') as zipf:
                    for arq in arquivos_baixados:
                        zipf.write(arq, os.path.basename(arq))
                        os.remove(arq) # Apaga o arquivo individual para limpar o servidor

        if os.path.exists(st.session_state.caminho_arquivo):
            st.session_state.processado = True
            st.rerun()
        else:
            st.error("Erro ao gerar o arquivo de mídia. Verifique se o link ou os tempos de corte estão corretos.")

# BOTÃO DE DOWNLOAD
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
