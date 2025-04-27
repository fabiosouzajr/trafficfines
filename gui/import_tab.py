# gui/import_tab.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os

from config import DEFAULT_PDF_FOLDER
from pdf.parser import PDFParser
from utils.helpers import format_currency

class ImportTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding="10")
        
        self.pdf_parser = PDFParser()
        self.on_fines_updated = None  # Callback to notify when fines are updated
        self.compatible_files = []  # List to store compatible files
        
        self.create_widgets()
    
    def create_widgets(self):
        ttk.Label(self, text="Selecione a pasta contendo os PDFs de multas de trânsito:").grid(row=0, column=0, sticky=tk.W, pady=10)
        
        # Folder selection
        self.folder_path = tk.StringVar(value=DEFAULT_PDF_FOLDER)
        entry = ttk.Entry(self, textvariable=self.folder_path, width=50)
        entry.grid(row=1, column=0, padx=5, pady=5)
        
        browse_btn = ttk.Button(self, text="Procurar", command=self.browse_folder)
        browse_btn.grid(row=1, column=1, padx=5, pady=5)
        
        # Action buttons
        scan_btn = ttk.Button(self, text="Verificar Pasta", command=self.confirm_scan_folder)
        scan_btn.grid(row=2, column=0, pady=20)
        
        # Process button (initially hidden)
        self.process_btn = ttk.Button(self, text="Processar Arquivos", command=self.process_files)
        self.process_btn.grid(row=2, column=1, pady=20)
        self.process_btn.grid_remove()  # Hide initially
        
        # Results area
        self.result_label = ttk.Label(self, text="")
        self.result_label.grid(row=3, column=0, columnspan=2, pady=10)
        
        # Results list
        self.result_frame = ttk.LabelFrame(self, text="Arquivos Compatíveis")
        self.result_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        # Make the frame expandable
        self.columnconfigure(0, weight=1)
        self.rowconfigure(4, weight=1)
        
        # Create treeview for files
        columns = ("Arquivo", "Auto de Infração", "Placa", "Valor", "Data", "Status")
        self.files_tree = ttk.Treeview(self.result_frame, columns=columns, show="headings", selectmode="extended")
        
        # Define headings
        for col in columns:
            self.files_tree.heading(col, text=col)
            if col == "Arquivo":
                self.files_tree.column(col, width=200)
            elif col == "Auto de Infração":
                self.files_tree.column(col, width=150)
            else:
                self.files_tree.column(col, width=100)
        
        # Add scrollbars
        vsb = ttk.Scrollbar(self.result_frame, orient=tk.VERTICAL, command=self.files_tree.yview)
        hsb = ttk.Scrollbar(self.result_frame, orient=tk.HORIZONTAL, command=self.files_tree.xview)
        self.files_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.files_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Double-click to view details
        self.files_tree.bind("<Double-1>", self.show_file_details)
    
    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.folder_path.set(folder_selected)
    
    def confirm_scan_folder(self):
        """Show confirmation dialog before scanning folder"""
        folder = self.folder_path.get()
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("Erro", "Por favor, selecione uma pasta válida")
            return
        
        # Count PDFs in the folder
        pdf_count = sum(1 for f in os.listdir(folder) if f.lower().endswith('.pdf'))
        
        if pdf_count == 0:
            messagebox.showinfo("Informação", "Nenhum arquivo PDF encontrado na pasta selecionada.")
            return
        
        # Show confirmation dialog
        confirm = messagebox.askyesno(
            "Confirmar Verificação",
            f"Encontrados {pdf_count} arquivos PDF na pasta selecionada.\nDeseja verificar estes arquivos para informações de multas de trânsito?"
        )
        
        if confirm:
            self.scan_folder()
    
    def scan_folder(self):
        """Scan folder and verify PDF files for required fields"""
        folder = self.folder_path.get()
        
        try:
            # Clear previous results
            for item in self.files_tree.get_children():
                self.files_tree.delete(item)
            
            self.compatible_files = []
            incompatible_files = []
            
            # Check each PDF file
            for filename in os.listdir(folder):
                if filename.lower().endswith('.pdf'):
                    pdf_path = os.path.join(folder, filename)
                    fine_data = self.pdf_parser.verify_pdf(pdf_path)
                    
                    if fine_data and fine_data.get('valid', False):
                        self.compatible_files.append(fine_data)
                        self.files_tree.insert("", tk.END, values=(
                            filename,
                            fine_data['fine_number'],
                            fine_data['license_plate'],
                            format_currency(fine_data['amount']),
                            fine_data['issue_date'],
                            "Compatível"
                        ))
                    else:
                        missing = "Campos faltando" if fine_data else "Erro na análise"
                        if fine_data and 'missing_fields' in fine_data:
                            missing_fields = ', '.join(fine_data['missing_fields'])
                            missing = f"Faltando: {missing_fields}"
                            
                        incompatible_files.append(filename)
                        self.files_tree.insert("", tk.END, values=(
                            filename,
                            "N/A",
                            "N/A",
                            "N/A",
                            "N/A",
                            missing
                        ))
            
            # Update result summary
            total_files = len(self.compatible_files) + len(incompatible_files)
            self.result_label.config(
                text=f"Encontrados {len(self.compatible_files)} arquivos compatíveis de um total de {total_files} PDFs."
            )
            
            # Show process button if compatible files were found
            if self.compatible_files:
                self.process_btn.grid()
            else:
                self.process_btn.grid_remove()
                
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro durante a verificação: {e}")
    
    def process_files(self):
        """Process the compatible files and save them to database"""
        if not self.compatible_files:
            messagebox.showinfo("Informação", "Não há arquivos compatíveis para processar.")
            return
        
        try:
            from db.models import FineModel
            fine_model = FineModel()
            
            processed_count = 0
            failed_count = 0
            
            for fine_data in self.compatible_files:
                if fine_model.save_fine(fine_data):
                    processed_count += 1
                else:
                    failed_count += 1
            
            # Show results
            if failed_count == 0:
                messagebox.showinfo("Sucesso", f"Processados com sucesso todos os {processed_count} arquivos.")
            else:
                messagebox.showwarning("Sucesso Parcial", 
                    f"Processados {processed_count} arquivos com sucesso. {failed_count} arquivos falharam.")
            
            # Hide process button after processing
            self.process_btn.grid_remove()
            
            # Notify other components that fines have been updated
            if self.on_fines_updated:
                self.on_fines_updated()
                
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro durante o processamento: {e}")
    
    def show_file_details(self, event):
        """Show details of the selected file"""
        selected = self.files_tree.selection()
        if not selected:
            return
            
        item = self.files_tree.item(selected[0])
        filename = item['values'][0]
        status = item['values'][5]
        
        if status != "Compatível":
            messagebox.showinfo("Informação", f"O arquivo {filename} não é compatível e não pode ser processado.")
            return
            
        # Find the file data
        pdf_path = os.path.join(self.folder_path.get(), filename)
        fine_data = self.pdf_parser.parse_pdf(pdf_path)
        
        if fine_data:
            # Create a details window
            details_window = tk.Toplevel(self)
            details_window.title(f"Detalhes: {filename}")
            details_window.geometry("600x500")
            
            # Create frame with padding
            frame = ttk.Frame(details_window, padding="20")
            frame.pack(fill=tk.BOTH, expand=True)
            
            # Field mappings (Portuguese name to field key)
            field_mapping = {
                "IDENTIFICAÇÃO DO AUTO DE INFRAÇÃO (Número do AIT)": "fine_number",
                "DATA": "issue_date",
                "VALOR DA MULTA": "amount",
                "PLACA": "license_plate",
                "DATA LIMITE PARA IDENTIFICAÇÃO DO CONDUTOR INFRATOR": "driver_id_due_date",
                "DESCRIÇÃO DA INFRAÇÃO": "violation_type",
                "LOCAL DA INFRAÇÃO": "violation_location",
                "HORA": "violation_time",
                "NOME": "person_name",
                "NÚMERO DO EQUIPAMENTO OU INSTRUMENTO DE AFERIÇÃO": "equipment_number",
                "IDENTIFICAÇÃO DO AGENTE OU AUTORIDADE DE TRÂNSITO": "agent_id"
            }
            
            # Display fields in order
            row = 0
            for pt_field, field_key in field_mapping.items():
                ttk.Label(frame, text=f"{pt_field}:", font=("", 10, "bold")).grid(
                    row=row, column=0, sticky=tk.W, padx=5, pady=5)
                
                value = fine_data.get(field_key, "")
                if field_key == "amount" and value:
                    value = format_currency(value)
                
                value_label = ttk.Label(frame, text=str(value) if value else "Não disponível", wraplength=300)
                value_label.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
                row += 1
                
            # OK button
            ttk.Button(frame, text="OK", command=details_window.destroy).grid(
                row=row, column=0, columnspan=2, pady=20)