import fitz  # PyMuPDF
import re

def get_value(text, key):
    """Helper function to extract value after a key"""
    pattern = f"{key}\\s*([^\\n]+)"
    match = re.search(pattern, text)
    return match.group(1).strip() if match else None

def read_pdf(file_path):
    try:
        # Open the PDF file
        doc = fitz.open(file_path)
        
        # Get text from first page
        text = doc[0].get_text()
        
        # Print the raw text
        print("Raw PDF Text:")
        print("-" * 50)
        print(text)
        print("-" * 50)
        
        # Test our parsing
        print("\nTesting field extraction:")
        print("-" * 50)
        
        # Test each field
        fields = [
            "IDENTIFICAÇÃO DO AUTO DE INFRAÇÃO",
            "DATA DA NOTIFICAÇÃO DA AUTUAÇÃO",
            "DATA LIMITE PARA INTERPOSIÇÃO DE DEFESA PRÉVIA",
            "DATA LIMITE PARA IDENTIFICAÇÃO DO CONDUTOR INFRATOR",
            "PLACA",
            "MARCA/MODELO/VERSÃO",
            "NOME",
            "CNH",	
            "LOCAL DA INFRAÇÃO",
            "DATA",
            "HORA",
            "CÓDIGO DA INFRAÇÃO",
            "VALOR DA MULTA",
            "DESCRIÇÃO DA INFRAÇÃO",
            "MEDIÇÃO REALIZADA",
            "VALOR CONSIDERADO",
            "LIMITE REGULAMENTADO",
            "NOME DO PROPRIETÁRIO",
            "CPF/CNPJ"
        ]
        
        for field in fields:
            value = get_value(text, field)
            print(f"{field}: {value}")
        
        print("-" * 50)
        
        # Close the document
        doc.close()
        
    except Exception as e:
        print(f"Error reading PDF: {e}")

if __name__ == "__main__":
    pdf_path = "multas/notificacaoAutuacao_OSL3F78_213890A6002222947455.pdf"
    read_pdf(pdf_path) 