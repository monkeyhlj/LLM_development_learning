-- 1. 用户表（一对一的“一”端，一对多的“一”端）
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. 用户档案表（一对一）
CREATE TABLE profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL, -- 唯一约束保证一对一
    full_name VARCHAR(100),
    phone VARCHAR(20),
    address TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 3. 商品表（多对多的“多”端）
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    stock INTEGER DEFAULT 0
);

-- 4. 订单表（一对多的“多”端）
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(10,2) DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 5. 订单-商品 中间表（多对多）
CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    price DECIMAL(10,2) NOT NULL, -- 快照下单时的商品价格
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- 插入用户
INSERT INTO users (username, email) VALUES
('alice_w', 'alice@example.com'),
('bob_chen', 'bob@example.com'),
('carol_lin', 'carol@example.com');

-- 插入用户档案（一对一）
INSERT INTO profiles (user_id, full_name, phone, address) VALUES
(1, 'Alice Wang', '13812345678', '上海市浦东新区xx路1号'),
(2, 'Bob Chen', '13987654321', '北京市朝阳区yy路2号'),
(3, 'Carol Lin', '13788889999', '深圳市南山区zz路3号');

-- 插入商品
INSERT INTO products (name, price, stock) VALUES
('机械键盘', 299.00, 50),
('游戏鼠标', 129.00, 100),
('4K显示器', 1999.00, 20),
('USB-C扩展坞', 89.00, 80);

-- 插入订单（一对多：一个用户多个订单）
INSERT INTO orders (user_id, total_amount) VALUES
(1, 0), (1, 0),  -- 用户alice有2个订单
(2, 0),          -- 用户bob有1个订单
(3, 0);          -- 用户carol有1个订单

-- 插入订单项（多对多关联订单与商品，并更新订单总金额）

-- 订单1（用户1）：键盘 *1 + 鼠标 *2
INSERT INTO order_items (order_id, product_id, quantity, price)
VALUES
(1, 1, 1, (SELECT price FROM products WHERE id=1)),
(1, 2, 2, (SELECT price FROM products WHERE id=2));

-- 订单2（用户1）：显示器 *1
INSERT INTO order_items (order_id, product_id, quantity, price)
VALUES (2, 3, 1, (SELECT price FROM products WHERE id=3));

-- 订单3（用户2）：扩展坞 *3
INSERT INTO order_items (order_id, product_id, quantity, price)
VALUES (3, 4, 3, (SELECT price FROM products WHERE id=4));

-- 订单4（用户3）：键盘 *1 + 鼠标 *1 + 扩展坞 *1
INSERT INTO order_items (order_id, product_id, quantity, price)
VALUES
(4, 1, 1, (SELECT price FROM products WHERE id=1)),
(4, 2, 1, (SELECT price FROM products WHERE id=2)),
(4, 4, 1, (SELECT price FROM products WHERE id=4));

-- 更新订单总金额（根据订单项计算）
UPDATE orders SET total_amount = (
    SELECT SUM(quantity * price) FROM order_items WHERE order_items.order_id = orders.id
);





-- 表注释
COMMENT ON TABLE users IS '用户表（一对一的“一”端，一对多的“一”端）';
COMMENT ON TABLE profiles IS '用户档案表（与users表为一对一关系）';
COMMENT ON TABLE products IS '商品表（多对多的“多”端）';
COMMENT ON TABLE orders IS '订单表（与users表为一对多关系）';
COMMENT ON TABLE order_items IS '订单-商品中间表（实现orders与products多对多关系）';

-- 字段注释
-- users 表
COMMENT ON COLUMN users.id IS '用户ID，主键，自增';
COMMENT ON COLUMN users.username IS '用户名，唯一，不可为空';
COMMENT ON COLUMN users.email IS '邮箱，唯一，不可为空';
COMMENT ON COLUMN users.created_at IS '创建时间，默认为当前时间戳';

-- profiles 表
COMMENT ON COLUMN profiles.id IS '档案ID，主键，自增';
COMMENT ON COLUMN profiles.user_id IS '用户ID，外键关联users表，唯一约束保证一对一关系';
COMMENT ON COLUMN profiles.full_name IS '真实姓名';
COMMENT ON COLUMN profiles.phone IS '手机号码';
COMMENT ON COLUMN profiles.address IS '地址';

-- products 表
COMMENT ON COLUMN products.id IS '商品ID，主键，自增';
COMMENT ON COLUMN products.name IS '商品名称';
COMMENT ON COLUMN products.price IS '商品价格（元），保留两位小数';
COMMENT ON COLUMN products.stock IS '库存数量，默认为0';

-- orders 表
COMMENT ON COLUMN orders.id IS '订单ID，主键，自增';
COMMENT ON COLUMN orders.user_id IS '用户ID，外键关联users表';
COMMENT ON COLUMN orders.order_date IS '下单时间，默认为当前时间戳';
COMMENT ON COLUMN orders.total_amount IS '订单总金额（元），保留两位小数，默认为0';

-- order_items 表
COMMENT ON COLUMN order_items.id IS '订单项ID，主键，自增';
COMMENT ON COLUMN order_items.order_id IS '订单ID，外键关联orders表';
COMMENT ON COLUMN order_items.product_id IS '商品ID，外键关联products表';
COMMENT ON COLUMN order_items.quantity IS '购买数量，必须大于0';
COMMENT ON COLUMN order_items.price IS '下单时商品的快照价格（元），保留两位小数';






