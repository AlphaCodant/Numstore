# NumStore v2.1 - Plateforme de Vente CI

## Problem Statement
Application web de vente de produits numériques et services de création de portfolio professionnel pour le marché ivoirien.

## Architecture
- **Backend**: FastAPI + MongoDB + Resend (emails)
- **Frontend**: React + Tailwind CSS + Shadcn UI
- **Payment**: Stripe
- **Currency**: FCFA (XOF)

## Services Principaux
### 1. Création de Portfolio Professionnel
- Standard (25 000 FCFA): Site web personnalisé basique
- Premium (50 000 FCFA): Design sur-mesure + animations + support 3 mois

### 2. Produits Numériques
- E-books, Templates avec code d'accès temporaire (6h)

## Flux Utilisateur - Portfolio
1. Client choisit une offre et paie
2. Client remplit formulaire (infos perso, compétences, expériences, projets)
3. Admin reçoit notification de nouvelle demande
4. Admin crée le portfolio web
5. Admin marque "Terminé" et entre l'URL
6. Client reçoit email avec son portfolio

## What's Been Implemented
- [x] Page d'accueil avec hero "Digitalisez votre Profil Professionnel"
- [x] Cartes services portfolio avec prix FCFA
- [x] Formulaire portfolio 4 étapes
- [x] Dashboard admin avec "Portfolios en attente"
- [x] Interface admin pour gérer les soumissions
- [x] Notification email au client quand portfolio terminé
- [x] Produits numériques avec code d'accès 6h

## Prioritized Backlog
### P1 (À configurer)
- [ ] Clé API Resend pour emails
- [ ] Images réalistes pour services portfolio

### P2 (Améliorations)
- [ ] Mobile Money (Flutterwave)
- [ ] Templates de portfolio générés automatiquement
- [ ] Système de relance pour formulaires non complétés
