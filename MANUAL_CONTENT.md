# Manuel d'Utilisation Complet - Gestion Commerciale ECDE

Ce manuel détaille l'ensemble des fonctionnalités du logiciel de Gestion Commerciale pour le dépôt de ciment ECDE. Il est conçu pour guider les utilisateurs, de la gestion quotidienne aux tâches administratives avancées.

---

## Table des Matières

1. [Introduction](#1-introduction)
2. [Connexion et Démarrage](#2-connexion-et-démarrage)
3. [Interface Principale (Tableau de Bord)](#3-interface-principale-tableau-de-bord)
4. [Gestion des Clients](#4-gestion-des-clients)
    * Fiche Client et Documents
    * Gestion des Contrats
    * Suivi des Soldes
5. [Gestion des Produits](#5-gestion-des-produits)
    * Création et Modification
    * Historique des Prix
    * Produits Parents/Enfants
6. [Gestion des Stocks (Réceptions)](#6-gestion-des-stocks-réceptions)
    * Saisir une Réception
    * Modification et Suppression (Sécurité)
7. [Facturation (Ventes)](#7-facturation-ventes)
    * Créer une Facture
    * Contrôles (Stock et Crédit)
    * Validation et Impression
    * Avoirs et Annulations
8. [Gestion des Paiements](#8-gestion-des-paiements)
    * Saisir un Règlement
    * Bordereaux de Remise
9. [Rapports et Situations](#9-rapports-et-situations)
    * État de Consommation
    * Stock Valorisé
    * Suivi Annuel des Créances
10. [Administration et Maintenance](#10-administration-et-maintenance)

---

## 1. Introduction

Le logiciel **Gestion Commerciale ECDE** est une solution intégrée pour la gestion de dépôts de matériaux de construction. Il permet de :

* Suivre les stocks en temps réel.
* Gérer la relation client (dettes, seuils de crédit, contrats).
* Éditer des factures et bons de réception conformes.
* Générer des rapports financiers et comptables précis.

---

## 2. Connexion et Démarrage

### Authentification

Au lancement, une fenêtre de connexion sécurise l'accès :

* **Utilisateur** : Sélectionnez votre compte dans la liste.
* **Mot de Passe** : Saisissez votre code confidentiel.
* **Connexion** : Valide l'accès. En cas d'erreur, un message vous avertira.

> **Note** : Les droits d'accès différencient les administrateurs (accès total) des utilisateurs simples (restrictions sur la suppression et les paramètres).

---

## 3. Interface Principale (Tableau de Bord)

Dès la connexion, le **Tableau de Bord** offre une vue synthétique de l'activité.

### Indicateurs Clés

* **Chiffre d'Affaires (CA)** : Graphique ou résumé des ventes sur la période.
* **État 104** : Aperçu rapide des taxes collectées.
* **Situation Clients** : Alertes sur les clients dépassant leur seuil de crédit.

### Navigation

La barre latérale gauche permet de basculer entre les modules :

* **Dashboard** : Vue d'ensemble.
* **Clients** : Base de données partenaires.
* **Produits** : Catalogue articles.
* **Réceptions** : Entrées de stock.
* **Factures** : Sorties et ventes.
* **Paiements** : Trésorerie.
* **Situation** : Rapports avancés.
* **Stock** : État actuel du dépôt.

---

## 4. Gestion des Clients

Ce module est le cœur de la relation commerciale.

### Fiche Client

Pour créer un client, cliquez sur **"Ajouter"**. Les champs obligatoires assurent la conformité des factures :

* **Code Client** : Identifiant unique (Généré ou Manuel).
* **Raison Sociale** : Nom de l'entreprise ou du client.
* **Informations Fiscales** : NIF, NIS, RC, Article d'Imposition (Art Impo). Ces mentions apparaîtront sur les factures.
* **Solde Inital (Report N-1)** : Dette ou crédit reporté de l'année précédente.
* **Seuil de Crédit** : Montant maximum de dette autorisée. Le logiciel bloquera la facturation si ce montant est atteint.

### Gestion des Contrats

Le bouton **"Contrats"** permet d'associer des documents contractuels à un client (PDF, Date de signature, Échéance). Utile pour le suivi juridique.

### Export

Le bouton **"Excel"** exporte la liste complète des clients avec leurs soldes actuels pour analyse externe.

---

## 5. Gestion des Produits

### Création de Produit

Définissez ici les articles vendus :

* **Désignation** et **Référence**.
* **Unités** : T (Tonne), U (Unité), etc.
* **Prix** : Prix d'Achat HT (pour la valorisation) et Prix de Vente HT.
* **TVA** : Taux applicable (généralement 19%).

### Historique des Prix

Le bouton **"Historique Prix"** est crucial. Si vous changez le prix d'un produit :

1. Le système archive l'ancien prix.
2. Les anciennes factures gardent l'ancien prix.
3. Les nouvelles factures utilisent le nouveau prix.

### Produits Parents (Gestion de Stock Avancée)

Certains produits peuvent être liés (ex: Vrac et Sac). La fonction "Parent" permet de décompter le stock d'un produit "Mère" lors de la vente d'un produit "Fille" (si configuré).

---

## 6. Gestion des Stocks (Réceptions)

Ce module enregistre les entrées de marchandises.

### Nouvelle Réception

Cliquez sur **"Ajouter"** pour saisir un Bon de Réception :

* **Fournisseur** & **Chauffeur/Matricule** : Pour la traçabilité du transport.
* **Date** : Date réelle de réception.
* **Lignes** : Sélectionnez le produit et la quantité.
  * *Quantité Annoncée* : Celle du BL fournisseur.
  * *Quantité Reçue* : Celle pesée/comptée à l'arrivée (C'est celle-ci qui incrémente le stock).

### Modification et Suppression (Soft Delete)

Pour garantir l'intégrité comptable :

* **Supprimer une réception** ne l'efface pas de la base. Elle passe en **statut "ANNULEE"**, s'affiche en **orange** dans la liste, et son impact sur le stock est annulé.
* Cela permet de garder une trace des erreurs de saisie sans fausser les stocks.

---

## 7. Facturation (Ventes)

### Créer une Facture

1. **Client** : Sélectionnez le client. Son solde et son seuil s'affichent.
2. **Date** : Par défaut la date du jour, modifiable (avec droits admin).
3. **Lignes** : Ajoutez les produits.
    * Le système vérifie instantanément la **disponibilité du stock**. Impossible de vendre ce qu'on n'a pas (Sauf autorisation spéciale).
    * **Remise** : Possibilité d'appliquer une remise en % (calcule automatiquement le net HT).
4. **Validation** :
    * *Brouillon* : Enregistre sans impacter le stock ni la dette client.
    * *Valider* : Décrémente le stock, augmente la dette du client, et génère le PDF.

### Contrôle de Crédit

Au moment de valider, si `Solde Actuel + Nouvelle Facture > Seuil Crédit`, le logiciel bloque la vente et demande une autorisation administrateur ou un paiement préalable.

### Impression

* **Original** : Exemplaire client.
* **Duplicata** : Pour l'archive.
* **Matrice** : Impression rapide sur imprimante matricielle (si configurée).

---

## 8. Gestion des Paiements

### Encaisser

Depuis le module Paiements ou directement depuis une facture :

* **Mode** : Espèces, Chèque, Virement, Versement Bancaire.
* **Montant** : Somme perçue.
* **Référence** : Numéro de chèque ou de virement obligatoire.

Le paiement vient immédiatement diminuer le solde (la dette) du client.

### Bordereaux

La fonction **"Créer Bordereau"** permet de regrouper plusieurs chèques ou paiements pour la remise en banque, générant un document récapitulatif imprimable.

---

## 9. Rapports et Situations

L'onglet **"Situation"** est le centre décisionnel.

### État de Consommation Journalière/Mensuelle

Génère un rapport (PDF ou Excel) détaillant pour une date donnée :

* Les quantités vendues par produit.
* La valeur des ventes (Chiffre d'Affaires).
* Les cumuls mensuels et annuels pour comparaison.

### Stock Valorisé (Inventaire Financier)

Ce rapport calcule la valeur de votre stock actuel.

* Méthode : Il utilise le **Prix d'Achat** (ou Coût de Revient) défini dans la fiche produit.
* Utilité : Indispensable pour le bilan comptable et l'assurance.

### Suivi Annuel des Créances

Un tableau complet "Grand Livre" qui pour chaque client affiche :

* Solde au 01/01 (Report).
* Total Achats de l'année.
* Total Paiements de l'année.
* Solde Final.
* Taux de recouvrement (%).

---

## 10. Administration et Maintenance

### Sauvegardes

* **Automatique** : Le logiciel effectue des sauvegardes régulières de la base de données dans le dossier `Backups`.
* **Miroir BDD** : Le bouton "Export Miroir" crée une copie de la base pour consulter les données sur un autre poste sans risquer de corrompre la base principale.

### Gestion des Utilisateurs

L'administrateur peut créer des comptes pour ses employés, définir leurs mots de passe, et réinitialiser les accès si nécessaire.

---

**Besoin d'assistance ?**
Pour toute question technique non couverte par ce manuel, veuillez contacter le support technique ou l'administrateur système.
