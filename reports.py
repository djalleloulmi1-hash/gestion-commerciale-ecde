from datetime import datetime
import os
try:
    import openpyxl
    from openpyxl.styles import Font, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import landscape, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.pdfgen import canvas
except ImportError:
    print("Missing dependencies: openpyxl or reportlab")

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        """add page info to each page (page x of y)"""
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.setFont("Helvetica", 9)
        width, height = self._pagesize
        self.drawCentredString(width / 2.0, 0.7 * cm,
                               "Page %d / %d" % (self._pageNumber, page_count))

def format_currency(value):
    return f"{value:,.2f} DA".replace(",", " ").replace(".", ",")

def format_currency_report(value):
    if value is None: return "0,00"
    try:
        val = float(value)
        return f"{val:,.2f}".replace(",", " ").replace(".", ",")
    except (ValueError, TypeError):
        return str(value)

def generate_stock_valuation_excel(data, output_path):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Etat Stock Valorise"
    
    # Styles
    bold_font = Font(bold=True, name='Arial', size=10)
    title_font = Font(bold=True, name='Arial', size=14)
    center_align = Alignment(horizontal='center', vertical='center')
    border = Border(left=Side(style='thin'), 
                   right=Side(style='thin'), 
                   top=Side(style='thin'), 
                   bottom=Side(style='thin'))
    
    # Title
    ws['B2'] = "ETAT DES MOUVEMENTS DES STOCKS (VALORISES)"
    ws['B2'].font = title_font
    ws['B2'].alignment = center_align
    ws.merge_cells('B2:K2')
    
    # Meta Data
    prod_name = data['product']['nom']
    start_date = data['period']['start']
    end_date = data['period']['end']
    unit = data['product']['unite']
    
    ws['A3'] = f"PRODUIT : {prod_name}"
    ws['A3'].font = bold_font
    
    ws['D3'] = f"DU : {start_date}"
    ws['D3'].font = bold_font
    
    ws['F3'] = f"AU : {end_date}"
    ws['F3'].font = bold_font
    
    ws['I3'] = f"Date d'établissement : {datetime.now().strftime('%d/%m/%Y')}"
    
    ws['A4'] = f"UNITE DE MESURE : {unit}"
    ws['A4'].font = bold_font
    
    # Headers
    # Row 6
    headers_row6 = [
        ("A6", "JOURNEE"),
        ("B6", "STOCK INITIAL"), 
        ("D6", "P.UNITAIRE"),
        ("E6", "RECEPTIONS"),
        ("G6", "VENTES"),
        ("I6", "STOCK FINAL")
    ]
    
    for cell_ref, text in headers_row6:
        cell = ws[cell_ref]
        cell.value = text
        cell.font = bold_font
        cell.alignment = center_align
        cell.border = border
        
    # Merges
    ws.merge_cells('A6:A7') # Journee merges vertically
    ws.merge_cells('B6:C6') # Stock Initial merges horizontally
    # ws.merge_cells('D6:D7') # REMOVED: P.Unit and C.Achat are separate cells vertically
    ws.merge_cells('E6:F6')
    ws.merge_cells('G6:H6')
    ws.merge_cells('I6:J6')
    
    # Correcting merges based on logic
    # REMOVED DUPLICATES
    
    # Row 7 Sub-headers
    headers_row7 = [
        ("B7", "QUANTITES"), ("C7", "VALEURS"),
        ("D7", "C.ACHAT"),
        ("E7", "QUANTITES"), ("F7", "VALEURS"),
        ("G7", "QUANTITES"), ("H7", "VALEURS"),
        ("I7", "QUANTITES"), ("J7", "VALEURS"),
    ]
    
    for cell_ref, text in headers_row7:
        cell = ws[cell_ref]
        cell.value = text
        cell.font = bold_font
        cell.alignment = center_align
        cell.border = border

    # Data
    row_idx = 8
    for row_data in data['data']:
        # Format date
        date_obj = datetime.strptime(row_data['date'], '%Y-%m-%d')
        date_fmt = date_obj.strftime('%d/%m/%Y')
        
        # Columns:
        # A: Date
        # B: Stock Init Qty
        # C: Stock Init Val
        # D: C.Achat
        # E: Recep Qty
        # F: Recep Val
        # G: Vente Qty
        # H: Vente Val
        # I: Final Qty
        # J: Final Val
        
        ws.cell(row=row_idx, column=1, value=date_fmt).border = border
        
        ws.cell(row=row_idx, column=2, value=format_currency_report(row_data['stock_initial_qty'])).border = border
        ws.cell(row=row_idx, column=3, value=format_currency_report(row_data['stock_initial_val'])).border = border
        
        ws.cell(row=row_idx, column=4, value=format_currency_report(row_data['cout_achat'])).border = border
        
        ws.cell(row=row_idx, column=5, value=format_currency_report(row_data['reception_qty'])).border = border
        ws.cell(row=row_idx, column=6, value=format_currency_report(row_data['reception_val'])).border = border
        
        ws.cell(row=row_idx, column=7, value=format_currency_report(row_data['vente_qty'])).border = border
        ws.cell(row=row_idx, column=8, value=format_currency_report(row_data['vente_val'])).border = border
        
        ws.cell(row=row_idx, column=9, value=format_currency_report(row_data['stock_final_qty'])).border = border
        ws.cell(row=row_idx, column=10, value=format_currency_report(row_data['stock_final_val'])).border = border
        
        row_idx += 1
        
    # Footer
    row_idx += 2
    ws.cell(row=row_idx, column=1, value="LE CHEF SERVICE COMMERCIAL").font = bold_font
    ws.cell(row=row_idx, column=5, value="LE CHEF SERVICE COMPTABILITE").font = bold_font
    ws.cell(row=row_idx, column=8, value="LE CHEF DU DEPOT").font = bold_font
    
    # Column Widths
    ws.column_dimensions['A'].width = 15
    for col in ['B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']:
        ws.column_dimensions[col].width = 12

    wb.save(output_path)
    return output_path

