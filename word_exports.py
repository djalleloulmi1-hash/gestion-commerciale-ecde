"""
Word Export Module for ECDE Commercial Management
Handles generation of .docx reports mirroring existing PDF layouts.
"""

import os
import shutil
from datetime import datetime
try:
    from docx import Document
    from docx.shared import Cm, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
    from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ROW_HEIGHT_RULE
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
except ImportError:
    print("python-docx not installed.")
    Document = None

# ==================== HELPERS ====================

def check_logo_exists():
    "Check if logo exists, prioritizing logo_entete.png, then logo.png"
    # Helper duplicated from utils to avoid circular imports if utils imports this
    logo_names = ["logo_entete.png", "logo.png", "logo_gica.png"]
    for name in logo_names:
        if os.path.exists(name):
            return name
        # Check resource path manually if needed, but os.path.exists usually works
    return None

def format_currency(value):
    """Format currency (2 decimals, space separator) - Matches utils.format_currency"""
    if value is None: value = 0.0
    try:
        s = f"{float(value):,.2f}"
        return s.replace(",", " ").replace(".", ",")
    except:
        return "0,00"

def set_repeat_table_header(row):
    """Set table row as header to repeat on each page"""
    tr = row._tr
    trPr = tr.get_or_add_trPr()
    tblHeader = OxmlElement('w:tblHeader')
    trPr.append(tblHeader)
    return row

def set_cell_background(cell, hex_color):
    """Set cell background color (hex string without #)"""
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:fill'), hex_color)
    tcPr.append(shd)

def create_base_document(landscape=False):
    """Create a Document with A4 page size and standard margins"""
    if Document is None:
        return None
    
    doc = Document()
    section = doc.sections[0]
    
    # A4 Dimensions
    if landscape:
        section.page_height = Cm(21)
        section.page_width = Cm(29.7)
        section.orientation = WD_ALIGN_PARAGRAPH.LEFT # Actually enum values but this doesn't set orientation directly in python-docx properly without width/height swap
    else:
        section.page_height = Cm(29.7)
        section.page_width = Cm(21)
    
    # Margins
    section.top_margin = Cm(1.0)
    section.bottom_margin = Cm(1.0)
    section.left_margin = Cm(1.0)
    section.right_margin = Cm(1.0)
    
    return doc

def add_header(doc, title, subtitle=None, date_str=None, landscape=False):
    """Add standard header with Logo and Title"""
    # Use a table for layout: Logo Left, Text Center
    header_table = doc.add_table(rows=1, cols=2)
    header_table.autofit = False
    header_table.allow_autofit = False
    
    # Widths
    logo_col_width = Cm(4)
    text_col_width = Cm(24 if landscape else 15)
    
    header_table.columns[0].width = logo_col_width
    header_table.columns[1].width = text_col_width
    
    # Logo
    logo_path = check_logo_exists()
    cell_logo = header_table.cell(0, 0)
    if logo_path:
        paragraph = cell_logo.paragraphs[0]
        paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
        run = paragraph.add_run()
        run.add_picture(logo_path, width=Cm(3.5), height=Cm(2.0))
        
    # Text
    cell_text = header_table.cell(0, 1)
    p = cell_text.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    run1 = p.add_run("GROUPE INDUSTRIEL DES CIMENTS D'ALGERIE\n")
    run1.font.name = 'Helvetica'
    run1.font.size = Pt(10)
    
    run2 = p.add_run("ENTREPRISE DES CIMENTS ET DERIVES D'ECH-CHELIFF\n")
    run2.font.name = 'Helvetica' # bold
    run2.bold = True
    run2.font.size = Pt(12)
    
    run3 = p.add_run(f"\n{title}\n")
    run3.font.name = 'Helvetica' # bold
    run3.bold = True
    run3.font.size = Pt(16)
    
    if subtitle:
        run4 = p.add_run(f"{subtitle}\n")
        run4.font.name = 'Helvetica'
        run4.font.size = Pt(11)
        
    if date_str:
        run5 = p.add_run(f"{date_str}")
        run5.font.name = 'Helvetica'
        run5.font.size = Pt(11)
        
    doc.add_paragraph() # Spacer

def style_table(table):
    """Apply standard borders and styling"""
    table.style = 'Table Grid'
    # Additional manual borders can be complicated in python-docx, relying on 'Table Grid' for now which puts borders everywhere.

def ensure_export_dir():
    directory = "Exports_Word"
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory

# ==================== REPORTS ====================

