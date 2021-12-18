import sqlite3
import requests
from datetime import date

db = sqlite3.connect('database.db', isolation_level=None)

def CheckCreditCard(number):
    try:
        last = int(number[-1])
        number = number[:-1][::-1]
        total = last
        i=0
        for digit in number:
            digit = int(digit)
            if(i % 2 == 0):
                if(digit*2 <= 9):
                    total += digit*2
                else:
                    total += digit * 2 - 9
            else:
                total += digit
            i+=1
        return total % 10 == 0
    except:
        return False

def convertToEuro(amount, currency):
    today = str(date.today())
    actualRate = db.execute(
        'SELECT * FROM rates WHERE currency = ? AND date = ?', (currency, today)).fetchall()
    rate = 1
    if(len(actualRate) > 0):
        rate = actualRate[0][3]
    else:
        rateFromApi = requests.get(
            'https://v6.exchangerate-api.com/v6/9f3b63e712fb3bf92872a235/latest/'+currency).json()
        if(rateFromApi['result'] == "success"):
            rate = rateFromApi['conversion_rates']['EUR']
            db.execute('INSERT INTO rates (date, currency, rate) VALUES (?,?,?)', (today, currency, rate))
        else:
            rate = 1
    return amount * rate

def calculateStatistics(company):
    quotes_of_companies = db.execute(
        'SELECT * FROM quotes WHERE company = ?',
        ([str(company)])
    ).fetchall()
    
    number_of_subscriptions = 0
    MRR = 0

    for quote in quotes_of_companies:
        price = convertToEuro(quote[3], quote[4])

        subscriptions_of_companies = db.execute(
            'SELECT * FROM subscriptions WHERE quote = ? AND accepted = 1',
            ([quote[0]])
        ).fetchall()

        number_of_subscriptions += len(subscriptions_of_companies)

        MRR += len(subscriptions_of_companies) * price

    company_customers = db.execute(
        'SELECT * FROM customers WHERE company = ?',
        ([str(company)])
    ).fetchall()

    return {
        "MRR": MRR,
        "ARR": 12 * MRR,
        "ARC": (MRR / number_of_subscriptions) if number_of_subscriptions > 0 else 0,
        "CUSTOMERS": len(company_customers)
    }


def revenueRanking(company):
    all_MRR = []
    all_companies = db.execute(
        'SELECT * FROM companies'
        ).fetchall()
    
    for comp in all_companies:
        MRR = calculateStatistics(comp[0])['MRR']
        all_MRR.append(MRR)
        all_MRR.sort(reverse=True)
    
    company_MRR = calculateStatistics(company[0])['MRR']

    company_rank = all_MRR.index(company_MRR)

    return company_rank + 1

def customersRanking(company): 
    all_CUSTOMERS = []
    all_companies = db.execute(
        'SELECT * FROM companies'
    ).fetchall()
    
    for comp in all_companies:
        CUSTOMERS = calculateStatistics(comp[0])['CUSTOMERS']
        all_CUSTOMERS.append(CUSTOMERS)
        all_CUSTOMERS.sort(reverse=True)
    
    company_CUSTOMERS = calculateStatistics(company[0])['CUSTOMERS']

    company_rank = all_CUSTOMERS.index(company_CUSTOMERS)

    return company_rank + 1