def generate_stock_valuation_pdf(data, output_path):
    doc = SimpleDocTemplate(output_path, pagesize=landscape(A4),
                            rightMargin=1*cm, leftMargin=1*cm,
                            topMargin=1*cm, bottomMargin=1*cm)
    
    elements = []
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    title_style.alignment = 1 # Center
    
    title = Paragraph("ETAT DES MOUVEMENTS DES STOCKS (VALORISES)", title_style)
    elements.append(title)
    elements.append(Spacer(1, 1*cm))
    
    # Meta Data
    prod_name = data['product']['nom']
    start_date = data['period']['start']
    end_date = data['period']['end']
    unit = data['product']['unite']
    
    meta_data = [
        [f"PRODUIT : {prod_name}", f"DU : {start_date}   AU : {end_date}", f"Editée le : {datetime.now().strftime('%d/%m/%Y')}"],
        [f"UNITE DE MESURE : {unit}", "", ""]
    ]
    t_meta = Table(meta_data, colWidths=[8*cm, 10*cm, 8*cm])
    t_meta.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
    ]))
    elements.append(t_meta)
    elements.append(Spacer(1, 0.5*cm))
    
    # Table Data
    # Headers
    # We need to simulate merged cells by managing the grid manually or using span
    # ReportLab Table allows span
    
    # Header Row 1
    h1 = [
        "JOURNEE", 
        "STOCK INITIAL", "", 
        "P.UNITAIRE", 
        "RECEPTIONS", "", 
        "VENTES", "", 
        "STOCK FINAL", ""
    ]
    
    # Header Row 2
    h2 = [
        "", # Under Journee
        "QUANTITES", "VALEURS", 
        "C.ACHAT", # Under P.Unit
        "QUANTITES", "VALEURS",
        "QUANTITES", "VALEURS",
        "QUANTITES", "VALEURS"
    ]
    
    table_data = [h1, h2]
    
    for row in data['data']:
        date_obj = datetime.strptime(row['date'], '%Y-%m-%d')
        date_fmt = date_obj.strftime('%d/%m/%Y')
        
        table_data.append([
            date_fmt,
            format_currency_report(row['stock_initial_qty']),
            format_currency_report(row['stock_initial_val']),
            format_currency_report(row['cout_achat']),
            format_currency_report(row['reception_qty']),
            format_currency_report(row['reception_val']),
            format_currency_report(row['vente_qty']),
            format_currency_report(row['vente_val']),
            format_currency_report(row['stock_final_qty']),
            format_currency_report(row['stock_final_val']),
        ])
        
    t = Table(table_data, colWidths=[2.5*cm] + [2.5*cm]*9)
    
    # Base Styles
    base_styles = [
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'), # GLOBAL BOLD
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        
        # Merges
        ('SPAN', (0,0), (0,1)), # Journee
        ('SPAN', (1,0), (2,0)), # Stock Initial
        # ('SPAN', (3,0), (3,1)), # REMOVED
        ('SPAN', (4,0), (5,0)), # Receptions
        ('SPAN', (6,0), (7,0)), # Ventes
        ('SPAN', (8,0), (9,0)), # Stock Final
        
        ('BACKGROUND', (0,0), (-1,1), colors.lightgrey),
        ('FONTSIZE', (0,0), (-1,-1), 8),
    ]
    
    # Conditional Styles (Skip 2 header rows, Col 0 is Date - handled by parser)
    cond_styles = get_conditional_styles(table_data[2:], start_row=2, start_col=0)
    
    t.setStyle(TableStyle(base_styles + cond_styles))
    
    elements.append(t)
    elements.append(Spacer(1, 2*cm))
    
    # Footer
    footer_data = [
        ["LE CHEF SERVICE COMMERCIAL", "", "LE CHEF SERVICE COMPTABILITE", "", "LE CHEF DU DEPOT"]
    ]
    t_foot = Table(footer_data, colWidths=[6*cm, 2*cm, 6*cm, 2*cm, 6*cm])
    t_foot.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ]))
    elements.append(t_foot)
    
    doc.build(elements)
    return output_path

