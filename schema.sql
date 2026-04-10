-- Schema PostgreSQL pour NumStore
-- Exécuter ce script lors de la création de la base de données

-- Table des produits
CREATE TABLE IF NOT EXISTS products (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'XOF',
    category VARCHAR(50) NOT NULL,
    image_url TEXT,
    download_url TEXT,
    file_size VARCHAR(20),
    is_service BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table des transactions de paiement
CREATE TABLE IF NOT EXISTS payment_transactions (
    id VARCHAR(36) PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    product_id VARCHAR(36) REFERENCES products(id),
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'XOF',
    email VARCHAR(255) NOT NULL,
    payment_status VARCHAR(20) DEFAULT 'pending',
    access_code_sent BOOLEAN DEFAULT FALSE,
    is_service BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table des codes d'accès
CREATE TABLE IF NOT EXISTS access_codes (
    id VARCHAR(36) PRIMARY KEY,
    code VARCHAR(10) NOT NULL,
    product_id VARCHAR(36) REFERENCES products(id),
    email VARCHAR(255) NOT NULL,
    order_id VARCHAR(36),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_used BOOLEAN DEFAULT FALSE
);

-- Table des soumissions de portfolio
CREATE TABLE IF NOT EXISTS portfolio_submissions (
    id VARCHAR(36) PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    job_title VARCHAR(255) NOT NULL,
    bio TEXT NOT NULL,
    phone VARCHAR(50),
    location VARCHAR(255),
    photo_url TEXT,
    skills JSONB DEFAULT '[]',
    experiences JSONB DEFAULT '[]',
    education JSONB DEFAULT '[]',
    projects JSONB DEFAULT '[]',
    linkedin_url TEXT,
    twitter_url TEXT,
    github_url TEXT,
    website_url TEXT,
    product_id VARCHAR(36) REFERENCES products(id),
    payment_status VARCHAR(20) DEFAULT 'pending',
    session_id VARCHAR(255),
    status VARCHAR(20) DEFAULT 'pending',
    portfolio_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index pour améliorer les performances
CREATE INDEX IF NOT EXISTS idx_products_active ON products(is_active);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_payment_transactions_session ON payment_transactions(session_id);
CREATE INDEX IF NOT EXISTS idx_payment_transactions_email ON payment_transactions(email);
CREATE INDEX IF NOT EXISTS idx_access_codes_code ON access_codes(code);
CREATE INDEX IF NOT EXISTS idx_portfolio_submissions_status ON portfolio_submissions(status);
