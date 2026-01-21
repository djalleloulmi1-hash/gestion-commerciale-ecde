import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
import re

def generate_manual_pdf():
    input_file = "MANUAL_CONTENT.md"
    output_file = "Manuel_Utilisateur_Complet_ECDE.pdf"
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    doc = SimpleDocTemplate(
        output_file,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )

    styles = getSampleStyleSheet()
    
    # Custom Styles
    style_title = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=24,
        spaceAfter=30,
        textColor=colors.HexColor('#1a237e')
    )
    
    style_h1 = ParagraphStyle(
        'CustomH1',
        parent=styles['Heading1'],
        fontSize=18,
        spaceBefore=20,
        spaceAfter=10,
        textColor=colors.HexColor('#283593'),
        borderPadding=5,
        borderColor=colors.HexColor('#e8eaf6'),
        borderWidth=0,
        backColor=None
    )
    
    style_h2 = ParagraphStyle(
        'CustomH2',
        parent=styles['Heading2'],
        fontSize=14,
        spaceBefore=15,
        spaceAfter=8,
        textColor=colors.HexColor('#303f9f')
    )
    
    style_body = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=11,
        leading=14,
        spaceAfter=6
    )
    
    style_bullet = ParagraphStyle(
        'CustomBullet',
        parent=styles['Normal'],
        fontSize=11,
        leading=14,
        leftIndent=20,
        spaceAfter=4
    )
    
    style_quote = ParagraphStyle(
        'CustomQuote',
        parent=styles['Normal'],
        fontSize=10,
        leading=12,
        leftIndent=30,
        rightIndent=30,
        spaceBefore=10,
        spaceAfter=10,
        textColor=colors.darkgrey,
        backColor=colors.whitesmoke,
        borderPadding=10
    )

    story = []
    
    # Read Markdown content
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    def parse_bold(text):
        # Replace **text** with <b>text</b>
        return re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)

    current_list_items = []

    def flush_list():
        if current_list_items:
            story.append(ListFlowable(
                current_list_items,
                bulletType='bullet',
                start='circle',
                leftIndent=10
            ))
            current_list_items.clear()
            story.append(Spacer(1, 0.2*cm))

    for line in lines:
        line = line.strip()
        
        if not line:
            flush_list()
            continue
            
        # Parse Line
        parsed_line = parse_bold(line)
        
        if line.startswith('# '):
            flush_list()
            story.append(Paragraph(parsed_line[2:].strip(), style_title))
            story.append(Spacer(1, 1*cm))
            
        elif line.startswith('## '):
            flush_list()
            story.append(Spacer(1, 0.5*cm))
            story.append(Paragraph(parsed_line[3:].strip(), style_h1))
            
        elif line.startswith('### '):
            flush_list()
            story.append(Paragraph(parsed_line[4:].strip(), style_h2))
            
        elif line.startswith('* '):
            # List item
            text = parsed_line[2:].strip()
            # Check for sub-items (simple 2-space indent assumed in processing, but here we strip)
            # Actually, let's handle the indentation from original line if possible? 
            # For simplicity, we just treat all * as bullets. 
            # If the original line had spaces, we might process that.
            # But converting MD lists to ReportLab lists is tricky in a simple loop.
            # We'll use Paragraph with indentation for simplicity or collect them.
            
            # Let's try collecting them
            current_list_items.append(ListItem(Paragraph(text, style_body)))
            
        elif line.startswith('> '):
            flush_list()
            story.append(Paragraph(parsed_line[2:].strip(), style_quote))
            
        elif re.match(r'^\d+\.', line):
             # Ordered list (treated as bullet for simplicity or paragraph)
             flush_list()
             story.append(Paragraph(parsed_line, style_body))
             
        else:
            flush_list()
            # Standard paragraph
            if line == '---':
                story.append(Spacer(1, 0.5*cm))
                # Draw a line? For now, just space.
            else:
                story.append(Paragraph(parsed_line, style_body))

    flush_list()
    
    try:
        doc.build(story)
        print(f"Success: Manual generated at {output_file}")
    except Exception as e:
        print(f"Error generating PDF: {e}")

if __name__ == "__main__":
    generate_manual_pdf()