def generate_global_consumption_excel(date_str, output_path=None):
    from logic import get_logic
    logic = get_logic()
    data = logic.get_global_consumption_data(date_str)
    
    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"Etat_Conso_Global_{date_str}_{timestamp}.xlsx"

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Etat Consommation"
    
    # Styles
    bold_font = Font(bold=True, name='Arial', size=10)
    title_font = Font(bold=True, name='Arial', size=14)
    center_align = Alignment(horizontal='center', vertical='center')
    border = Border(left=Side(style='thin'), 
                   right=Side(style='thin'), 
                   top=Side(style='thin'), 
                   bottom=Side(style='thin'))
    
    # Title
    ws['B2'] = f"ETAT DE CONSOMMATION GLOBAL - JOURNEE DU {datetime.strptime(date_str, '%Y-%m-%d').strftime('%d/%m/%Y')}"
    ws['B2'].font = title_font
    ws['B2'].alignment = center_align
    ws.merge_cells('B2:J2')
    
    # Headers
    headers = [
        ("A4", "Désignation"), ("B4", "U"),
        ("C4", "JOURNEE"), ("E4", "CUMUL MOIS"), ("G4", "CUMUL ANNEE")
    ]
    
    # Sub-headers
    sub_headers = [
        ("C5", "Qté"), ("D5", "Valeur"),
        ("E5", "Qté"), ("F5", "Valeur"),
        ("G5", "Qté"), ("H5", "Valeur")
    ]
    
    for cell_ref, text in headers:
        cell = ws[cell_ref]
        cell.value = text
        cell.font = bold_font
        cell.alignment = center_align
        cell.border = border

    for cell_ref, text in sub_headers:
        cell = ws[cell_ref]
        cell.value = text
        cell.font = bold_font
        cell.alignment = center_align
        cell.border = border
        
    # Merges
    ws.merge_cells('A4:A5')
    ws.merge_cells('B4:B5')
    ws.merge_cells('C4:D4')
    ws.merge_cells('E4:F4')
    ws.merge_cells('G4:H4')
    
    row_idx = 6
    for row in data['data']:
        # A: Name, B: Unit, C: Day Q, D: Day V, E: Month Q, F: Month V, G: Year Q, H: Year V
        
        ws.cell(row=row_idx, column=1, value=row['product_name']).border = border
        ws.cell(row=row_idx, column=2, value=row['unit']).border = border
        ws.cell(row=row_idx, column=2).alignment = center_align
        
        ws.cell(row=row_idx, column=3, value=format_currency_report(row['daily_qty'])).border = border
        ws.cell(row=row_idx, column=4, value=format_currency_report(row['daily_val'])).border = border
        
        ws.cell(row=row_idx, column=5, value=format_currency_report(row['monthly_qty'])).border = border
        ws.cell(row=row_idx, column=6, value=format_currency_report(row['monthly_val'])).border = border
        
        ws.cell(row=row_idx, column=7, value=format_currency_report(row['yearly_qty'])).border = border
        ws.cell(row=row_idx, column=8, value=format_currency_report(row['yearly_val'])).border = border
        
        row_idx += 1
        
    # Signatures
    row_idx += 3
    ws.cell(row=row_idx, column=2, value="Section Facturation").font = bold_font
    ws.cell(row=row_idx, column=7, value="Chef Service Commercial").font = bold_font

    # Column Widths
    ws.column_dimensions['A'].width = 30
    for col in ['B', 'C', 'D', 'E', 'F', 'G', 'H']:
        ws.column_dimensions[col].width = 15

    wb.save(output_path)
    return output_path

def generate_global_consumption_pdf(date_str, output_path=None):
    from logic import get_logic
    logic = get_logic()
    data = logic.get_global_consumption_data(date_str)
    
    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"Etat_Conso_Global_{date_str}_{timestamp}.pdf"

    doc = SimpleDocTemplate(output_path, pagesize=landscape(A4),
                            rightMargin=1*cm, leftMargin=1*cm,
                            topMargin=1*cm, bottomMargin=1*cm)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Logo Check
    from utils import check_logo_exists
    if check_logo_exists():
        try:
            from reportlab.platypus import Image as RLImage
            im = RLImage("logo_gica.png", width=4*cm, height=2*cm)
            im.hAlign = 'LEFT'
            elements.append(im)
        except: pass
        
    title_style = styles['Heading1']
    title_style.alignment = 1 # Center
    
    date_fmt = datetime.strptime(date_str, '%Y-%m-%d').strftime('%d/%m/%Y')
    title = Paragraph(f"ETAT DE CONSOMMATION GLOBAL - A FIN {date_fmt}", title_style)
    elements.append(title)
    elements.append(Spacer(1, 1*cm))
    
    # Table Header
    h1 = ["Désignation", "U", "JOURNEE", "", "CUMUL MOIS", "", "CUMUL ANNEE", ""]
    h2 = ["", "", "Qté", "Valeur", "Qté", "Valeur", "Qté", "Valeur"]
    
    table_data = [h1, h2]
    
    for row in data['data']:
        table_data.append([
            row['product_name'],
            row['unit'],
            format_currency_report(row['daily_qty']),
            format_currency_report(row['daily_val']),
            format_currency_report(row['monthly_qty']),
            format_currency_report(row['monthly_val']),
            format_currency_report(row['yearly_qty']),
            format_currency_report(row['yearly_val'])
        ])
        
    col_widths = [6*cm, 1.5*cm] + [3*cm]*6
    t = Table(table_data, colWidths=col_widths, repeatRows=2)
    
    base_styles = [
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'), # GLOBAL BOLD
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,2), (0,-1), 'LEFT'), # Products left align
        
        # Merges
        ('SPAN', (0,0), (0,1)), # Designation
        ('SPAN', (1,0), (1,1)), # Unit
        ('SPAN', (2,0), (3,0)), # Journee
        ('SPAN', (4,0), (5,0)), # Mois
        ('SPAN', (6,0), (7,0)), # Annee
        
        ('BACKGROUND', (0,0), (-1,1), colors.lightgrey),
        ('FONTSIZE', (0,0), (-1,-1), 9),
    ]
    
    # Conditional Styles (Skip 2 header rows, Skip Col 0,1 (Des, U))
    cond_styles = get_conditional_styles(table_data[2:], start_row=2, start_col=0)
    
    t.setStyle(TableStyle(base_styles + cond_styles))
    
    elements.append(t)
    elements.append(Spacer(1, 2*cm))
    
    # Footer
    footer_data = [
        ["Section Facturation", "", "Chef Service Commercial"]
    ]
    t_foot = Table(footer_data, colWidths=[8*cm, 8*cm, 8*cm])
    t_foot.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ]))
    elements.append(t_foot)
    
    doc.build(elements)
    return output_path

