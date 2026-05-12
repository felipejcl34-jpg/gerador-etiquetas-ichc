import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
import re
import io

def extrair_dados_completos(texto):
    # 1. Cabeçalho (Mantido conforme você aprovou)
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

    # 2. Processamento de Medicações (Focado em Número, Nome, Qtd, Unidade, Via)
    linhas = [l.strip() for l in texto.split('\n') if l.strip()]
    meds_encontradas = []
    
    item_atual = ""
    nome_atual = ""
    qtd_atual = ""
    unidade_atual = ""
    via_atual = ""

    for i, linha in enumerate(linhas):
        # Identifica início da medicação (Ex: 7 ondansetrona...)
        match_med = re.search(r"^(\d+)\s+([\w\s\(\)\+]+)", linha)
        if match_med and any(x in linha.upper() for x in ["MILIGRAMA", "MILILITRO", "AMPOLA", "FRASCO", "COMPRIMIDO", "GOTA", "GTS"]):
            item_atual = match_med.group(1)
            nome_atual = match_med.group(2).split("  ")[0].strip().upper()
            
            # Extração inteligente de Qtd, Unidade e Via baseada em espaços
            partes = re.split(r'\s{2,}', linha)
            if len(partes) >= 3:
                qtd_atual = partes[1]
                unidade_atual = partes[2].replace("MILIGRAMA", "mg").replace("MILILITRO", "ml").replace("GOTA", "gts").lower()
                via_atual = partes[-1] if len(partes) > 3 else "IV" # Assume IV se não achar
            
        # Identifica Horários
        if "." in linha and re.search(r"\.\s?(\d{2})", linha):
            horas = re.findall(r"(?<=\.)\s?(\d{2})", linha)
            for h in horas:
                if int(h) < 24:
                    meds_encontradas.append({
                        "id": f"{item_atual}-{nome_atual}-{h}", # ID único para o checkbox
                        "exibir": f"{item_atual}. {nome_atual} ({h}:00)",
                        "dados": {
                            "item": item_atual, "med": nome_atual, "qtd": qtd_atual,
                            "un": unidade_atual, "via": via_atual, "hora": f"{h}:00"
                        }
                    })
        
        # Caso especial para horários tipo 07:30 (Ondansetrona)
        match_hora_especial = re.findall(r"(\d{2}:\d{2})", linha)
        for he in match_hora_especial:
            if "Atendimento" not in linha and "Emitido" not in linha:
                meds_encontradas.append({
                    "id": f"{item_atual}-{nome_atual}-{he}",
                    "exibir": f"{item_atual}. {nome_atual} ({he})",
                    "dados": {
                        "item": item_atual, "med": nome_atual, "qtd": qtd_atual,
                        "un": unidade_atual, "via": via_atual, "hora": he
                    }
                })

    return dados_paciente, meds_encontradas

# --- INTERFACE WEB ---
st.set_page_config(page_title="Gerador ICHC", layout="wide")
st.title("🏷️ Gerador de Etiquetas ICHC (Seleção Manual)")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Cole a Prescrição")
    texto_input = st.text_area("Copie tudo do PDF (Marilia.pdf) e cole aqui:", height=400)
    processar = st.button("Analisar Prescrição")

if "lista_final" not in st.session_state:
    st.session_state.lista_final = []
if "paciente" not in st.session_state:
    st.session_state.paciente = {}

if processar and texto_input:
    p, meds = extrair_dados_completos(texto_input)
    st.session_state.paciente = p
    st.session_state.lista_final = meds

with col2:
    if st.session_state.lista_final:
        st.subheader("2. Escolha os Horários")
        selecionados = []
        for m in st.session_state.lista_final:
            if st.checkbox(m["exibir"], key=m["id"], value=True):
                selecionados.append(m["dados"])
        
        if st.button("GERAR PDF SELECIONADO", type="primary"):
            p = st.session_state.paciente
            buffer = io.BytesIO()
            c = canvas.Canvas(buffer, pagesize=(70*mm, 30*mm))
            
            for s in selecionados:
                # Cabeçalho Fixo
                c.setFont("Helvetica-Bold", 8)
                c.drawString(2*mm, 25*mm, f"{p['leito']} - {p['nome'][:28]}")
                c.setFont("Helvetica", 7)
                c.drawString(2*mm, 21*mm, f"At: {p['at']} | Nasc: {p['nasc']}")
                c.line(2*mm, 19*mm, 68*mm, 19*mm)
                
                # Meio: 7. ONDANSETRONA...
                c.setFont("Helvetica-Bold", 10)
                c.drawString(2*mm, 13*mm, f"{s['item']}. {s['med']}"[:35])
                
                # Linha de Detalhes: 8 mg IV
                c.setFont("Helvetica-Bold", 9)
                c.drawString(2*mm, 8*mm, f"{s['qtd']} {s['un']}")
                c.setFont("Helvetica", 9)
                c.drawString(25*mm, 8*mm, s['via'])
                
                # Horário em destaque
                c.setFont("Helvetica-Bold", 14)
                c.drawRightString(68*mm, 5*mm, f"Hs: {s['hora']}")
                c.showPage()
            
            c.save()
            st.download_button("📥 Baixar PDF das Etiquetas", buffer.getvalue(), f"Etiquetas_{p['leito']}.pdf")
