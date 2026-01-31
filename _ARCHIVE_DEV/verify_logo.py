import utils
import os

print("Testing PDF Generation with Logo...")

# Dummy Data for Invoice
facture_data = {
    'numero': 'TEST-001',
    'type_document': 'Facture',
    'date_facture': '27/12/2025',
    'raison_sociale': 'Client Test',
    'adresse': '123 Rue Test',
    'rc': 'RC123',
    'nis': 'NIS123',
    'nif': 'NIF123',
    'lignes': [
        {'product_nom': 'Ciment CPJ42.5', 'unite': 'Tonne', 'quantite': 10, 'prix_unitaire': 12000, 'montant': 120000}
    ],
    'montant_ht': 120000,
    'montant_tva': 22800,
    'montant_ttc': 142800
}

# Dummy Data for Creances
creance_data = [
    {'client': 'Client Test', 'numero': 'F001', 'date': '01/01/2025', 'montant': 50000}
]

try:
    if os.path.exists("test_invoice.pdf"):
        os.remove("test_invoice.pdf")
    if os.path.exists("test_creance.pdf"):
        os.remove("test_creance.pdf")

    print(f"Logo detected: {utils.check_logo_exists()}")

    utils.generate_invoice_pdf(facture_data, "test_invoice.pdf")
    print("Invoice PDF generated successfully.")

    utils.generate_creances_pdf(creance_data, "test_creance.pdf")
    print("Creances PDF generated successfully.")

except Exception as e:
    print(f"FAILED: {e}")
    exit(1)

print("Verification Passed.")
