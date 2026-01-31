import sqlite3
import pandas as pd
from database import DatabaseManager

def generate_report():
    db = DatabaseManager()
    conn = db._get_connection()
    
    # query to get stock movements with related info
    query = """
        SELECT 
            s.created_at as "Date et Heure Serveur",
            s.type_mouvement as "Type de Mouvement",
            s.reference_document as "ID Document",
            p.nom as "Produit",
            s.stock_avant as "Quantité Avant",
            s.quantite as "Mouvement",
            s.stock_apres as "Quantité Après",
            u.username as "Utilisateur"
        FROM stock_movements s
        JOIN products p ON s.product_id = p.id
        LEFT JOIN users u ON s.created_by = u.id
        WHERE (p.nom LIKE '%CEM I/42.5%' OR p.nom LIKE '%CEMII A-L 42.5%')
          AND s.created_at >= '2026-01-01 00:00:00' 
          AND s.created_at <= '2026-01-14 23:59:59'
        ORDER BY s.created_at ASC
    """
    
    try:
        df = pd.read_sql_query(query, conn)
        
        # Add calculated flux column for clarity if needed, but 'Mouvement' is already signed (usually? check logic)
        # Logic: stock_apres = stock_avant + quantite. So quantite is the signed flux.
        # But for 'Vente', quantity might be stored positive in 'quantite' column but subtracted?
        # Let's check logic:
        # process_reception -> log(..., quantite=q_recue) -> stock + q
        # process_facture -> log(..., quantite=-q_vendu) ? 
        # Waiting for verification.
        # In dump_logs output: Vente 38 has Avant 200, Apres 160. Movements table usually stores signed delta?
        # Or does logic handle sign?
        # Database Schema for stock_movements: "quantite" REAL NOT NULL.
        # In dump logs: 
        # 16: Vente, Avant 200, Apres 160. Diff = -40.
        # Let's assume 'quantite' in stock_movements is the DELTA.
        
        output_file = "Rapport_Audit_Stock_CEM.xlsx"
        
        # Formatting for Excel
        writer = pd.ExcelWriter(output_file, engine='openpyxl') 
        df.to_excel(writer, index=False, sheet_name='Audit Flux')
        
        # Adjust column widths
        worksheet = writer.sheets['Audit Flux']
        for idx, col in enumerate(df.columns):
            max_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
            worksheet.column_dimensions[chr(65 + idx)].width = max_len
            
        writer.close()
        print(f"Rapport généré avec succès : {output_file}")
        
    except Exception as e:
        print(f"Erreur lors de la génération du rapport : {e}")

if __name__ == "__main__":
    generate_report()
