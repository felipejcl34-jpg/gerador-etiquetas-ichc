import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
import io

# Configuração da página
st.set_page_config(page_title="Gerador Manual ICHC", layout="wide")

# Inicializa a lista de etiquetas na memória do navegador
if "fila_etiquetas" not in st.session_state:
    st.session_state.fila_etiquetas = []

st.title("🏷️ Gerador de Etiquetas ICHC (Manual)")

# --- SEÇÃO 1: CABEÇALHO (O que você quer manter igual) ---
st.subheader("1. Dados do Paciente (Cabeçalho)")
col_p1, col_p2, col_p3, col_p4 = st.columns(4)
with col_p1: nome_pac = st.text_input("Nome do Paciente", placeholder="Ex: MARILIA LOPES...")
with col_p2: leito_pac = st.text_input("Leito", placeholder="Ex: 03CAM07")
with col_p3: at_pac = st.text_input("Atendimento", placeholder="Ex: 10344393")
with col_p4: nasc_pac = st.text_input("Data de Nasc.", placeholder="Ex: 21/09/1973")

st.divider()

# --- SEÇÃO 2: CORPO DA ETIQUETA (O que você vai preencher) ---
st.subheader("2. Dados da Medicação")
c1, c2, c3, c4, c5 = st.columns([2, 1, 1, 1, 1])

with c1: med_nome = st.text_input("Nome da Medicação (e número)")
with c2: med_qtd = st.text_input("Qtd")
with c3: med_un = st.selectbox("Unidade", ["mg", "ml", "UI", "gts", "comp", "frasco"])
with c4: med_via = st.selectbox("Via", ["IV", "IM", "SC", "GTRS", "SNE", "VO", "NASAL", "RETAL"])
with c5: med_hora = st.text_input("Horário", placeholder="Ex: 22:00")

if st.button("➕ Adicionar Medicação à Lista"):
    if med_nome and med_hora:
        nova_med = {
            "med": med_nome.upper(),
            "dose": f"{med_qtd} {med_un}",
            "via": med_via,
            "hora": med_hora
        }
        st.session_state.fila_etiquetas.append(nova_med)
        st.success(f"Adicionado: {med_nome} às {med_hora}")
    else:
        st.error("Preencha pelo menos o Nome e o Horário!")

st.divider()

# --- SEÇÃO 3: FILA E GERAÇÃO DO PDF ---
if st.session_state.fila_etiquetas:
    st.subheader("3. Etiquetas na Fila")
    
    for i, e in enumerate(st.session_state.fila_etiquetas):
        st.write(f"**{i+1}.** {e['med']} | {e['dose']} | {e['via']} | **Hs: {e['hora']}**")
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        if st.button("🗑️ Limpar Lista", type="secondary"):
            st.session_state.fila_etiquetas = []
            st.rerun()
            
    with col_f2:
        # GERAR O PDF
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=(70*mm, 30*mm))
        
        for item in st.session_state.fila_etiquetas:
            # CABEÇALHO (Idêntico ao aprovado)
            c.setFont("Helvetica-Bold", 8)
            c.drawString(2*mm, 25*mm, f"{leito_pac} - {nome_pac[:28]}".upper())
            c.setFont("Helvetica", 7)
            c.drawString(2*mm, 21*mm, f"At: {at_pac} | Nasc: {nasc_pac}")
            c.line(2*mm, 19*mm, 68*mm, 19*mm)
            
            # CORPO (Conforme sua nova solicitação)
            c.setFont("Helvetica-Bold", 10)
            c.drawString(2*mm, 13*mm, item["med"][:40]) # Nome e Número
            
            c.setFont("Helvetica-Bold", 9)
            c.drawString(2*mm, 8*mm, item["dose"]) # Qtd e Unidade
            
            c.setFont("Helvetica", 9)
            c.drawString(25*mm, 8*mm, item["via"]) # Via de aplicação
            
            # HORÁRIO
            c.setFont("Helvetica-Bold", 14)
            c.drawRightString(68*mm, 5*mm, f"Hs: {item['hora']}")
            c.showPage()
            
        c.save()
        st.download_button(
            label="📥 BAIXAR TODAS AS ETIQUETAS (PDF)",
            data=buffer.getvalue(),
            file_name=f"Etiquetas_{leito_pac}.pdf",
            mime="application/pdf",
            type="primary"
        )
