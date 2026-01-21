import sys
from unittest.mock import MagicMock
import os
import datetime

# Mock the logic module before importing reports
sys.modules['logic'] = MagicMock()
mock_logic = sys.modules['logic']
mock_get_logic = MagicMock()
mock_logic.get_logic = mock_get_logic

# Mock data
mock_data = {
    'data': [
        {
            'designation': f"Product {i}",
            'unite': 'U',
            'cout_unitaire': 100.0,
            'day': {'init': 10, 'in': 5, 'out': 2},
            'month': {'init': 100, 'in': 50, 'out': 20},
            'year': {'init': 1000, 'in': 500, 'out': 200},
            'final': 13,
            'values': {
                'day': {'init': 1000, 'in': 500, 'out': 200},
                'month': {'init': 10000, 'in': 5000, 'out': 2000},
                'year': {'init': 100000, 'in': 50000, 'out': 20000}
            },
            'val_final': 1300
        } for i in range(50) # Generate enough rows to force multiple pages
    ],
    'totals': {
        'day': {'init': 0, 'in': 0, 'out': 0},
        'month': {'init': 0, 'in': 0, 'out': 0},
        'year': {'init': 0, 'in': 0, 'out': 0},
        'final': 0
    }
}

mock_get_logic.return_value.get_movements_valorises_data.return_value = mock_data

# Mock utils if needed (check_logo_exists)
sys.modules['utils'] = MagicMock()
sys.modules['utils'].check_logo_exists.return_value = False # Test without logo first, or mock if we want

# Now import reports
try:
    import reports
    print("Successfully imported reports")
except ImportError as e:
    print(f"ImportError: {e}")
    sys.exit(1)

def test_generate_pdf():
    output_file = "test_header_fix.pdf"
    try:
        reports.generate_movements_valorises_pdf("2026-01-18", output_file)
        print(f"PDF generated successfully: {output_file}")
        if os.path.exists(output_file):
            print("File exists.")
        else:
            print("File not found after generation.")
    except Exception as e:
        print(f"Error generating PDF: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_generate_pdf()
