# scripts/generate_data.py
import random, json, os, uuid
from faker import Faker
from datetime import datetime, timedelta

fake = Faker()
FRAUD_RATE = 0.02  # baseline fraud proportion (adjustable)
US_MERCHANTS = {
    "groceries": ["CornerCafe","FreshMart","VeggieStop"],
    "electronics": ["GadgetWorld","UnknownElectronics","ElectroHub"],
    "travel": ["SkylinesTravel","BudgetJet","HotelComfort"],
    "dining": ["TacoTown","PastaHouse","SushiSpot"],
    "atm": ["ATM Network"],
    "others": ["SubscriptionSvc","InsuranceCo","UtilitiesCo"]
}

merchant_risk = {
    "groceries": 0.05,
    "electronics": 0.25,
    "travel": 0.15,
    "dining": 0.08,
    "atm": 0.02,
    "others": 0.04
}

def make_account(uid):
    avg = round(random.uniform(300, 2000),2)
    bal = round(random.uniform(0, 10000),2)
    return {
        "user_id": uid,
        "name": fake.name(),
        "account_type": random.choice(["checking","savings"]),
        "opened_at": fake.date_between(start_date='-6y', end_date='-1y').isoformat(),
        "account_balance": bal,
        "avg_monthly_spend": avg,
        "std_monthly_spend": round(avg * random.uniform(0.2,0.8),2),
        "card_status": random.choice(["Active","Frozen"]),
        "reported_priority": random.choice(["LOW","MEDIUM","HIGH"]),
        "true_risk_flag": 0,
        "chargeback_history": random.randint(0,2),
        "last_login_ip_country": random.choice(["US","CA","GB"]),
        "device_fingerprint": f"dev_{fake.lexify('???')}"
    }

def simulate_transactions_for_account(account, n_tx=500, inject_fraud_patterns=True):
    txns = []
    base_dt = datetime.utcnow()
    avg = account["avg_monthly_spend"]
    device = account["device_fingerprint"]
    for i in range(n_tx):
        dt = base_dt - timedelta(minutes=random.randint(0, 60*24*90))  # last 90 days
        cat = random.choices(list(US_MERCHANTS.keys()), weights=[30,10,5,20,3,32])[0]
        merchant = random.choice(US_MERCHANTS[cat])
        # amount distribution: small purchases common, occasional large ones
        if random.random() < 0.95:
            amount = round(random.expovariate(1/20),2)  # many small ones
        else:
            amount = round(random.uniform(200, 5000),2)
        # foreign chance
        is_foreign = 1 if random.random() < 0.03 else 0
        country = "JP" if is_foreign else "US"
        # velocity: simplistic
        velocity_24h = random.randint(1,6)
        # merchant risk
        m_risk = merchant_risk.get(cat, 0.05)
        # guess high amount relative to avg
        is_high_amount = 1 if amount > (avg * 2.5) else 0

        # Fraud label (baseline)
        label = 1 if random.random() < FRAUD_RATE else 0

        txn = {
            "txn_id": f"t_{account['user_id']}_{i:05d}",
            "user_id": account["user_id"],
            "timestamp": dt.isoformat()+"Z",
            "amount": amount,
            "currency": "USD",
            "merchant": merchant,
            "merchant_category": cat,
            "city": fake.city(),
            "country": country,
            "channel": random.choice(["POS","online","atm"]),
            "is_foreign": is_foreign,
            "is_high_amount": is_high_amount,
            "velocity_24h": velocity_24h,
            "device_fingerprint": device,
            "ip_country": country,
            "merchant_risk_score": round(m_risk + random.uniform(-0.02,0.05), 2),
            "label_fraud": label,
            "user_reported_issue": False
        }
        txns.append(txn)

    # inject fraud patterns if needed
    if inject_fraud_patterns:
        # pattern 1: burst large foreign txns
        if random.random() < 0.2:
            idx = random.randint(0, len(txns)-1)
            txns[idx]["amount"] = round(random.uniform(1500, 5000),2)
            txns[idx]["is_foreign"] = 1
            txns[idx]["ip_country"] = random.choice(["RU","CN","NG"])
            txns[idx]["merchant_risk_score"] = 0.95
            txns[idx]["label_fraud"] = 1
            # mark account risk
            account["true_risk_flag"] = 1
        # pattern 2: many small rapid txns (card test)
        if random.random() < 0.15:
            base_idx = random.randint(0, len(txns)-20)
            for j in range(base_idx, base_idx+8):
                txns[j]["amount"] = round(random.uniform(0.5,5.0),2)
                txns[j]["timestamp"] = (datetime.utcnow() - timedelta(minutes=j)).isoformat()+"Z"
                txns[j]["label_fraud"] = 1
            account["true_risk_flag"] = 1

    return txns

def simulate_users(n_users=3, tx_per_user=800):
    accounts = []
    all_txns = []
    for k in range(n_users):
        uid = f"user_{k+1:03d}"
        acct = make_account(uid)
        # bias reported priority: some users lie to get attention
        if random.random() < 0.12:
            acct["reported_priority"] = "HIGH"  # user exaggerates
        accounts.append(acct)
        txns = simulate_transactions_for_account(acct, n_tx=tx_per_user)
        all_txns.extend(txns)
    return accounts, all_txns

if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    accounts, txns = simulate_users(n_users=5, tx_per_user=1000)
    with open("data/accounts.json","w") as f:
        json.dump(accounts, f, indent=2)
    with open("data/transactions.json","w") as f:
        json.dump(txns, f, indent=2)
    # also write CSVs for ML convenience
    import csv
    with open("data/transactions.csv","w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(txns[0].keys()))
        writer.writeheader()
        writer.writerows(txns)
    with open("data/accounts.csv","w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(accounts[0].keys()))
        writer.writeheader()
        writer.writerows(accounts)
    print("Wrote data/accounts.json, data/transactions.json, data/transactions.csv")
