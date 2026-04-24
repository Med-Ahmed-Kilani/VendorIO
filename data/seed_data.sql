-- VendorIO seed data: creates schema + indexes + sample records

-- Products
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    unit_price DECIMAL(10,2) NOT NULL,
    cost_per_unit DECIMAL(10,2),
    current_stock INT DEFAULT 0,
    lead_time_days INT DEFAULT 7,
    reorder_point INT,
    attributes JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE
);

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

-- Order Items
CREATE TABLE IF NOT EXISTS order_items (
    id SERIAL PRIMARY KEY,
    order_id INT NOT NULL REFERENCES orders(id),
    product_id INT NOT NULL REFERENCES products(id),
    quantity INT NOT NULL,
    unit_price DECIMAL(10,2),
    line_total DECIMAL(12,2),
    UNIQUE(order_id, product_id)
);

-- Inventory Snapshots
CREATE TABLE IF NOT EXISTS inventory_snapshots (
    id SERIAL PRIMARY KEY,
    product_id INT NOT NULL REFERENCES products(id),
    stock_level INT,
    holding_cost DECIMAL(10,2),
    snapshot_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_orders_order_date ON orders(order_date);
CREATE INDEX IF NOT EXISTS idx_order_items_product ON order_items(product_id);
CREATE INDEX IF NOT EXISTS idx_inventory_snapshots_product_date ON inventory_snapshots(product_id, snapshot_date);
CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email);

-- Sample products
INSERT INTO products (name, category, unit_price, cost_per_unit, current_stock, lead_time_days, reorder_point) VALUES
('Arabica Coffee Beans 1kg',  'Coffee',   24.99, 9.50,  80,  7, 20),
('Green Tea 200g',            'Tea',       8.99, 2.50,   5,  5, 15),
('Earl Grey 100 bags',        'Tea',       7.99, 2.00,  40,  5, 10),
('Espresso Blend 500g',       'Coffee',   18.99, 7.00,  60,  7, 15),
('Matcha Powder 50g',         'Tea',      14.99, 5.00,  25,  7, 10),
('French Press 600ml',        'Equipment',34.99,12.00,  15, 14,  5),
('Reusable Coffee Filter',    'Equipment', 9.99, 3.00,  30,  7, 10),
('Cold Brew Bag Set (10pk)',   'Coffee',   12.99, 4.50,   8,  7, 10),
('Herbal Chamomile 50 bags',  'Tea',       6.99, 1.80, 200,  3, 30),
('Specialty Dark Roast 250g', 'Coffee',   16.99, 6.50,   3,  7, 10)
ON CONFLICT DO NOTHING;

-- Sample customers
INSERT INTO customers (email, first_order_date, total_spent, order_count) VALUES
('alice@example.com',   '2023-06-01', 450.00, 8),
('bob@example.com',     '2023-09-15', 125.00, 2),
('charlie@example.com', '2024-01-10', 890.00,15),
('diana@example.com',   '2024-02-20',  55.00, 1),
('eve@example.com',     '2023-11-05', 320.00, 5)
ON CONFLICT DO NOTHING;
