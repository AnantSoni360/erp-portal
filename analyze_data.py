import openpyxl
import pandas as pd

wb = openpyxl.load_workbook('MMTPL_Store_Tracker.xlsx', data_only=True)

# 1. Balance sheet
ws_bal = wb['Balance']
bal_data = []
for r in range(8, ws_bal.max_row + 1):
    item_id = ws_bal.cell(r, 1).value
    if item_id:
        bal_data.append({
            'item_id': str(item_id).strip(),
            'name': ws_bal.cell(r, 2).value,
            'category': ws_bal.cell(r, 3).value,
            'unit': ws_bal.cell(r, 4).value,
            'booked_inward': ws_bal.cell(r, 5).value or 0,
            'issued': ws_bal.cell(r, 6).value or 0,
            'returned': ws_bal.cell(r, 7).value or 0,
            'book_balance': ws_bal.cell(r, 8).value or 0,
            'reorder_level': ws_bal.cell(r, 9).value,
            'stock_status': ws_bal.cell(r, 10).value
        })
df_bal = pd.DataFrame(bal_data)
print(f"Total Materials in Balance: {len(df_bal)}")
print("Categories:", df_bal['category'].value_counts().to_dict())
print("Stock status breakdown:", df_bal['stock_status'].value_counts().to_dict())
print("Materials with reorder level:", df_bal['reorder_level'].dropna().count())
reorder_items = df_bal[df_bal['stock_status'] == 'Reorder']
print(f"Reorder alerts count: {len(reorder_items)}")
negative_items = df_bal[df_bal['stock_status'] == 'Negative']
print(f"Negative items count: {len(negative_items)}")

# 2. Inward sheet
ws_inw = wb['Inward']
inw_data = []
for r in range(8, ws_inw.max_row + 1):
    item_id = ws_inw.cell(r, 2).value
    qty = ws_inw.cell(r, 5).value
    status = ws_inw.cell(r, 6).value
    check = ws_inw.cell(r, 11).value
    receipt_id = ws_inw.cell(r, 10).value
    if item_id or qty is not None or status:
        inw_data.append({
            'date': ws_inw.cell(r, 1).value,
            'item_id': item_id,
            'qty': qty,
            'status': status,
            'check': check,
            'receipt_id': receipt_id
        })
df_inw = pd.DataFrame(inw_data)
print(f"\nTotal Inward records: {len(df_inw)}")
print("Inward Status breakdown:", df_inw['status'].value_counts(dropna=False).to_dict())
print("Inward Check breakdown:", df_inw['check'].value_counts(dropna=False).to_dict())

# 3. Contractors
contractors = []
total_contractor_tx = 0
for sheet in wb.sheetnames:
    if sheet in ['Balance', 'Inward']:
        continue
    ws = wb[sheet]
    acct = 'Unknown'
    for r in range(1, 6):
        v = ws.cell(r, 1).value
        if v and 'Account C' in str(v):
            acct = str(v).split('Account')[1].split('.')[0].strip()
    
    tx_count = 0
    posted_count = 0
    flagged_count = 0
    excluded_count = 0
    ok_count = 0
    for r in range(8, ws.max_row + 1):
        item_id = ws.cell(r, 2).value
        status = ws.cell(r, 7).value
        check = ws.cell(r, 14).value
        if item_id or status or ws.cell(r, 5).value is not None or ws.cell(r, 6).value is not None:
            tx_count += 1
            if status == 'Posted': posted_count += 1
            elif status == 'Flagged': flagged_count += 1
            elif status == 'Excluded': excluded_count += 1
            if check == 'OK': ok_count += 1
    total_contractor_tx += tx_count
    contractors.append({
        'sheet': sheet,
        'code': acct,
        'tx_count': tx_count,
        'posted': posted_count,
        'flagged': flagged_count,
        'excluded': excluded_count,
        'check_ok': ok_count
    })

print(f"\nTotal Contractor Sheets: {len(contractors)}")
print(f"Total Contractor Transactions: {total_contractor_tx}")
for c in contractors:
    print(f"{c['sheet']} ({c['code']}): {c['tx_count']} txs | Posted: {c['posted']}, Flagged: {c['flagged']}, Excluded: {c['excluded']}, OK: {c['check_ok']}")

wb.close()
