# Gestion Commerciale GICA - ECDE

Application professionnelle complète pour la gestion commerciale d'une unité de distribution de ciment (ECDE - Groupe GICA). Développée en Python avec une interface moderne Tkinter et une base de données SQLite robuste.

## 🚀 Fonctionnalités Principales

### 🛠️ Architecture & Système

- **Base de Données Auto-Réparatrice ("Self-Healing")** : Au démarrage, le programme vérifie l'intégrité de la structure de la base de données par rapport au `MASTER_SCHEMA`. Il détecte et crée automatiquement les tables ou colonnes manquantes sans perte de données.
- **Sauvegarde Automatique** : Création automatique de backups horodatés dans le dossier `/Backups` à chaque fermeture de l'application.
- **Traçabilité** : Chaque action est loggée avec l'ID de l'utilisateur (Audit Logs).

### 💼 Gestion Commerciale

- **Tableau de Bord Dynamique** : Visualisation en temps réel des ventes, de la situation client, et de l'état "104".
- **Clients** :
  - Gestion complète (Info, Catégorie, RC, NIF, ART).
  - **Contrôle de Solde** : Bloque la facturation si le seuil de crédit est dépassé.
  - Calcul automatique du solde : `(Report N-1 + Paiements + Avoirs) - Factures`.
- **Produits & Stocks** :
  - Gestion des produits (Sac 25kg, 50kg, Vrac).
  - **Logique Parent/Enfant** : Gestion des codes prix liés à un produit parent.
  - **Réceptions** : Entrées de stock avec distinction "Sur Stock" ou "Sur Chantier".
  - **Mouvements de Stock** : Historique complet et recalcul possible.
  - **Self-Healing Stock** : Fonctionnalité pour recalculer et corriger les incohérences de stock.

### 📄 Facturation & Paiements

- **Factures** :
  - Création intuitive avec vérification de stock et de crédit.
  - **Champs Transport** : Gestion intégrée du Chauffeur, Matricule Tracteur et Remorque.
  - Impression PDF professionnelle avec logo GICA/ECDE et montant en lettres.
- **Avoirs (Notes de Crédit)** :
  - Génération simplifiée à partir d'une facture existante (pré-remplissage).
  - Contrôle strict : Le montant TTC de l'avoir ne peut excéder le "Reste dû" de la facture d'origine.
- **Paiements** :
  - Multi-modes : Espèces, Chèque, Virement, Versement.
  - **Bordereaux** : Génération de bordereaux de remise de chèques/virements pour la banque.

### 📊 Rapports & Exports

- **États PDF** :
  - Situation Globale Client.
  - Etat des Ventes Journalières (Format transposé pour meilleure lisibilité).
  - Factures, Bons de Réception, Bordereaux.
- **Exports Excel** : Listes clients, produits, situations.

## 💻 Installation

### Prérequis

- Python 3.8 ou supérieur
- Windows (recommandé pour l'impression directe et compatibilité)

### Installation des dépendances

Le fichier `requirements.txt` contient les bibliothèques nécessaires. Installez-les via pip :

```bash
pip install -r requirements.txt
```

**Dépendances clés :**

- `reportlab` : Génération de PDF.
- `openpyxl` : Export Excel.
- `Pillow` (PIL) : Gestion des images (Logos).
- `tkcalendar` : Widgets de calendrier (Optionnel mais recommandé).
- `pywin32` : Impression directe (Optionnel).

### Configuration Initiale

1. Assurez-vous que les fichiers logos (`logo_entete.png`, `logo_gica.png`) sont dans le répertoire racine.
2. Lancez l'application : `python main.py`
3. Identifiants par défaut :
   - **Utilisateur** : `admin`
   - **Mot de passe** : `admin123`

## 🏗️ Structure du Code

- **`main.py`** : Point d'entrée. Gère l'authentification et la boucle principale.
- **`ui.py`** : Interface Utilisateur (Tkinter). Contient toutes les fenêtres et onglets (Dashboard, Factures, etc.).
- **`logic.py`** : "Cerveau" de l'application. Contient toute la logique métier, calculs financiers, règles de stock.
- **`database.py`** : Couche d'accès aux données. Définit le `MASTER_SCHEMA` et gère le "Self-Healing".
- **`utils.py`** : Utilitaires pour la génération de PDF, exports Excel, et backups.

## 🔄 Workflows Types

### Faire une Facture

1. Aller dans l'onglet **Factures**.
2. Cliquer sur **Nouvelle Facture**.
3. Sélectionner le Client (les champs se remplissent).
4. Ajouter les produits. Le système vérifie le stock disponible.
5. Remplir les infos de transport (Chauffeur, Mat. Tracteur, etc.).
6. Valider. La facture est enregistrée, le stock décrémenté, et le PDF généré.

### Faire un Avoir

1. Sélectionner une facture existante dans la liste.
2. Cliquer sur **Créer Avoir**.
3. Le formulaire s'ouvre avec les infos du client pré-remplies.
4. Saisir les quantités retournées.
5. Valider. Le stock est réincrémenté.

### Clôture Annuelle

1. Via le menu **Configuration -> Clôture Annuelle**.
2. Le système archive les données de l'année en cours.
3. Calcule les reports à nouveau (Soldes clients, Stocks initiaux).
4. Prépare la base pour la nouvelle année.

---
**Développé pour ECDE - Groupe GICA**
