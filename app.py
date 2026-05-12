import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
import re
import io

# Função para resetar o estado do app
def limpar_tela():
    st.session_state.lista_final = []
    st.session_state.paciente = {}
    st.session_state.texto_input = ""
    st.rerun()

def extrair_dados_completos(texto):
    # Cabeçalho
    paciente = re.search(r"Paciente...: (?:[\d\s-]+)?([\w\s]+)", texto)
    at = re.search(r"Atendimento: (\d+)", texto)
    nasc = re.search(r"Dt Nasc: ([\d/]+)", texto)
    leito = re.search(r"Leito..: ([\w\d]+)", texto)

    dados_paciente = {
        "nome": paciente.group(1).split('\n')[0].strip() if paciente else "PACIENTE",
        "at": at.group(1) if at else "",
        "nasc": nasc.group(1) if nasc else "",
        "leito": leito.group(1) if leito else "S/L"
    }

    linhas = [l.strip() for l in texto.split('\n') if l.strip()]
    meds_encontradas = []
    
    item_atual, nome_atual, qtd_atual, unidade_atual, via_atual = "", "", "", "", ""

    for i, linha in enumerate(linhas):
        # Identifica medicação: Número + Nome
        match_med = re.search(r"^(\d+)\s+([\w\s\(\)\+]+)", linha)
        if match_med and any(x in linha.upper() for x in ["MILIGRAMA", "MILILITRO", "AMPOLA", "FRASCO", "COMPRIMIDO", "GOTA", "GTS"]):
            item_atual = match_med.group(1)
            nome_atual = match_med.group(2).split("  ")[0].strip().upper()
            
            partes = re.split(r'\s{2,}', linha)
            if len(partes) >= 3:
                qtd_atual = partes[1]
                unidade_atual = partes[2].replace("MILIGRAMA", "mg").replace("MILILITRO", "ml").replace("GOTA", "gts").lower()
                via_atual = partes[-1] if len(partes) > 3 else "IV"
            
        # Identifica Horários com ponto (. 22)
        if "." in linha and re.search(r"\.\s?(\d{2})", linha):
            horas = re.findall(r"(?<=\.)\s?(\d{2})", linha)
            for h in horas:
                if int(h) < 24:
                    meds_encontradas.append({
                        "id": f"{item_atual}-{nome_atual}-{h}-{i}", 
                        "exibir": f"{item_atual}. {nome_atual} ({h}:00)",
                        "dados": {"item": item_atual, "med": nome_atual, "qtd": qtd_atual, "un": unidade_atual, "via": via_atual, "hora": f"{h}:00"}
                    })
        
        # Horários especiais (07:30)
        match_hora_esp = re.findall(r"(\d{2}:\d{2})", linha)
        for he in match_hora_esp:
            if "Atendimento" not in linha and "Emitido" not in linha:
                meds_encontradas.append({
                    "id": f"{item_atual}-{nome_atual}-{he}-{i}",
                    "exibir": f"{item_atual}. {nome_atual} ({he})",
                    "dados": {"item": item_atual, "med": nome_atual, "qtd": qtd_atual, "un": unidade_atual, "via": via_atual, "hora": he}
                })

    return dados_paciente, meds_encontradas

# --- INTERFACE ---
st.set_page_config(page_title="Gerador ICHC", layout="wide")

# Inicializa estados
if "lista_final" not in st.session_state: st.session_state.lista_final = []
if "paciente" not in st.session_state: st.session_state.paciente = {}

st.title("🏷️ Gerador de Etiquetas ICHC")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Nova Prescrição")
    texto_input = st.text_area("Cole o texto do PDF aqui:", height=300, key="texto_input_area")
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("Analisar Texto", use_container_width=True):
            if texto_input:
                p, meds = extrair_dados_completos(texto_input)
                st.session_state.paciente = p
                st.session_state.lista_final = meds
    with col_btn2:
        if st.button("Limpar Tudo", on_click=limpar_tela, use_container_width=True):
            pass

with col2:
    if st.session_state.lista_final:
        st.subheader("2. Selecione e Gere")
        selecionados = []
        
        # Opção de selecionar todos de uma vez
        sel_todos = st.toggle("Selecionar todos os horários", value=True)
        
        for m in st.session_state.lista_final:
            if st.checkbox(m["exibir"], key=m["id"], value=sel_todos):
                selecionados.append(m["dados"])
        
        if selecionados:
            if st.button("BAIXAR ETIQUETAS SELECIONADAS", type="primary", use_container_width=True):
                p = st.session_state.paciente
                buffer = io.BytesIO()
                c = canvas.Canvas(buffer, pagesize=(70*mm, 30*mm))
                
                for s in selecionados:
                    # Cabeçalho
                    c.setFont("Helvetica-Bold", 8)
                    c.drawString(2*mm, 25*mm, f"{p['leito']} - {p['nome'][:28]}")
                    c.setFont("Helvetica", 7)
                    c.drawString(2*mm, 21*mm, f"At: {p['at']} | Nasc: {p['nasc']}")
                    c.line(2*mm, 19*mm, 68*mm, 19*mm)
                    
                    # Medicação (Número + Nome)
                    c.setFont("Helvetica-Bold", 10)
                    c.drawString(2*mm, 13*mm, f"{s['item']}. {s['med']}"[:35])
                    
                    # Detalhes (Qtd Unidade e Via)
                    c.setFont("Helvetica-Bold", 9)
                    c.drawString(2*mm, 8*mm, f"{s['qtd']} {s['un']}")
                    c.setFont("Helvetica", 9)
                    c.drawString(25*mm, 8*mm, s['via'])
                    
                    c.setFont("Helvetica-Bold", 14)
                    c.drawRightString(68*mm, 5*mm, f"Hs: {s['hora']}")
                    c.showPage()
                
                c.save()
                st.download_button("📥 Clique para salvar o PDF", buffer.getvalue(), f"Etiquetas_{p['leito']}.pdf", use_container_width=True)
                st.info("Após baixar, você pode clicar em 'Limpar Tudo' para a próxima prescrição.")
