import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
import io
import re

st.set_page_config(page_title="Gerador Manual ICHC", layout="wide")

if "fila_etiquetas" not in st.session_state:
    st.session_state.fila_etiquetas = []
if "edit_index" not in st.session_state:
    st.session_state.edit_index = None

st.title("🏷️ Gerador de Etiquetas ICHC")

# --- SEÇÃO 1: CABEÇALHO ---
st.subheader("1. Dados do Paciente")
col_p1, col_p2, col_p3, col_p4 = st.columns(4)
with col_p1: nome_pac = st.text_input("Nome do Paciente", key="pac_nome").upper()
with col_p2: leito_pac = st.text_input("Leito", key="pac_leito").upper()
with col_p3: at_pac = st.text_input("Atendimento", key="pac_at")
with col_p4: nasc_pac = st.text_input("Data de Nasc.", key="pac_nasc")

st.divider()

# --- SEÇÃO 2: FORMULÁRIO DE MEDICAÇÃO ---
st.subheader("2. Dados da Medicação")
c1, c2, c3, c4, c5 = st.columns([2, 1, 1, 1, 1])

idx = st.session_state.edit_index
val_med = st.session_state.fila_etiquetas[idx]["med"] if idx is not None else ""
val_qtd = st.session_state.fila_etiquetas[idx]["qtd_pura"] if idx is not None else ""
val_hora = st.session_state.fila_etiquetas[idx]["hora"] if idx is not None else ""
val_soro_comp = st.session_state.fila_etiquetas[idx].get("soro_comp", "") if idx is not None else ""

with c1: med_nome = st.text_input("Nome e Número", value=val_med)
with c2: med_qtd = st.text_input("Qtd Base (ex: 1000)", value=val_qtd)
with c3: med_un = st.selectbox("Unidade", ["ML", "MG", "UI", "GTS", "COMP", "FRASCO", "BISNAGA", "DOSE"])
with c4: med_via = st.selectbox("Via", ["IV", "IM", "SC", "GTRS", "SNE", "VO", "NASAL", "RETAL", "DERM", "INAL", "IN O", "SL", "VAG", "OTO", "OTOE", "OTOD", "OFT", "OFTE", "OFTD"])
with c5: med_hora = st.text_input("Horário (HH:MM)", value=val_hora)

# --- CAMPOS ESPECIAIS PARA SORO ---
is_soro = any(x in med_nome.upper() for x in ["SF", "GLICOSE", "SORO", "RINGER"])
soro_
