
import os
import sys
from datetime import datetime

# Adjust path to find modules
sys.path.append('c:/GICA_PROJET')

try:
    from word_exports import generate_relance_word
except ImportError as e:
    print(f"Error importing word_exports: {e}")
    sys.exit(1)

def test_relance_generation():
    print("Testing Relance Generation...")

    # Mock Data
    mock_data = {
        'client': {
            'raison_sociale': 'SARL CONSTRUCTION DURABLE',
            'adresse': '123 RUE DE L\'USINE, ZONE INDUSTRIELLE, ALGER',
            'convention_n': 'CV-2025/001', # Optional, can be None
            'date_effet': '01/01/2025',
            'date_fin': '31/12/2025'
        },
        'balance': {
            'total_dette': 1250400.00
        },
        'period': {
            'start': '01/01/2025',
            'end': '31/01/2025'
        },
        'invoices': [
            {'numero': 'FACT-001', 'date': '2025-01-10', 'montant_ttc': 500000.00},
            {'numero': 'FACT-002', 'date': '2025-01-15', 'montant_ttc': 250000.00},
            {'numero': 'FACT-005', 'date': '2025-01-20', 'montant_ttc': 500400.00}
        ]
    }

    try:
        output_file = generate_relance_word(mock_data)
        print(f"SUCCESS: Generated Relance at: {output_file}")
        
        # Verify file exists
        if os.path.exists(output_file):
            print("File exists on disk.")
            # Optional: Ask user to check it manually or use startfile
            # os.startfile(output_file) 
        else:
            print("ERROR: File not found on disk.")
            
    except Exception as e:
        print(f"FAILURE: Generation failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_relance_generation()
