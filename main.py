from fastapi import FastAPI, Request
import sqlite3
import uvicorn
import requests
from datetime import date

app = FastAPI()

# Init database - Axel
db = sqlite3.connect('database.db', isolation_level=None)

db.execute(
    '''
        CREATE TABLE IF NOT EXISTS companies(
            vat TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            adress TEXT NOT NULL,
            iban TEXT NOT NULL
        )
    '''
)

db.execute(
    '''
        CREATE TABLE IF NOT EXISTS customers(
            iban TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            adress TEXT NOT NULL,
            company TEXT NOT NULL
        )
    '''
)

db.execute(
    '''
        CREATE TABLE IF NOT EXISTS quotes(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            quantity INT NOT NULL,
            price FLOAT NOT NULL,
            currency TEXT NOT NULL
        )
    '''
)

db.execute(
    '''
        CREATE TABLE IF NOT EXISTS subscriptions(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer TEXT NOT NULL,
            quote INT NOT NULL,
            accepted BOOL NOT NULL,
            starting TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    '''
)

db.execute(
    '''
        CREATE TABLE IF NOT EXISTS invoices(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subscription INT NOT NULL,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            paid BOOL NOT NULL
        )
    '''
)

db.execute(
    '''
        CREATE TABLE IF NOT EXISTS rates(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            currency TEXT NOT NULL,
            rate FLOAT NOT NULL
        )
    '''
)
#dans le cours ils ferment à chaque fois bien la base de données, à faire aussi ici? 

# Helper functions - Axel
# Check credit card validity
def CheckCreditCard(number):
    try:
        last = int(number[-1])
        number = number[:-1][::-1]
        total = last
        for digit in number:
            digit = int(digit)
            if(digit % 2 == 0):
                if(digit*2 <= 9):
                    total += digit*2
                else:
                    total += digit * 2 - 9
        return total % 10 == 0
    except:
        return False

# Conversion between currencies
# - Example
# - Convert 100$ to €:
# - AnyVariableName = convertToEuro(100, "USD")
def convertToEuro(amount, currency):
    today = today = str(date.today())
    actualRate = db.execute('SELECT * FROM rates WHERE currency = ? AND date = ?', (currency, today)).fetchall()
    rate = 1
    if(len(actualRate) > 0):
        rate = actualRate[0][3]
    else:
        rateFromApi = requests.get('https://v6.exchangerate-api.com/v6/9f3b63e712fb3bf92872a235/latest/'+currency).json()
        if(rateFromApi['result'] == "success"):
            rate = rateFromApi['conversion_rates']['EUR']
            db.execute('INSERT INTO rates (date, currency, rate) VALUES (?,?,?)', (today, currency, rate))
        else:
            rate = 1
    return amount * rate

# # Routes
# # Create company account - Salma
            # vat TEXT PRIMARY KEY, # name TEXT NOT NULL, # email TEXT NOT NULL, # adress TEXT NOT NULL, # iban TEXT NOT NULL
@app.post("/create-company-account")
async def root(payload: Request):
            # No need to open the db again ? 
    body = await payload.json()
            #'nom', 'TVA', 'mail', 'adresse','banque' to change with API variable names
    name = body['nom']
    vat = body['TVA']
    email = body['mail']
    adress = body['adresse']
    iban = body['banque']
    query_company = dbase.execute('''
    INSERT INTO companies(vat, name, email, adress, iban)
    VALUES (?,?,?,?,?)''',
    (vat, name, email, adress, iban))
            # IF Conversion à faire selon la forme des variables données :
            #   VALUES ({TVA}, {nom},{mail},{adresse},{iban})             
            #   '''.format(TVA=value_dict['TVA'], nom=values_dict['nom'], mail=value_dict['mail'], adresse=value_dict['adresse', banque=value_dict['banque']))
    return vat, name, email, adress, iban

# # Create customer account - Salma
            #iban TEXT PRIMARY KEY, #name TEXT NOT NULL, #email TEXT NOT NULL, #adress TEXT NOT NULL, #company TEXT NOT NULL
@app.post("/create-customer-account")
async def root(payload: Request):
    body = await payload.json()
            #'banque', 'nom', 'mail', adresse', 'entreprise' to change with API variable names
    iban = body['banque']
    name = body['nom']
    email = body['mail']
    adress = body['adresse']
    company = body['entreprise']
    query_company = dbase.execute('''
    INSERT INTO customers(iban, name, email, adress, company_id)
    VALUES (?,?,?,?,?)'''
    (iban,name,email,adress,company))
            #'''.format(iban=value_dict['TVA'], nom=values_dict['nom'], mail=value_dict['mail'], adresse=value_dict['adresse', banque=value_dict['banque']))
    return iban, name, email, adress, company

# # Create quote - Zelie
@app.post("/create-quote")
async def root(payload: Request):
    body = await payload.json()
    db = sqlite3.connect('database.db', isolation_level=None)
    
    quote = db.execute('''
            INSERT INTO quotes
            (company, quantity, price, currency)
            VALUES ('{company}','{quantity}','{price}','{currency}')
            '''.format(company=body['company'],quantity=body['quantity'],price=body['price'],currency=body['currency']))
    return quote 


# # Create subscription - Zélie
@app.post("/create-subscription")
async def root(payload: Request):
    body = await payload.json()
    db = sqlite3.connect('database.db', isolation_level=None)

    subscription = db.execute('''
                INSERT INTO subscription
                (customer, quote, accepted, starting)
                VALUES ('{customer}', '{quote}','0','{starting}')
                 '''.format(customer=body['customer'],quote=body['quote'],starting= xxx))
                 #j'ai mis la valeur 0 par défaut à 'accepted' mais jsp si c'est correct
                 #aussi, je sais comment définir la date, c'est une fonction spéciale? 
    return subscription 

# # Update subscription - Victor
@app.post("/update-subscription")
async def root(payload: Request):
    body = await payload.json()

    return

# # Retrieve pending invoices - Victor
@app.post("/pending-invoices")
async def root(payload: Request):
    body = await payload.json()

    return

# # Update invoice (paid/unpaid) - Tom
@app.post("/update-invoice")
async def root(payload: Request):
    body = await payload.json()

    return

# # Retrieve company's statistics - Tom
@app.post("/company-statistics")
async def root(payload: Request):
    body = await payload.json()

    return

# # Start server
if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8000)
