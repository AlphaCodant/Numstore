-- =====================================================
-- Script d'insertion des produits NumStore
-- Exécuter après schema.sql
-- =====================================================

-- =====================================================
-- SERVICES PORTFOLIO
-- =====================================================

INSERT INTO products (id, name, description, price, currency, category, image_url, is_service, is_active, created_at)
VALUES 
(
    'prod_portfolio_essentiel',
    'Portfolio Essentiel',
    'Votre premier pas vers une présence digitale professionnelle. Site web one-page élégant avec présentation, parcours et compétences. Design moderne et responsive.',
    25000,
    'XOF',
    'portfolio',
    'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400',
    TRUE,
    TRUE,
    NOW()
),
(
    'prod_portfolio_premium',
    'Portfolio Premium',
    'Portfolio web multi-pages avec design sur-mesure, animations fluides, intégration réseaux sociaux, formulaire de contact et support pendant 3 mois.',
    50000,
    'XOF',
    'portfolio',
    'https://images.unsplash.com/photo-1560250097-0b93528c311a?w=400',
    TRUE,
    TRUE,
    NOW()
),
(
    'prod_portfolio_vip',
    'Pack VIP — Identité Digitale Complète',
    'L''offre ultime. Portfolio web premium + CV digital interactif + carte de visite NFC digitale + optimisation LinkedIn + support 6 mois.',
    95000,
    'XOF',
    'portfolio',
    'https://images.unsplash.com/photo-1551836022-d5d88e9218df?w=400',
    TRUE,
    TRUE,
    NOW()
),
(
    'prod_cv_digital',
    'Refonte CV Digital',
    'Transformation de votre CV classique en un CV digital moderne et interactif. Format web responsive accessible via lien personnalisé.',
    15000,
    'XOF',
    'portfolio',
    'https://images.unsplash.com/photo-1697292859784-c319e612ea15?w=400',
    TRUE,
    TRUE,
    NOW()
),
(
    'prod_linkedin_optim',
    'Optimisation Profil LinkedIn',
    'Audit complet et optimisation de votre profil LinkedIn: photo, bannière, résumé, expériences, et mots-clés pour maximiser votre visibilité.',
    20000,
    'XOF',
    'portfolio',
    'https://images.unsplash.com/photo-1611944212129-29977ae1398c?w=400',
    TRUE,
    TRUE,
    NOW()
);

-- =====================================================
-- TEMPLATES POWERPOINT
-- =====================================================

INSERT INTO products (id, name, description, price, currency, category, image_url, download_url, file_size, is_service, is_active, created_at)
VALUES 
(
    'prod_ppt_business',
    'Pack Templates PPT Business',
    'Collection de 10 templates PowerPoint professionnels pour vos présentations d''entreprise. Design moderne, graphiques inclus, entièrement personnalisables.',
    8000,
    'XOF',
    'template',
    'https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=400',
    'https://example.com/downloads/ppt_business.zip',
    '45 MB',
    FALSE,
    TRUE,
    NOW()
),
(
    'prod_ppt_startup',
    'Templates PPT Pitch Deck Startup',
    '5 templates de pitch deck conçus pour convaincre les investisseurs. Structure optimisée, slides financières, mockups produits inclus.',
    12000,
    'XOF',
    'template',
    'https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=400',
    'https://example.com/downloads/ppt_startup.zip',
    '35 MB',
    FALSE,
    TRUE,
    NOW()
),
(
    'prod_ppt_creative',
    'Pack Templates PPT Créatif',
    '15 templates PowerPoint au design créatif et coloré. Parfait pour les agences, freelances et présentations marketing.',
    10000,
    'XOF',
    'template',
    'https://images.unsplash.com/photo-1557804506-669a67965ba0?w=400',
    'https://example.com/downloads/ppt_creative.zip',
    '60 MB',
    FALSE,
    TRUE,
    NOW()
),
(
    'prod_ppt_minimal',
    'Templates PPT Minimaliste Pro',
    '8 templates élégants au design minimaliste. Idéal pour les consultants, formateurs et conférenciers.',
    7000,
    'XOF',
    'template',
    'https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=400',
    'https://example.com/downloads/ppt_minimal.zip',
    '25 MB',
    FALSE,
    TRUE,
    NOW()
);

-- =====================================================
-- SUPPORTS DE FORMATION
-- =====================================================

