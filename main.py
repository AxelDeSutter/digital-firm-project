from fastapi import FastAPI, Request
import sqlite3
import uvicorn
from datetime import datetime
from helpers import calculateStatistics, convertToEuro, CheckCreditCard, classement_revenue, classement_client
from database import InitDatabase

app = FastAPI()
InitDatabase()

db = sqlite3.connect('database.db', isolation_level=None)

# # Routes
@app.post("/create-company-account")
async def root(payload: Request):
    body = await payload.json()

    name = body['name']
    vat = body['VAT']
    email = body['email']
    adress = body['adress']
    iban = body['IBAN']

    db.execute(
        'INSERT INTO companies (vat, name, email, adress, iban) VALUES (?,?,?,?,?)',
        (vat, name, email, adress, iban)
    )

    return {
        "message": name + " company has been saved!"
    }

# # Create customer account - Salma


@app.post("/create-customer-account")
async def root(payload: Request):
    body = await payload.json()

    iban = body['IBAN']
    name = body['name']
    email = body['email']
    adress = body['adress']
    company = body['company']

    db.execute(
        'INSERT INTO customers(iban, name, email, adress, company) VALUES (?,?,?,?,?)',
        (iban, name, email, adress, company)
    )

    return {
        "message": name + " customer has been saved!"
    }

# # Create quote - Zelie


@app.post("/create-quote")
async def root(payload: Request):
    body = await payload.json()

    quote = db.execute(
        'INSERT INTO quotes(company, quantity, price, currency) VALUES (?,?,?,?)',
        (body['company'], body['quantity'], body['price'], body['currency'])
    )

    return {
        "message": "Quote (id: " + str(quote.lastrowid) + ") has been saved!"
    }


# # Create subscription - Zélie
@app.post("/create-subscription")
async def root(payload: Request):
    body = await payload.json()

    subscription = db.execute(
        'INSERT INTO subscriptions (customer, quote, accepted) VALUES (?,?,0)',
        (body['customer'], body['quote'])
    )

    return {
        "message": "Subscription (id: " + str(subscription.lastrowid) + ") has been saved for customer " + body['customer'] + "!"
    }

# # Update subscription - Victor


@app.post("/update-subscription")
async def root(payload: Request):
    body = await payload.json()

    subscription = int(body['subscription'])

    subscription_quote = db.execute(
        'SELECT quote FROM subscriptions WHERE id = ?',
        ([subscription])
    ).fetchall()

    subscription_data = db.execute(
        'SELECT price FROM quotes WHERE id = ?',
        ([subscription_quote[0][0]])
    ).fetchall()

    price = subscription_data[0][0]

    if body['status'] == "accepted":

        # We set the subscription as accepted
        db.execute(
            'UPDATE subscriptions SET accepted = 1 WHERE id = ?',
            ([subscription])
        )

        # We create the first invoice for the subscription
        db.execute(
            'INSERT INTO invoices (subscription, paid, due) VALUES (?,0,?)',
            ([subscription, price])
        )

        return {
            "message": "Subscription (id: " + str(subscription) + ") has been accepted!"
        }
    else:
        return {
            "message": "Bad request."
        }


# # Retrieve pending invoices - Victor
@app.post("/pending-invoices")
async def root(payload: Request):
    body = await payload.json()

    customer_subscriptions = db.execute(
        'SELECT * FROM subscriptions WHERE customer = ?',
        ([body['customer']])
    ).fetchall()

    invoices = []
    for subscription in customer_subscriptions:
        pending_invoices = db.execute(
            'SELECT * FROM invoices WHERE paid=0 AND subscription = ?',
            (str(subscription[0]))
        ).fetchall()

        if(len(pending_invoices) > 0):
            for invoice in pending_invoices:
                # Transforms a tuple in a modifiable list
                # Needed to be able to .append()
                inv = list(invoice)
                inv[4] * 1.21
                inv.append(inv[4] * 1.21)
                invoices.append(inv)

    return {
        "message": "The following invoices are still waiting to be regularized, the following (TVA incl.) amounts are to be paid :",
        "invoices": invoices
    }