def generate_situation_word(data):
    """Situation Client"""
    doc = create_base_document(landscape=False)
    
    client = data['client']
    balance = data['balance']
    date_str = f"Date: {datetime.now().strftime('%d/%m/%Y')}"
    
    add_header(doc, "SITUATION CLIENT", date_str=date_str)
    
    # Client Info
    p = doc.add_paragraph()
    p.add_run(f"Client: {client['raison_sociale']}\n").bold = True
    p.add_run(f"Adresse: {client['adresse']}")
    
    doc.add_paragraph()
    
    # Balance Summary Table
    table = doc.add_table(rows=6, cols=2)
    style_table(table)
    table.autofit = False
    
    # Header
    row = table.rows[0]
    set_repeat_table_header(row)
    cell = row.cells[0]
    cell.merge(row.cells[1])
    cell.text = "Résumé Financier"
    cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    cell.paragraphs[0].runs[0].bold = True
    set_cell_background(cell, "D3D3D3") # Light Grey
    
    # Data
    rows_data = [
        ("Report N-1:", balance['report']),
        ("Total Factures:", balance['total_factures']),
        ("Total Paiements:", balance['total_paiements']),
        ("Total Avoirs:", balance['total_avoirs']),
        ("SOLDE ACTUEL:", balance['solde'])
    ]
    
    for i, (label, val) in enumerate(rows_data):
        r = table.rows[i+1]
        r.cells[0].text = label
        r.cells[1].text = f"{format_currency(val)} DA" if i == 4 else format_currency(val)
        r.cells[1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
        
        if i == 4: # Solde Row
            r.cells[0].paragraphs[0].runs[0].bold = True
            r.cells[1].paragraphs[0].runs[0].bold = True
            set_cell_background(r.cells[0], "F5F5F5")
            set_cell_background(r.cells[1], "F5F5F5")

    directory = ensure_export_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_name = "".join([c for c in client['raison_sociale'] if c.isalnum() or c in (' ', '_')]).strip()
    filename = os.path.join(directory, f"Situation_{clean_name}_{timestamp}.docx")
    
    doc.save(filename)
    return filename

def generate_daily_sales_word(data):
    """État Journalier des Ventes"""
    doc = create_base_document(landscape=True)
    
    date_fmt = data['date'] # Already formatted or YYYY-MM-DD? usually string
    # Move Header to Word Header Section for repetition
    section = doc.sections[0]
    header = section.header
    
    # Custom Header (Matched to Sales by Category style)
    header_table = header.add_table(rows=1, cols=3, width=Cm(27.7))
    header_table.autofit = False
    
    header_table.columns[0].width = Cm(3.0)
    header_table.columns[1].width = Cm(21.7) 
    header_table.columns[2].width = Cm(3.0)
    
    # Logo
    logo_path = check_logo_exists()
    cell_logo = header_table.cell(0, 0)
    if logo_path:
        p = cell_logo.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        run = p.add_run()
        run.add_picture(logo_path, width=Cm(2.9), height=Cm(1.8))
        
    # Text
    cell_text = header_table.cell(0, 1)
    p = cell_text.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    run1 = p.add_run("GROUPE INDUSTRIEL DES CIMENTS D'ALGERIE\n")
    run1.font.name = 'Cambria'
    run1.font.size = Pt(16) 
    run1.bold = True
    
    run2 = p.add_run("ENTREPRISE DES CIMENTS ET DERIVES D'ECH-CHELIFF\n")
    run2.font.name = 'Cambria'
    run2.bold = True
    run2.font.size = Pt(11) 
    
    # Title Section (Also in Header)
    p_title = header.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_title = p_title.add_run("\nETAT DES VENTES QUOTIDIENNES\n")
    r_title.font.name = 'Cambria'
    r_title.font.size = Pt(14)
    r_title.bold = True
    
    r_sub = p_title.add_run("Dépôt Oued Smar\n")
    r_sub.font.name = 'Cambria'
    r_sub.font.size = Pt(11)
    r_sub.bold = True
    r_sub.underline = True
    
    r_date = p_title.add_run(f"Journée du : {date_fmt}")
    r_date.font.name = 'Cambria'
    r_date.font.size = Pt(11)
    r_date.bold = True
    r_date.underline = True
    
    # Pagination in Footer
    footer = section.footer
    p_foot = footer.paragraphs[0]
    p_foot.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_foot.add_run("Page ")
    
    # Page field
    run_page = p_foot.add_run()
    fldChar1 = OxmlElement('w:fldChar')
    fldChar1.set(qn('w:fldCharType'), 'begin')
    run_page._r.append(fldChar1)
    
    run_instr = p_foot.add_run()
    instrText = OxmlElement('w:instrText')
    instrText.set(qn('xml:space'), 'preserve')
    instrText.text = "PAGE"
    run_instr._r.append(instrText)
    
    run_end = p_foot.add_run()
    fldChar2 = OxmlElement('w:fldChar')
    fldChar2.set(qn('w:fldCharType'), 'end')
    run_end._r.append(fldChar2)
    
    p_foot.add_run(" / ")
    
    # NumPages field
    run_numpages = p_foot.add_run()
    fldChar3 = OxmlElement('w:fldChar')
    fldChar3.set(qn('w:fldCharType'), 'begin')
    run_numpages._r.append(fldChar3)
    
    run_instr2 = p_foot.add_run()
    instrText2 = OxmlElement('w:instrText')
    instrText2.set(qn('xml:space'), 'preserve')
    instrText2.text = "NUMPAGES"
    run_instr2._r.append(instrText2)
    
    run_end2 = p_foot.add_run()
    fldChar4 = OxmlElement('w:fldChar')
    fldChar4.set(qn('w:fldCharType'), 'end')
    run_end2._r.append(fldChar4)
    
    
    doc.add_paragraph() # Spacer in body
    
    # Table Details
    headers = ['Clients', 'Produit\nCode', 'Facture\nN.', 'Facture\nDate', 'Qte', 'HT', 'M.remise', 'TVA', 'TTC']
    # Widths approximation for A4 Landscape
    widths = [Cm(4.5), Cm(2.2), Cm(2.2), Cm(2.2), Cm(1.8), Cm(2.5), Cm(1.5), Cm(2.5), Cm(2.8)]
    
    table = doc.add_table(rows=1, cols=len(headers))
    style_table(table)
    table.autofit = False
    
    # Header Row
    hdr_cells = table.rows[0].cells
    set_repeat_table_header(table.rows[0])
    
    for i, text in enumerate(headers):
        hdr_cells[i].text = text
        hdr_cells[i].paragraphs[0].runs[0].bold = True
        hdr_cells[i].paragraphs[0].runs[0].font.name = 'Cambria'
        hdr_cells[i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_cell_background(hdr_cells[i], "D3D3D3")
        if i == 6: # M.remise Column (index 6 after removal)
             pass # Removed Yellow Background
        table.columns[i].width = widths[i]
        
    # Data
    for row in data['details']:
        tr = table.add_row()
        cells = tr.cells
        
        cells[0].text = str(row['client'])
        cells[1].text = str(row['code_produit'] or row['produit'][:10])
        cells[2].text = str(row['facture_num'])
        
        # Date fmt
        try:
            d_obj = datetime.strptime(row['date'], '%Y-%m-%d')
            d_txt = d_obj.strftime('%d-%b-%y')
        except:
            d_txt = row['date']
        cells[3].text = d_txt
        
        cells[4].text = f"{row['qte']:,.3f}".replace(",", " ").replace(".", ",")
        cells[5].text = format_currency(row['ht'])
        cells[6].text = "0,00"
        cells[7].text = format_currency(row['tva'])
        cells[8].text = format_currency(row['ttc'])
        
        # Font Cambria & MR Yellow
        for idx in range(9):
            p = cells[idx].paragraphs[0]
            if len(p.runs) > 0: p.runs[0].font.name = 'Cambria'
            else: p.add_run().font.name = 'Cambria' # Ensure run exists
            
            p.runs[0].font.size = Pt(10)
            p.runs[0].bold = True # Looks bold in screenshot
            
            if idx == 6: # M.remise
                pass # Removed Yellow


        # Align numbers
        # Align numbers
        for idx in range(4, 9):
            cells[idx].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT

    # Total Row Details
    totals = data['totals']
    tr = table.add_row()
    cells = tr.cells
    cells[3].text = "TOTAL"
    cells[3].paragraphs[0].runs[0].bold = True
    cells[3].paragraphs[0].runs[0].font.name = 'Cambria'
    cells[3].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
    
    cells[4].text = f"{totals['day_qty']:,.3f}".replace(",", " ").replace(".", ",")
    cells[5].text = format_currency(totals['day_ht'])
    cells[6].text = "0,00"
    cells[7].text = format_currency(totals['day_tva'])
    cells[8].text = format_currency(totals['day_ttc'])
    
    for idx in range(4, 9):
         p = cells[idx].paragraphs[0]
         p.runs[0].bold = True
         p.runs[0].font.name = 'Cambria'
         p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
         if idx == 6: pass # set_cell_background(cells[idx], "FFFF00")
    
    
    doc.add_paragraph()
    
    # Summary Table (Products)
    headers_sum = ['Désignation', 'Qte Journée', 'Qte Cumulée']
    table_sum = doc.add_table(rows=1, cols=3)
    style_table(table_sum)
    table_sum.autofit = False
    
    set_repeat_table_header(table_sum.rows[0])
    h_cells = table_sum.rows[0].cells
    for i, h in enumerate(headers_sum):
        h_cells[i].text = h
        h_cells[i].paragraphs[0].runs[0].bold = True
        h_cells[i].paragraphs[0].runs[0].font.name = 'Cambria'
        set_cell_background(h_cells[i], "F5F5F5")
    
    # Increased by 15% from the 40% reduced size: 4.2 -> 4.83; 2.1 -> 2.415
    # Note: table.columns[].width is often ignored by Word if autofit is off but cells aren't set
    col_widths = [Cm(4.83), Cm(2.42), Cm(2.42)]
    for i in range(3):
        table_sum.columns[i].width = col_widths[i]
        h_cells[i].width = col_widths[i]

    for p in data['product_stats']:
        tr = table_sum.add_row()
        tr.cells[0].text = p['nom']
        tr.cells[1].text = f"{p['daily_qty']:,.3f}".replace(",", " ").replace(".", ",")
        tr.cells[2].text = f"{p['cumul_qty']:,.3f}".replace(",", " ").replace(".", ",")
        for i in range(3):
            tr.cells[i].width = col_widths[i]
            
    doc.add_paragraph()
    
    # Footer Totals
    # Footer Totals (Blue Bar)
    # Use a 2-col table to simulate the bar: Label Left, Value Right
    # "TOTAL ANNEE HT:"    "2 019 312,00 DA"
    
    footer_table = doc.add_table(rows=1, cols=2)
    footer_table.autofit = False
    footer_table.columns[0].width = Cm(15)
    footer_table.columns[1].width = Cm(10)
    
    fc = footer_table.rows[0].cells
    
    fc[0].text = "TOTAL ANNEE HT:"
    fc[1].text = f"{format_currency(totals['year_net_ht'])} DA"
    
    for c in fc:
        set_cell_background(c, "4F81BD") # Blue color from screenshot equivalent
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.runs[0]
        run.bold = True
        run.font.name = 'Cambria'
        run.font.color.rgb = RGBColor(0, 0, 0) # Black text? Or White? Screenshot looks like Black text on Blue.
    
    fc[1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
    
    directory = ensure_export_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(directory, f"Ventes_Journalieres_{data['date']}_{timestamp}.docx")
    doc.save(filename)
    return filename

def generate_sales_by_category_word(data, start_date, end_date):
    """État CA par Famille"""
    doc = create_base_document(landscape=True)
    
    # Custom Header for this report (Swapped sizes per user request)
    # Header Table: 3 columns to perfectly center the text [Logo, Text, Spacer]
    header_table = doc.add_table(rows=1, cols=3)
    header_table.autofit = False
    
    # Page width 29.7 - 2cm margins = 27.7cm
    # Adjusted to maximize center space while keeping logo fit:
    # Reduce side columns to 3.0cm to give 21.7cm to text.
    header_table.columns[0].width = Cm(3.0)
    header_table.columns[1].width = Cm(21.7) 
    header_table.columns[2].width = Cm(3.0)
    
    # Logo (Left)
    logo_path = check_logo_exists()
    cell_logo = header_table.cell(0, 0)
    if logo_path:
        paragraph = cell_logo.paragraphs[0]
        paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
        run = paragraph.add_run()
        # Slightly smaller logo to fit in 3cm col
        run.add_picture(logo_path, width=Cm(2.9), height=Cm(1.8))
        
    # Text (Center)
    cell_text = header_table.cell(0, 1)
    p = cell_text.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    run1 = p.add_run("GROUPE INDUSTRIEL DES CIMENTS D'ALGERIE\n")
    run1.font.name = 'Cambria'
    # First line Larger (16pt to match visual dominance)
    run1.font.size = Pt(16) 
    run1.bold = True
    
    run2 = p.add_run("ENTREPRISE DES CIMENTS ET DERIVES D'ECH-CHELIFF\n")
    run2.font.name = 'Cambria'
    run2.bold = True
    # Second line Smaller (11pt to ensure single line)
    run2.font.size = Pt(11) 
    
    run3 = p.add_run(f"\nÉTAT DU CHIFFRE D'AFFAIRES PÉRIODIQUE PAR FAMILLE D'ARTICLE\n")
    run3.font.name = 'Cambria'
    run3.bold = True
    run3.font.size = Pt(12) 
    
    run4 = p.add_run(f"Période: {start_date} au {end_date}")
    run4.font.name = 'Cambria'
    run4.bold = True # Added bold to match header style
    run4.font.size = Pt(11)
        
    doc.add_paragraph()
    
    grand_total = 0.0
    categories = ["Ciment"] + [k for k in data.keys() if k != "Ciment" and data[k]]
    
    for cat in categories:
        if cat not in data or not data[cat]: continue
        
        p = doc.add_paragraph(f"FAMILLE: {cat.upper()}")
        p.runs[0].bold = True
        p.runs[0].font.name = 'Cambria'
        p.runs[0].font.color.rgb = RGBColor(0x1a, 0x23, 0x7e) # Dark Blue
        
        # Table
        table = doc.add_table(rows=1, cols=3)
        style_table(table)
        table.autofit = False
        table.alignment = WD_TABLE_ALIGNMENT.CENTER # Center table
        
        # Headers: Designation, Qte, Montant HT
        headers = ["Désignation", "Quantité", "Montant HT"]
        
        row = table.rows[0]
        set_repeat_table_header(row)
        for i, text in enumerate(headers):
            row.cells[i].text = text
            row.cells[i].paragraphs[0].runs[0].bold = True
            row.cells[i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            set_cell_background(row.cells[i], "1A237E") # Dark Blue
            row.cells[i].paragraphs[0].runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF) # White
            
        table.columns[0].width = Cm(10.5) 
        table.columns[1].width = Cm(2.45)  
        table.columns[2].width = Cm(3.15)  
        
        subtotal = 0.0
        
        for idx, item in enumerate(data[cat]):
            tr = table.add_row()
            tr.cells[0].text = item['nom']
            tr.cells[0].paragraphs[0].runs[0].font.name = 'Cambria'
            
            tr.cells[1].text = f"{item['qte']:,.3f}".replace(",", " ").replace(".", ",")
            tr.cells[1].paragraphs[0].runs[0].font.name = 'Cambria'
            tr.cells[1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            tr.cells[2].text = format_currency(item['montant_ht'])
            tr.cells[2].paragraphs[0].runs[0].font.name = 'Cambria'
            tr.cells[2].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            # Alternate Background Colors (White / Light Grey)
            if idx % 2 != 0: # Odd index = Even row number (2nd, 4th...) since 0 is 1st
                for c in tr.cells:
                    set_cell_background(c, "F5F5F5")
            
            subtotal += item['montant_ht']
            
        # Subtotal Row
        tr = table.add_row()
        tr.cells[1].text = "SOUS-TOTAL"
        tr.cells[1].paragraphs[0].runs[0].bold = True
        tr.cells[1].paragraphs[0].runs[0].font.name = 'Cambria'
        tr.cells[1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
        
        tr.cells[2].text = format_currency(subtotal)
        tr.cells[2].paragraphs[0].runs[0].bold = True
        tr.cells[2].paragraphs[0].runs[0].font.name = 'Cambria'
        tr.cells[2].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_cell_background(tr.cells[2], "D3D3D3")
        
        grand_total += subtotal
        doc.add_paragraph()
        
    # Grand Total
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = p.add_run(f"TOTAL GÉNÉRAL HT: {format_currency(grand_total)} DA")
    run.bold = True
    run.font.name = 'Cambria'
    run.font.size = Pt(14)
    
    # Signatures
    doc.add_paragraph()
    doc.add_paragraph()
    
    sig_table = doc.add_table(rows=1, cols=2)
    sig_table.autofit = False
    sig_table.columns[0].width = Cm(9.8)
    sig_table.columns[1].width = Cm(9.8)
    
    c1 = sig_table.cell(0, 0)
    p1 = c1.paragraphs[0]
    p1.add_run("LE FACTURIER").bold = True
    p1.alignment = WD_ALIGN_PARAGRAPH.LEFT
    
    c2 = sig_table.cell(0, 1)
    p2 = c2.paragraphs[0]
    p2.add_run("LE CHEF DE SERVICE COMMERCIAL").bold = True
    p2.alignment = WD_ALIGN_PARAGRAPH.LEFT # User said "a gauche", assuming left align in Right column?
    
    directory = ensure_export_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(directory, f"CA_Par_Famille_{start_date}_{end_date}_{timestamp}.docx")
    doc.save(filename)
    return filename

def generate_stock_valuation_word(data):
    """Rapport Stock Valorisé"""
    doc = create_base_document(landscape=True)
    
    prod_name = data['product']['nom']
    period_str = f"DU : {data['period']['start']}   AU : {data['period']['end']}"
    
    add_header(doc, "ETAT DES MOUVEMENTS DES STOCKS (VALORISES)", 
              subtitle=f"PRODUIT : {prod_name}\nUNITE : {data['product']['unite']}", 
              date_str=period_str, landscape=True)
              
    doc.add_paragraph()
    
    # Table structure
    # Header 1: JOURNEE | STOCK INITIAL | P.UNITAIRE | RECEPTIONS | VENTES | STOCK FINAL
    # Header 2:         | QTE | VAL     |            | QTE | VAL  | QTE | VAL | QTE | VAL
    
    # We will use a single header row for simplicity in Word or merge cells?
    # Word tables support merging.
    
    table = doc.add_table(rows=2, cols=10)
    style_table(table)
    table.autofit = False
    set_repeat_table_header(table.rows[0])
    set_repeat_table_header(table.rows[1])
    
    # Col Widths: 2.5cm each approx
    for i in range(10):
        table.columns[i].width = Cm(1.75)
        
    # Row 0
    r0 = table.rows[0]
    r0.cells[0].text = "JOURNEE"
    
    r0.cells[1].text = "STOCK INITIAL"
    r0.cells[1].merge(r0.cells[2])
    
    r0.cells[3].text = "P.UNITAIRE"
    # r0.cells[3].merge(r0.cells[3]) # No horizontal merge
    
    r0.cells[4].text = "RECEPTIONS"
    r0.cells[4].merge(r0.cells[5])
    
    r0.cells[6].text = "VENTES"
    r0.cells[6].merge(r0.cells[7])
    
    r0.cells[8].text = "STOCK FINAL"
    r0.cells[8].merge(r0.cells[9])
    
    # Vertical Merges (Journee, P.Unit)
    r0.cells[0].merge(table.rows[1].cells[0])
    r0.cells[3].merge(table.rows[1].cells[3])
    
    # Row 1 (Subheaders)
    r1 = table.rows[1]
    subheaders = ["", "QTE", "VAL", "", "QTE", "VAL", "QTE", "VAL", "QTE", "VAL"]
    for i, txt in enumerate(subheaders):
        if txt: r1.cells[i].text = txt
        
    # Style Headers
    for r in table.rows[:2]:
        for cell in r.cells:
            if cell.text.strip():
                p = cell.paragraphs[0]
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p.runs[0].bold = True
                set_cell_background(cell, "D3D3D3")
                
    # Data
    for row in data['data']:
        tr = table.add_row()
        cells = tr.cells
        
        # Date
        try:
            d = datetime.strptime(row['date'], '%Y-%m-%d').strftime('%d/%m/%Y')
        except: d = row['date']
        cells[0].text = d
        
        cells[1].text = format_currency(row['stock_initial_qty'])
        cells[2].text = format_currency(row['stock_initial_val'])
        cells[3].text = format_currency(row['cout_achat'])
        cells[4].text = format_currency(row['reception_qty'])
        cells[5].text = format_currency(row['reception_val'])
        cells[6].text = format_currency(row['vente_qty'])
        cells[7].text = format_currency(row['vente_val'])
        cells[8].text = format_currency(row['stock_final_qty'])
        cells[9].text = format_currency(row['stock_final_val'])
        
        # Coloring Logic (Mirrors get_conditional_styles)
        # Pos > 0 Green, Neg < 0 Orange.
        # Word doesn't support text color easily without Oxml, stick to Black for now or use RGBColor.
        
        for i in range(1, 10):
            try:
                val = float(cells[i].text.replace(" ", "").replace(",", "."))
                p = cells[i].paragraphs[0]
                run = p.runs[0]
                if val > 0.001:
                    run.font.color.rgb = RGBColor(0, 128, 0) # Green
                elif val < -0.001:
                    run.font.color.rgb = RGBColor(255, 152, 0) # Orange
                else:
                    run.font.color.rgb = RGBColor(0, 0, 255) # Blue
            except: pass
            
            cells[i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            
    directory = ensure_export_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_prod = "".join([c for c in prod_name if c.isalnum()]).strip()
    filename = os.path.join(directory, f"Stock_Valorise_{clean_prod}_{timestamp}.docx")
    doc.save(filename)
    return filename

def generate_global_consumption_word(data, date_str):
    """État de Consommation Global"""
    doc = create_base_document(landscape=True)
    
    date_fmt = datetime.strptime(date_str, '%Y-%m-%d').strftime('%d/%m/%Y')
    add_header(doc, "ETAT DE CONSOMMATION GLOBAL", 
              subtitle=None, 
              date_str=f"A FIN : {date_fmt}", landscape=True)
              
    doc.add_paragraph()
    
    # Table Header:
    # Designation | U | JOURNEE | MOIS | ANNEE
    #             |   | Qte | Val | Qte | Val | Qte | Val
    
    table = doc.add_table(rows=2, cols=8)
    style_table(table)
    table.autofit = False
    
    set_repeat_table_header(table.rows[0])
    set_repeat_table_header(table.rows[1])
    
    # Row 0
    r0 = table.rows[0]
    r0.cells[0].text = "Désignation"
    r0.cells[1].text = "U"
    r0.cells[2].text = "JOURNEE"
    r0.cells[2].merge(r0.cells[3])
    r0.cells[4].text = "CUMUL MOIS"
    r0.cells[4].merge(r0.cells[5])
    r0.cells[6].text = "CUMUL ANNEE"
    r0.cells[6].merge(r0.cells[7])
    
    # Vertical Merges
    r0.cells[0].merge(table.rows[1].cells[0])
    r0.cells[1].merge(table.rows[1].cells[1])
    
    # Row 1
    r1 = table.rows[1]
    subheaders = ["", "", "Qté", "Valeur", "Qté", "Valeur", "Qté", "Valeur"]
    for i, txt in enumerate(subheaders):
        if txt: r1.cells[i].text = txt
        
    # Styling Headers
    for r in table.rows[:2]:
        for c in r.cells:
            if c.text:
                c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
                c.paragraphs[0].runs[0].bold = True
                set_cell_background(c, "D3D3D3")
                
    # Column Widths
    widths = [Cm(4.2), Cm(1.05), Cm(2.1), Cm(2.1), Cm(2.1), Cm(2.1), Cm(2.1), Cm(2.1)]
    for i, w in enumerate(widths):
        table.columns[i].width = w
        
    for row in data['data']:
        tr = table.add_row()
        cells = tr.cells
        cells[0].text = row['product_name']
        cells[1].text = row['unit']
        
        cells[2].text = format_currency(row['daily_qty'])
        cells[3].text = format_currency(row['daily_val'])
        cells[4].text = format_currency(row['monthly_qty'])
        cells[5].text = format_currency(row['monthly_val'])
        cells[6].text = format_currency(row['yearly_qty'])
        cells[7].text = format_currency(row['yearly_val'])
        
        # Styling Numbers (2 to 7)
        for i in range(2, 8):
            cells[i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            try:
                val = float(cells[i].text.replace(" ", "").replace(",", "."))
                p = cells[i].paragraphs[0]
                run = p.runs[0]
                if val > 0.001:
                    run.font.color.rgb = RGBColor(0, 128, 0)
                elif val < -0.001:
                    run.font.color.rgb = RGBColor(255, 152, 0)
                else:
                    run.font.color.rgb = RGBColor(0, 0, 255)
            except: pass

    directory = ensure_export_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(directory, f"Etat_Conso_Global_{date_str}_{timestamp}.docx")
    doc.save(filename)
    return filename

def generate_movements_valorises_word(data_result, date_str):
    """Mouvements Valorisés"""
    data = data_result['data']
    totals = data_result['totals']
    
    doc = create_base_document(landscape=True)
    date_fmt = datetime.strptime(date_str, '%Y-%m-%d').strftime('%d/%m/%Y')
    add_header(doc, "ETAT DES MOUVEMENTS DES STOCKS VALORISES", 
              date_str=f"JOURNEE DU {date_fmt}", landscape=True)
    
    doc.add_paragraph()
    
    # Function to create table (Quantities or Values)
    def create_mv_table(title, is_value_table=False):
        doc.add_paragraph(title).runs[0].bold = True
        
        table = doc.add_table(rows=2, cols=12)
        style_table(table)
        table.autofit = False
        set_repeat_table_header(table.rows[0])
        set_repeat_table_header(table.rows[1])
        
        # Headers
        r0 = table.rows[0]
        r1 = table.rows[1]
        
        if is_value_table:
             h1 = ["Désignation", "Cout U.", "JOURNEE", "", "", "MOIS", "", "", "ANNEE", "", "", "VAL. FINALE"]
        else:
             h1 = ["Désignation", "U", "JOURNEE", "", "", "MOIS", "", "", "ANNEE", "", "", "STOCK FINAL"]
             
        # Merges
        r0.cells[0].text = h1[0]
        r0.cells[0].merge(r1.cells[0])
        
        r0.cells[1].text = h1[1]
        r0.cells[1].merge(r1.cells[1])
        
        # Journee
        r0.cells[2].text = "JOURNEE"
        r0.cells[2].merge(r0.cells[4]) # 2, 3, 4
        
        # Mois
        r0.cells[5].text = "MOIS"
        r0.cells[5].merge(r0.cells[7]) # 5, 6, 7
        
        # Annee
        r0.cells[8].text = "ANNEE"
        r0.cells[8].merge(r0.cells[10]) # 8, 9, 10
        
        # Final
        r0.cells[11].text = h1[11]
        r0.cells[11].merge(r1.cells[11])
        
        # Subheaders
        sub = ["", "", "S.Init", "Entrées", "Sorties"] * 3 # We need 3 sets? No.
        # Indices: 2,3,4 | 5,6,7 | 8,9,10
        for i in range(2, 11):
            lbl = ["S.Init", "Entrées", "Sorties"]
            r1.cells[i].text = lbl[(i-2)%3]
            
        # Style
        for r in table.rows[:2]:
            for c in r.cells:
                if c.text:
                    p = c.paragraphs[0]
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    p.runs[0].bold = True
                    set_cell_background(c, "D3D3D3")
                    
        # Widths
        # 12 cols, 28cm.
        # Des: 5cm, U: 2cm. Rem: 10 cols. 21cm left. ~2.1cm each.
        table.columns[0].width = Cm(3.5)
        table.columns[1].width = Cm(1.05)
        for i in range(2, 12):
            table.columns[i].width = Cm(1.5)
            
        return table
        
    # Table 1: Quantities
    t1 = create_mv_table("TABLEAU 1: QUANTITES")
    
    for row in data:
        tr = t1.add_row()
        tr.cells[0].text = row['designation']
        tr.cells[1].text = row['unite']
        tr.cells[2].text = format_currency(row['day']['init'])
        tr.cells[3].text = format_currency(row['day']['in'])
        tr.cells[4].text = format_currency(row['day']['out'])
        tr.cells[5].text = format_currency(row['month']['init'])
        tr.cells[6].text = format_currency(row['month']['in'])
        tr.cells[7].text = format_currency(row['month']['out'])
        tr.cells[8].text = format_currency(row['year']['init'])
        tr.cells[9].text = format_currency(row['year']['in'])
        tr.cells[10].text = format_currency(row['year']['out'])
        tr.cells[11].text = format_currency(row['final'])
        
        for k in range(2, 12):
            tr.cells[k].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            
    # Total T1
    tr = t1.add_row()
    tr.cells[0].text = "TOTAL"
    tr.cells[0].paragraphs[0].runs[0].bold = True
    tr.cells[2].text = format_currency(totals['day']['init'])
    tr.cells[3].text = format_currency(totals['day']['in'])
    tr.cells[4].text = format_currency(totals['day']['out'])
    tr.cells[5].text = format_currency(totals['month']['init'])
    tr.cells[6].text = format_currency(totals['month']['in'])
    tr.cells[7].text = format_currency(totals['month']['out'])
    tr.cells[8].text = format_currency(totals['year']['init'])
    tr.cells[9].text = format_currency(totals['year']['in'])
    tr.cells[10].text = format_currency(totals['year']['out'])
    tr.cells[11].text = format_currency(totals['final'])
    
    for c in tr.cells: set_cell_background(c, "E0E0E0")
    
    doc.add_paragraph()
    
    # Table 2: Values
    t2 = create_mv_table("TABLEAU 2: VALEURS (DA)", is_value_table=True)
    
    v_totals = [0.0] * 10
    
    for row in data:
        tr = t2.add_row()
        tr.cells[0].text = row['designation']
        tr.cells[1].text = format_currency(row['cout_unitaire'])
        tr.cells[2].text = format_currency(row['values']['day']['init'])
        tr.cells[3].text = format_currency(row['values']['day']['in'])
        tr.cells[4].text = format_currency(row['values']['day']['out'])
        tr.cells[5].text = format_currency(row['values']['month']['init'])
        tr.cells[6].text = format_currency(row['values']['month']['in'])
        tr.cells[7].text = format_currency(row['values']['month']['out'])
        tr.cells[8].text = format_currency(row['values']['year']['init'])
        tr.cells[9].text = format_currency(row['values']['year']['in'])
        tr.cells[10].text = format_currency(row['values']['year']['out'])
        tr.cells[11].text = format_currency(row['val_final'])
        
        for k in range(1, 12):
            tr.cells[k].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            
        # Accumulate totals
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

    # Total T2
    tr = t2.add_row()
    tr.cells[0].text = "TOTAL"
    tr.cells[0].paragraphs[0].runs[0].bold = True
    
    # Fill totals
    for i, val in enumerate(v_totals):
        tr.cells[i+2].text = format_currency(val) # +2 because index 0 is Des, 1 is Cout U (skipped for total?)
    
    for c in tr.cells: set_cell_background(c, "E0E0E0")

    directory = ensure_export_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(directory, f"Etat_Mouvements_Stocks_Valorises_{date_str}_{timestamp}.docx")
    doc.save(filename)
    return filename

def generate_annual_receivables_word(data, date_str):
    """État Annuel des Créances"""
    doc = create_base_document(landscape=True)
    date_fmt = datetime.strptime(date_str, "%Y-%m-%d").strftime("%d/%m/%Y")
    
    add_header(doc, "ÉTAT RÉCAPITULATIF ANNUEL DES CRÉANCES ET RECOUVREMENTS CLIENTS", 
              date_str=f"SITUATION AU {date_fmt}", landscape=True)
              
    doc.add_paragraph()
    
    headers = ["Raison Sociale", "Solde au 01/01", "Achats (Année)", "Paiements (Année)", "Solde Final", "% Recouvrement"]
    table = doc.add_table(rows=1, cols=len(headers))
    style_table(table)
    table.autofit = False
    
    set_repeat_table_header(table.rows[0])
    
    for i, h in enumerate(headers):
        table.rows[0].cells[i].text = h
        table.rows[0].cells[i].paragraphs[0].runs[0].bold = True
        table.rows[0].cells[i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_cell_background(table.rows[0].cells[i], "D3D3D3")
        
    # Widths 
    # [5, 4, 4, 4, 4, 3] = 24cm -- plenty of room
    widths = [Cm(4.2), Cm(2.8), Cm(2.8), Cm(2.8), Cm(2.8), Cm(2.1)]
    for i, w in enumerate(widths):
        table.columns[i].width = w
        
    for row in data['data']:
        tr = table.add_row()
        tr.cells[0].text = row['raison_sociale']
        tr.cells[1].text = format_currency(row['solde_01_01'])
        tr.cells[2].text = format_currency(row['achats'])
        tr.cells[3].text = format_currency(row['paiements'])
        tr.cells[4].text = format_currency(row['solde_final'])
        tr.cells[5].text = f"{row['recouvrement']:.1f}%"
        
        for k in range(1, 6):
            tr.cells[k].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
            
    # Totals
    totals = data['totals']
    tr = table.add_row()
    tr.cells[0].text = f"SOLDE GLOBAL AU {date_fmt}"
    tr.cells[0].paragraphs[0].runs[0].bold = True
    
    tr.cells[1].text = format_currency(totals['solde_init'])
    tr.cells[2].text = format_currency(totals['achats'])
    tr.cells[3].text = format_currency(totals['paiements'])
    tr.cells[4].text = format_currency(totals['solde_final'])
    tr.cells[5].text = ""
    
    for c in tr.cells: 
        set_cell_background(c, "E0E0E0")
        c.paragraphs[0].runs[0].bold = True
        
    directory = ensure_export_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(directory, f"Etat_Creances_Annuelles_{date_str}_{timestamp}.docx")
    doc.save(filename)
    return filename

def generate_cancellations_analysis_word(annulations):
    """Analyse des Annulations (Specific Visuals)"""
    doc = create_base_document(landscape=False)
    
    add_header(doc, "ANALYSE DES FACTURES ANNULÉES")
    doc.add_paragraph()
    
    if not annulations:
        doc.add_paragraph("Aucune annulation enregistrée.")
    else:
        # Table of cancellations
        headers = ["DATE", "NUMERO", "MONTANT HT", "MOTIF"]
        table = doc.add_table(rows=1, cols=4)
        style_table(table)
        table.autofit = False
        set_repeat_table_header(table.rows[0])
        
        for i, h in enumerate(headers):
            table.rows[0].cells[i].text = h
            table.rows[0].cells[i].paragraphs[0].runs[0].bold = True
            set_cell_background(table.rows[0].cells[i], "D3D3D3")
            
        table.columns[0].width = Cm(2.1)
        table.columns[1].width = Cm(2.1)
        table.columns[2].width = Cm(2.8)
        table.columns[3].width = Cm(5.6)
        
        total_perdu = 0.0
        by_motif = {}
        
        for row in annulations:
             # Normalize data (tuple vs dict)
            try:
                date_val = str(row['date_annulation'])[:10]
                num = str(row['numero_facture'])
                motif = row['motif']
                mht = row['montant_original_ht']
            except:
                date_val = str(row[2])[:10]
                num = str(row[5])
                motif = row[4]
                mht = row[6]
            
            total_perdu += mht
            if motif not in by_motif: by_motif[motif] = 0
            by_motif[motif] += 1
            
            tr = table.add_row()
            cells = tr.cells
            cells[0].text = date_val
            cells[1].text = num
            cells[2].text = format_currency(mht)
            cells[3].text = motif
            
            # Styling: Orange & Bold
            for c in cells:
                p = c.paragraphs[0]
                run = p.runs[0]
                run.bold = True
                run.font.color.rgb = RGBColor(255, 140, 0) # Dark Orange
            
            # Add watermark text "ANNULÉE" in cells? No, per spec: "Si l'état concerne une facture annulée..."
            # For this report, the whole report is about cancellations.
            # "Le document Word doit simplement refléter l'affichage visuel existant (Police Orange et Grasse)" -> Done above.
            
        doc.add_paragraph()
        p = doc.add_paragraph()
        run = p.add_run(f"TOTAL MANQUE À GAGNER (HT): {format_currency(total_perdu)} DA")
        run.bold = True
        run.font.size = Pt(14)
        run.font.color.rgb = RGBColor(255, 0, 0) # Red
        
        doc.add_paragraph()
        doc.add_paragraph("SYNTHÈSE PAR MOTIF:").runs[0].bold = True
        
        for m, count in by_motif.items():
            doc.add_paragraph(f"- {m}: {count} fois", style='List Bullet')

    directory = ensure_export_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(directory, f"Analyse_Annulations_{timestamp}.docx")
    doc.save(filename)
    return filename
