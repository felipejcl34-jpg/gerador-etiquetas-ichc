import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
import re
import io

def extrair_dados(texto):
    etiquetas = []
    
    # Captura cabeçalho (Leito, Nome, At, Nasc)
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
    
    # Variáveis temporárias para guardar o último medicamento lido
    item_atual = ""
    med_atual = ""
    detalhes_atuais = ""

    for i, linha in enumerate(linhas):
        # 1. Procura o início da medicação (Número + Nome)
        # Ex: "2 ondansetrona" ou "11 piperacilina"
        match_med = re.search(r"^(\d+)\s+([\w\s\(\)\+]+)", linha)
        if match_med and any(x in linha.upper() for x in ["MILIGRAMA", "MILILITRO", "AMPOLA", "FRASCO", "COMPRIMIDO", "DOSE"]):
            item_atual = match_med.group(1) # O número (Ex: 2)
            med_atual = match_med.group(2).split("  ")[0].strip().upper() # O nome
            
            # Tenta capturar Qtd, Unidade e Via (Apl)
            partes = re.split(r'\s{2,}', linha)
            if len(partes) >= 4:
                # partes[1]=Qtd, partes[2]=Unidade, partes[-1]=Via
                detalhes_atuais = f"{partes[1]} {partes[2]} - {partes[-1]}"
            else:
                detalhes_atuais = "Verificar Prescrição"

        # 2. Procura horários (. 04 . 10) - SÓ GERA ETIQUETA SE ACHAR ISTO
        if "." in linha and re.search(r"\.\s?(\d{2})", linha):
            horas = re.findall(r"(?<=\.)\s?(\d{2})", linha)
            for h in horas:
                if int(h) < 24:
                    etiquetas.append({
                        "item": item_atual,
                        "med": med_atual,
                        "detalhes": detalhes_atuais,
                        "hora": f"{h}:00"
                    })
    
    return dados_paciente, etiquetas

# Interface Web Streamlit
st.set_page_config(page_title="Gerador ICHC", layout="centered")
st.title("🏷️ Gerador de Etiquetas ICHC")

texto_input = st.text_area("Cole aqui o texto da prescrição (Ctrl+A e Ctrl+C no PDF):", height=300)

if st.button("GERAR ETIQUETAS"):
    if texto_input:
        p, lista_etiquetas = extrair_dados(texto_input)
        
        if lista_etiquetas:
            buffer = io.BytesIO()
            c = canvas.Canvas(buffer, pagesize=(70*mm, 30*mm))
            
            for e in lista_etiquetas:
                # Cabeçalho Fixo (O que estava certinho)
                c.setFont("Helvetica-Bold", 8)
                c.drawString(2*mm, 25*mm, f"{p['leito']} - {p['nome'][:28]}")
                c.setFont("Helvetica", 7)
                c.drawString(2*mm, 21*mm, f"At: {p['at']} | Nasc: {p['nasc']}")
                c.line(2*mm, 19*mm, 68*mm, 19*mm)
                
                # Parte do Meio: Número + Nome do Medicamento
                c.setFont("Helvetica-Bold", 10)
                c.drawString(2*mm, 13*mm, f"{e['item']} - {e['med']}"[:40])
                
                # Detalhes: Qtd, Unidade e Via
                c.setFont("Helvetica", 8)
                c.drawString(2*mm, 8*mm, e['detalhes'][:45])
                
                # Horário em Destaque
                c.setFont("Helvetica-Bold", 14)
                c.drawRightString(68*mm, 5*mm, f"Hs: {e['hora']}")
                c.showPage()
            
            c.save()
            st.success(f"Pronto! {len(lista_etiquetas)} etiquetas geradas.")
            st.download_button("📥 Baixar PDF para Impressão", buffer.getvalue(), f"Etiquetas_{p['leito']}.pdf")
        else:
            st.error("Não encontrei horários (. 00) para as medicações.")