# # Update invoice (paid/unpaid) - Tom
@app.post("/update-invoice")
async def root(payload: Request):
    body = await payload.json()

    id = body['invoice']
    received = body['received']
    number = body['card']

    invoice = db.execute(
        'SELECT * FROM invoices WHERE id = ?',
        (int(id),)
    ).fetchall()

    due = invoice[0][4]
    received_previously = invoice[0][5]

    # invoice[0] = Invoice to be updated
    # invoice[0][4] = Fouth column of invoice to be updated: 'received'

    if (len(invoice) > 0):
        if CheckCreditCard(number) == True:
            if (received <= due - received_previously):

                if (received + received_previously == due):
                    db.execute(
                        'UPDATE invoices SET paid = 1, received = ? WHERE id = ?',
                        (float(received) + float(received_previously), int(id))
                    )
                else:
                    db.execute(
                        'UPDATE invoices SET received = ? WHERE id = (?)',
                        (float(received) + float(received_previously), int(id))
                    )

                return {
                    "message": "Invoice successfully updated!"
                }
            else:
                return {
                    "message": "Total received amount can't exceed invoice amount."
                }
        else:
            return {
                "message": "Invalid credit card."
            }
    else:
        return {
            "message": "Invalid invoice."
        }


# # Retrieve company's statistics - Tom
@ app.post("/company-statistics")
async def root(payload: Request):
    body = await payload.json()

    company = body['company']

    stats = calculateStatistics(company)

    company_customers = db.execute(
        'SELECT * FROM customers WHERE company = ?',
        ([str(company)])
    ).fetchall()

    customers_array = []
    for customer in company_customers:

        customer_subscriptions = db.execute(
            'SELECT * FROM subscriptions WHERE customer = ?',
            ([customer[0]])
        ).fetchall()

        customers_array.append({
            'customer': customer,
            'subscriptions': customer_subscriptions
        })


    return {
        "MRR": {
            "NOTAX": stats['MRR'],
            "TAX": stats['MRR'] * 1.21
        },
        "ARR": {
            "NOTAX": stats['ARR'],
            "TAX": stats['ARR'] * 1.21
        },
        "ACR": {
            "NOTAX": stats['ARC'],
            "TAX": stats['ARC'] * 1.21
        },
        "CUSTOMERS": {
            "total": stats['CUSTOMERS'],
            "details": customers_array
        }
    }


@app.post('/cron-send-invoices')
async def root(payload: Request):

    all_customers = db.execute(
        'SELECT * FROM customers',
    ).fetchall()

    # Pour chaque client, on prend sa dernière invoice
    for customer in all_customers:
        customer_subscriptions = db.execute(
            'SELECT * FROM subscriptions WHERE customer = ?',
            ([customer[0]])
        ).fetchall()
        for subscription in customer_subscriptions:
            last_invoice = db.execute(
                'SELECT * FROM invoices WHERE subscription = ? ORDER BY id DESC',
                ([subscription[0]])
            ).fetchone()

            if(last_invoice):
                last_invoice_date = last_invoice[2]

                year = int(last_invoice_date.split('-')[0])
                month = int(last_invoice_date.split('-')[1])
                day = int(last_invoice_date.split('-')[2].split(' ')[0])
                
                next_month = datetime(year + int(month / 12), ((month % 12) + 1), day)

                db.execute(
                    'INSERT INTO invoices (subscription, date, paid, due) VALUES (?,?,0,?)',
                    ([subscription[0], next_month, last_invoice[4]])
                )

    return {
        "message": "New invoices have been generated.",
    }

@app.post('/ask-classement')
async def root(payload: Request):
    body = await payload.json()

    #dans le body ils mettront leur vat de la company 
    vat = body['vat']

    company = db.execute(
        'SELECT * FROM companies WHERE vat = ?',
        ([vat])
    ).fetchall()
    
    place_revenue=classement_revenue(company[0]) #fonction à faire 
    place_client =classement_client(company[0]) #fonction à faire

    #nombre de companies à avoir 
    companies = db.execute(
        'SELECT * FROM companies'
    ).fetchall()
    
    companies_counter = len(companies)

    return {
        "message": "In terms of revenue , you are currently placed in "
        + str(place_revenue)+ " place in the ranking of companies and in terms of number of clients, you are currently ranked in"
        + str(place_client)+ "place in the ranking of companies, out of "+ str(companies_counter)+ " companies",
        "place_revenue": place_revenue,
        "place_clients": place_client,
    }


# # Start server
if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8000)
