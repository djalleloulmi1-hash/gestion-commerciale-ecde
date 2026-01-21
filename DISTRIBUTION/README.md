# GESTION COMMERCIALE GICA (ECDE) - MANUEL D'INSTALLATION ET D'UTILISATION

> [!IMPORTANT]
> **A LIRE IMPERATIVEMENT AVANT LA PREMIERE UTILISATION**
> Ce logiciel est configuré pour fonctionner dans un répertoire spécifique pour garantir la stabilité de la base de données et des sauvegardes.

## 📥 INSTALLATION RAPIDE (POUR L'UTILISATEUR FINAL)

Pour que le logiciel fonctionne correctement, veuillez suivre scrupuleusement ces étapes lors de la première installation :

### 1. Emplacement du Dossier

Le logiciel **DOIIT** être installé directement à la racine du disque `C:`.

1. Copiez le dossier complet contenant le programme.
2. Collez-le dans `C:\` (Disque Local C).
3. **IMPORTANT** : Le dossier doit s'appeler exactement `GICA_PROJET`.
    * ❌ Incorrect : `C:\Users\Nom\Bureau\GICA_PROJET`
    * ❌ Incorrect : `C:\GICA_PROJET_FINAL`
    * ✅ **Correct** : `C:\GICA_PROJET`

### 2. Lancement du Logiciel

Pour faciliter l'utilisation quotidienne, ne lancez pas le programme via Python manuellement. Utilisez le script automatique :

1. Allez dans le dossier `C:\GICA_PROJET`.
2. Trouvez le fichier **`Lancer gestion.bat`**.
3. Faites un clic droit dessus > "Envoyer vers" > "Bureau (créer un raccourci)".
4. Vous pouvez maintenant lancer le logiciel depuis votre bureau en double-cliquant sur ce raccourci.

---

## 🔑 PREMIÈRE CONNEXION

Lors du premier lancement, utilisez les identifiants administrateur par défaut (sauf si une base de données existante est fournie) :

* **Identifiant** : `admin`
* **Mot de passe** : `admin`

> [!TIP]
> Il est fortement recommandé de changer ce mot de passe ou de créer des comptes utilisateurs personnels via le menu **Configuration -> Utilisateurs**.

---

## 🚀 FONCTIONNALITÉS PRINCIPALES

Ce logiciel gère l'activité commerciale complète de l'unité de distribution.

### 1. Tableau de Bord

* Vue d'ensemble du Chiffre d'Affaires.
* Suivi des Tonnes Vendues et Restantes.
* État du Stock en temps réel ("104").

### 2. Ventes (Facturation)

* **Créer une Facture** :
  * Sélectionnez le client pour voir son solde et son seuil de crédit.
  * Ajoutez les produits (alertes stock automatique).
  * Le PDF s'imprime automatiquement ou s'ouvre pour vérification.
* **Avoirs** :
  * Possibilité d'annuler une facture ou de faire un retour marchandise via l'onglet "Avoirs".

### 3. Stocks & Réceptions

* **Réception** : Saisie des entrées (Achats) venant de l'usine.
* **Historique** : Traçabilité complète de chaque mouvement (Entrée/Sortie).
* **Inventaire** : Le stock est calculé automatiquement `(Stock Initial + Réceptions - Ventes)`.

### 4. Clients

* Suivi des **Soldes** en temps réel (Code couleur : Rouge = Créditeur, Orange = Débiteur).
* Historique des paiements et chèques.

### 5. Rapports (Éditions)

Le logiciel génère automatiquement vos rapports quotidiens et mensuels :

* **État des Ventes Journalières** (Récapitulatif pour la comptabilité).
* **État de Stock Valorisé**.
* **Rapport de Consommation Globale**.

---

## 🛠️ MAINTENANCE ET SAUVEGARDE

* **Sauvegarde (Backup)** : Le logiciel crée AUTOMATIQUEMENT une copie de sécurité de vos données à chaque fermeture dans le dossier `C:\GICA_PROJET\Backups`. Ne supprimez pas ce dossier.
* **Miroir** : Une copie de la base de données est accessible en lecture seule pour la direction sans bloquer la saisie.

---

## ⚠️ EN CAS DE PROBLÈME

Si le logiciel ne se lance pas :

1. Vérifiez que le dossier est bien dans `C:\GICA_PROJET`.
2. Vérifiez que vous ne l'avez pas lancé depuis une clé USB ou un dossier compressé (.zip/.rar). Il faut d'abord l'extraire.
3. Contactez l'administrateur système si le problème persiste.

---
**Développé par Mr: OULMI ABDELDJALLIL**
**N° Téléphone : 0554 15 57 37**
**E-mail : <djalleloulmi1@gmail.com>**
