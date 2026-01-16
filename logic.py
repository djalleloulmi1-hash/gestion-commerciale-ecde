"""
Business Logic Module - Commercial Management System
Handles financial calculations, stock management, and business rules
"""

from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from database import get_db

try:
    import win32print
    WIN32PRINT_AVAILABLE = True
except ImportError:
    WIN32PRINT_AVAILABLE = False


class BusinessLogic:
    """Main business logic handler"""
    
    def __init__(self):
        self.db = get_db()

    # ==================== CA NET CALCULATION ====================
    
    def calculate_ca_net(self, start_date: str, end_date: str) -> float:
        """
        Calculate CA Net logic:
        Result = Sum(All Transaction Amounts HT)
        Since Avoirs are stored as negative values, simple SUM works.
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COALESCE(SUM(montant_ht), 0)
            FROM factures
            WHERE date_facture BETWEEN ? AND ?
            AND statut != 'Annulée'
        """, (start_date, end_date))
        
        return cursor.fetchone()[0]
    
    # ==================== STOCK MANAGEMENT ====================
    
    def process_reception(self, reception_id: int, user_id: int) -> bool:
        """
        Process reception and update stock if 'Sur Stock'
        Returns True if successful
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()
        
        # Get reception details
        cursor.execute("""
            SELECT lieu_livraison, product_id, quantite_recue, numero, date_reception
            FROM receptions WHERE id = ?
        """, (reception_id,))
        reception = cursor.fetchone()
        
        if not reception:
            return False
        
        lieu, product_id, quantite, numero, date_reception = reception
        
        # [CRITICAL] Block Child Products from Reception
        product = self.db.get_product_by_id(product_id)
        if product and product.get('parent_stock_id'):
            # It is a child product (e.g. Price Variation). Reception Forbidden.
            # Stock must be managed on the Parent.
            return False 

        # Only update stock if 'Sur Stock'
        if lieu == 'Sur Stock':
            self.db.log_stock_movement(
                product_id=product_id,
                type_mouvement='Réception',
                quantite=quantite,
                reference_document=numero,
                document_id=reception_id,
                created_by=user_id,
                date_mouvement=date_reception
            )
            
            # Update actual stock quantity is already handled by log_stock_movement
            # self.db.update_stock(product_id, quantite)
        
        return True
    
    def revert_reception_stock_impact(self, reception_id: int) -> bool:
        """
        Revert stock impact for a reception (undo +Qty).
        Used before updating a reception to ensure clean state.
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()
        
        # Get reception details
        cursor.execute("SELECT lieu_livraison, product_id, quantite_recue FROM receptions WHERE id = ?", (reception_id,))
        reception = cursor.fetchone()
        
        if not reception:
            return False
            
        lieu, product_id, quantite = reception
        
        if lieu == 'Sur Stock':
            try:
                # Reverse stock level (Subtract the quantity that was added)
                cursor.execute("UPDATE products SET stock_actuel = stock_actuel - ? WHERE id = ?", (quantite, product_id))
            
                # Delete the specific 'Réception' movement
                cursor.execute("DELETE FROM stock_movements WHERE document_id = ? AND type_mouvement = 'Réception'", (reception_id,))
                
                conn.commit()
                return True
            except Exception as e:
                conn.rollback()
                return False
                
        return True

    def delete_reception(self, reception_id: int) -> bool:
        """
        Delete reception and reverse stock movement if applicable.
        Strategy: Hard Delete / Undo.
        1. Revert stock quantity physically.
        2. Delete the associated stock movement.
        3. Delete the reception record.
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()
        
        # Get reception details
        cursor.execute("SELECT lieu_livraison, product_id, quantite_recue, numero FROM receptions WHERE id = ?", (reception_id,))
        reception = cursor.fetchone()
        
        if not reception:
            return False
            
        lieu, product_id, quantite, numero = reception
        
        try:
            conn.execute("BEGIN TRANSACTION")
            
            if lieu == 'Sur Stock':
                # 1. Reverse stock level physically
                # Since we are deleting the +Q movement, we must subtract Q from current stock
                # to align with the removal of the history.
                cursor.execute("UPDATE products SET stock_actuel = stock_actuel - ? WHERE id = ?", (quantite, product_id))
            
                # 2. Delete all stock movements related to this reception
                cursor.execute("DELETE FROM stock_movements WHERE document_id = ? AND type_mouvement = 'Réception'", (reception_id,))
                
                # Also delete any 'Annulation' artifacts if they exist (cleanup from previous bugs)
                cursor.execute("DELETE FROM stock_movements WHERE document_id = ? AND type_mouvement = 'Annulation Réception'", (reception_id,))
            
            # 3. Delete reception
            cursor.execute("DELETE FROM receptions WHERE id = ?", (reception_id,))
            
            conn.commit()
            return True
            
        except Exception:
            conn.rollback()
            return False

    
    def annuler_facture(self, facture_id: int, user_id: int, motif: str) -> Tuple[bool, str]:
        """
        Annule une facture par neutralisation.
        1. Vérifie si déjà annulée.
        2. Ré-intègre le stock (inverse de la vente).
        3. Journalise l'opération.
        4. Passe les montants à 0 et statut à 'ANNULEE'.
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()
        
        try:
            conn.execute("BEGIN TRANSACTION")
            
            # 1. Fetch Facture
            facture = self.db.get_facture_by_id(facture_id)
            if not facture:
                return False, "Facture introuvable."
            
            if facture.get('statut') == 'ANNULEE' or facture.get('statut_facture') == 'Annulée':
                return False, "Facture déjà annulée."

            if facture['type_document'] != 'Facture':
                 return False, "Seules les factures peuvent être annulées (pas les Avoirs)."

            # 2. Re-credit Stock (Inverse of Invoice)
            # Invoice reduced stock (-Qty), so Cancellation increases it (+Qty).
            # We log this as "Annulation Facture" to be traced.
            
            details_stock = []
            
            for ligne in facture['lignes']:
                pid = ligne['product_id']
                qty = ligne['quantite'] # This is positive in DB for lines
                
                # Check if product exists
                product = self.db.get_product_by_id(pid)
                if product:
                     # Log Movement
                     self.db.log_stock_movement(
                        product_id=pid,
                        type_mouvement='Annulation Facture',
                        quantite=qty, # Positive to add back to stock
                        reference_document=f"Annul {facture['numero']}",
                        document_id=facture_id, # Link to same ID? Or new? Standard is link to Doc.
                        created_by=user_id,
                        date_mouvement=facture['date_facture']
                     )
                     details_stock.append(f"{product['nom']}: +{qty}")

            # 3. Log to Journal_Annulations
            import json
            cursor.execute("""
                INSERT INTO journal_annulations 
                (facture_id, numero_facture, user_id, motif, montant_original_ht, montant_original_ttc, details_stock)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                facture_id, 
                facture['numero'], 
                user_id, 
                motif, 
                facture['montant_ht'], 
                facture['montant_ttc'],
                json.dumps(details_stock, ensure_ascii=False)
            ))
            
            # 4. Neutralize Facture
            # Set amounts to 0.00
            cursor.execute("""
                UPDATE factures 
                SET montant_ht = 0, montant_tva = 0, montant_ttc = 0, 
                    statut = 'ANNULEE', motif_annulation = ?
                WHERE id = ?
            """, (motif, facture_id))
            
            # Set lines to 0? Or keep them for history?
            # User requirement: "Mise à Zéro : Passer toutes les quantités et montants de la facture à 0 en base de données."
            # This is destructive but required.
            cursor.execute("""
                UPDATE lignes_facture
                SET quantite = 0, montant = 0, prix_unitaire = 0
                WHERE facture_id = ?
            """, (facture_id,))
            
            conn.commit()
            return True, "Facture annulée avec succès."
            
        except Exception as e:
            conn.rollback()
            return False, f"Erreur lors de l'annulation: {str(e)}"

    def process_facture_stock(self, facture_id: int, user_id: int) -> bool:
        """
        Process invoice stock impact (decrease for facture, increase for avoir)
        """
        facture = self.db.get_facture_by_id(facture_id)
        if not facture:
            return False
        
        type_document = facture['type_document']
        numero = facture['numero']
        
        # Process each line item
        for ligne in facture['lignes']:
            # For invoices, decrease stock (negative quantity)
            # For credit notes, increase stock (positive quantity)
            if type_document == 'Facture':
                quantite = -ligne['quantite']
                mouvement = 'Vente'
            else:  # Avoir
                quantite = ligne['quantite']
                mouvement = 'Retour Avoir'

            self.db.log_stock_movement(
                product_id=ligne['product_id'],
                type_mouvement=mouvement,
                quantite=quantite,
                reference_document=numero,
                document_id=facture_id,
                created_by=user_id,
                date_mouvement=facture['date_facture']
            )
        
        return True
    
    def is_parent_product(self, product_id: int) -> bool:
        """
        Check if a product is a parent for other products (has children).
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM products WHERE parent_stock_id = ? AND id != ?", (product_id, product_id))
        count = cursor.fetchone()[0]
        return count > 0

    def get_current_stock(self, product_id: int) -> float:
        """Get current stock for a product"""
        product = self.db.get_product_by_id(product_id)
        return product['stock_actuel'] if product else 0.0
    
    def check_stock_availability(self, product_id: int, quantite: float) -> Tuple[bool, float]:
        """
        Check if stock is sufficient for a sale.
        If product has a parent, check parent's stock.
        Returns (is_available, current_stock)
        """
        product = self.db.get_product_by_id(product_id)
        if not product:
            return (False, 0.0)
            
        target_id = product.get('parent_stock_id') or product_id
        
        # If target is different, fetch parent
        if target_id != product_id:
            parent = self.db.get_product_by_id(target_id)
            if parent:
                current_stock = parent['stock_actuel']
            else:
                # Fallback to own stock if parent linking is broken
                current_stock = product['stock_actuel']
        else:
            current_stock = product['stock_actuel']
            
        return (current_stock >= quantite, current_stock)

    def recalculate_global_stock(self) -> Dict[str, int]:
        """
        Repair and Recalculate all stock levels.
        1. Reset stock_actuel = stock_initial for all products.
        2. Ensure all Receptions (Sur Stock) have a stock_movement.
        3. Recalculate stock based on all movements.
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()
        
        stats = {"receptions_fixed": 0, "products_updated": 0}
        
        try:
            conn.execute("BEGIN TRANSACTION")
            
            # 1. Reset Stock to Initial
            cursor.execute("UPDATE products SET stock_actuel = stock_initial")
            
            # 2. Fix Missing Reception Movements
            cursor.execute("SELECT id, product_id, quantite_recue, numero, created_by FROM receptions WHERE lieu_livraison = 'Sur Stock'")
            receptions = cursor.fetchall()
            
            for r in receptions:
                # Check if movement exists
                cursor.execute("""
                    SELECT id FROM stock_movements 
                    WHERE document_id = ? AND type_mouvement = 'Réception' 
                    AND product_id = ?
                """, (r['id'], r['product_id']))
                mv = cursor.fetchone()
                
                if not mv:
                    # Create missing movement
                    # Note: We don't update stock_actuel here, we do it in bulk later or let the loop handle it
                    # actually log_stock_movement updates stock_actuel.
                    # But since we reset to initial, we can just replay all movements.
                    
                    # Wait, log_stock_movement adds to current stock.
                    # If we just reset to initial, we should iterate ALL movements (existing + new) and apply.
                    # OR we can just use SQL to sum them up.
                    
                    # Let's insert the missing movement first.
                    stock_avant = 0 # Placeholder, we will recalc numbers anyway
                    stock_apres = 0 
                    
                    # Correctly attribute to Parent if Child
                    target_pid = r['product_id']
                    
                    # Check if product is child
                    cursor.execute("SELECT parent_stock_id FROM products WHERE id=?", (target_pid,))
                    res = cursor.fetchone()
                    if res and res[0]:
                        target_pid = res[0]
                    
                    cursor.execute("""
                        INSERT INTO stock_movements 
                        (product_id, type_mouvement, quantite, reference_document,
                         document_id, stock_avant, stock_apres, created_by)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (target_pid, 'Réception', r['quantite_recue'], r['numero'],
                          r['id'], stock_avant, stock_apres, r['created_by']))
                    stats["receptions_fixed"] += 1
            
            # 3. Recalculate Stock for ALL Products from Movements
            # Stock = Initial + Sum(Movements)
            
            cursor.execute("SELECT id, stock_initial FROM products")
            products = cursor.fetchall()
            
            for p in products:
                pid = p['id']
                initial = p['stock_initial'] or 0.0
                
                cursor.execute("SELECT SUM(quantite) FROM stock_movements WHERE product_id = ?", (pid,))
                delta = cursor.fetchone()[0] or 0.0
                
                final_stock = initial + delta
                
                cursor.execute("UPDATE products SET stock_actuel = ? WHERE id = ?", (final_stock, pid))
                stats["products_updated"] += 1
            
            conn.commit()
            return stats
            
        except Exception as e:
            conn.rollback()
            raise e
    
    def get_stock_valuation_data(self, product_id: int, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Get daily stock valuation logic.
        """
        import pandas as pd
        
        conn = self.db._get_connection()
        product = self.db.get_product_by_id(product_id)
        if not product:
            return {}
            
        # Cost Price
        cout_achat = product.get('cout_revient', 0.0)
        
        # 1. Calculate Initial Stock (Before Start Date)
        # Base
        stock_initial_db = product.get('stock_initial', 0.0)
        
        # Receptions before start_date
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COALESCE(SUM(quantite_recue), 0)
            FROM receptions 
            WHERE product_id = ? AND date_reception < ? AND lieu_livraison = 'Sur Stock'
        """, (product_id, start_date))
        receptions_before = cursor.fetchone()[0]
        
        # Sales (Factures) before start_date
        # Must join to filter by date AND product
        cursor.execute("""
            SELECT COALESCE(SUM(lf.quantite), 0)
            FROM lignes_facture lf
            JOIN factures f ON lf.facture_id = f.id
            WHERE lf.product_id = ? AND f.date_facture < ? AND f.type_document = 'Facture' AND f.statut != 'Annulée'
        """, (product_id, start_date))
        sales_before = cursor.fetchone()[0]
        
        # Avoirs (Returns) before start_date - Adds to stock
        cursor.execute("""
            SELECT COALESCE(SUM(lf.quantite), 0)
            FROM lignes_facture lf
            JOIN factures f ON lf.facture_id = f.id
            WHERE lf.product_id = ? AND f.date_facture < ? AND f.type_document = 'Avoir' AND f.statut != 'Annulée'
        """, (product_id, start_date))
        avoirs_before = cursor.fetchone()[0]
        
        calculated_initial = stock_initial_db + receptions_before - sales_before + avoirs_before
        
        # 2. Get Daily Movements in Range
        
        # Generate date range
        date_range = pd.date_range(start=start_date, end=end_date)
        daily_data = []
        
        current_stock = calculated_initial
        
        for single_date in date_range:
            day_str = single_date.strftime("%Y-%m-%d")
            
            # Receptions for this day
            cursor.execute("""
                SELECT COALESCE(SUM(quantite_recue), 0)
                FROM receptions
                WHERE product_id = ? AND date_reception = ? AND lieu_livraison = 'Sur Stock'
            """, (product_id, day_str))
            rec_day = cursor.fetchone()[0]
            
            # Sales for this day
            cursor.execute("""
                SELECT COALESCE(SUM(lf.quantite), 0)
                FROM lignes_facture lf
                JOIN factures f ON lf.facture_id = f.id
                WHERE lf.product_id = ? AND f.date_facture = ? AND f.type_document = 'Facture' AND f.statut != 'Annulée'
            """, (product_id, day_str))
            sale_day = cursor.fetchone()[0]
            
            # Avoirs for this day
            cursor.execute("""
                SELECT COALESCE(SUM(lf.quantite), 0)
                FROM lignes_facture lf
                JOIN factures f ON lf.facture_id = f.id
                WHERE lf.product_id = ? AND f.date_facture = ? AND f.type_document = 'Avoir' AND f.statut != 'Annulée'
            """, (product_id, day_str))
            avoir_day = cursor.fetchone()[0]
            
            net_sales = sale_day - avoir_day
            
            stock_start = current_stock
            stock_end = stock_start + rec_day - net_sales
            
            # Values
            daily_data.append({
                "date": day_str,
                "stock_initial_qty": stock_start,
                "stock_initial_val": stock_start * cout_achat,
                "cout_achat": cout_achat,
                "reception_qty": rec_day,
                "reception_val": rec_day * cout_achat,
                "vente_qty": net_sales,
                "vente_val": net_sales * cout_achat,
                "stock_final_qty": stock_end,
                "stock_final_val": stock_end * cout_achat
            })
            
            current_stock = stock_end
            
        return {
            "product": product,
            "period": {"start": start_date, "end": end_date},
            "data": daily_data
        }

    def get_global_consumption_data(self, date_str: str) -> Dict[str, Any]:
        """
        Get global consumption data for a specific date.
        Returns data for Excel/PDF report:
        - Daily Consumption (Day J)
        - Monthly Cumulative (1st of Month -> J)
        - Annual Cumulative (1st of Jan -> J)
        Valuation is based on Product Cost Price (cout_revient).
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()
        
        target_date = datetime.strptime(date_str, "%Y-%m-%d")
        year_start = target_date.replace(month=1, day=1).strftime("%Y-%m-%d")
        month_start = target_date.replace(day=1).strftime("%Y-%m-%d")
        day_str = date_str
        
        # Get all products
        cursor.execute("SELECT id, nom, unite, cout_revient FROM products WHERE active = 1 ORDER BY nom")
        products = cursor.fetchall()
        
        report_data = []
        
        for p in products:
            pid = p['id']
            cout = p['cout_revient'] or 0.0
            
            # Helper to get sum of negative movements (Sales/Consumption)
            # We assume Consumption = Negative Movements (Vente, Sortie, etc)
            # We take ABS() to show positive consumption.
            
            def get_consumption(start_d, end_d):
                # Note: creating a dedicated query for each product/period might be slow if many products.
                # Optimized approach: Filter by date range first, then group by product. 
                # But for simplicity and robustness first:
                query = """
                    SELECT ABS(COALESCE(SUM(quantite), 0))
                    FROM stock_movements
                    WHERE product_id = ? 
                    AND type_mouvement IN ('Vente', 'Sortie', 'Consommation') 
                    AND quantite < 0
                    AND date(created_at) >= ? AND date(created_at) <= ?
                """
                # Note: stock_movements has created_at which is timestamp. 
                # Ideally we should use the DATE of the document (date_facture etc).
                # But stock_movements doesn't store the document date directly, only created_at.
                # However, for consistency with 'Situation', usually we rely on the document date.
                # The stock_movements table has `created_at` which is usually NOW().
                # For `stock_valuation`, I used `receptions` and `factures` tables directly.
                # I should probably do the same here for accuracy if backdating is allowed.
                return 0.0

            # refined approach using Factures table for 'Vente' to respect `date_facture`
            # Consumption = Ventes (Factures) + Retours (Avoirs negative impact? No, Avoir is positive stock).
            # So Consumption is purely Sales (Factures). 
            # Unless there are internal consumptions?
            # User said "Consommation", usually implies Sales in this context or internal usage.
            # verify_movement_types showed 'Vente' and 'Réception'.
            # So strictly 'Vente'.
            
            def get_sales_qty(start_d, end_d):
                 cursor.execute("""
                    SELECT COALESCE(SUM(lf.quantite), 0)
                    FROM lignes_facture lf
                    JOIN factures f ON lf.facture_id = f.id
                    WHERE lf.product_id = ? 
                    AND f.date_facture >= ? AND f.date_facture <= ?
                    AND f.type_document = 'Facture' 
                    AND f.statut != 'Annulée'
                 """, (pid, start_d, end_d))
                 return cursor.fetchone()[0]

            daily_qty = get_sales_qty(day_str, day_str)
            monthly_qty = get_sales_qty(month_start, day_str)
            yearly_qty = get_sales_qty(year_start, day_str)
            
            if daily_qty == 0 and monthly_qty == 0 and yearly_qty == 0:
                continue # Skip products with no movement? Or show all? 
                # Usually reports show active items. Let's keep all or skip empty.
                # User request: "État de Consommation". If nothing consumed, maybe skip.
                # But often "Stock" reports want to see everything.
                # Let's include everything for completeness.
                pass

            report_data.append({
                "product_name": p['nom'],
                "unit": p['unite'],
                "cout_revient": cout,
                "daily_qty": daily_qty,
                "daily_val": daily_qty * cout,
                "monthly_qty": monthly_qty,
                "monthly_val": monthly_qty * cout,
                "yearly_qty": yearly_qty,
                "yearly_val": yearly_qty * cout
            })
            
        return {
            "date": day_str,
            "data": report_data
        }

    # ==================== FINANCIAL CALCULATIONS ====================
    
    def get_annual_receivables_data(self, date_n: str) -> Dict[str, Any]:
        """
        Calculate annual receivables tracking for all clients up to date_n.
        
        Logic:
        1. Start of Year = 01/01/{Year of date_n}
        2. Solde 01/01:
           - Base: client.report_n_moins_1 (Initial Balance)
           - Plus: Movements (Factures - Paiements + Avoirs) BEFORE Start of Year.
        3. Movements Year (Start of Year to date_n):
           - Achats: Sum(Factures)
           - Paiements: Sum(Paiements)
           - Avoirs: Sum(Avoirs) [Usually deducted from Achats or treated as Credit]
             * Rule: "Cumuler les Achats (Débit) et les Paiements (Crédit)"
             * Avoirs are credit notes. They reduce debt.
             * Standard accounting: Solde = Init + Sales - Payments - Avoirs.
             * Or: Sales = Gross Sales - Avoirs?
             * User prompt says "Achats (Débit)" and "Paiements (Crédit)".
             * Where do Avoirs go?
             * Usually Avoirs reduce the "Achats" amount or are added to "Paiements" side (Credits).
             * Let's treat (Achats - Avoirs) as Net Sales? Or allow Avoirs to be separate?
             * The table columns are: | Solde 01/01 | Achats (Année) | Paiements (Année) | Solde Final |
             * Ideally: Achats = Total Factures.
             * Solde Final = Solde 01/01 + Achats - Paiements - Avoirs.
             * IF Avoirs are not in columns, they must be netted from Achats.
             * Let's Net them from Achats: Achats (Net) = Factures - Avoirs.
        
        4. Solde Final = Solde 01/01 + Achats - Paiements.
        5. % Recouvrement = (Paiements / (Solde 01/01 + Achats)) * 100
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()
        
        target_date = datetime.strptime(date_n, "%Y-%m-%d")
        year = target_date.year
        start_year_str = f"{year}-01-01"
        
        # Get all active clients
        cursor.execute("SELECT * FROM clients WHERE active = 1 ORDER BY raison_sociale")
        clients = cursor.fetchall()
        
        results = []
        
        # Totals
        total_solde_init = 0.0
        total_achats = 0.0
        total_paiements = 0.0
        total_solde_final = 0.0
        
        for client in clients:
            cid = client['id']
            report_n_1 = client['report_n_moins_1'] or 0.0
            
            # --- 1. Calculate Solde 01/01 ---
            # Sum movements BEFORE start_year_str
            
            # Invoices before 01/01
            cursor.execute("""
                SELECT COALESCE(SUM(montant_ttc), 0) FROM factures 
                WHERE client_id = ? AND date_facture < ? AND type_document = 'Facture' AND statut != 'Annulée'
            """, (cid, start_year_str))
            hist_factures = cursor.fetchone()[0]
            
            # Avoirs before 01/01
            cursor.execute("""
                SELECT COALESCE(SUM(montant_ttc), 0) FROM factures 
                WHERE client_id = ? AND date_facture < ? AND type_document = 'Avoir' AND statut != 'Annulée'
            """, (cid, start_year_str))
            hist_avoirs = cursor.fetchone()[0]
            
            # Payments before 01/01
            cursor.execute("""
                SELECT COALESCE(SUM(montant), 0) FROM paiements 
                WHERE client_id = ? AND date_paiement < ?
            """, (cid, start_year_str))
            hist_paiements = cursor.fetchone()[0]
            
            # Solde 01/01 = Initial - (Factures - Avoirs) + Paiements
            # User Logic: Negative = Debt. Purchase increases debt ( more negative). Payment reduces debt (adds positive).
            solde_01_01 = report_n_1 - (hist_factures - hist_avoirs) + hist_paiements
            
            # --- 2. Calculate Movements Year (01/01 to date_n) ---
            
            # Achats (Invoices) in range
            cursor.execute("""
                SELECT COALESCE(SUM(montant_ttc), 0) FROM factures 
                WHERE client_id = ? AND date_facture >= ? AND date_facture <= ? 
                AND type_document = 'Facture' AND statut != 'Annulée'
            """, (cid, start_year_str, date_n))
            achats_year = cursor.fetchone()[0]
            
            # Avoirs in range
            cursor.execute("""
                SELECT COALESCE(SUM(montant_ttc), 0) FROM factures 
                WHERE client_id = ? AND date_facture >= ? AND date_facture <= ? 
                AND type_document = 'Avoir' AND statut != 'Annulée'
            """, (cid, start_year_str, date_n))
            avoirs_year = cursor.fetchone()[0]
            
            achats_net = achats_year - avoirs_year
            
            # Paiements in range
            cursor.execute("""
                SELECT COALESCE(SUM(montant), 0) FROM paiements 
                WHERE client_id = ? AND date_paiement >= ? AND date_paiement <= ?
            """, (cid, start_year_str, date_n))
            paiements_year = cursor.fetchone()[0]
            
            # --- 3. Final Balance ---
            # Balance = Init - Purchases + Payments
            solde_final = solde_01_01 - achats_net + paiements_year
            
            # Filter: Include only if Solde Final != 0 OR any movement not 0
            if abs(solde_final) < 0.01 and abs(achats_net) < 0.01 and abs(paiements_year) < 0.01:
                continue
                
            # --- 4. % Recouvrement ---
            # Formula: (Paiements / Available Debt) * 100
            # Available Debt = |Solde Initial - Purchases| (Total Negative Debt Value)
            # If Solde is Positive (Credit), Purchases reduce it. 
            # We use ABS to get the magnitude of the debt obligation constructed.
            denominator = abs(solde_01_01 - achats_net)
            
            if denominator > 0.01:
                recouvrement = (paiements_year / denominator) * 100
            else:
                recouvrement = 0.0
                
            results.append({
                "raison_sociale": client['raison_sociale'],
                "solde_01_01": solde_01_01,
                "achats": achats_net,
                "paiements": paiements_year,
                "solde_final": solde_final,
                "recouvrement": recouvrement
            })
            
            # Update totals
            total_solde_init += solde_01_01
            total_achats += achats_net
            total_paiements += paiements_year
            total_solde_final += solde_final

        # Sort by Raison Sociale? User said "Structure du Tableau Unique", implies list.
        # SQL already sorted by raison_sociale.
        
        return {
            "date": date_n,
            "data": results,
            "totals": {
                "solde_init": total_solde_init,
                "achats": total_achats,
                "paiements": total_paiements,
                "solde_final": total_solde_final
            }
        }

    def calculate_client_balance(self, client_id: int) -> Dict[str, float]:
        """
        Calculate client balance using formula:
        Solde = (Report N-1 + Σ Paiements + Σ Avoirs) - Σ Factures
        
        Returns dict with:
        - report: Report from previous year
        - total_paiements: Sum of all payments
        - total_avoirs: Sum of all credit notes
        - total_factures: Sum of all invoices
        - solde: Final balance (positive = available credit, negative = debt)
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()
        
        # Get report N-1
        cursor.execute("SELECT report_n_moins_1 FROM clients WHERE id = ?", (client_id,))
        report = cursor.fetchone()[0] or 0.0
        
        # Get last closed year
        cursor.execute("SELECT MAX(annee) FROM clotures")
        last_closed_year = cursor.fetchone()[0]
        
        # If no closure, we take all history (or start_year = 0)
        start_year = last_closed_year if last_closed_year else 0
        
        # Sum of payments
        cursor.execute("""
            SELECT COALESCE(SUM(montant), 0) FROM paiements 
            WHERE client_id = ? AND strftime('%Y', date_paiement) > ?
        """, (client_id, str(start_year)))
        total_paiements = cursor.fetchone()[0]
        
        # Sum of credit notes (avoirs)
        cursor.execute("""
            SELECT COALESCE(SUM(montant_ttc), 0) FROM factures 
            WHERE client_id = ? AND type_document = 'Avoir' AND annee > ?
        """, (client_id, start_year))
        total_avoirs = cursor.fetchone()[0]
        
        # Sum of invoices
        cursor.execute("""
            SELECT COALESCE(SUM(montant_ttc), 0) FROM factures 
            WHERE client_id = ? AND type_document = 'Facture' AND annee > ?
        """, (client_id, start_year))
        total_factures = cursor.fetchone()[0]
        
        # Calculate balance
        solde = (report + total_paiements + total_avoirs) - total_factures
        
        return {
            'report': report,
            'total_paiements': total_paiements,
            'total_avoirs': total_avoirs,
            'total_factures': total_factures,
            'solde': solde
        }
    
    def check_credit_limit(self, client_id: int, nouveau_montant: float) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if new invoice would exceed credit limit
        Returns (is_within_limit, balance_info)
        """
        client = self.db.get_client_by_id(client_id)
        if not client:
            return (False, {})
        
        seuil_credit = client['seuil_credit']
        balance_info = self.calculate_client_balance(client_id)
        
        # Calculate future balance after this invoice
        solde_futur = balance_info['solde'] - nouveau_montant
        
        # Check if future balance would be below threshold (more negative than allowed)
        # Positive balance = available credit
        # Negative balance = debt
        # Threshold is the maximum negative balance allowed
        is_within_limit = solde_futur >= -seuil_credit
        
        balance_info['solde_futur'] = solde_futur
        balance_info['seuil_credit'] = seuil_credit
        balance_info['depassement'] = -seuil_credit - solde_futur if not is_within_limit else 0.0
        
        return (is_within_limit, balance_info)
    
    def calculate_facture_totals(self, lignes: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate invoice totals from line items using per-product TVA
        Returns dict with montant_ht, montant_tva, montant_ttc
        """
        montant_ht_total = 0.0
        montant_tva_total = 0.0
        
        for ligne in lignes:
            # Fetch product to get TVA rate
            product = self.db.get_product_by_id(ligne['product_id'])
            tva_rate = product.get('tva', 19.0) if product else 19.0
            
            # ROUNDING FIX: Round at line level
            ligne_ht = round(ligne['quantite'] * ligne['prix_unitaire'], 2)
            ligne_tva = round(ligne_ht * (tva_rate / 100), 2)
            
            montant_ht_total += ligne_ht
            montant_tva_total += ligne_tva
            
        montant_ttc_total = montant_ht_total + montant_tva_total
        
        return {
            'montant_ht': round(montant_ht_total, 2),
            'montant_tva': round(montant_tva_total, 2),
            'montant_ttc': round(montant_ttc_total, 2)
        }
    
    
    def validate_avoir_amount(self, facture_origine_id: int, montant_avoir_ttc: float) -> bool:
        """
        Ensure Avoir amount does not exceed remaining due on original invoice.
        Also checks if original invoice exists.
        For logic strictly as requested: "Montant TTC <= Restant dû" implies we should check 
        (Original Amount - Previous Avoirs).
        """
        facture = self.db.get_facture_by_id(facture_origine_id)
        if not facture:
            return False
        
        montant_facture_ttc = facture['montant_ttc']
        
        # Get all existing avoirs for this invoice
        conn = self.db._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COALESCE(SUM(montant_ttc), 0)
            FROM factures
            WHERE facture_origine_id = ? AND type_document = 'Avoir' AND statut != 'Annulée'
        """, (facture_origine_id,))
        previous_avoirs_ttc = cursor.fetchone()[0]
        
        remaining = montant_facture_ttc - previous_avoirs_ttc
        
        # Allow small epsilon for float comparison or exact
        return montant_avoir_ttc <= (remaining + 0.01)

    # ==================== INVOICE CREATION ====================
    
    def create_invoice_with_validation(self, type_document: str, client_id: int,
                                      lignes: List[Dict[str, Any]], 
                                      facture_origine_id: Optional[int] = None,
                                      etat_paiement: str = 'Comptant',
                                      motif: str = None,
                                      type_vente: str = None, # 'A terme' or 'Au comptant'
                                      mode_paiement: str = None,
                                      ref_paiement: str = None,
                                      banque: str = None,
                                      contract_id: Optional[int] = None,
                                      contrat_code: str = None,
                                      chauffeur: str = None, 
                                      matricule_tracteur: str = None, 
                                      matricule_remorque: str = None,
                                      transporteur: str = None,

                                      client_compte_bancaire: str = None,
                                      client_categorie: str = None,
                                      statut_final: str = 'Brouillon', # 'Brouillon' or 'Validée'
                                      custom_date: str = None, # YYYY-MM-DD
                                      user_id: Optional[int] = None) -> Tuple[bool, str, Optional[int]]:
        """
        Create invoice with full validation
        Returns (success, message, facture_id)
        """
        # Validate credit note has origin
        if type_document == 'Avoir':
            if not facture_origine_id:
                return (False, "Un avoir doit référencer une facture d'origine", None)
            if not motif:
                 return (False, "Un motif est obligatoire pour un avoir", None)
        
        # Calculate totals
        totals = self.calculate_facture_totals(lignes)
        
        if type_document == 'Avoir':
             # Validate Avoir Amount
             if not self.validate_avoir_amount(facture_origine_id, totals['montant_ttc']):
                 return (False, "Le montant de l'avoir dépasse le reste à valider de la facture d'origine", None)

        # Validate Contract if linked
        if contract_id:
            conn = self.db._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT date_fin, active FROM contracts WHERE id=?", (contract_id,))
            row = cursor.fetchone()
            if not row:
                return (False, "Contrat invalide ou introuvable", None)
            
            date_fin = row[0]
            active = row[1]
            
            if not active:
                return (False, "Ce contrat n'est pas actif", None)
            
            current_date = datetime.now().strftime("%Y-%m-%d")
            if current_date > date_fin:
                return (False, f"Le contrat est expiré depuis le {date_fin}", None)

        # For invoices (not credit notes), check stock and credit limit
        if type_document == 'Facture':
            # Check stock availability
            for ligne in lignes:
                is_available, current_stock = self.check_stock_availability(
                    ligne['product_id'], 
                    ligne['quantite']
                )
                if not is_available:
                    product = self.db.get_product_by_id(ligne['product_id'])
                if not is_available:
                    product = self.db.get_product_by_id(ligne['product_id'])
                    return (False, f"Stock insuffisant pour {product['nom']}. Stock actuel: {current_stock}", None)
                
                # Check if Parent Product (Blocking)
                if self.is_parent_product(ligne['product_id']):
                     product = self.db.get_product_by_id(ligne['product_id'])
                     return (False, f"Le produit '{product['nom']}' est un produit parent (Groupe). Impossible de le vendre directement.", None)
            
            # --- Type Vente Logic ---
            if type_vente == 'Au comptant':
                 # Validation for Comptant
                if mode_paiement in ['Chèque', 'Virement', 'Versement'] and not ref_paiement:
                    return (False, "Référence paiement obligatoire pour le mode sélectionné", None)
                
                # Validation Espèces > 100k
                if mode_paiement == 'Espèces' and totals['montant_ttc'] > 100000:
                    return (False, "ALERTE: Paiement espèces > 100 000 DA interdit par la réglementation", None)
                    
            elif type_vente == 'A terme':
                # Check credit limit
                is_within_limit, balance_info = self.check_credit_limit(client_id, totals['montant_ttc'])
                if not is_within_limit:
                    client = self.db.get_client_by_id(client_id)
                    return (False, 
                           f"Seuil de crédit dépassé de {balance_info['depassement']:.2f} DA.\n\nSolde Actuel: {balance_info['solde']:.2f} DA\nSeuil: {balance_info['seuil_credit']:.2f} DA", 
                           None)

            elif type_vente == 'Sur Avances':
                # Check if client has sufficient advances (Negative Solde Creance)
                conn = self.db._get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT solde_creance FROM clients WHERE id = ?", (client_id,))
                current_balance = cursor.fetchone()[0] or 0.0
                
                # Advances are negative balance. e.g. -1000.
                # Available to spend = abs(current_balance) if current_balance < 0 else 0
                available = abs(current_balance) if current_balance < 0 else 0.0
                
                if available < totals['montant_ttc']:
                    return (False, f"Solde avances insuffisant. Disponible: {available:.2f} DA. Requis: {totals['montant_ttc']:.2f} DA", None)

        
        # Determine status
        statut_facture = statut_final
        if type_vente in ['Au comptant', 'Sur Avances']:
            statut_facture = 'Soldée' # Should override Brouillon if paid? 
            # WAIT. If it's "Confirmer sans impression" (Step 1), it implies "Brouillon".
            # But if it's "Au comptant", usually payment is immediate.
            # Strategy: If "Confirmer sans impression", we force 'Brouillon' even if paid.
            # But the requirement says "peut être modifiée".
            # If we enforce 'Brouillon', we say it's paid but not finalized?
            # Let's trust the 'statut_final' passed strictly.
            if statut_final == 'Validée' and type_vente in ['Au comptant', 'Sur Avances']:
                 statut_facture = 'Soldée'
            else:
                 statut_facture = statut_final

        elif type_document == 'Avoir':
             statut_facture = 'Remboursée' # Or applied

        # Create invoice
        current_year = datetime.now().year
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        if custom_date:
             current_date = custom_date
             try:
                 current_year = int(custom_date.split('-')[0])
             except: pass
        
        if type_vente == 'A terme':
             is_ok, info = self.check_credit_limit(client_id, totals['montant_ttc'])
             if not is_ok:
                  return (False, f"Crédit insuffisant. Solde futur: {info['solde_futur']:.2f}, Limite: {info['seuil_credit']:.2f}", None)

        try:
            conn = self.db._get_connection()
            cursor = conn.cursor()
            
            # Generate Number
            # Logic: If custom date year != current year, we should likely generate number for THAT year?
            # Usually generation depends on fiscal year.
            annee = current_year
            numero = self.db.generate_facture_number(type_document, annee)
            
            # Determine Initial Etat Paiement
            etat_paiement = 'Comptant' if type_vente == 'Au comptant' else 'A Terme'
            
            cursor.execute("""
                INSERT INTO factures (numero, type_document, type_vente, annee, date_facture, 
                client_id, facture_origine_id, montant_ht, montant_tva, montant_ttc, statut, mode_paiement, 
                ref_paiement, banque, contract_id, contrat_code, chauffeur, matricule_tracteur, matricule_remorque,
                transporteur, client_compte_bancaire, client_categorie, created_by, statut_facture, etat_paiement)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (numero, type_document, type_vente, annee, current_date, 
                  client_id, facture_origine_id, totals['montant_ht'], totals['montant_tva'], totals['montant_ttc'],
                  statut_facture, mode_paiement, ref_paiement, banque, contract_id, contrat_code, 
                  chauffeur, matricule_tracteur, matricule_remorque, transporteur, client_compte_bancaire, client_categorie, user_id, statut_facture, etat_paiement))
            
            facture_id = cursor.lastrowid
            
            # Create Lines
            for ligne in lignes:
                cursor.execute("""
                    INSERT INTO lignes_facture (facture_id, product_id, quantite, prix_unitaire, montant, taux_remise, prix_initial)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (facture_id, ligne['product_id'], ligne['quantite'], ligne['prix_unitaire'], ligne['montant'], 
                      ligne.get('taux_remise', 0.0), ligne.get('prix_initial', ligne['prix_unitaire'])))
                
                # Update Stock
                # Update Stock and Log Movement
                if type_document == 'Facture':
                    # Sales decrease stock
                    self.db.log_stock_movement(
                        product_id=ligne['product_id'],
                        type_mouvement='Vente',
                        quantite=-ligne['quantite'],
                        reference_document=numero,
                        document_id=facture_id,
                        created_by=user_id
                    )
                elif type_document == 'Avoir':
                     # Returns increase stock
                     self.db.log_stock_movement(
                        product_id=ligne['product_id'],
                        type_mouvement='Retour Avoir',
                        quantite=-ligne['quantite'], # Avoir qty is negative, so negate to make positive (Stock Add)
                        reference_document=numero,
                        document_id=facture_id,
                        created_by=user_id
                    )

            conn.commit()
            
            # Post-Creation Logic
            if type_document == 'Facture':
                if type_vente in ['A terme', 'Sur Avances']:
                    # Update Client Solde Creance
                    c = conn.cursor()
                    c.execute("UPDATE clients SET solde_creance = solde_creance + ? WHERE id = ?", 
                              (totals['montant_ttc'], client_id))
                    conn.commit()
                elif type_vente == 'Au comptant':
                     # Create Payment Record
                     self.create_payment(
                         client_id=client_id,
                         montant=totals['montant_ttc'],
                         mode_paiement=mode_paiement,
                         facture_id=facture_id,
                         reference=ref_paiement,
                         banque=banque,
                         user_id=user_id
                     )
            
            # Helper for Avoir Status Update
            if type_document == 'Avoir' and facture_origine_id:
                 c = conn.cursor()
                 c.execute("""
                    SELECT COALESCE(SUM(montant_ttc), 0)
                    FROM factures
                    WHERE facture_origine_id = ? AND type_document = 'Avoir' AND statut != 'Annulée'
                 """, (facture_origine_id,))
                 total_avoirs = c.fetchone()[0]
                 
                 facture_org = self.db.get_facture_by_id(facture_origine_id)
                 if facture_org:
                     new_status = 'Partiellement remboursée'
                     # Avoirs are negative, so we use abs() to compare magnitude
                     if abs(total_avoirs) >= (facture_org['montant_ttc'] - 0.01):
                         new_status = 'Remboursée' # Or 'Annulée' if preferred, but usually Remboursée implies money returned
                     
                     c.execute("UPDATE factures SET statut = ? WHERE id = ?", (new_status, facture_origine_id))
                     
                     # Decrease debt
                     c.execute("UPDATE clients SET solde_creance = solde_creance - ? WHERE id = ?", 
                               (totals['montant_ttc'], client_id))
                     conn.commit()

            return (True, f"{type_document} {numero} créée avec succès", facture_id)

        except Exception as e:
            # conn.rollback() # Warning: conn might be local
            return (False, f"Erreur base de données: {str(e)}", None)

    def update_invoice_draft(self, facture_id: int, new_lignes: List[Dict[str, Any]], user_id: int, **kwargs) -> Tuple[bool, str]:
        """
        Update a 'Brouillon' invoice.
        Logic:
        1. Verify status.
        2. Revert Old Stock (ADD back).
        3. Delete old lines.
        4. Insert new lines (REMOVE stock).
        5. Update Invoice Totals and Header Fields.
        Returns (success, message)
        """
        conn = self.db._get_connection()
        
        # 1. Verify Status
        facture = self.db.get_facture_by_id(facture_id)
        if not facture or facture['statut_facture'] != 'Brouillon':
             return (False, "Seules les factures 'Brouillon' peuvent être modifiées.")

        try:
             conn.execute("BEGIN TRANSACTION")
             
             # 2. Revert Old Stock
             cursor = conn.cursor()
             cursor.execute("SELECT product_id, quantite FROM lignes_facture WHERE facture_id = ?", (facture_id,))
             old_lines = cursor.fetchall()
             
             numero = facture['numero']
             
             for old in old_lines:
                 # Add back to stock (Reverse Sale)
                 self.db.log_stock_movement(
                    product_id=old['product_id'],
                    type_mouvement='Modification (Reversion)',
                    quantite=old['quantite'], # Positive to add back
                    reference_document=f"MODIF-{numero}",
                    document_id=facture_id,
                    created_by=user_id
                 )
             
             # 3. Delete Old Lines
             cursor.execute("DELETE FROM lignes_facture WHERE facture_id = ?", (facture_id,))
             
             # 4. Insert New Lines and Deduct Stock
             totals = self.calculate_facture_totals(new_lignes)
             
             for ligne in new_lignes:
                 # Check Parent
                 if self.is_parent_product(ligne['product_id']):
                     raise Exception(f"Produit parent interdit: {ligne['product_id']}")

                 cursor.execute("""
                    INSERT INTO lignes_facture (facture_id, product_id, quantite, prix_unitaire, montant, taux_remise, prix_initial)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                 """, (facture_id, ligne['product_id'], ligne['quantite'], ligne['prix_unitaire'], ligne['montant'], 
                       ligne.get('taux_remise', 0.0), ligne.get('prix_initial', ligne['prix_unitaire'])))
                 
                 self.db.log_stock_movement(
                     product_id=ligne['product_id'],
                     type_mouvement='Vente', 
                     quantite=-ligne['quantite'],
                     reference_document=numero,
                     document_id=facture_id,
                     created_by=user_id
                 )

             # 5. Update Invoice Totals and Header in DB
             # Build dynamic update for header fields
             update_fields = [
                 "montant_ht = ?", "montant_tva = ?", "montant_ttc = ?"
             ]
             update_values = [
                 totals['montant_ht'], totals['montant_tva'], totals['montant_ttc']
             ]
             
             # Allowed header fields to be updated
             header_map = {
                 'client_id': 'client_id',
                 'type_vente': 'type_vente',
                 'chauffeur': 'chauffeur',
                 'matricule_tracteur': 'matricule_tracteur',
                 'matricule_remorque': 'matricule_remorque',
                 'transporteur': 'transporteur',
                 'contract_id': 'contract_id',
                 'contrat_code': 'contrat_code',
                 'client_compte_bancaire': 'client_compte_bancaire',
                 'client_categorie': 'client_categorie',
                 'mode_paiement': 'mode_paiement',
                 'ref_paiement': 'ref_paiement',
                 'banque': 'banque',
                 'motif': 'motif' # If Avoir
             }
             
             for arg_name, col_name in header_map.items():
                 if arg_name in kwargs:
                     update_fields.append(f"{col_name} = ?")
                     update_values.append(kwargs[arg_name])
             
             update_query = f"UPDATE factures SET {', '.join(update_fields)} WHERE id = ?"
             update_values.append(facture_id)
             
             cursor.execute(update_query, tuple(update_values))
             
             conn.commit()
             return (True, "Facture mise à jour avec succès")
             
        except Exception as e:
             conn.rollback()
             return (False, str(e))

    def confirm_invoice(self, facture_id: int) -> Tuple[bool, str]:
        """
        Transition Status from 'Brouillon' to 'Validée' (or 'Non soldée'/'Soldée').
        Locks the invoice.
        """
        facture = self.db.get_facture_by_id(facture_id)
        if not facture:
            return (False, "Facture introuvable")
        
        if facture['statut_facture'] != 'Brouillon':
            return (True, "Facture déjà validée") # Idempotent-ish
            
        conn = self.db._get_connection()
        try:
            # Determine new status based on payment
            # If 'Au comptant' or 'Soldée' was intended...
            # We revert to logic: logic determines if Paid.
            
            new_status = 'Non soldée'
            if facture['type_vente'] in ['Au comptant', 'Sur Avances']:
                new_status = 'Soldée'
            
            # Use 'Validée' as a general "Locked" state if not paid?
            # Or just use the standard statuses but 'Brouillon' is the special one.
            # Plan said: "'Validée' (Step 2)".
            # Let's check `database.py` again. `statut` vs `statut_facture`.
            # `statut` (Non soldée, Soldée...) vs `statut_facture` (maybe this is the one?).
            # In `create_facture`, `statut_facture` defaults to 'Non soldée'.
            # I should essentially remove 'Brouillon' from `statut_facture`.
            
            # If I use `statut_facture` column for Brouillon/Validée, then `statut` column handles Payment logic?
            # Looking at schema:
            # "statut": "TEXT DEFAULT 'Non soldée'",
            # "statut_facture": "TEXT",
            
            # Ah! `statut_facture` seems unused or redundant in previous code?
            # Let's use `statut_facture` for the workflow state: 'Brouillon' -> 'Validée'.
            
            cursor = conn.cursor()
            cursor.execute("UPDATE factures SET statut_facture = 'Validée', statut = ? WHERE id = ?", (new_status, facture_id))
            conn.commit()
            
            return (True, "Facture confirmée et verrouillée")
            
        except Exception as e:
            conn.rollback()
            return (False, str(e))
    
    # ==================== PAYMENT PROCESSING ====================
    
    def create_payment(self, client_id: int, montant: float, mode_paiement: str,
                      facture_id: Optional[int] = None, reference: str = None,
                      banque: str = None, contrat_num: str = None,
                      contrat_date_debut: str = None, contrat_date_fin: str = None,
                      user_id: Optional[int] = None) -> Tuple[bool, str, Optional[int]]:
        """
        Create payment (including advance payments without facture_id)
        Returns (success, message, paiement_id)
        """
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        # Validate bank details for non-cash payments
        if mode_paiement in ['Chèque', 'Virement', 'Versement']:
            if not reference or not banque:
                return (False, "Référence et banque obligatoires pour ce mode de paiement", None)
        
        paiement_id = self.db.create_paiement(
            date_paiement=current_date,
            client_id=client_id,
            montant=montant,
            mode_paiement=mode_paiement,
            facture_id=facture_id,
            reference=reference,
            banque=banque,
            contrat_num=contrat_num,
            contrat_date_debut=contrat_date_debut,
            contrat_date_fin=contrat_date_fin,
            created_by=user_id
        )
        
        # Update Client Solde Creance (Decrease debt)
        conn = self.db._get_connection()
        c = conn.cursor()
        c.execute("UPDATE clients SET solde_creance = solde_creance - ? WHERE id = ?", 
                  (montant, client_id))
        conn.commit()
        
        # Update Invoice Payment Status
        if facture_id:
             self.update_invoice_payment_status(facture_id)
        
        return (True, "Paiement enregistré avec succès", paiement_id)

    def update_invoice_payment_status(self, facture_id: int):
        """
        Recalculate and update 'etat_paiement' for a facture based on payments and total.
        Statuses: 'Comptant' (if initially so and 0 pay?), 'A Terme' (initial), 'Non soldée', 'Payée'
        """
        try:
            conn = self.db._get_connection()
            c = conn.cursor()
            
            # Get Invoice info
            c.execute("SELECT montant_ttc, type_vente FROM factures WHERE id = ?", (facture_id,))
            row = c.fetchone()
            if not row: return
            
            total_ttc = row[0]
            type_vente = row[1]
            
            # Get Sum of Payments (excluding rejected/cancelled if any? check 'statut')
            # Assuming 'En attente' and 'Validé' count? Or just all? 
            # Usually strict accounting counts validated. But for UI feedback let's count all non-cancelled?
            # Existing `get_all_factures` query utilized: (SELECT SUM(montant) FROM paiements WHERE facture_id = f.id)
            c.execute("SELECT COALESCE(SUM(montant), 0) FROM paiements WHERE facture_id = ?", (facture_id,))
            paid_amount = c.fetchone()[0]
            
            new_status = 'A Terme' # Default fallback
            
            if abs(paid_amount) >= (total_ttc - 0.05): # Tolerance for float
                new_status = 'Payée'
            elif paid_amount > 0:
                new_status = 'Non soldée'
            else:
                # 0 Payments
                if type_vente == 'Au comptant':
                    new_status = 'Comptant'
                else:
                    new_status = 'A Terme'
            
            c.execute("UPDATE factures SET etat_paiement = ? WHERE id = ?", (new_status, facture_id))
            conn.commit()
            
        except Exception as e:
            print(f"Error updating payment status for {facture_id}: {e}")
    
    def create_bordereau(self, banque: str, paiement_ids: List[int], 
                        user_id: Optional[int] = None) -> Tuple[bool, str, Optional[int]]:
        """
        Create bank deposit voucher from selected payments
        Returns (success, message, bordereau_id)
        """
        if not paiement_ids:
            return (False, "Aucun paiement sélectionné", None)
        
        # Validate all payments are 'En attente'
        paiements = []
        for pid in paiement_ids:
            conn = self.db._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT statut FROM paiements WHERE id = ?", (pid,))
            row = cursor.fetchone()
            if not row or row[0] != 'En attente':
                return (False, f"Le paiement {pid} n'est pas en attente", None)
            paiements.append(pid)
        
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        bordereau_id = self.db.create_bordereau(
            date_bordereau=current_date,
            banque=banque,
            paiement_ids=paiement_ids,
            created_by=user_id
        )
        
        return (True, "Bordereau créé avec succès", bordereau_id)
    
    # ==================== ANNUAL CLOSURE ====================
    
    def perform_annual_closure(self, annee: int, user_id: Optional[int] = None) -> Tuple[bool, str]:
        """
        Perform annual closure:
        1. Check if already closed
        2. Archive data
        3. Calculate and store snapshots
        4. Prepare for new year
        """
        # Check if already closed
        existing = self.db.get_cloture_by_annee(annee)
        if existing:
            return (False, f"L'année {annee} est déjà clôturée")
        
        # Calculate client balances for snapshot
        clients = self.db.get_all_clients()
        soldes_snapshot = {}
        for client in clients:
            balance = self.calculate_client_balance(client['id'])
            soldes_snapshot[client['id']] = {
                'raison_sociale': client['raison_sociale'],
                'solde': balance['solde']
            }
        
        # Create closure record with snapshots
        import json
        conn = self.db._get_connection()
        cursor = conn.cursor()
        
        # Get stock snapshot
        products = self.db.get_all_products()
        stocks_snapshot = {p['id']: {'nom': p['nom'], 'stock': p['stock_actuel']} 
                          for p in products}
        
        date_cloture = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute("""
            INSERT INTO clotures 
            (annee, date_cloture, stocks_snapshot, soldes_snapshot, created_by)
            VALUES (?, ?, ?, ?, ?)
        """, (annee, date_cloture, json.dumps(stocks_snapshot), 
              json.dumps(soldes_snapshot), user_id))
        
        conn.commit()
        
        # Update client reports for next year (N+1)
        for client_id, data in soldes_snapshot.items():
            self.db.update_client(client_id, report_n_moins_1=data['solde'])
        
        return (True, f"Clôture de l'année {annee} effectuée avec succès")
    
    # ==================== REPORTING ====================
    
    def get_client_situation(self, client_id: int) -> Dict[str, Any]:
        """
        Get complete client situation including:
        - Client details
        - Balance calculation
        - Recent invoices
        - Recent payments
        """
        client = self.db.get_client_by_id(client_id)
        if not client:
            return {}
        
        balance = self.calculate_client_balance(client_id)
        factures = self.db.get_all_factures(client_id=client_id)
        paiements = self.db.get_all_paiements(client_id=client_id)
        
        return {
            'client': client,
            'balance': balance,
            'factures': factures[:10],  # Last 10 invoices
            'paiements': paiements[:10]  # Last 10 payments
        }
    
    def get_stock_report(self) -> List[Dict[str, Any]]:
        """Get stock report with movements"""
        products = self.db.get_all_products()
        report = []
        
        for product in products:
            movements = self.db.get_stock_movements(product['id'])
            report.append({
                'product': product,
                'recent_movements': movements[:5]  # Last 5 movements
            })
        
        return report

    def get_daily_sales_stats(self, report_date: str) -> Dict[str, Any]:
        """
        Get statistics for Daily Sales Report:
        1. Detailed invoices/avoirs for the specific date.
        2. Per-product daily quantity (on report_date).
        3. Per-product cumulative quantity (Jan 1st to report_date).
        FILTERS OUT: Fully refunded invoices and their cancelling Avoirs to show only "Real Sales".
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()
        
        year = report_date.split('-')[0]
        start_of_year = f"{year}-01-01"
        
        # 1. Fetch detailed invoices for the day
        cursor.execute("""
            SELECT l.quantite, l.montant as montant_ht, 
                   f.id as facture_id, f.numero, f.date_facture, f.type_document, f.statut,
                   f.montant_ttc, f.facture_origine_id,
                   c.code_client, c.raison_sociale,
                   p.nom as product_nom, p.code_produit, p.tva, l.product_id
            FROM lignes_facture l
            JOIN factures f ON l.facture_id = f.id
            JOIN clients c ON f.client_id = c.id
            JOIN products p ON l.product_id = p.id
            WHERE f.date_facture = ? AND f.statut != 'Annulée'
            ORDER BY f.numero
        """, (report_date,))
        
        raw_rows = [dict(row) for row in cursor.fetchall()]
        
        # --- LOGIC TO FILTER REFUNDED TRANSACTIONS ---
        # We need to identify invoices that are fully Refunded/Cancelled
        # and hide BOTH the Invoice and the Avoir.
        
        # 1. Identify IDs of invoices that are effectively cancelled
        # Checks: Status is 'Remboursée...' OR 'Partiellement...' with 0 remaining
        
        hidden_invoice_ids = set()
        
        # Helper to check if invoice is fully refunded
        def is_fully_refunded(facture_id, total_ttc):
            # Sum Avoirs for this invoice
            cursor.execute("""
                SELECT COALESCE(SUM(montant_ttc), 0)
                FROM factures
                WHERE facture_origine_id = ? AND type_document = 'Avoir' AND statut != 'Annulée'
            """, (facture_id,))
            total_av = cursor.fetchone()[0]
            # CHECK ABSOLUTE VALUE
            # Avoirs are negative, invoices positive. 
            # If abs(total_av) >= invoice_ttc, it's fully refunded.
            return abs(total_av) >= (total_ttc - 0.5)

        # First pass: Check Invoices
        for r in raw_rows:
            if r['type_document'] == 'Facture':
                # Check status. Also check if we just missed the status update but sums match
                if 'Remboursée' in r['statut'] or r['statut'] == 'Partiellement remboursée':
                    if is_fully_refunded(r['facture_id'], r['montant_ttc']):
                        hidden_invoice_ids.add(r['facture_id'])

        # Second pass: Check Avoirs
        # If Avoir points to a hidden invoice, hide it too
        for r in raw_rows:
            if r['type_document'] == 'Avoir' and r['facture_origine_id'] in hidden_invoice_ids:
                hidden_invoice_ids.add(r['facture_id']) # Hide the Avoir itself

        # Filter rows
        details = []
        
        total_day_ht = 0.0
        total_day_tva = 0.0
        total_day_ttc = 0.0
        total_day_qty = 0.0
        
        # Track product quantities for the "Product Stats" section (Daily only)
        # We need to recalculate daily product stats based on the filtered list
        filtered_daily_product_qty = {} 

        for r in raw_rows:
            if r['facture_id'] in hidden_invoice_ids:
                continue
            
            qty = r['quantite']
            ht = r['montant_ht']
            tva_rate = r['tva']
            tva_amount = ht * (tva_rate / 100)
            ttc = ht + tva_amount
            
            # Determine sign based on document type
            # Use strict type check
            is_avoir = (r['type_document'] == 'Avoir')
            sign = -1 if is_avoir else 1
            
            # Add to totals (using sign)
            total_day_ht += (ht * sign)
            total_day_tva += (tva_amount * sign)
            total_day_ttc += (ttc * sign)
            total_day_qty += (qty * sign)
            
            # Add to product stats
            pid = r['product_id']
            if pid not in filtered_daily_product_qty:
                filtered_daily_product_qty[pid] = 0.0
            filtered_daily_product_qty[pid] += (qty * sign)
            
            details.append({
                'code_client': r['code_client'],
                'client': r['raison_sociale'],
                'code_produit': r['code_produit'],
                'produit': r['product_nom'],
                'facture_num': r['numero'],
                'date': r['date_facture'],
                'qte': qty * sign,         # Display negative for Avoirs if shown
                'ht': ht * sign,
                'tva': tva_amount * sign,
                'ttc': ttc * sign
            })
            
        # 2. Product Summary (Daily & Cumulative)
        # For Daily: Use our filtered calculation
        # For Cumulative: We accept that historical data might include some refunds, 
        # but technically we should apply same logic. 
        # optimizing: For cumulative, we just run standard query but exclude 'Annulée'.
        # Recalculating fully refunded for the whole year is expensive. 
        # We stick to standard query for cumulative, but use filtered for daily.
        
        products = self.db.get_all_products()
        product_stats = []
        
        for p in products:
            pid = p['id']
            
            # Daily Qty from filtered list
            net_daily_qty = filtered_daily_product_qty.get(pid, 0.0)
            
            
            # Cumulative Qty (Start of Year to Report Date Included)
            # Since Avoirs are negative in DB, we just SUM everything
            cursor.execute("""
                SELECT COALESCE(SUM(l.quantite), 0)
                FROM lignes_facture l
                JOIN factures f ON l.facture_id = f.id
                WHERE l.product_id = ? 
                AND f.date_facture BETWEEN ? AND ?
                AND f.statut != 'Annulée'
            """, (pid, start_of_year, report_date))
            net_cumul_qty = cursor.fetchone()[0]
            
            product_stats.append({
                'nom': p['nom'],
                'daily_qty': net_daily_qty,
                'cumul_qty': net_cumul_qty
            })
            
        # Calculate Yearly Global Turnover (Net)
        # Just SUM all amounts (Avoirs are negative)
        cursor.execute("""
            SELECT COALESCE(SUM(montant_ht), 0) FROM factures 
            WHERE date_facture BETWEEN ? AND ? 
            AND statut != 'Annulée'
        """, (start_of_year, report_date))
        year_net_ht = cursor.fetchone()[0]

        return {
            'date': report_date,
            'details': details,
            'product_stats': product_stats,
            'totals': {
                'day_qty': total_day_qty,
                'day_ht': total_day_ht,
                'day_tva': total_day_tva,
                'day_ttc': total_day_ttc,
                'year_net_ht': year_net_ht
            }
        }



    def print_delivery_note_text(self, facture_id: int, printer_name: str = None) -> Tuple[bool, str]:
        """
        Print delivery note using matrix printer (Text Mode)
        Uses win32print for raw printing
        """
        if not WIN32PRINT_AVAILABLE:
            return (False, "Module win32print non disponible. Installation requise: pip install pywin32")
            
        facture = self.db.get_facture_by_id(facture_id)
        if not facture:
            return (False, "Facture introuvable")
            
        try:
            # Prepare data
            client_nom = facture.get('client_nom', '')[:30] # Truncate for layout
            date_str = facture['date_facture']
            numero = facture['numero']
            
            # Layout Configuration (Offsets in spaces/lines)
            OFFSET_X = " " * 5  # Left margin
            OFFSET_Y = 3        # Top margin lines
            
            # Construct text content
            content = "\n" * OFFSET_Y
            content += f"{OFFSET_X}{'Date:':<10} {date_str:<20} {'N°:':<5} {numero}\n"
            content += f"{OFFSET_X}{'Client:':<10} {client_nom}\n"
            content += "\n" * 2 # Spacing before items
            
            content += f"{OFFSET_X}{'Produit':<30} {'Qté':>10} {'Unité':>10}\n"
            content += f"{OFFSET_X}{'-'*50}\n"
            
            for ligne in facture['lignes']:
                prod_nom = ligne['product_nom'][:30]
                qte = f"{ligne['quantite']:.2f}"
                unite = ligne['unite']
                content += f"{OFFSET_X}{prod_nom:<30} {qte:>10} {unite:>10}\n"
                
            content += f"{OFFSET_X}{'-'*50}\n"
            content += "\f" # Form Feed
            
            # Print
            if not printer_name:
                printer_name = win32print.GetDefaultPrinter()
                
            hPrinter = win32print.OpenPrinter(printer_name)
            try:
                hJob = win32print.StartDocPrinter(hPrinter, 1, ("Bon de Livraison", None, "RAW"))
                try:
                    win32print.StartPagePrinter(hPrinter)
                    win32print.WritePrinter(hPrinter, content.encode('cp1252', errors='replace')) # simple encoding
                    win32print.EndPagePrinter(hPrinter)
                finally:
                    win32print.EndDocPrinter(hPrinter)
            finally:
                win32print.ClosePrinter(hPrinter)
                
            return (True, f"Impression envoyée vers {printer_name}")
            
        except Exception as e:
            return (False, f"Erreur d'impression: {str(e)}")

    def get_sales_by_category(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Get sales aggregated by category (Ciment vs Autre)
        Subtracts Credit Notes (Avoirs) automatically if quantities are negative.
        """
        conn = self.db._get_connection()
        c = conn.cursor()
        
        # We assume 'categorie' column exists (migrated)
        # We group by Category -> Product
        query = """
            SELECT 
                COALESCE(p.categorie, 'Autre') as cat,
                p.nom,
                p.unite,
                SUM(lf.quantite) as qte,
                SUM(lf.montant) as montant_ht
            FROM lines_facture lf
            JOIN factures f ON lf.facture_id = f.id
            JOIN products p ON lf.product_id = p.id
            WHERE f.date_facture BETWEEN ? AND ?
              AND f.statut != 'Annulée'
            GROUP BY cat, p.nom, p.unite
            ORDER BY cat, p.nom
        """
        
        # 'lignes_facture' is the correct table name
        query = query.replace("lines_facture", "lignes_facture")
        
        c.execute(query, (start_date, end_date))
        rows = c.fetchall()
        
        result = {}
        
        for row in rows:
            cat = row['cat']
            if cat not in result:
                result[cat] = []
            
            result[cat].append({
                'nom': row['nom'],
                'unite': row['unite'],
                'qte': row['qte'],
                'montant_ht': row['montant_ht']
            })
            
        return result

    def get_clients_export_data(self) -> List[Dict[str, Any]]:
        """
        Get detailed client data for Excel export.
        Includes:
        - Raison Sociale, Seuil Credit, Solde N-1
        - Payment breakdown by mode (Chèque, Versement, Virement)
        - Net Sales (Factures TTC - |Avoirs TTC|)
        - Current Solde
        """
        conn = self.db._get_connection()
        c = conn.cursor()
        
        # Get all active clients
        clients = self.db.get_all_clients(active_only=True)
        export_data = []
        
        current_year = datetime.now().year # Or use logic similar to calculate_client_balance
        
        for client in clients:
            client_id = client['id']
            # Basic Info
            data = {
                'raison_sociale': client['raison_sociale'],
                'seuil_credit': client['seuil_credit'],
                'report_n_moins_1': client['report_n_moins_1']
            }
            
            # Payment Breakdown
            # We want all payments, no date filter mentioned, likely "Current State"
            # But normally logic.calculate_client_balance filters by closure year.
            # Here we follow the global balance logic for consistency.
            
            # 1. Get total payments breakdown
            payments_breakdown = {'Chèque': 0.0, 'Versement': 0.0, 'Virement': 0.0, 'Global': 0.0}
            
            c.execute("""
                SELECT mode_paiement, SUM(montant)
                FROM paiements 
                WHERE client_id = ?
                GROUP BY mode_paiement
            """, (client_id,))
            
            rows = c.fetchall()
            for r in rows:
                mode, montant = r[0], r[1]
                if mode in payments_breakdown:
                    payments_breakdown[mode] = montant
                else:
                    # Map other modes if any (Espèces, etc) or ignore? 
                    # User asked for specific columns but "Total Paiements Global" should include everything?
                    # "total des paiements (cheque) total des paiements (versements) + total des paiement (virements) + (total des paiements cheque+versements+cheques)"
                    # Typically "Global" implies sum of ALL.
                    pass
                payments_breakdown['Global'] += montant

            data.update({
                'paiements_cheque': payments_breakdown['Chèque'],
                'paiements_versement': payments_breakdown['Versement'],
                'paiements_virement': payments_breakdown['Virement'],
                'paiements_global': payments_breakdown['Global']
            })
            
            # Factures & Avoirs
            # Net Sales = Sum(Factures TTC) - Sum(Abs(Avoirs TTC))
            c.execute("""
                SELECT type_document, SUM(montant_ttc)
                FROM factures
                WHERE client_id = ? AND statut != 'Annulée'
                GROUP BY type_document
            """, (client_id,))
            
            rows = c.fetchall()
            total_factures = 0.0
            total_avoirs = 0.0
            
            for r in rows:
                doc_type, amount = r[0], r[1]
                if doc_type == 'Facture':
                    total_factures = amount
                elif doc_type == 'Avoir':
                    # Amount is stored as negative or positive? 
                    # create_facture inserts positive amounts? 
                    # Let's check schema/insertion. 
                    # logic.py Line 706 calculates totals. 
                    # ui.py usually passes positive quantites for Avoir but logic converts stock.
                    # Standard logic: Invoice Amount is Positive. Avoir Amount is Positive (magnitude).
                    # Avoirs usually have type_document='Avoir'.
                    total_avoirs = abs(amount) 

            # User Request: "Total Factures TTC (les factures et leurs avoirs doivent etre considerés comme 0)"
            # Meaning Net Sales.
            # Assuming Avoirs cancel Factures.
            
            net_sales = total_factures - total_avoirs
            data['factures_net_ttc'] = net_sales
            
            # Solde Actuel
            # Standard Formula: (Report + Paiements + Avoirs_Credit_Value) - Factures
            # Or simplified: (Report + Paiements) - Net_Sales (mathematically equivalent if Avoirs used correctly)
            # Let's use the robust function
            balance_info = self.calculate_client_balance(client_id)
            data['solde_actuel'] = balance_info['solde']
            
            export_data.append(data)
            
        return export_data

    def get_movements_valorises_data(self, date_str: str) -> Dict[str, Any]:
        """
        Get detailed stock movements and valuation for a specific date.
        Returns data for 'ETAT DES MOUVEMENTS DES STOCKS VALORISES'.
        Columns: Day (Init, In, Out), Month (Init, In, Out), Year (Init, In, Out), Final.
        Physics: Entrées = Receptions + Avoirs. Sorties = Ventes.
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()
        
        target_date = datetime.strptime(date_str, "%Y-%m-%d")
        year_start = target_date.replace(month=1, day=1).strftime("%Y-%m-%d")
        month_start = target_date.replace(day=1).strftime("%Y-%m-%d")
        day_str = date_str
        
        # Get all products
        cursor.execute("SELECT id, nom, unite, cout_revient, stock_initial FROM products WHERE active = 1 ORDER BY nom")
        products = cursor.fetchall()
        
        report_data = []
        seen_units = set()
        
        grand_totals = {
            "day": {"init": 0.0, "in": 0.0, "out": 0.0},
            "month": {"init": 0.0, "in": 0.0, "out": 0.0},
            "year": {"init": 0.0, "in": 0.0, "out": 0.0},
            "final": 0.0,
            "val_final": 0.0
        }

        # Helper to get Sum Quantities in Range
        def get_sum(query, pid, d_start, d_end):
            cursor.execute(query, (pid, d_start, d_end))
            return cursor.fetchone()[0]

        # Queries
        # Receptions (Sur Stock)
        q_reception = "SELECT COALESCE(SUM(quantite_recue), 0) FROM receptions WHERE product_id = ? AND date_reception >= ? AND date_reception <= ? AND lieu_livraison = 'Sur Stock'"
        
        # Sales (Factures)
        q_sales = """
            SELECT COALESCE(SUM(lf.quantite), 0) 
            FROM lignes_facture lf 
            JOIN factures f ON lf.facture_id = f.id 
            WHERE lf.product_id = ? AND f.date_facture >= ? AND f.date_facture <= ? 
            AND f.type_document = 'Facture' AND f.statut != 'Annulée'
        """
        
        # Returns (Avoirs) -> Treat as Entries
        q_avoirs = """
            SELECT COALESCE(SUM(lf.quantite), 0) 
            FROM lignes_facture lf 
            JOIN factures f ON lf.facture_id = f.id 
            WHERE lf.product_id = ? AND f.date_facture >= ? AND f.date_facture <= ? 
            AND f.type_document = 'Avoir' AND f.statut != 'Annulée'
        """
        
        # Base Initial Stock (Before Year Start)
        q_rec_before = "SELECT COALESCE(SUM(quantite_recue), 0) FROM receptions WHERE product_id = ? AND date_reception < ? AND lieu_livraison = 'Sur Stock'"
        q_sale_before = "SELECT COALESCE(SUM(lf.quantite), 0) FROM lignes_facture lf JOIN factures f ON lf.facture_id = f.id WHERE lf.product_id = ? AND f.date_facture < ? AND f.type_document = 'Facture' AND f.statut != 'Annulée'"
        q_avoir_before = "SELECT COALESCE(SUM(lf.quantite), 0) FROM lignes_facture lf JOIN factures f ON lf.facture_id = f.id WHERE lf.product_id = ? AND f.date_facture < ? AND f.type_document = 'Avoir' AND f.statut != 'Annulée'"

        for p in products:
            pid = p['id']
            cout = p['cout_revient'] or 0.0
            base_init = p['stock_initial'] or 0.0
            
            if p['unite']:
                seen_units.add(p['unite'])
            
            # 1. Calculate S.Init (Year)
            rec_b = cursor.execute(q_rec_before, (pid, year_start)).fetchone()[0]
            sale_b = cursor.execute(q_sale_before, (pid, year_start)).fetchone()[0]
            avoir_b = cursor.execute(q_avoir_before, (pid, year_start)).fetchone()[0]
            
            s_init_year = base_init + rec_b + avoir_b - sale_b
            
            # 2. Year Movements (Jan 1 to Date)
            rec_y = get_sum(q_reception, pid, year_start, day_str)
            sale_y = get_sum(q_sales, pid, year_start, day_str)
            avoir_y = get_sum(q_avoirs, pid, year_start, day_str)
            
            in_year = rec_y + avoir_y
            out_year = sale_y
            
            # S.Final
            s_final = s_init_year + in_year - out_year
            
            # 3. Month Movements (1st to Date)
            rec_m = get_sum(q_reception, pid, month_start, day_str)
            sale_m = get_sum(q_sales, pid, month_start, day_str)
            avoir_m = get_sum(q_avoirs, pid, month_start, day_str)
            
            in_month = rec_m + avoir_m
            out_month = sale_m
            
            # S.Init(Month)
            s_init_month = s_final - in_month + out_month
            
            # 4. Day Movements (Date)
            rec_d = get_sum(q_reception, pid, day_str, day_str)
            sale_d = get_sum(q_sales, pid, day_str, day_str)
            avoir_d = get_sum(q_avoirs, pid, day_str, day_str)
            
            in_day = rec_d + avoir_d
            out_day = sale_d
            
            # S.Init(Day)
            s_init_day = s_final - in_day + out_day
            
            item = {
                "code": p['id'],
                "designation": p['nom'],
                "unite": p['unite'],
                "cout_unitaire": cout,
                
                "day": {"init": s_init_day, "in": in_day, "out": out_day},
                "month": {"init": s_init_month, "in": in_month, "out": out_month},
                "year": {"init": s_init_year, "in": in_year, "out": out_year},
                "final": s_final,
                
                "val_final": s_final * cout,
                "values": {
                     "day": {"init": s_init_day * cout, "in": in_day * cout, "out": out_day * cout},
                     "month": {"init": s_init_month * cout, "in": in_month * cout, "out": out_month * cout},
                     "year": {"init": s_init_year * cout, "in": in_year * cout, "out": out_year * cout},
                }
            }
            report_data.append(item)
            
            grand_totals["day"]["init"] += s_init_day
            grand_totals["day"]["in"] += in_day
            grand_totals["day"]["out"] += out_day
            grand_totals["month"]["init"] += s_init_month
            grand_totals["month"]["in"] += in_month
            grand_totals["month"]["out"] += out_month
            grand_totals["year"]["init"] += s_init_year
            grand_totals["year"]["in"] += in_year
            grand_totals["year"]["out"] += out_year
            grand_totals["final"] += s_final
            grand_totals["val_final"] += (s_final * cout)
            

            
        # Check for mixed units
        if len(seen_units) > 1:
            # Suppress quantity totals
            grand_totals["day"]["init"] = ""
            grand_totals["day"]["in"] = ""
            grand_totals["day"]["out"] = ""
            grand_totals["month"]["init"] = ""
            grand_totals["month"]["in"] = ""
            grand_totals["month"]["out"] = ""
            grand_totals["year"]["init"] = ""
            grand_totals["year"]["in"] = ""
            grand_totals["year"]["out"] = ""
            grand_totals["final"] = ""

        return {
            "date": day_str,
            "data": report_data,
            "totals": grand_totals
        }

# Global business logic instance
_logic_instance: Optional[BusinessLogic] = None

def get_logic() -> BusinessLogic:
    """Get global business logic instance"""
    global _logic_instance
    if _logic_instance is None:
        _logic_instance = BusinessLogic()
    return _logic_instance