def get_conditional_styles(data_matrix, start_row=0, start_col=0):
    """
    Generate ReportLab TableStyle commands for conditional formatting.
    Positives (>0) -> Green
    Negatives (<0) -> Orange (#ff9800)
    Zeros/Text -> Blue (if 0) or Black (default)
    """
    styles = []
    orange_color = colors.HexColor('#ff9800')
    green_color = colors.green
    blue_color = colors.blue
    
    for r_idx, row in enumerate(data_matrix):
        for c_idx, cell_value in enumerate(row):
            # Val cleanup
            val_str = str(cell_value).replace(" DA", "").replace(" ", "").replace(",", ".").replace("%", "")
            try:
                # Check for empty string or non-numeric first
                if not val_str.strip():
                    continue

                val = float(val_str)
                actual_row = r_idx + start_row
                actual_col = c_idx + start_col
                
                if val > 0.001:
                    styles.append(('TEXTCOLOR', (actual_col, actual_row), (actual_col, actual_row), green_color))
                elif val < -0.001:
                    styles.append(('TEXTCOLOR', (actual_col, actual_row), (actual_col, actual_row), orange_color))
                else:
                    # Effectively Zero
                    styles.append(('TEXTCOLOR', (actual_col, actual_row), (actual_col, actual_row), blue_color))
            except (ValueError, TypeError):
                # Text or other non-numeric content -> Default Black
                pass
                
    return styles

