CREATE TABLE customers (id INT PRIMARY KEY, email VARCHAR(100));
CREATE TABLE orders (id INT, customer_id INT, PRIMARY KEY (id), FOREIGN KEY (customer_id) REFERENCES customers(id));
