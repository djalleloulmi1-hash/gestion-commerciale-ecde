import sys
import os
from datetime import datetime
from word_exports import generate_daily_sales_word

# Dummy data structure mirroring logic.get_daily_sales_data
data = {
    'date': '2026-01-21',
    'details': [
        {
            'code_client': 'C001',
            'client': 'Client Test',
            'code_produit': 'P001',
            'produit': 'Produit Test',
            'facture_num': 'F12345',
            'date': '2026-01-21',
            'qte': 100.0,
            'ht': 1000.0,
            'tva': 190.0,
            'ttc': 1190.0
        }
    ],
    'totals': {
        'day_qty': 100.0,
        'day_ht': 1000.0,
        'day_tva': 190.0,
        'day_ttc': 1190.0,
        'year_net_ht': 50000.0
    },
    'product_stats': [
        {
            'nom': 'Produit Test',
            'daily_qty': 100.0,
            'cumul_qty': 500.0
        }
    ]
}

try:
    print("Generating Daily Sales Word Report...")
    filename = generate_daily_sales_word(data)
    print(f"Success! Saved to {filename}")
except Exception as e:
    print(f"Caught Exception: {e}")
    import traceback
    traceback.print_exc()
