import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
import re
import io

def extrair_dados(texto):
    etiquetas = []
    
    # Captura cabeçalho
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
    med_atual = ""
    detalhes_atuais = ""

    for i, linha in enumerate(linhas):
        # Identifica o início da medicação pelo número + Nome (Ex: "4 dipirONA")
        # Padrão: Começa com número, seguido de texto e unidades de medida
        if re.search(r"^\d+\s", linha) and any(x in linha.upper() for x in ["MILIGRAMA", "MILILITRO", "AMPOLA", "FRASCO", "COMPRIMIDO"]):
            med_atual = linha.split("  ")[0].strip().upper() # Pega número e nome
            
            # Tenta capturar Qtd, Unidade e Via (Apl) que costumam estar na mesma linha
            partes = re.split(r'\s{2,}', linha)
            if len(partes) >= 4:
                # Une Qtd (partes[1]), Unidade (partes[2]) e Via (partes[4] ou final)
                detalhes_atuais = f"{partes[1]} {partes[2]} - {partes[-1]}"
            else:
                detalhes_atuais = ""

        # Identifica os horários do SoulMV (. 08 . 14)
        if "." in linha and re.search(r"\.\s?(\d{2})", linha):
            horas = re.findall(r"(?<=\.)\s?(\d{2})", linha)
            for h in horas:
                if int(h) < 24:
                    etiquetas.append({
                        "med": med_atual,
                        "detalhes": detalhes_atuais,
                        "hora": f"{h}:00"
                    })
    
    return dados_paciente, etiquetas

# Interface Web
st.set_page_config(page_title="Gerador de Etiquetas ICHC", layout="centered")
st.title("🏷️ Gerador de Etiquetas TSC (Web)")
st.write("Cole o texto da prescrição para gerar o PDF.")

texto_input = st.text_area("Cole aqui o texto do SoulMV:", height=300)

if st.button("Gerar PDF"):
    if texto_input:
        p, lista_etiquetas = extrair_dados(texto_input)
        
        if lista_etiquetas:
            # Criar PDF em memória
            buffer = io.BytesIO()
            c = canvas.Canvas(buffer, pagesize=(70*mm, 30*mm))
            
            for e in lista_etiquetas:
                # Cabeçalho
                c.setFont("Helvetica-Bold", 8)
                c.drawString(2*mm, 25*mm, f"{p['leito']} - {p['nome'][:28]}")
                c.setFont("Helvetica", 7)
                c.drawString(2*mm, 21*mm, f"At: {p['at']} | Nasc: {p['nasc']}")
                c.line(2*mm, 19*mm, 68*mm, 19*mm)
                
                # Meio: Número + Nome
                c.setFont("Helvetica-Bold", 9)
                c.drawString(2*mm, 14*mm, e['med'][:40])
                
                # Detalhes: Qtd, Unidade, Via
                c.setFont("Helvetica", 8)
                c.drawString(2*mm, 9*mm, e['detalhes'][:45])
                
                # Horário
                c.setFont("Helvetica-Bold", 14)
                c.drawRightString(68*mm, 5*mm, f"Hs: {e['hora']}")
                c.showPage()
            
            c.save()
            st.success(f"Sucesso! {len(lista_etiquetas)} etiquetas geradas.")
            st.download_button(label="📥 Baixar Etiquetas PDF", data=buffer.getvalue(), file_name=f"Etiquetas_{p['leito']}.pdf", mime="application/pdf")
        else:
            st.error("Nenhuma medicação com horário encontrada.")
    else:
        st.warning("Por favor, cole o texto antes de clicar.")