INSERT INTO products (id, name, description, price, currency, category, image_url, download_url, file_size, is_service, is_active, created_at)
VALUES 
(
    'prod_formation_excel',
    'Formation Excel Avancé',
    'Support de formation complet Excel: tableaux croisés dynamiques, formules avancées, macros VBA, dashboards. 150 pages + exercices pratiques.',
    15000,
    'XOF',
    'course',
    'https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=400',
    'https://example.com/downloads/formation_excel.zip',
    '85 MB',
    FALSE,
    TRUE,
    NOW()
),
(
    'prod_formation_marketing',
    'Guide Marketing Digital Complet',
    'E-book de 200 pages sur les stratégies marketing digital: SEO, réseaux sociaux, email marketing, publicité en ligne, analytics.',
    12000,
    'XOF',
    'course',
    'https://images.unsplash.com/photo-1432888622747-4eb9a8efeb07?w=400',
    'https://example.com/downloads/guide_marketing.pdf',
    '18 MB',
    FALSE,
    TRUE,
    NOW()
),
(
    'prod_formation_gestion_projet',
    'Support Formation Gestion de Projet',
    'Manuel complet de gestion de projet: méthodologies (Agile, Scrum, Waterfall), outils, templates, études de cas. 180 pages.',
    18000,
    'XOF',
    'course',
    'https://images.unsplash.com/photo-1507925921958-8a62f3d1a50d?w=400',
    'https://example.com/downloads/gestion_projet.zip',
    '95 MB',
    FALSE,
    TRUE,
    NOW()
),
(
    'prod_formation_finance',
    'Formation Finance pour Non-Financiers',
    'Comprendre les états financiers, analyser un bilan, calculer des ratios clés. Support PDF + tableurs Excel de pratique.',
    14000,
    'XOF',
    'course',
    'https://images.unsplash.com/photo-1554224155-6726b3ff858f?w=400',
    'https://example.com/downloads/formation_finance.zip',
    '40 MB',
    FALSE,
    TRUE,
    NOW()
),
(
    'prod_formation_powerbi',
    'Formation Power BI de A à Z',
    'Maîtrisez Power BI: importation de données, modélisation, DAX, visualisations, dashboards interactifs. Support + fichiers d''exercices.',
    20000,
    'XOF',
    'course',
    'https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=400',
    'https://example.com/downloads/formation_powerbi.zip',
    '120 MB',
    FALSE,
    TRUE,
    NOW()
);

-- =====================================================
-- COMPTES NETFLIX
-- =====================================================

INSERT INTO products (id, name, description, price, currency, category, image_url, download_url, file_size, is_service, is_active, created_at)
VALUES 
(
    'prod_netflix_1mois',
    'Compte Netflix Premium — 1 Mois',
    'Accès Netflix Premium (4 écrans, Ultra HD) pendant 1 mois. Profil individuel sur un compte partagé. Activation sous 24h.',
    3500,
    'XOF',
    'subscription',
    'https://images.unsplash.com/photo-1574375927938-d5a98e8ffe85?w=400',
    NULL,
    NULL,
    FALSE,
    TRUE,
    NOW()
),
(
    'prod_netflix_3mois',
    'Compte Netflix Premium — 3 Mois',
    'Accès Netflix Premium (4 écrans, Ultra HD) pendant 3 mois. Profil individuel garanti. Économisez 15% par rapport au mensuel.',
    9000,
    'XOF',
    'subscription',
    'https://images.unsplash.com/photo-1574375927938-d5a98e8ffe85?w=400',
    NULL,
    NULL,
    FALSE,
    TRUE,
    NOW()
),
(
    'prod_netflix_6mois',
    'Compte Netflix Premium — 6 Mois',
    'Accès Netflix Premium (4 écrans, Ultra HD) pendant 6 mois. Profil individuel garanti. Économisez 25% par rapport au mensuel.',
    16000,
    'XOF',
    'subscription',
    'https://images.unsplash.com/photo-1574375927938-d5a98e8ffe85?w=400',
    NULL,
    NULL,
    FALSE,
    TRUE,
    NOW()
),
(
    'prod_netflix_12mois',
    'Compte Netflix Premium — 12 Mois',
    'Accès Netflix Premium (4 écrans, Ultra HD) pendant 1 an complet. Profil individuel garanti. Meilleure offre: économisez 35%!',
    28000,
    'XOF',
    'subscription',
    'https://images.unsplash.com/photo-1574375927938-d5a98e8ffe85?w=400',
    NULL,
    NULL,
    FALSE,
    TRUE,
    NOW()
);

-- =====================================================
-- VERIFICATION
-- =====================================================

-- Afficher le résumé des produits insérés
SELECT 
    category,
    COUNT(*) as nombre,
    CASE WHEN is_service THEN 'Service' ELSE 'Produit' END as type
FROM products 
GROUP BY category, is_service
ORDER BY category;
