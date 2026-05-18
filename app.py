import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
import io
import re

st.set_page_config(page_title="Gerador Manual ICHC", layout="wide")

# Inicializa estados essenciais para a fila e edição
if "fila_etiquetas" not in st.session_state:
    st.session_state.fila_etiquetas = []
if "edit_index" not in st.session_state:
    st.session_state.edit_index = None

# Inicializa chaves do formulário no session_state para permitir limpeza instantânea
if "f_med" not in st.session_state: st.session_state.f_med = ""
if "f_qtd" not in st.session_state: st.session_state.f_qtd = ""
if "f_hora" not in st.session_state: st.session_state.f_hora = ""
if "f_soro" not in st.session_state: st.session_state.f_soro = ""

st.title("🏷️ Gerador de Etiquetas ICHC")

# --- SEÇÃO 1: CABEÇALHO DO PACIENTE ---
st.subheader("1. Dados do Paciente")
col_p1, col_p2, col_p3, col_p4 = st.columns(4)
with col_p1: nome_pac = st.text_input("Nome do Paciente", key="pac_nome").upper()
with col_p2: leito_pac = st.text_input("Leito", key="pac_leito").upper()
with col_p3: at_pac = st.text_input("Atendimento", key="pac_at")
with col_p4: nasc_pac = st.text_input("Data de Nasc.", key="pac_nasc")

st.divider()

# --- SEÇÃO 2: FORMULÁRIO DE MEDICAÇÃO (VISUAL LADO A LADO + TEMPO REAL) ---
st.subheader("2. Dados da Medicação")

idx = st.session_state.edit_index

if idx is not None:
    st.warning(f"⚠️ Editando o item {idx + 1} da lista")

# 5 Campos perfeitamente alinhados lado a lado
c1, c2, c3, c4, c5 = st.columns([2, 1, 1, 1, 1])

with c1: med_nome = st.text_input("Nome e Número", key="f_med")
with c2: med_qtd = st.text_input("Qtd Base (ex: 1000)", key="f_qtd")
with c3: med_un = st.selectbox("Unidade", ["ML", "MG", "UI", "GTS", "COMP", "FRASCO", "BISNAGA", "DOSE"], key="f_un")
with c4: med_via = st.selectbox("Via", ["IV", "IM", "SC", "GTRS", "SNE", "VO", "NASAL", "RETAL", "DERM", "INAL", "IN O", "SL", "VAG", "OTO", "OTOE", "OTOD", "OFT", "OFTE", "OFTD"], key="f_via")
with c5: med_hora = st.text_input("Horário (HH:MM)", key="f_hora")

# Lista expandida: monitora em tempo real com espaço ou tudo colado
termos_soro = [
    "SF 0,9%", "SF0,9%", 
    "SG 5%", "SG5%", 
    "SG 10%", "SG10%", 
    "SORO FISIOLÓGICO 0,9%", "SORO FISIOLOGICO 0,9%", 
    "SORO GLICOSADO 5%", "SORO GLICOSADO 10%"
]
deve_mostrar_aditivos = any(termo in med_nome.upper() for termo in termos_soro)

# A caixinha de aditivos aparece SOZINHA na tela assim que o usuário digita a última letra, sem Enter!
soro_comp = ""
if deve_mostrar_aditivos:
    st.info("🧪 Soro identificado! Informe os aditivos abaixo:")
    soro_comp = st.text_area("Aditivos / Complemento", key="f_soro", placeholder="Ex: cloreto de SODIO 20% - amp 10ml")

# Função interna para zerar as caixas de texto com segurança
def limpar_tudo():
    st.session_state.f_med = ""
    st.session_state.f_qtd = ""
    st.session_state.f_hora = ""
    st.session_state.f_soro = ""

# Área de botões de salvamento
st.write("")
col_btn1, col_btn2 = st.columns([1.5, 5])

