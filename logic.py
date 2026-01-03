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
        1. Identify all invoices in period
        2. Find all credit notes linked to these invoices (any date)
        3. Result = Sum(Invoices HT) - Sum(Linked Avoirs HT)
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()
        
        # 1. Sum of Invoices in period
        cursor.execute("""
            SELECT COALESCE(SUM(montant_ht), 0)
            FROM factures
            WHERE type_document = 'Facture'
            AND date_facture BETWEEN ? AND ?
            AND statut != 'Annulée'
        """, (start_date, end_date))
        total_factures_ht = cursor.fetchone()[0]
        
        # 2. Sum of Avoirs linked to invoices from this period
        # CA Calculation: Sum(Invoices in period) - Sum(All Avoirs linked to these invoices)
        cursor.execute("""
            SELECT COALESCE(SUM(a.montant_ht), 0)
            FROM factures a
            JOIN factures f ON a.facture_origine_id = f.id
            WHERE a.type_document = 'Avoir'
            AND f.type_document = 'Facture'
            AND f.date_facture BETWEEN ? AND ?
            AND a.statut != 'Annulée'
        """, (start_date, end_date))
        total_avoirs_linked_ht = cursor.fetchone()[0]
        
        return total_factures_ht - total_avoirs_linked_ht
    
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
            SELECT lieu_livraison, product_id, quantite_recue, numero
            FROM receptions WHERE id = ?
        """, (reception_id,))
        reception = cursor.fetchone()
        
        if not reception:
            return False
        
        lieu, product_id, quantite, numero = reception
        
        # Only update stock if 'Sur Stock'
        if lieu == 'Sur Stock':
            self.db.log_stock_movement(
                product_id=product_id,
                type_mouvement='Réception',
                quantite=quantite,
                reference_document=numero,
                document_id=reception_id,
                created_by=user_id
            )
            
            # Update actual stock quantity is already handled by log_stock_movement
            # self.db.update_stock(product_id, quantite)
        # 'Sur Chantier' is direct consumption - no stock update
        
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
                created_by=user_id
            )
        
        return True
    
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
                    
                    cursor.execute("""
                        INSERT INTO stock_movements 
                        (product_id, type_mouvement, quantite, reference_document,
                         document_id, stock_avant, stock_apres, created_by)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (r['product_id'], 'Réception', r['quantite_recue'], r['numero'],
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
    
    # ==================== FINANCIAL CALCULATIONS ====================
    
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

                                      client_compte_bancaire: str = None,
                                      client_categorie: str = None,
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
                    return (False, f"Stock insuffisant pour {product['nom']}. Stock actuel: {current_stock}", None)
            
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
                           f"Dépassement: {balance_info['depassement']:.2f} DA", 
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
        statut_facture = 'Non soldée'
        if type_vente in ['Au comptant', 'Sur Avances']:
            statut_facture = 'Soldée'
        elif type_document == 'Avoir':
             statut_facture = 'Remboursée' # Or applied

        # Create invoice
        current_year = datetime.now().year
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        if type_vente == 'A terme':
             is_ok, info = self.check_credit_limit(client_id, totals['montant_ttc'])
             if not is_ok:
                  return (False, f"Crédit insuffisant. Solde futur: {info['solde_futur']:.2f}, Limite: {info['seuil_credit']:.2f}", None)

        try:
            conn = self.db._get_connection()
            cursor = conn.cursor()
            
            # Generate Number
            annee = datetime.now().year
            numero = self.db.generate_facture_number(type_document, annee)
            
            cursor.execute("""
                INSERT INTO factures (numero, type_document, type_vente, annee, date_facture, 
                client_id, facture_origine_id, montant_ht, montant_tva, montant_ttc, statut, mode_paiement, 
                ref_paiement, banque, contract_id, contrat_code, chauffeur, matricule_tracteur, matricule_remorque,
                client_compte_bancaire, client_categorie, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (numero, type_document, type_vente, annee, datetime.now().strftime("%Y-%m-%d"), 
                  client_id, facture_origine_id, totals['montant_ht'], totals['montant_tva'], totals['montant_ttc'],
                  statut_facture, mode_paiement, ref_paiement, banque, contract_id, contrat_code, 
                  chauffeur, matricule_tracteur, matricule_remorque, client_compte_bancaire, client_categorie, user_id))
            
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
                        quantite=ligne['quantite'],
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
                     if total_avoirs >= (facture_org['montant_ttc'] - 0.01):
                         new_status = 'Remboursée / Avoir Total'
                     c.execute("UPDATE factures SET statut = ? WHERE id = ?", (new_status, facture_origine_id))
                     
                     # Decrease debt
                     c.execute("UPDATE clients SET solde_creance = solde_creance - ? WHERE id = ?", 
                               (totals['montant_ttc'], client_id))
                     conn.commit()

            return (True, f"{type_document} {numero} créée avec succès", facture_id)

        except Exception as e:
            # conn.rollback() # Warning: conn might be local
            return (False, f"Erreur base de données: {str(e)}", None)
    
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
        
        return (True, "Paiement enregistré avec succès", paiement_id)
    
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
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()
        
        year = report_date.split('-')[0]
        start_of_year = f"{year}-01-01"
        
        # 1. Fetch detailed invoices for the day
        # Join with client and product info via line items
        # Note: We need line-level detail for the report
        cursor.execute("""
            SELECT l.quantite, l.montant as montant_ht, 
                   f.numero, f.date_facture, f.type_document,
                   c.code_client, c.raison_sociale,
                   p.nom as product_nom, p.code_produit, p.tva
            FROM lignes_facture l
            JOIN factures f ON l.facture_id = f.id
            JOIN clients c ON f.client_id = c.id
            JOIN products p ON l.product_id = p.id
            WHERE f.date_facture = ? AND f.statut != 'Annulée'
            ORDER BY f.numero
        """, (report_date,))
        
        details = []
        rows = cursor.fetchall()
        
        # Calculate row-level TTC for display
        total_day_ht = 0.0
        total_day_tva = 0.0
        total_day_ttc = 0.0
        total_day_qty = 0.0
        
        for r in rows:
            qty = r['quantite']
            ht = r['montant_ht']
            tva_rate = r['tva']
            tva_amount = ht * (tva_rate / 100)
            ttc = ht + tva_amount
            
            # For Avoirs, amounts are effective deductions but displayed positively in list?
            # Or if it's a sales report, usually Avoirs are negative.
            # Let's keep them positive but mark type. 
            # If the user wants "Ventes", maybe we only show Factures?
            # User said "Etat de vente", usually includes Sales (Factures). 
            # If Avoirs are significant, we might subtract. 
            # For now, we list everything. 
            # If type is Avoir, logically it should decrease the daily total.
            
            sign = -1 if r['type_document'] == 'Avoir' else 1
            
            total_day_ht += (ht * sign)
            total_day_tva += (tva_amount * sign)
            total_day_ttc += (ttc * sign)
            total_day_qty += (qty * sign)
            
            details.append({
                'code_client': r['code_client'],
                'client': r['raison_sociale'],
                'code_produit': r['code_produit'],
                'produit': r['product_nom'],
                'facture_num': r['numero'],
                'date': r['date_facture'],
                'qte': qty * sign,
                'ht': ht * sign,
                'tva': tva_amount * sign,
                'ttc': ttc * sign
            })
            
        # 2. Product Summary (Daily & Cumulative)
        products = self.db.get_all_products()
        product_stats = []
        
        total_cumul_ht = 0.0 # Just for info if needed, though report mostly asks for Qty
        
        for p in products:
            pid = p['id']
            
            # Daily Qty
            cursor.execute("""
                SELECT COALESCE(SUM(l.quantite), 0)
                FROM lignes_facture l
                JOIN factures f ON l.facture_id = f.id
                WHERE l.product_id = ? 
                AND f.date_facture = ? 
                AND f.type_document = 'Facture'
                AND f.statut != 'Annulée'
            """, (pid, report_date))
            daily_sales = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COALESCE(SUM(l.quantite), 0)
                FROM lignes_facture l
                JOIN factures f ON l.facture_id = f.id
                WHERE l.product_id = ? 
                AND f.date_facture = ? 
                AND f.type_document = 'Avoir'
                AND f.statut != 'Annulée'
            """, (pid, report_date))
            daily_returns = cursor.fetchone()[0]
            
            net_daily_qty = daily_sales - daily_returns
            
            # Cumulative Qty (Start of Year to Report Date Included)
            cursor.execute("""
                SELECT COALESCE(SUM(l.quantite), 0)
                FROM lignes_facture l
                JOIN factures f ON l.facture_id = f.id
                WHERE l.product_id = ? 
                AND f.date_facture BETWEEN ? AND ?
                AND f.type_document = 'Facture'
                AND f.statut != 'Annulée'
            """, (pid, start_of_year, report_date))
            cumul_sales = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COALESCE(SUM(l.quantite), 0)
                FROM lignes_facture l
                JOIN factures f ON l.facture_id = f.id
                WHERE l.product_id = ? 
                AND f.date_facture BETWEEN ? AND ?
                AND f.type_document = 'Avoir'
                AND f.statut != 'Annulée'
            """, (pid, start_of_year, report_date))
            cumul_returns = cursor.fetchone()[0]
            
            net_cumul_qty = cumul_sales - cumul_returns
            
            product_stats.append({
                'nom': p['nom'],
                'daily_qty': net_daily_qty,
                'cumul_qty': net_cumul_qty
            })
            
        # Calculate Yearly Global Turnover (for footer)
        # Assuming Global HT turnover
        cursor.execute("""
            SELECT COALESCE(SUM(montant_ht), 0) FROM factures 
            WHERE date_facture BETWEEN ? AND ? 
            AND type_document = 'Facture' AND statut != 'Annulée'
        """, (start_of_year, report_date))
        year_sales_ht = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COALESCE(SUM(montant_ht), 0) FROM factures 
            WHERE date_facture BETWEEN ? AND ? 
            AND type_document = 'Avoir' AND statut != 'Annulée'
        """, (start_of_year, report_date))
        year_returns_ht = cursor.fetchone()[0]
        
        year_net_ht = year_sales_ht - year_returns_ht

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

# Global business logic instance
_logic_instance: Optional[BusinessLogic] = None

def get_logic() -> BusinessLogic:
    """Get global business logic instance"""
    global _logic_instance
    if _logic_instance is None:
        _logic_instance = BusinessLogic()
    return _logic_instance
