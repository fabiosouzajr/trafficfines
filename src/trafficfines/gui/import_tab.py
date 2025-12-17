# gui/import_tab.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading

from trafficfines.config import DEFAULT_PDF_FOLDER
from trafficfines.pdf.parser import PDFParser
from trafficfines.utils.helpers import format_currency, format_date, format_datetime
import datetime
from trafficfines.utils.logger import get_logger
from trafficfines.utils.error_messages import ErrorMessageMapper

logger = get_logger(__name__)

class ImportTab(ttk.Frame):
    # Define required fields for validation here
    REQUIRED_FIELDS = ['fine_number', 'license_plate', 'amount']  # <-- Change as needed

    def __init__(self, parent):
        super().__init__(parent, padding="10")
        
        self.pdf_parser = PDFParser()
        self.on_fines_updated = None  # Callback to notify when fines are updated
        self.compatible_files = []  # List to store compatible files
        # Get root window reference
        self.root = self._get_root()
        
        self.create_widgets()
    
    def _get_root(self):
        """Get the root Tk window"""
        widget = self
        while widget.master:
            widget = widget.master
        return widget
    
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
        
        # Progress indicator frame (initially hidden)
        self.progress_frame = ttk.Frame(self)
        self.progress_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        self.progress_label = ttk.Label(self.progress_frame, text="")
        self.progress_label.pack(pady=5)
        
        self.progress_bar = ttk.Progressbar(self.progress_frame, mode='determinate', length=400)
        self.progress_bar.pack(pady=5, fill=tk.X, expand=True)
        
        self.progress_frame.grid_remove()  # Hide initially
        
        # Results area
        self.result_label = ttk.Label(self, text="")
        self.result_label.grid(row=4, column=0, columnspan=2, pady=10)
        
        # Results list
        self.result_frame = ttk.LabelFrame(self, text="Arquivos Compatíveis")
        self.result_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        # Make the frame expandable
        self.columnconfigure(0, weight=1)
        self.rowconfigure(5, weight=1)
        
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
        
        # Disable buttons during scan
        self.process_btn.config(state=tk.DISABLED)
        
        # Clear previous results
        for item in self.files_tree.get_children():
            self.files_tree.delete(item)
        
        # Get list of PDF files first
        pdf_files = [f for f in os.listdir(folder) if f.lower().endswith('.pdf')]
        
        if not pdf_files:
            messagebox.showinfo("Informação", "Nenhum arquivo PDF encontrado na pasta selecionada.")
            self.process_btn.config(state=tk.NORMAL)
            return
        
        # Show progress indicator
        self.progress_frame.grid()
        self.progress_bar['maximum'] = len(pdf_files)
        self.progress_bar['value'] = 0
        self.progress_label.config(text="Iniciando verificação...")
        self.result_label.config(text="")
        self.update_idletasks()
        
        # Run scan in separate thread to prevent UI freezing
        def scan_thread():
            try:
                self.compatible_files = []
                incompatible_files = []
                
                # Check each PDF file
                for i, filename in enumerate(pdf_files):
                    pdf_path = os.path.join(folder, filename)
                    
                    # Update progress
                    self.root.after(0, lambda i=i, total=len(pdf_files), name=filename: self._update_scan_progress(i + 1, total, name))
                    
                    fine_data = self.pdf_parser.parse_pdf(pdf_path)

                    # Validation: check required fields
                    missing_fields = [field for field in self.REQUIRED_FIELDS if not fine_data or not fine_data.get(field)]
                    is_valid = fine_data is not None and not missing_fields

                    if is_valid:
                        self.compatible_files.append(fine_data)
                        self.root.after(0, lambda f=filename, d=fine_data: self._add_file_to_tree(f, d, "Compatível"))
                    else:
                        missing = "Campos faltando" if fine_data else "Erro na análise"
                        if missing_fields:
                            missing = f"Faltando: {', '.join(missing_fields)}"
                        incompatible_files.append(filename)
                        self.root.after(0, lambda f=filename, m=missing: self._add_file_to_tree(f, None, m))
                
                # Update UI on main thread
                self.root.after(0, lambda: self._finish_scan(len(self.compatible_files), len(incompatible_files)))
                
            except Exception as e:
                logger.error(f"Error during folder scan: {e}", exc_info=True)
                user_message = ErrorMessageMapper.format_error_for_user(e, {'operation': 'folder_scan', 'folder': folder})
                self.root.after(0, lambda: messagebox.showerror("Erro", user_message))
                self.root.after(0, lambda: self._finish_scan(0, 0, error=True))
        
        thread = threading.Thread(target=scan_thread, daemon=True)
        thread.start()
    
    def _update_scan_progress(self, current, total, filename):
        """Update progress bar and label"""
        self.progress_bar['value'] = current
        self.progress_label.config(text=f"Verificando: {filename} ({current}/{total})")
        self.update_idletasks()
    
    def _add_file_to_tree(self, filename, fine_data, status):
        """Add file to treeview"""
        if fine_data:
            self.files_tree.insert("", tk.END, values=(
                filename,
                fine_data.get('fine_number', ''),
                fine_data.get('license_plate', ''),
                format_currency(fine_data.get('amount', 0)),
                fine_data.get('violation_date', ''),
                status
            ))
        else:
            self.files_tree.insert("", tk.END, values=(
                filename,
                "N/A",
                "N/A",
                "N/A",
                "N/A",
                status
            ))
    
    def _finish_scan(self, compatible_count, incompatible_count, error=False):
        """Finish scan and update UI"""
        # Hide progress indicator
        self.progress_frame.grid_remove()
        
        if not error:
            # Update result summary
            total_files = compatible_count + incompatible_count
            self.result_label.config(
                text=f"Encontrados {compatible_count} arquivos compatíveis de um total de {total_files} PDFs."
            )
            
            # Show process button if compatible files were found
            if self.compatible_files:
                self.process_btn.grid()
                self.process_btn.config(state=tk.NORMAL)
            else:
                self.process_btn.grid_remove()
        else:
            self.process_btn.config(state=tk.NORMAL)
    
    def process_files(self):
        """Process the compatible files and save them to database"""
        if not self.compatible_files:
            messagebox.showinfo("Informação", "Não há arquivos compatíveis para processar.")
            return
        
        # Disable process button
        self.process_btn.config(state=tk.DISABLED)
        
        # Show progress indicator
        self.progress_frame.grid()
        self.progress_bar['maximum'] = len(self.compatible_files)
        self.progress_bar['value'] = 0
        self.progress_label.config(text="Processando arquivos...")
        self.update_idletasks()
        
        # Run processing in separate thread to prevent UI freezing
        def process_thread():
            try:
                from trafficfines.db.models import FineModel
                fine_model = FineModel()
                processed_count = 0
                failed_count = 0
                
                for i, fine_data in enumerate(self.compatible_files):
                    # Update progress
                    self.root.after(0, lambda i=i, total=len(self.compatible_files): self._update_process_progress(i + 1, total))
                    
                    if fine_model.save_fine(fine_data):
                        processed_count += 1
                    else:
                        failed_count += 1
                
                # Update UI on main thread
                self.root.after(0, lambda: self._finish_processing(processed_count, failed_count))
                
            except Exception as e:
                logger.error(f"Error during file processing: {e}", exc_info=True)
                user_message = ErrorMessageMapper.format_error_for_user(e, {'operation': 'file_processing'})
                self.root.after(0, lambda: messagebox.showerror("Erro", user_message))
                self.root.after(0, lambda: self._finish_processing(0, 0, error=True))
        
        thread = threading.Thread(target=process_thread, daemon=True)
        thread.start()
    
    def _update_process_progress(self, current, total):
        """Update progress bar and label"""
        self.progress_bar['value'] = current
        self.progress_label.config(text=f"Processando arquivo {current}/{total}...")
        self.update_idletasks()
    
    def _finish_processing(self, processed_count, failed_count, error=False):
        """Finish processing and update UI"""
        # Hide progress indicator
        self.progress_frame.grid_remove()
        
        if not error:
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
        else:
            self.process_btn.config(state=tk.NORMAL)
    
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
                "DATA DA NOTIFICAÇÃO DA AUTUAÇÃO": "notification_date",
                "DATA LIMITE PARA INTERPOSIÇÃO DE DEFESA PRÉVIA": "defense_due_date",
                "DATA LIMITE PARA IDENTIFICAÇÃO DO CONDUTOR INFRATOR": "driver_id_due_date",
                "PLACA": "license_plate",
                "MARCA/MODELO/VERSÃO": "vehicle_model",
                "LOCAL DA INFRAÇÃO": "violation_location",
                "DATA": "violation_date",
                "HORA": "violation_time",
                "CÓDIGO DA INFRAÇÃO": "violation_code",
                "VALOR DA MULTA": "amount",
                "DESCRIÇÃO DA INFRAÇÃO": "description",
                "MEDIÇÃO REALIZADA": "measured_speed",
                "VALOR CONSIDERADO": "considered_speed",
                "LIMITE REGULAMENTADO": "speed_limit",
                "NOME DO PROPRIETÁRIO": "owner_name",
                "CPF/CNPJ": "owner_document"
            }
            
            # Display fields in order
            row = 0
            for pt_field, field_key in field_mapping.items():
                ttk.Label(frame, text=f"{pt_field}:", font=("", 10, "bold")).grid(
                    row=row, column=0, sticky=tk.W, padx=5, pady=5)
                
                value = fine_data.get(field_key, "")
                if field_key == "amount" and value:
                    value = format_currency(value)
                elif isinstance(value, datetime.date):
                    value = format_date(value)
                elif isinstance(value, datetime.datetime):
                    value = format_datetime(value)
                
                value_label = ttk.Label(frame, text=str(value) if value else "Não disponível", wraplength=300)
                value_label.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
                row += 1
                
            # OK button
            ttk.Button(frame, text="OK", command=details_window.destroy).grid(
                row=row, column=0, columnspan=2, pady=20)