def generate_movements_valorises_pdf(date_str, output_path=None):
    from logic import get_logic
    logic = get_logic()
    result = logic.get_movements_valorises_data(date_str)
    data = result['data']
    totals = result['totals']
    
    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"Etat_Mouvements_Stocks_Valorises_{date_str}_{timestamp}.pdf"

    # Increased topMargin to accommodate fixed header
    doc = SimpleDocTemplate(output_path, pagesize=landscape(A4),
                            rightMargin=0.5*cm, leftMargin=0.5*cm,
                            topMargin=3.5*cm, bottomMargin=1.5*cm) 
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Define Header Drawing Function
    def draw_header(canvas, doc):
        canvas.saveState()
        
        # 1. Logo
        from utils import check_logo_exists
        if check_logo_exists():
            try:
                # Draw Image directly on canvas
                # Top-Left corner validation
                logo_path = "logo_gica.png"
                img_width = 4*cm
                img_height = 2*cm
                # Position: Left margin, Top of page - margin + buffer ?? 
                # Actually, canvas (0,0) is bottom-left. 
                # Top of page is A4[1] (height).
                page_width, page_height = landscape(A4)
                
                x_pos = 0.5 * cm # Left margin
                y_pos = page_height - 0.5*cm - img_height # Top margin area
                
                canvas.drawImage(logo_path, x_pos, y_pos, width=img_width, height=img_height, preserveAspectRatio=True, mask='auto')
            except Exception as e:
                print(f"Error drawing logo: {e}")

        # 2. Title
        title_style = styles['Heading1']
        title_style.alignment = 1 # Center
        date_fmt = datetime.strptime(date_str, '%Y-%m-%d').strftime('%d/%m/%Y')
        title_text = f"ETAT DES MOUVEMENTS DES STOCKS VALORISES - JOURNEE DU {date_fmt}"
        
        # Draw string centered
        canvas.setFont('Helvetica-Bold', 14)
        page_width, page_height = landscape(A4)
        text_width = canvas.stringWidth(title_text, 'Helvetica-Bold', 14)
        canvas.drawString((page_width - text_width) / 2.0, page_height - 2*cm, title_text)
        
        canvas.restoreState()

    # REMOVED: Flowable Logo and Title from 'elements'
    
    # TABLE 1: QUANTITIES
    p_style = ParagraphStyle('Bold', parent=styles['Normal'], fontName='Helvetica-Bold', alignment=1)
    elements.append(Paragraph("TABLEAU 1: QUANTITES", p_style))
    elements.append(Spacer(1, 0.2*cm))
    
    # Headers
    h1 = ["Désignation", "U", "JOURNEE", "", "", "MOIS", "", "", "ANNEE", "", "", "STOCK FINAL"]
    h2 = ["", "", "S.Init", "Entrées", "Sorties", "S.Init", "Entrées", "Sorties", "S.Init", "Entrées", "Sorties", ""]
    
    t1_data = [h1, h2]
    
    for row in data:
        t1_data.append([
            row['designation'],
            row['unite'],
            format_currency_report(row['day']['init']),
            format_currency_report(row['day']['in']),
            format_currency_report(row['day']['out']),
            format_currency_report(row['month']['init']),
            format_currency_report(row['month']['in']),
            format_currency_report(row['month']['out']),
            format_currency_report(row['year']['init']),
            format_currency_report(row['year']['in']),
            format_currency_report(row['year']['out']),
            format_currency_report(row['final'])
        ])
        
    # TOTAL ROW
    t1_data.append([
        "TOTAL", "", 
        format_currency_report(totals['day']['init']),
        format_currency_report(totals['day']['in']),
        format_currency_report(totals['day']['out']),
        format_currency_report(totals['month']['init']),
        format_currency_report(totals['month']['in']),
        format_currency_report(totals['month']['out']),
        format_currency_report(totals['year']['init']),
        format_currency_report(totals['year']['in']),
        format_currency_report(totals['year']['out']),
        format_currency_report(totals['final'])
    ])

    # Col Widths
    cw = 2.15*cm
    col_widths = [5*cm, 1.8*cm] + [cw]*10
    
    t1 = Table(t1_data, colWidths=col_widths, repeatRows=2)
    
    # Base Styles
    base_styles = [
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'), # GLOBAL BOLD
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,2), (0,-2), 'LEFT'), # Products left align (exclude header/total)
        ('WORDWRAP', (0,0), (-1,-1), 'CJK'), # Allow wrapping
        
        # Merges
        ('SPAN', (0,0), (0,1)), # Des
        ('SPAN', (1,0), (1,1)), # Unit
        ('SPAN', (2,0), (4,0)), # Day
        ('SPAN', (5,0), (7,0)), # Month
        ('SPAN', (8,0), (10,0)), # Year
        ('SPAN', (11,0), (11,1)), # Final
        
        ('BACKGROUND', (0,0), (-1,1), colors.lightgrey),
        ('BACKGROUND', (0,-1), (-1,-1), colors.lightgrey), # Total Row Grey
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 2),
        ('RIGHTPADDING', (0,0), (-1,-1), 2),
    ]
    
    # Apply Conditional Formatting (Skip headers [0,1])
    cond_styles = get_conditional_styles(t1_data[2:], start_row=2, start_col=0) # Start col 0 to match data
    
    t1.setStyle(TableStyle(base_styles + cond_styles))
    elements.append(t1)
    elements.append(Spacer(1, 0.5*cm))
    
    # TABLE 2: VALUES
    elements.append(Paragraph("TABLEAU 2: VALEURS (DA)", p_style))
    elements.append(Spacer(1, 0.2*cm))
    
    # Same Header Structure but for values
    h1_v = ["Désignation", "Cout U.", "JOURNEE", "", "", "MOIS", "", "", "ANNEE", "", "", "VAL. FINALE"]
    h2_v = ["", "", "S.Init", "Entrées", "Sorties", "S.Init", "Entrées", "Sorties", "S.Init", "Entrées", "Sorties", ""]
    
    t2_data = [h1_v, h2_v]
    
    for row in data:
        t2_data.append([
            row['designation'],
            format_currency_report(row['cout_unitaire']),
            format_currency_report(row['values']['day']['init']),
            format_currency_report(row['values']['day']['in']),
            format_currency_report(row['values']['day']['out']),
            format_currency_report(row['values']['month']['init']),
            format_currency_report(row['values']['month']['in']),
            format_currency_report(row['values']['month']['out']),
            format_currency_report(row['values']['year']['init']),
            format_currency_report(row['values']['year']['in']),
            format_currency_report(row['values']['year']['out']),
            format_currency_report(row['val_final'])
        ])
    
    # TOTAL ROW FOR VALUES
    v_totals = [0.0] * 10 # 10 value columns
    
    for row in data:
        v_totals[0] += row['values']['day']['init']
        v_totals[1] += row['values']['day']['in']
        v_totals[2] += row['values']['day']['out']
        v_totals[3] += row['values']['month']['init']
        v_totals[4] += row['values']['month']['in']
        v_totals[5] += row['values']['month']['out']
        v_totals[6] += row['values']['year']['init']
        v_totals[7] += row['values']['year']['in']
        v_totals[8] += row['values']['year']['out']
        v_totals[9] += row['val_final']
        
    t2_data.append([
        "TOTAL", "", 
        format_currency_report(v_totals[0]),
        format_currency_report(v_totals[1]),
        format_currency_report(v_totals[2]),
        format_currency_report(v_totals[3]),
        format_currency_report(v_totals[4]),
        format_currency_report(v_totals[5]),
        format_currency_report(v_totals[6]),
        format_currency_report(v_totals[7]),
        format_currency_report(v_totals[8]),
        format_currency_report(v_totals[9])
    ])
    
    t2 = Table(t2_data, colWidths=col_widths, repeatRows=2)
    # Apply Conditional Formatting (Skip headers [0,1], Start Col 0)
    cond_styles_v = get_conditional_styles(t2_data[2:], start_row=2, start_col=0)
    
    t2.setStyle(TableStyle(base_styles + cond_styles_v)) # Reuse base style
    elements.append(t2)
    elements.append(Spacer(1, 0.5*cm))
    
    # Signature Blocks
    sig_data = [
        ["Section Facturation", "Le Chef Service Commercial", "Chef Service Comptabilité", "Le Chef Depot/Assistant PDG"],
        ["", "", "", ""] # Space for signing
    ]
    
    t_sig = Table(sig_data, colWidths=[7*cm, 7*cm, 7*cm, 7*cm])
    t_sig.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('MINROWHEIGHT', (1,0), (1,0), 2*cm), # Space for signature
    ]))
    
    elements.append(t_sig)
    
    # Use NumberedCanvas for Page X / Y AND draw_header for repeating header
    doc.build(elements, onFirstPage=draw_header, onLaterPages=draw_header, canvasmaker=NumberedCanvas)
    return output_path

