import streamlit as st
import subprocess
import re
import os
import io
import tempfile
import zipfile

URL_DA_LOGO = "https://i.postimg.cc/dt63gCnc/Vidy-Logo.png"

st.set_page_config(page_title="Vidy Downloader", page_icon=URL_DA_LOGO, layout="centered")

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
Saiba mais sobre direitos autorais 👉 https://vimeo.com/1199219472?share=copy&fl=sv&fe=ci""")

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

# ✂️ CORTAR UM PEDAÇO DO VÍDEO
st.markdown("### ✂️ Cortar um Pedaço (Opcional)")
col_tempo1, col_tempo2 = st.columns(2)
with col_tempo1:
    tempo_inicio = st.text_input("Início (Ex: 00:01:25)", placeholder="Deixe vazio para o início")
with col_tempo2:
    tempo_fim = st.text_input("Fim (Ex: 00:01:47)", placeholder="Deixe vazio para o final")

# 🎶 CONFIGURAÇÃO DE PLAYLIST
st.markdown("### 🎶 Configuração de Playlist")
eh_playlist = st.checkbox("Baixar a PLAYLIST INTEIRA (Se o link contiver uma)", value=False)

st.write("")

if st.button("🚀 Iniciar Processamento", use_container_width=True):
    if not url:
        st.error("Por favor, insira uma URL válida do YouTube!")
    # VALIDAÇÃO INTELIGENTE DE LINK COM REGEX
    elif not re.match(r"^(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+", url.strip()):
        st.error("🚨 Link inválido! Por segurança, este aplicativo aceita apenas URLs oficiais do YouTube.")
    else:
        st.session_state.processado = False
        st.info("Analisando o link e capturando informações...")
        
        # Coleta do título de forma segura (CORRIGIDO)
        try:
            flag_titulo = '--get-filename' if eh_playlist else '--get-title'
            resultado_titulo = subprocess.run(
                ['yt-dlp', flag_titulo, url.strip()], 
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True
            )
            linhas_retorno = resultado_titulo.stdout.strip().split('\n')
            titulo_original = linhas_retorno[0].strip() if linhas_retorno else "Vidy_Download"
            titulo_limpo = re.sub(r'[/\\\\?%*:|"<>.]', '', titulo_original)
        except:
            titulo_limpo = "Vidy_Download"

        extensao = "mp4" if formato == "Video (MP4)" else "mp3"
        
        # Criação de diretório temporário isolado por sessão
        if "temp_dir" not in st.session_state:
            st.session_state.temp_dir = tempfile.mkdtemp()
            
        comando = ['yt-dlp', '--newline', '--ignore-errors', '--embed-metadata', url.strip()]
        
        # Configuração de rotas (Playlist vs Único)
        if not eh_playlist:
            comando.append('--no-playlist')
            nome_final = os.path.join(st.session_state.temp_dir, f"download_{int(os.getpid())}.{extensao}")
            st.session_state.nome_arquivo = f"{titulo_limpo}.{extensao}"
            st.session_state.caminho_arquivo = nome_final
        else:
            comando.append('--yes-playlist')
            nome_final_template = os.path.join(st.session_state.temp_dir, "%(title)s.%(ext)s")
            comando.extend(['-o', nome_final_template])
            st.session_state.nome_arquivo = f"Playlist_{titulo_limpo}.zip"
            st.session_state.caminho_arquivo = os.path.join(st.session_state.temp_dir, st.session_state.nome_arquivo)

        # Filtros de Resolução de Vídeo
        filtro_video = "bv*+ba/b"
        if resolucao == "720p (HD)":
            filtro_video = "bv*[height<=720]+ba/b[height<=720]"
        elif resolucao == "480p (Standard)":
            filtro_video = "bv*[height<=480]+ba/b[height<=480]"

        if formato == "Video (MP4)":
            comando.extend(['-f', filtro_video, '--merge-output-format', 'mp4'])
        else:
            comando.extend(['-x', '--audio-format', 'mp3', '--audio-quality', '0', '--embed-thumbnail'])

        # Se houver solicitação de corte, o yt-dlp baixará o vídeo completo primeiro
        precisa_cortar = (tempo_inicio or tempo_fim) and not eh_playlist
        if precisa_cortar:
            nome_baixar = os.path.join(st.session_state.temp_dir, f"download_completo_{int(os.getpid())}.{extensao}")
            comando.extend(['-o', nome_baixar])
        elif not eh_playlist:
            comando.extend(['-o', nome_final])

        # Execução do download com a barra de progresso
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
        
        # ✂️ EXECUÇÃO DO CORTE SEGURO COM FFMEG INDEPENDENTE (CORREGIDO)
        if precisa_cortar:
            if os.path.exists(nome_baixar):
                status_progresso.text("Cortando o arquivo no intervalo selecionado...")
                
                def para_segundos(tempo_str):
                    if not tempo_str: return None
                    unidades = list(map(int, tempo_str.strip().split(':')))
                    if len(unidades) == 3:  # hh:mm:ss
                        return unidades[0] * 3600 + unidades[1] * 60 + unidades[2]
                    elif len(unidades) == 2:  # mm:ss
                        return unidades[0] * 60 + unidades[1]
                    return unidades[0]

                seg_inicio = para_segundos(tempo_inicio) if tempo_inicio else 0
                seg_fim = para_segundos(tempo_fim) if tempo_fim else None
                
                cmd_corte = ['ffmpeg', '-y', '-ss', str(seg_inicio)]
                if seg_fim:
                    cmd_corte.extend(['-t', str(seg_fim - seg_inicio)])
                
                cmd_corte.extend(['-i', nome_baixar, '-c', 'copy', nome_final])
                subprocess.run(cmd_corte, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                if os.path.exists(nome_baixar):
                    os.remove(nome_baixar)

        # Compactação em ZIP se for download de Playlist inteira
        if eh_playlist:
            arquivos_baixados = [os.path.join(st.session_state.temp_dir, f) for f in os.listdir(st.session_state.temp_dir) if f.endswith(extensao) and not f.startswith("download_")]
            if arquivos_baixados:
                with zipfile.ZipFile(st.session_state.caminho_arquivo, 'w') as zipf:
                    for arq in arquivos_baixados:
                        zipf.write(arq, os.path.basename(arq))
                        os.remove(arq)

        if os.path.exists(st.session_state.caminho_arquivo):
            st.session_state.processado = True
            st.rerun()
        else:
            st.error("Erro ao gerar o arquivo de mídia. Verifique se o link ou os tempos de corte estão corretos.")

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
