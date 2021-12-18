from fastapi import FastAPI, Request
import sqlite3
import uvicorn
from datetime import datetime
from helpers import calculateStatistics, convertToEuro, CheckCreditCard, revenueRanking, customersRanking
from database import InitDatabase

app = FastAPI()
InitDatabase()

db = sqlite3.connect('database.db', isolation_level=None)

@app.post("/create-company-account")
async def handler(payload: Request):
    try:
        body = await payload.json()

        name = body['name']
        vat = body['VAT']
        email = body['email']
        adress = body['adress']
        iban = body['IBAN']

        company = db.execute(
            'INSERT INTO companies (vat, name, email, adress, iban) VALUES (?,?,?,?,?)',
            (vat, name, email, adress, iban)
        )

        return {
            "message": name + " company has been saved (id: " + str(company.lastrowid) + ") !"
        }
    except:
        return {
            "message": "Bad request."
        }

@app.post("/create-customer-account")
async def handler(payload: Request):
    try:
        body = await payload.json()

        iban = body['IBAN']
        name = body['name']
        email = body['email']
        adress = body['adress']
        company = body['company']

        customer = db.execute(
            'INSERT INTO customers(iban, name, email, adress, company) VALUES (?,?,?,?,?)',
            (iban, name, email, adress, company)
        )

        return {
            "message": name + " customer has been saved (id: " + str(customer.lastrowid) + ") !"
        }
    except:
        return {
            "message": "Bad request."
        }

@app.post("/create-quote")
async def handler(payload: Request):
    try:
        body = await payload.json()

        quote = db.execute(
            'INSERT INTO quotes(company, quantity, price, currency) VALUES (?,?,?,?)',
            (body['company'], body['quantity'], body['price'], body['currency'])
        )

        return {
            "message": "Quote (id: " + str(quote.lastrowid) + ") has been saved!"
        }
    except:
        return {
            "message": "Bad request."
        }

@app.post("/create-subscription")
async def handler(payload: Request):
    try:
        body = await payload.json()

        subscription = db.execute(
            'INSERT INTO subscriptions (customer, quote, accepted) VALUES (?,?,0)',
            (body['customer'], body['quote'])
        )

        return {
            "message": "Subscription (id: " + str(subscription.lastrowid) + ") has been saved for customer " + body['customer'] + "!"
        }
    except:
        return {
            "message": "Bad request."
        }
    

@app.post("/update-subscription")
async def handler(payload: Request):
    try:
        body = await payload.json()

        subscription = int(body['subscription'])

        subscription_quote = db.execute(
            'SELECT quote FROM subscriptions WHERE id = ?',
            ([subscription])
        ).fetchall()

        subscription_data = db.execute(
            'SELECT price, currency FROM quotes WHERE id = ?',
            ([subscription_quote[0][0]])
        ).fetchall()

        price = convertToEuro(subscription_data[0][0],subscription_data[0][1])
        price_tva_included = price * 1.21

        if body['status'] == "accepted":

            db.execute(
                'UPDATE subscriptions SET accepted = 1 WHERE id = ?',
                ([subscription])
            )

            db.execute(
                'INSERT INTO invoices (subscription, paid, due) VALUES (?,0,?)',
                ([subscription, price_tva_included])
            )

            return {
                "message": "Subscription (id: " + str(subscription) + ") has been accepted!"
            }
        else:
            return {
                "message": "Bad request."
            }
    except:
        return {
            "message": "Bad request."
        }

@app.post("/pending-invoices")
async def handler(payload: Request):
    try:
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
                    inv = list(invoice)
                    invoices.append({
                        "id": inv[0],
                        "subscription": inv[1],
                        "date": inv[2],
                        "status": "Unpaid",
                        "NOTAX": inv[4] / 1.21,
                        "TAX": inv[4],
                        "received": inv[5],
                        "due": inv[4] - inv[5],
                    })

        return {
            "message": "The following invoices are still waiting to be regularized:",
            "details": {
                "invoices": invoices
            }
        }
    except:
        return {
            "message": "Bad request."
        }

@app.post("/update-invoice")
async def handler(payload: Request):
    try:
        body = await payload.json()

        id = body['invoice']
        received = convertToEuro(float(body['received']), body['currency'])
        number = body['card']

        invoice = db.execute(
            'SELECT * FROM invoices WHERE id = ?',
            (int(id),)
        ).fetchall()

        if (len(invoice) > 0):

            due = invoice[0][4]
            received_previously = invoice[0][5]

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
                        "message": "Invoice (id: "+ str(id) +") successfully updated!"
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
    except:
        return {
            "message": "Bad request."
        }


@ app.post("/company-statistics")
async def handler(payload: Request):
    try:
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
            "message": "Here are the statistics of your company (" + str(company) + "):",
            "details": {
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
        }
    except:
        return {
            "message": "Bad request."
        }

@app.post('/cron-send-invoices')
async def handler(payload: Request):
    try:
        all_customers = db.execute(
            'SELECT * FROM customers',
        ).fetchall()

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
    except:
        return {
            "message": "Bad request."
        }

@app.post('/ask-classement')
async def handler(payload: Request):
    try:
        body = await payload.json()

        vat = body['vat']

        company = db.execute(
            'SELECT * FROM companies WHERE vat = ?',
            ([vat])
        ).fetchall()
        
        place_revenue=revenueRanking(company[0])
        place_client =customersRanking(company[0])

        companies = db.execute(
            'SELECT * FROM companies'
        ).fetchall()
        
        companies_counter = len(companies)

        return {
            "message": "Here are your company's ("+ str(vat) +") place in our ranking, out of "+str(companies_counter)+" companies :",
            "revenue": place_revenue,
            "customers": place_client,
        }
    except:
        return {
            "message": "Bad request."
        }

if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8000)