def generate_annual_receivables_excel(data, date_n, output_path=None):
    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"Etat_Creances_Annuelles_{date_n}_{timestamp}.xlsx"

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Etat Creances Annuelles"
    
    # Styles
    bold_font = Font(bold=True, name='Arial', size=10)
    title_font = Font(bold=True, name='Arial', size=14)
    center_align = Alignment(horizontal='center', vertical='center')
    border = Border(left=Side(style='thin'), 
                   right=Side(style='thin'), 
                   top=Side(style='thin'), 
                   bottom=Side(style='thin'))
    
    # Title
    date_fmt = datetime.strptime(date_n, "%Y-%m-%d").strftime("%d/%m/%Y")
    ws['B2'] = f"ÉTAT RÉCAPITULATIF ANNUEL DES CRÉANCES ET RECOUVREMENTS CLIENTS (SITUATION AU {date_fmt})"
    ws['B2'].font = title_font
    ws['B2'].alignment = center_align
    ws.merge_cells('B2:G2')
    
    # Headers
    headers = [
        ("A4", "Raison Sociale"),
        ("B4", "Solde au 01/01"),
        ("C4", "Achats (Année)"),
        ("D4", "Paiements (Année)"),
        ("E4", "Solde Final (Jour N)"),
        ("F4", "% Recouvrement")
    ]
    
    for cell_ref, text in headers:
        cell = ws[cell_ref]
        cell.value = text
        cell.font = bold_font
        cell.alignment = center_align
        cell.border = border
        
    # Data
    row_idx = 5
    for row in data['data']:
        ws.cell(row=row_idx, column=1, value=row['raison_sociale']).border = border
        
        ws.cell(row=row_idx, column=2, value=format_currency_report(row['solde_01_01'])).border = border
        ws.cell(row=row_idx, column=3, value=format_currency_report(row['achats'])).border = border
        ws.cell(row=row_idx, column=4, value=format_currency_report(row['paiements'])).border = border
        ws.cell(row=row_idx, column=5, value=format_currency_report(row['solde_final'])).border = border
        
        perc_val = f"{row['recouvrement']:.1f}%"
        ws.cell(row=row_idx, column=6, value=perc_val).border = border
        ws.cell(row=row_idx, column=6).alignment = center_align
        
        row_idx += 1
        
    # Totals Row
    totals = data['totals']
    ws.cell(row=row_idx, column=1, value=f"SOLDE GLOBAL DES CRÉANCES AU {date_fmt}").font = bold_font
    ws.cell(row=row_idx, column=1).border = border
    
    ws.cell(row=row_idx, column=2, value=format_currency_report(totals['solde_init'])).font = bold_font
    ws.cell(row=row_idx, column=2).border = border
    
    ws.cell(row=row_idx, column=3, value=format_currency_report(totals['achats'])).font = bold_font
    ws.cell(row=row_idx, column=3).border = border
    
    ws.cell(row=row_idx, column=4, value=format_currency_report(totals['paiements'])).font = bold_font
    ws.cell(row=row_idx, column=4).border = border
    
    ws.cell(row=row_idx, column=5, value=format_currency_report(totals['solde_final'])).font = bold_font
    ws.cell(row=row_idx, column=5).border = border
    
    ws.cell(row=row_idx, column=6, value="").border = border
    
    # Column Widths
    ws.column_dimensions['A'].width = 35
    for col in ['B', 'C', 'D', 'E']:
         ws.column_dimensions[col].width = 18
    ws.column_dimensions['F'].width = 15

    wb.save(output_path)
    return output_path

