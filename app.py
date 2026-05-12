import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
import io

st.set_page_config(page_title="Gerador Manual ICHC", layout="wide")

# Inicializa estados
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

# Se estiver editando, preenche com os dados antigos
idx = st.session_state.edit_index
val_med = st.session_state.fila_etiquetas[idx]["med"] if idx is not None else ""
val_qtd = st.session_state.fila_etiquetas[idx]["qtd_pura"] if idx is not None else ""
val_hora = st.session_state.fila_etiquetas[idx]["hora"] if idx is not None else ""

with c1: med_nome = st.text_input("Nome e Número", value=val_med)
with c2: med_qtd = st.text_input("Qtd", value=val_qtd)
with c3: med_un = st.selectbox("Unidade", ["mg", "ml", "UI", "gts", "comp", "frasco"])
with c4: med_via = st.selectbox("Via", ["IV", "IM", "SC", "GTRS", "SNE", "VO", "NASAL", "RETAL"])
with c5: med_hora = st.text_input("Horário (HH:MM)", value=val_hora)

col_btn_add, col_btn_can = st.columns([1, 5])
with col_btn_add:
    if idx is None:
        if st.button("➕ Adicionar"):
            if med_nome and med_hora:
                st.session_state.fila_etiquetas.append({
                    "med": med_nome.upper(), "qtd_pura": med_qtd,
                    "dose": f"{med_qtd} {med_un}", "via": med_via, "hora": med_hora
                })
                st.rerun()
    else:
        if st.button("💾 Salvar Alteração"):
            st.session_state.fila_etiquetas[idx] = {
                "med": med_nome.upper(), "qtd_pura": med_qtd,
                "dose": f"{med_qtd} {med_un}", "via": med_via, "hora": med_hora
            }
            st.session_state.edit_index = None
            st.rerun()

with col_btn_can:
    if idx is not None:
        if st.button("❌ Cancelar Edição"):
            st.session_state.edit_index = None
            st.rerun()

st.divider()

# --- SEÇÃO 3: LISTA E EDIÇÃO ---
if st.session_state.fila_etiquetas:
    st.subheader("3. Itens Lançados")
    
    for i, e in enumerate(st.session_state.fila_etiquetas):
        col_txt, col_ed, col_rem = st.columns([4, 1, 1])
        with col_txt:
            st.write(f"**{i+1}.** {e['med']} | {e['dose']} | {e['via']} | **Hs: {e['hora']}**")
        with col_ed:
            if st.button("📝 Editar", key=f"ed_{i}"):
                st.session_state.edit_index = i
                st.rerun()
        with col_rem:
            if st.button("🗑️ Remover", key=f"rem_{i}"):
                st.session_state.fila_etiquetas.pop(i)
                st.rerun()

    # GERAÇÃO DO PDF
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=(70*mm, 30*mm))
    for item in st.session_state.fila_etiquetas:
        c.setFont("Helvetica-Bold", 8)
        c.drawString(2*mm, 25*mm, f"{leito_pac} - {nome_pac[:28]}".upper())
        c.setFont("Helvetica", 7)
        c.drawString(2*mm, 21*mm, f"At: {at_pac} | Nasc: {nasc_pac}")
        c.line(2*mm, 19*mm, 68*mm, 19*mm)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(2*mm, 13*mm, item["med"][:40])
        c.setFont("Helvetica-Bold", 9)
        c.drawString(2*mm, 8*mm, item["dose"])
        c.setFont("Helvetica", 9)
        c.drawString(25*mm, 8*mm, item["via"])
        c.setFont("Helvetica-Bold", 14)
        c.drawRightString(68*mm, 5*mm, f"Hs: {item['hora']}")
        c.showPage()
    c.save()

    st.download_button("📥 BAIXAR ETIQUETAS", buffer.getvalue(), f"Etiquetas_{leito_pac}.pdf", type="primary")
