CREATE TABLE IF NOT EXISTS companies(
    vat TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    adress TEXT NOT NULL,
    iban TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS customers(
    iban TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    adress TEXT NOT NULL,
    company TEXT,
    FOREIGN KEY (company) REFERENCES companies(vat)
);

CREATE TABLE IF NOT EXISTS quotes(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company TEXT NOT NULL,
    quantity INT NOT NULL,
    price FLOAT NOT NULL,
    currency TEXT NOT NULL,
    FOREIGN KEY (company) REFERENCES companies(vat)
);

CREATE TABLE IF NOT EXISTS subscriptions(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer TEXT NOT NULL,
    quote INT NOT NULL,
    accepted BOOL NOT NULL DEFAULT 0,
    starting TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer) REFERENCES customers(iban),
    FOREIGN KEY (company) REFERENCES companies(vat)
);

CREATE TABLE IF NOT EXISTS invoices(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subscription INT NOT NULL,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    paid BOOL NOT NULL,
    due FLOAT NOT NULL,
    received FLOAT NOT NULL DEFAULT 0,
    FOREIGN KEY (subscription) REFERENCES subscriptions(id)
);

CREATE TABLE IF NOT EXISTS rates(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    currency TEXT NOT NULL,
    rate FLOAT NOT NULL
);