def generate_annual_receivables_pdf(data, date_n, output_path=None):
    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"Etat_Creances_Annuelles_{date_n}_{timestamp}.pdf"

    doc = SimpleDocTemplate(output_path, pagesize=landscape(A4),
                            rightMargin=1*cm, leftMargin=1*cm,
                            topMargin=1*cm, bottomMargin=1*cm)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Logo Check
    from utils import check_logo_exists
    if check_logo_exists():
        try:
            from reportlab.platypus import Image as RLImage
            im = RLImage("logo_gica.png", width=4*cm, height=2*cm)
            im.hAlign = 'LEFT'
            elements.append(im)
        except: pass
        
    title_style = styles['Heading1']
    title_style.alignment = 1 # Center
    
    date_fmt = datetime.strptime(date_n, "%Y-%m-%d").strftime("%d/%m/%Y")
    title = Paragraph(f"ÉTAT RÉCAPITULATIF ANNUEL DES CRÉANCES ET RECOUVREMENTS CLIENTS<br/>(SITUATION AU {date_fmt})", title_style)
    elements.append(title)
    elements.append(Spacer(1, 1*cm))
    
    # Table Data
    headers = ["Raison Sociale", "Solde au 01/01", "Achats (Année)", "Paiements (Année)", "Solde Final", "% Recouvrement"]
    
    table_data = [headers]
    
    for row in data['data']:
        table_data.append([
            row['raison_sociale'],
            format_currency_report(row['solde_01_01']),
            format_currency_report(row['achats']),
            format_currency_report(row['paiements']),
            format_currency_report(row['solde_final']),
            f"{row['recouvrement']:.1f}%"
        ])
        
    # Totals Row
    totals = data['totals']
    table_data.append([
        f"SOLDE GLOBAL AU {date_fmt}",
        format_currency_report(totals['solde_init']),
        format_currency_report(totals['achats']),
        format_currency_report(totals['paiements']),
        format_currency_report(totals['solde_final']),
        ""
    ])
    
    # Column Widths
    col_widths = [7*cm, 4*cm, 4*cm, 4*cm, 4*cm, 3*cm]
    
    t = Table(table_data, colWidths=col_widths, repeatRows=1)
    
    # Base Styles
    base_styles = [
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'), # GLOBAL BOLD
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,1), (0,-1), 'LEFT'), # Raison Sociale Left
        
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey), # Header BG
        ('FONTSIZE', (0,0), (-1,-1), 8),
        
        # Total Row Style
        ('BACKGROUND', (0,-1), (-1,-1), colors.lightgrey),
        # ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'), # Redundant
    ]
    
    # Conditional Styles (Skip 1 header row, Skip Col 0 (Raison Soc))
    cond_styles = get_conditional_styles(table_data[1:], start_row=1, start_col=0)
    
    t.setStyle(TableStyle(base_styles + cond_styles))

    
    elements.append(t)
    elements.append(Spacer(1, 2*cm))
    
    # Signature Blocks
    sig_data = [
        ["Chef de Service Commercial", "", "Service Comptabilité"]
    ]
    t_sig = Table(sig_data, colWidths=[8*cm, 5*cm, 8*cm])
    t_sig.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('MINROWHEIGHT', (1,0), (1,0), 2*cm),
    ]))
    
    elements.append(t_sig)
    
    doc.build(elements)
    return output_path

