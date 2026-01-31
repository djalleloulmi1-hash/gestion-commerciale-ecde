import os
from datetime import datetime
from utils import generate_daily_sales_pdf, preview_and_print_pdf

def verify_daily_sales_pdf():
    # Mock data structure matching what logic.get_daily_sales_stats returns
    mock_data = {
        'date': datetime.now().strftime("%Y-%m-%d"),
        'details': [
            {
                'code_client': 'CL001',
                'client': 'Client Test A',
                'code_produit': 'CP001',
                'produit': 'Ciment CPJ42 (Sacs)',
                'facture_num': 'FAC-001',
                'date': '2023-10-27',
                'qte': 32.0,
                'ht': 32000.0,
                'tva': 6080.0,
                'ttc': 38080.0
            },
            {
                'code_client': 'CL002',
                'client': 'Client Test B',
                'code_produit': 'CP002',
                'produit': 'Ciment Gros Vrac',
                'facture_num': 'FAC-002',
                'date': '2023-10-27',
                'qte': 15.5,
                'ht': 15500.0,
                'tva': 2945.0,
                'ttc': 18445.0
            }
        ],
        'totals': {
            'day_qty': 47.5,
            'day_ht': 47500.0,
            'day_tva': 9025.0,
            'day_ttc': 56525.0,
            'year_net_ht': 1500000.0
        },
        'product_stats': [
            {'nom': 'Ciment CPJ42 (Sacs)', 'daily_qty': 32.0, 'cumul_qty': 500.0},
            {'nom': 'Ciment Gros Vrac', 'daily_qty': 15.5, 'cumul_qty': 200.0},
            {'nom': 'Produit Inactif', 'daily_qty': 0.0, 'cumul_qty': 0.0}
        ]
    }
    
    filename = "test_daily_report.pdf"
    
    print("Generating PDF...")
    try:
        generate_daily_sales_pdf(mock_data, filename)
        print(f"PDF generated successfully: {filename}")
        
        # Try to open it
        print("Opening PDF...")
        # preview_and_print_pdf(filename) 
        # Commented out preview to avoid blocking script execution in agent environment,
        # but user can check the file.
        
    except Exception as e:
        print(f"FAILED to generate PDF: {e}")
        raise

if __name__ == "__main__":
    verify_daily_sales_pdf()