with col_btn1:
    if idx is None:
        if st.button("➕ Adicionar na Lista", type="primary", use_container_width=True):
            if med_nome and med_hora:
                vol_final = med_qtd
                if deve_mostrar_aditivos and soro_comp:
                    try:
                        aditivos_ml = re.findall(r'(\d+)\s*ml', soro_comp.lower())
                        soma_aditivos = sum(int(v) for v in aditivos_ml)
                        vol_final = str(int(med_qtd) + soma_aditivos)
                    except:
                        vol_final = med_qtd

                st.session_state.fila_etiquetas.append({
                    "med": med_nome.upper(), "qtd_pura": med_qtd,
                    "dose": f"{vol_final} {med_un}", 
                    "via": "" if "DEXTRO" in med_nome.upper() else med_via, 
                    "hora": med_hora, "soro_comp": soro_comp if deve_mostrar_aditivos else ""
                })
                limpar_tudo()
                st.rerun()
    else:
        if st.button("💾 Salvar Alteração", type="primary", use_container_width=True):
            if med_nome and med_hora:
                vol_final = med_qtd
                if deve_mostrar_aditivos and soro_comp:
                    try:
                        aditivos_ml = re.findall(r'(\d+)\s*ml', soro_comp.lower())
                        soma_aditivos = sum(int(v) for v in aditivos_ml)
                        vol_final = str(int(med_qtd) + soma_aditivos)
                    except:
                        vol_final = med_qtd

                st.session_state.fila_etiquetas[idx] = {
                    "med": med_nome.upper(), "qtd_pura": med_qtd,
                    "dose": f"{vol_final} {med_un}", "via": med_via, "hora": med_hora,
                    "soro_comp": soro_comp if deve_mostrar_aditivos else ""
                }
                st.session_state.edit_index = None
                st.session_state.med_para_editar = None
                limpar_tudo()
                st.rerun()

with col_btn2:
    if idx is not None:
        if st.button("❌ Cancelar Edição", use_container_width=False):
            st.session_state.edit_index = None
            st.session_state.med_para_editar = None
            limpar_tudo()
            st.rerun()

st.divider()

# --- SEÇÃO 3: LISTA LANÇADOS (EDITAR/EXCLUIR) ---
if st.session_state.fila_etiquetas:
    st.subheader("3. Itens Lançados")
    
    for i, e in enumerate(st.session_state.fila_etiquetas):
        c_txt, c_ed, c_rem = st.columns([4, 0.5, 0.5])
        with c_txt:
            st.write(f"**{i+1}.** {e['med']} | {e['dose']} | {e['via']} | **Hs: {e['hora']}**")
        with c_ed:
            if st.button("📝", key=f"btn_ed_{i}"):
                st.session_state.edit_index = i
                # Injeta com total estabilidade os dados salvos de volta nas caixas de texto
                st.session_state.f_med = e["med"]
                st.session_state.f_qtd = e["qtd_pura"]
                st.session_state.f_hora = e["hora"]
                st.session_state.f_soro = e.get("soro_comp", "")
                st.rerun()
        with c_rem:
            if st.button("🗑️", key=f"btn_rem_{i}"):
                if st.session_state.edit_index == i:
                    st.session_state.edit_index = None
                    limpar_tudo()
                st.session_state.fila_etiquetas.pop(i)
                st.rerun()

    st.write("---")

    # GERAÇÃO DO PDF
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=(70*mm, 30*mm))
    for item in st.session_state.fila_etiquetas:
        c.setFont("Helvetica-Bold", 8)
        c.drawString(2*mm, 25*mm, f"{leito_pac} - {nome_pac[:28]}".upper())
        c.setFont("Helvetica", 7)
        c.drawString(2*mm, 21*mm, f"At: {at_pac} | Nasc: {nasc_pac}")
        c.line(2*mm, 19*mm, 68*mm, 19*mm)
        
        if item.get("soro_comp"):
            c.setFont("Helvetica-Bold", 8)
            c.drawString(2*mm, 16.5*mm, f"{item['med']} {item['dose']}"[:45])
            c.setFont("Helvetica", 6)
            text_obj = c.beginText(2*mm, 13*mm)
            text_obj.setLeading(7)
            for linha in item["soro_comp"].split('\n'):
                text_obj.textLine(linha[:65])
            c.drawText(text_obj)
        else:
            c.setFont("Helvetica-Bold", 10)
            c.drawString(2*mm, 14*mm, item["med"][:40])
            c.setFont("Helvetica-Bold", 9)
            c.drawString(2*mm, 9*mm, item["dose"])
            c.setFont("Helvetica", 9)
            c.drawString(25*mm, 9*mm, item["via"])
        
        c.setFont("Helvetica-Bold", 14)
        c.drawRightString(68*mm, 5*mm, f"Hs: {item['hora']}")
        c.showPage()
    c.save()

    col_f1, col_f2 = st.columns([2, 1])
    with col_f1:
        st.download_button("📥 BAIXAR ETIQUETAS", buffer.getvalue(), f"Etiquetas_{leito_pac}.pdf", type="primary")
    with col_f2:
        if st.button("🗑️ LIMPAR LISTA COMPLETA"):
            st.session_state.fila_etiquetas = []
            st.session_state.edit_index = None
            limpar_tudo()
            st.rerun()
