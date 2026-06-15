-- VendorIO seed data: recipe-based schema

-- Customers
CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255),
    first_order_date DATE,
    total_spent DECIMAL(12,2),
    order_count INT DEFAULT 0,
    customer_attributes JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Raw materials (ingredients / stock items)
CREATE TABLE IF NOT EXISTS raw_materials (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    category VARCHAR(100),
    unit VARCHAR(50),
    cost_per_unit DECIMAL(10,2),
    reorder_point INT,
    lead_time_days INT DEFAULT 7,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Live inventory per raw material
CREATE TABLE IF NOT EXISTS raw_material_inventory (
    id SERIAL PRIMARY KEY,
    material_id INT NOT NULL REFERENCES raw_materials(id) ON DELETE CASCADE,
    current_stock INT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Sellable products (no cost here — cost lives in recipes)
CREATE TABLE IF NOT EXISTS final_products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    category VARCHAR(100),
    unit_price DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Recipes: one row per (product, size) combination
CREATE TABLE IF NOT EXISTS recipes (
    id SERIAL PRIMARY KEY,
    product_id INT NOT NULL REFERENCES final_products(id) ON DELETE CASCADE,
    size VARCHAR(10),
    unit_cost DECIMAL(10,4) NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Recipe ingredients
CREATE TABLE IF NOT EXISTS recipe_items (
    id SERIAL PRIMARY KEY,
    recipe_id INT NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    material_id INT NOT NULL REFERENCES raw_materials(id) ON DELETE RESTRICT,
    quantity_needed DECIMAL(10,4) NOT NULL,
    unit VARCHAR(50),
    notes VARCHAR(255)
);

-- Orders
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    order_date TIMESTAMP WITH TIME ZONE NOT NULL,
    customer_id INT REFERENCES customers(id),
    total_amount DECIMAL(12,2),
    status VARCHAR(50) DEFAULT 'completed',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Order line items (unit_cost snapshotted at import time)
CREATE TABLE IF NOT EXISTS order_items (
    id SERIAL PRIMARY KEY,
    order_id INT NOT NULL REFERENCES orders(id),
    product_id INT NOT NULL REFERENCES final_products(id),
    recipe_id INT REFERENCES recipes(id),
    size VARCHAR(10),
    quantity INT NOT NULL,
    unit_price DECIMAL(10,2),
    unit_cost DECIMAL(10,4),
    line_total DECIMAL(12,2),
    UNIQUE(order_id, product_id, size)
);

-- Payment transactions
CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    order_id INT NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    amount_paid DECIMAL(12,2) NOT NULL,
    payment_method VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_raw_materials_category ON raw_materials(category);
CREATE INDEX IF NOT EXISTS idx_rmi_material_id ON raw_material_inventory(material_id);
CREATE INDEX IF NOT EXISTS idx_final_products_category ON final_products(category);
CREATE INDEX IF NOT EXISTS idx_recipes_product_id ON recipes(product_id);
CREATE INDEX IF NOT EXISTS idx_recipe_items_recipe_id ON recipe_items(recipe_id);
CREATE INDEX IF NOT EXISTS idx_recipe_items_material_id ON recipe_items(material_id);
CREATE INDEX IF NOT EXISTS idx_orders_order_date ON orders(order_date);
CREATE INDEX IF NOT EXISTS idx_order_items_product ON order_items(product_id);
CREATE INDEX IF NOT EXISTS idx_order_items_recipe ON order_items(recipe_id);
CREATE INDEX IF NOT EXISTS idx_transactions_order_id ON transactions(order_id);
CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email);

-- -----------------------------------------------------------------------
-- Sample data: coffee & tea business
-- -----------------------------------------------------------------------

-- Raw materials
INSERT INTO raw_materials (name, category, unit, cost_per_unit, reorder_point, lead_time_days) VALUES
('Arabica Beans',      'Coffee', 'grams',  0.0095, 5000,  7),
('Robusta Beans',      'Coffee', 'grams',  0.0070, 3000,  7),
('Green Tea Leaves',   'Tea',    'grams',  0.0125, 2000,  5),
('Earl Grey Leaves',   'Tea',    'grams',  0.0100, 1500,  5),
('Matcha Powder',      'Tea',    'grams',  0.0500, 1000,  7),
('Chamomile Flowers',  'Tea',    'grams',  0.0090,  800,  3),
('Whole Milk',         'Dairy',  'ml',     0.0012, 5000,  2),
('Oat Milk',           'Dairy',  'ml',     0.0018, 3000,  3),
('Sugar Syrup',        'Other',  'ml',     0.0008, 2000,  7),
('Espresso Shot',      'Coffee', 'ml',     0.0200, 1000,  3)
ON CONFLICT DO NOTHING;

-- Seed live inventory
INSERT INTO raw_material_inventory (material_id, current_stock)
SELECT id,
    CASE name
        WHEN 'Arabica Beans'     THEN 20000
        WHEN 'Robusta Beans'     THEN 15000
        WHEN 'Green Tea Leaves'  THEN 8000
        WHEN 'Earl Grey Leaves'  THEN 6000
        WHEN 'Matcha Powder'     THEN 3000
        WHEN 'Chamomile Flowers' THEN 5000
        WHEN 'Whole Milk'        THEN 20000
        WHEN 'Oat Milk'          THEN 10000
        WHEN 'Sugar Syrup'       THEN 8000
        WHEN 'Espresso Shot'     THEN 4000
    END
FROM raw_materials
ON CONFLICT DO NOTHING;

-- Final products
INSERT INTO final_products (name, category, unit_price) VALUES
('Espresso',        'Coffee',    3.50),
('Americano',       'Coffee',    3.80),
('Flat White',      'Coffee',    4.20),
('Matcha Latte',    'Tea',       4.50),
('Green Tea',       'Tea',       3.00),
('Earl Grey',       'Tea',       3.20),
('Chamomile Tea',   'Tea',       2.80),
('Cold Brew',       'Coffee',    4.00),
('Oat Flat White',  'Coffee',    4.80),
('Chai Latte',      'Tea',       4.20)
ON CONFLICT DO NOTHING;

-- Recipes (NULL size = no size variant; drinks may have S/M/L added later)
INSERT INTO recipes (product_id, size, unit_cost)
SELECT id,
    NULL,
    CASE name
        WHEN 'Espresso'       THEN 0.60
        WHEN 'Americano'      THEN 0.65
        WHEN 'Flat White'     THEN 0.90
        WHEN 'Matcha Latte'   THEN 1.20
        WHEN 'Green Tea'      THEN 0.50
        WHEN 'Earl Grey'      THEN 0.45
        WHEN 'Chamomile Tea'  THEN 0.40
        WHEN 'Cold Brew'      THEN 0.80
        WHEN 'Oat Flat White' THEN 1.10
        WHEN 'Chai Latte'     THEN 0.95
    END
FROM final_products
ON CONFLICT DO NOTHING;

-- Recipe items (simplified 1-ingredient mapping for seed data)
INSERT INTO recipe_items (recipe_id, material_id, quantity_needed, unit)
SELECT r.id, m.id, 18, 'grams'
FROM recipes r
JOIN final_products fp ON r.product_id = fp.id AND r.size IS NULL
JOIN raw_materials m ON m.name = 'Arabica Beans'
WHERE fp.name IN ('Espresso', 'Americano', 'Flat White', 'Cold Brew')
ON CONFLICT DO NOTHING;

INSERT INTO recipe_items (recipe_id, material_id, quantity_needed, unit)
SELECT r.id, m.id, 18, 'grams'
FROM recipes r
JOIN final_products fp ON r.product_id = fp.id AND r.size IS NULL
JOIN raw_materials m ON m.name = 'Arabica Beans'
WHERE fp.name = 'Oat Flat White'
ON CONFLICT DO NOTHING;

INSERT INTO recipe_items (recipe_id, material_id, quantity_needed, unit)
SELECT r.id, m.id, 150, 'ml'
FROM recipes r
JOIN final_products fp ON r.product_id = fp.id AND r.size IS NULL
JOIN raw_materials m ON m.name = 'Oat Milk'
WHERE fp.name = 'Oat Flat White'
ON CONFLICT DO NOTHING;

INSERT INTO recipe_items (recipe_id, material_id, quantity_needed, unit)
SELECT r.id, m.id, 3, 'grams'
FROM recipes r
JOIN final_products fp ON r.product_id = fp.id AND r.size IS NULL
JOIN raw_materials m ON m.name = 'Green Tea Leaves'
WHERE fp.name = 'Green Tea'
ON CONFLICT DO NOTHING;

INSERT INTO recipe_items (recipe_id, material_id, quantity_needed, unit)
SELECT r.id, m.id, 3, 'grams'
FROM recipes r
JOIN final_products fp ON r.product_id = fp.id AND r.size IS NULL
JOIN raw_materials m ON m.name = 'Earl Grey Leaves'
WHERE fp.name = 'Earl Grey'
ON CONFLICT DO NOTHING;

INSERT INTO recipe_items (recipe_id, material_id, quantity_needed, unit)
SELECT r.id, m.id, 5, 'grams'
FROM recipes r
JOIN final_products fp ON r.product_id = fp.id AND r.size IS NULL
JOIN raw_materials m ON m.name = 'Matcha Powder'
WHERE fp.name = 'Matcha Latte'
ON CONFLICT DO NOTHING;

INSERT INTO recipe_items (recipe_id, material_id, quantity_needed, unit)
SELECT r.id, m.id, 3, 'grams'
FROM recipes r
JOIN final_products fp ON r.product_id = fp.id AND r.size IS NULL
JOIN raw_materials m ON m.name = 'Chamomile Flowers'
WHERE fp.name = 'Chamomile Tea'
ON CONFLICT DO NOTHING;

-- Sample customers
INSERT INTO customers (email, first_order_date, total_spent, order_count) VALUES
('alice@example.com',   '2023-06-01', 450.00, 8),
('bob@example.com',     '2023-09-15', 125.00, 2),
('charlie@example.com', '2024-01-10', 890.00,15),
('diana@example.com',   '2024-02-20',  55.00, 1),
('eve@example.com',     '2023-11-05', 320.00, 5)
ON CONFLICT DO NOTHING;