def generate_grand_livre_pdf(data, period, output_path=None):
    """
    Generate Detailed Grand Livre PDF
    """
    if output_path is None:
        if not os.path.exists("Exports_PDF"): os.makedirs("Exports_PDF")
        output_path = os.path.join("Exports_PDF", f"Grand_Livre_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
        
    doc = SimpleDocTemplate(output_path, pagesize=landscape(A4),
                            rightMargin=1*cm, leftMargin=1*cm,
                            topMargin=1*cm, bottomMargin=1*cm)
    
    elements = []
    
    from reportlab.platypus import PageBreak, Image as ReportLabImage
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        alignment=1, # CENTER
        spaceAfter=10
    )
    subtitle_style = ParagraphStyle(
        'CustomSubTitle',
        parent=styles['Normal'],
        fontSize=12,
        alignment=1,
        spaceAfter=20
    )
    
    # Check if data exists
    if not data:
        elements.append(Paragraph("Aucune donnée trouvée pour la période.", styles['Normal']))
        doc.build(elements)
        return output_path

    # Iterate Clients
    for idx, client_data in enumerate(data):
        if idx > 0:
            elements.append(PageBreak())
            
        client = client_data['client']
        
        # --- HEADER ---
        # Logo Logic (Simplified)
        logo_path = "logo_entete.png" if os.path.exists("logo_entete.png") else "logo.png"
        if os.path.exists(logo_path):
            im = ReportLabImage(logo_path, width=4*cm, height=2.5*cm) # Adjust aspect ratio
            # Use a Table for Header Layout to center Title and align Logo
            # Col1: Logo, Col2: Title Info
            start_fmt = datetime.strptime(period['start'], '%Y-%m-%d').strftime('%d/%m/%Y')
            end_fmt = datetime.strptime(period['end'], '%Y-%m-%d').strftime('%d/%m/%Y')
            
            title_text = "<b>GRAND-LIVRE DÉTAILLÉ DES OPÉRATIONS CLIENTS</b>"
            sub_text = f"SITUATION DU {start_fmt} AU {end_fmt}"
            
            header_table_data = [[
                im, 
                [Paragraph(title_text, title_style), Paragraph(sub_text, subtitle_style)]
            ]]
            
            t_head = Table(header_table_data, colWidths=[5*cm, 20*cm])
            t_head.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('ALIGN', (0,0), (0,0), 'LEFT'),
                ('ALIGN', (1,0), (1,0), 'CENTER'),
            ]))
            elements.append(t_head)
        else:
            # Text Only Header
            start_fmt = datetime.strptime(period['start'], '%Y-%m-%d').strftime('%d/%m/%Y')
            end_fmt = datetime.strptime(period['end'], '%Y-%m-%d').strftime('%d/%m/%Y')
            elements.append(Paragraph("GRAND-LIVRE DÉTAILLÉ DES OPÉRATIONS CLIENTS", title_style))
            elements.append(Paragraph(f"SITUATION DU {start_fmt} AU {end_fmt}", subtitle_style))
            
        elements.append(Spacer(1, 0.5*cm))
        
        # Client Info
        c_info = f"<b>CLIENT: {client['raison_sociale']}</b> ({client['code_client'] or 'N/A'})"
        elements.append(Paragraph(c_info, styles['Heading2']))
        elements.append(Spacer(1, 0.3*cm))
        
        # --- TABLE DATA ---
        # Cols: Date, Ref, Libellé, Debit, Credit, Solde
        # Widths: ~27.7cm available (A4 Landscape 29.7 - 2 margins)
        # Date(2.5), Ref(2.5), Lib(9.7), Deb(3.5), Cred(3.5), Solde(4) => 25.7 ok
        col_widths = [2.5*cm, 2.5*cm, 9.7*cm, 3.5*cm, 3.5*cm, 4*cm]
        headers = ["DATE", "RÉF", "LIBELLÉ", "DÉBIT", "CRÉDIT", "SOLDE"]
        
        table_rows = [headers]
        
        # Initial Balance
        s_date = datetime.strptime(period['start'], '%Y-%m-%d').strftime('%d/%m/%Y')
        init_bal = client_data['initial_balance']
        table_rows.append([
            s_date, "-", "SOLDE INITIAL", "", "", format_currency_report(init_bal)
        ])
        
        # Movements
        for mv in client_data['movements']:
            # Formatting
            try: d_str = datetime.strptime(mv['date'], '%Y-%m-%d').strftime('%d/%m/%Y')
            except: d_str = mv['date']
            
            ref = str(mv['ref'])
            lib = mv['libelle']
            deb = format_currency_report(mv['debit']) if mv['debit'] != 0 else "-"
            cred = format_currency_report(mv['credit']) if mv['credit'] != 0 else "-"
            solde = format_currency_report(mv['solde_progressif'])
            
            table_rows.append([d_str, ref, lib, deb, cred, solde])
            
        # Totals
        table_rows.append([
            "", "", "TOTAUX PÉRIODE", 
            format_currency_report(client_data['total_debit']), 
            format_currency_report(client_data['total_credit']), 
            ""
        ])
        
        # Final
        e_date = datetime.strptime(period['end'], '%Y-%m-%d').strftime('%d/%m/%Y')
        fin_bal = client_data['final_balance']
        table_rows.append([
            "", "", f"SOLDE FINAL AU {e_date}", 
            "", "", format_currency_report(fin_bal)
        ])
        
        # Create Table
        t = Table(table_rows, colWidths=col_widths, repeatRows=1)
        
        # Styles
        tbl_styles = [
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), # Header Bold
            ('ALIGN', (0,0), (-1,0), 'CENTER'), # Header Align
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey), # Header BG
            
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('ALIGN', (0,0), (1,-1), 'CENTER'), # Date/Ref Center
            ('ALIGN', (3,0), (-1,-1), 'RIGHT'), # Numbers Right
            
            # Initial Solde Row (Row 1)
            ('BACKGROUND', (2,1), (2,1), colors.whitesmoke),
            ('FONTNAME', (2,1), (2,1), 'Helvetica-Bold'),
            
            # Totals Row (Second to last)
            ('BACKGROUND', (2,-2), (4,-2), colors.lightgrey),
            ('FONTNAME', (2,-2), (4,-2), 'Helvetica-Bold'),
            
            # Final Row (Last)
            ('BACKGROUND', (2,-1), (2,-1), colors.wheat), # Highligh Label
            ('BACKGROUND', (5,-1), (5,-1), colors.wheat), # Highlight Value
            ('FONTNAME', (2,-1), (-1,-1), 'Helvetica-Bold'),
        ]
        
        # Conditional Formatting Loop
        # Row 0 is Header. 
        # Row 1 is Init.
        # Rows 2 to (-2) are movements.
        
        # We need to map table row index to movement index to check 'is_cancelled'
        # Table Row i corresponds to movement i-2 (since row 0=Head, row 1=Init)
        # Length of movements = len(table_rows) - 3 (Head, Init, Totals, Final ... wait 4 rows extra?)
        # Let's count properly:
        # Rows: Head(0) -> Init(1) -> Moves(2...N) -> Total(N+1) -> Final(N+2)
        
        start_moves = 2
        moves = client_data['movements']
        
        for i, mv in enumerate(moves):
            row_idx = start_moves + i
            if mv.get('is_cancelled'):
                # Orange Text
                tbl_styles.append(('TEXTCOLOR', (0, row_idx), (-1, row_idx), colors.orange))
                tbl_styles.append(('FONTNAME', (0, row_idx), (-1, row_idx), 'Helvetica-Bold'))
                
            # Solde Color (Positive = Advance = Blue, Negative = Debt = Black)
            # Solde is Col 5
            try:
                val = float(mv['solde_progressif'])
                if val > 0.001:
                    tbl_styles.append(('TEXTCOLOR', (5, row_idx), (5, row_idx), colors.blue))
                else:
                    # Debt or Zero
                    if not mv.get('is_cancelled'):
                        tbl_styles.append(('TEXTCOLOR', (5, row_idx), (5, row_idx), colors.black))
            except: pass
            
        # Final Row Solde Color
        try:
            val = float(fin_bal)
            if val > 0.001: # Advance
                tbl_styles.append(('TEXTCOLOR', (5, -1), (5, -1), colors.blue))
            else: # Debt
                tbl_styles.append(('TEXTCOLOR', (5, -1), (5, -1), colors.black))
        except: pass

        t.setStyle(TableStyle(tbl_styles))
        elements.append(t)
        
    doc.build(elements, canvasmaker=NumberedCanvas)
    return output_path

