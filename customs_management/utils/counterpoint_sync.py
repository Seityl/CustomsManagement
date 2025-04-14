import frappe

import pymssql
import datetime
from datetime import time

from customs_management.api import upload_item

def send_missing_ticket_noticication():
    locations = frappe.get_doc('Store Location Mapping').store_location_mapping
    recipients = ['jeriel@jollys.local', 'cdgrant@jollysonline.com', 'jprevost@jollysonline.com', 'mwilkins@jollysonline.com', 'ecyrille@jollysonline.com']

    fetched_tickets = []

    for location in locations:
        location_id = location.store_location
        location_sales = get_counterpoint_sales(location_id)
        fetched_tickets.extend(location_sales)

    all_tickets = query_counterpoint_tickets(fetched_tickets)

    yesterday = frappe.utils.add_days(frappe.utils.nowdate(), -1)
    existing_tickets = frappe.db.get_all('CounterPoint Sales', 
        filters={'ticket_date': ['like', f'{yesterday} 00:00:00']}, 
        fields=['ticket_number'], 
        as_list=True
    )

    existing_ticket_numbers = {t[0] for t in existing_tickets}
    missing_tickets = []

    for ticket in all_tickets:
        ticket_number = ticket['ticket_number']
        if ticket_number not in existing_ticket_numbers:
            missing_tickets.append({
                'ticket_number': ticket_number,
                'location': ticket.get('ticket_location', ''),
                'customer': ticket.get('customer_name', '')
            })

    if not missing_tickets:
        return

    subject = f"Missing CounterPoint Tickets Report - {frappe.utils.nowdate()}"

    table_rows = "".join([
        f"""
        <tr>
            <td>{ticket['ticket_number']}</td>
            <td>{ticket['location']}</td>
            <td>{ticket['customer']}</td>
        </tr>
        """ for ticket in missing_tickets
    ])

    message = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
            }}
            .email-container {{
                margin: 0 auto;
                padding: 20px;
            }}
            .header {{
                background-color: #2c3e50;
                color: white;
                padding: 15px;
                border-radius: 5px 5px 0 0;
            }}
            .content {{
                border: 1px solid #ddd;
                border-top: none;
                padding: 20px;
                border-radius: 0 0 5px 5px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }}
            th {{
                background-color: #f2f2f2;
                color: #2c3e50;
                text-align: left;
                padding: 12px;
            }}
            td {{
                padding: 10px 12px;
                border-bottom: 1px solid #ddd;
            }}
            tr:nth-child(even) {{
                background-color: #f9f9f9;
            }}
            tr:hover {{
                background-color: #f1f1f1;
            }}
            .summary {{
                background-color: #f8f9fa;
                padding: 15px;
                border-radius: 5px;
                margin-top: 20px;
            }}
            .footer {{
                margin-top: 30px;
                font-size: 0.9em;
                color: #777;
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="header">
                <h2>Missing CounterPoint Tickets Report</h2>
                <p>{frappe.utils.format_date(frappe.utils.nowdate(), 'full')}</p>
            </div>
            
            <div class="content">
                <p>Dear Team,</p>
                <p>The following CounterPoint tickets from <strong>{yesterday}</strong> were not synced to the system:</p>
                
                <table>
                    <thead>
                        <tr>
                            <th>Ticket #</th>
                            <th>Location</th>
                            <th>Customer</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table_rows}
                    </tbody>
                </table>
                
                <div class="summary">
                    <p><strong>Total missing tickets:</strong> {len(missing_tickets)}</p>
                </div>
                
                <p>Please investigate and take appropriate action.</p>
                
                <div class="footer">
                    <p>This is an automated notification. Please do not reply to this email.</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

    frappe.sendmail(
        recipients=recipients,
        subject=subject,
        message=message,
        now=True
    )
	
def sync_counterpoint_sales():
    locations = frappe.get_doc('Store Location Mapping').store_location_mapping
    fetched_tickets = []
    for location in locations:
        location_id = location.store_location
        location_sales = get_counterpoint_sales(location_id)
        fetched_tickets.extend(location_sales)

    all_tickets = query_counterpoint_tickets(fetched_tickets)

    for ticket in all_tickets:
        frappe.enqueue(
            create_counterpoint_sales_ticket,
            queue = 'default', 
            timeout = 3600,
            is_async = True,
            now = False, 
            job_name = f"Sync Ticket {ticket['ticket_number']}",
            ticket = ticket
        )

def get_counterpoint_sales(location_id):
    conn = pymssql.connect(
        server = '10.0.10.5',
        user = 'SA',
        password = 'Counterpoint1',
        database = 'Jollyspharm',
        as_dict = True
    )
    cursor = conn.cursor()
    query = f"""
        SELECT
            PS_TKT_HIST_LIN.QTY_SOLD,
            PS_TKT_HIST.CUST_NO,
            PS_TKT_HIST_LIN.ITEM_NO,
            PS_TKT_HIST_LIN.TKT_NO,
            PS_TKT_HIST_LIN.EXT_PRC,
            PS_TKT_HIST_LIN.EXT_COST,
            AR_CUST.NAM,
            PS_TKT_HIST_LIN.DESCR,
            PS_TKT_HIST_LIN.BUS_DAT,
            PS_TKT_HIST.TKT_TYP,
            PS_TKT_HIST_LIN.LIN_TYP,
            PS_TKT_HIST.STR_ID
        FROM
            PS_TKT_HIST
        LEFT OUTER JOIN
            AR_CUST
        ON
            PS_TKT_HIST.CUST_NO = AR_CUST.CUST_NO
        INNER JOIN
            PS_TKT_HIST_LIN 
        ON
            PS_TKT_HIST.BUS_DAT = PS_TKT_HIST_LIN.BUS_DAT AND PS_TKT_HIST.DOC_ID = PS_TKT_HIST_LIN.DOC_ID
        WHERE
            PS_TKT_HIST_LIN.STR_ID = {location_id} AND
            PS_TKT_HIST.TKT_TYP <> 'A' AND
            PS_TKT_HIST.BUS_DAT = CAST(DATEADD(DAY, -2, GETDATE()) AS DATE)
    """

    cursor.execute(query)
    results = cursor.fetchall()
    ticket_data = {}

    for item in results:
        if item['TKT_NO'] not in ticket_data:
            ticket_data[item['TKT_NO']] = {
                'items': [
                    {
                        'exact_cost': item['EXT_COST'],
                        'description': item['DESCR'],
                        'item_code': item['ITEM_NO'],
                        'item_name': item['DESCR'],
                        'price': item['EXT_PRC'],
                        'qty': item['QTY_SOLD']
                    }
                ], 
                'customer_number': item['CUST_NO'],
                'total_quantity': item['QTY_SOLD'],
                'ticket_location': item['STR_ID'],
                'ticket_number': item['TKT_NO'],
                'ticket_type': item['TKT_TYP'],
                'ticket_date': item['BUS_DAT'],
                'customer_name': item['NAM'],
                'post_date': item['BUS_DAT'],
                'line_type': item['LIN_TYP'],
            }
        else: 
            item_data = {
                'exact_cost': item['EXT_COST'],
                'description': item['DESCR'],
                'item_code': item['ITEM_NO'],
                'item_name': item['DESCR'],
                'price': item['EXT_PRC'],
                'qty': item['QTY_SOLD']
            }
            ticket_data[item['TKT_NO']]['total_quantity'] += item['QTY_SOLD']
            ticket_data[item['TKT_NO']]['items'].append(item_data)

    tickets = [{**v} for k, v in ticket_data.items()]

    return tickets

def query_counterpoint_tickets(fetched_tickets):
    conn = pymssql.connect(
        server = '10.0.10.5',
        user = 'SA',
        password = 'Counterpoint1',
        database = 'Jollyspharm',
        as_dict = True
    )
    cursor = conn.cursor()
    query = """
        SELECT
            TKT_NO AS ticket_number
        FROM
            PS_TKT_HIST
        WHERE
            PS_TKT_HIST.TKT_TYP <> 'A' AND
            PS_TKT_HIST.BUS_DAT = CAST(DATEADD(DAY, -2, GETDATE()) AS DATE)
    """
    cursor.execute(query) 
    all_tickets = cursor.fetchall()

    all_ticket_numbers = {row['ticket_number'] for row in all_tickets}
    fetched_ticket_numbers = {ticket['ticket_number'] for ticket in fetched_tickets}
    missing_tickets = all_ticket_numbers - fetched_ticket_numbers

    if not missing_tickets:
        conn.close()
        return fetched_tickets
    
    ticket_numbers_str = ",".join([f"'{ticket}'" for ticket in missing_tickets])

    for ticket in missing_tickets:
        query2 = f"""
            SELECT
                PS_TKT_HIST_LIN.QTY_SOLD,
                PS_TKT_HIST.CUST_NO,
                PS_TKT_HIST_LIN.ITEM_NO,
                PS_TKT_HIST_LIN.TKT_NO,
                PS_TKT_HIST_LIN.EXT_PRC,
                PS_TKT_HIST_LIN.EXT_COST,
                AR_CUST.NAM,
                PS_TKT_HIST_LIN.DESCR,
                PS_TKT_HIST_LIN.BUS_DAT,
                PS_TKT_HIST.TKT_TYP,
                PS_TKT_HIST_LIN.LIN_TYP,
                PS_TKT_HIST.STR_ID
            FROM
                PS_TKT_HIST
            LEFT OUTER JOIN
                AR_CUST
            ON
                PS_TKT_HIST.CUST_NO = AR_CUST.CUST_NO
            INNER JOIN
                PS_TKT_HIST_LIN 
            ON
                PS_TKT_HIST.BUS_DAT = PS_TKT_HIST_LIN.BUS_DAT AND PS_TKT_HIST.DOC_ID = PS_TKT_HIST_LIN.DOC_ID
            WHERE
                PS_TKT_HIST_LIN.TKT_NO IN ({ticket_numbers_str}) AND
                PS_TKT_HIST.TKT_TYP <> 'A' AND
                PS_TKT_HIST.BUS_DAT = CAST(DATEADD(DAY, -2, GETDATE()) AS DATE)
        """
        cursor.execute(query2)
        results = cursor.fetchall()
        ticket_data = {}

        for item in results:
            if item['TKT_NO'] not in ticket_data:
                ticket_data[item['TKT_NO']] = {
                    'items': [
                        {
                            'exact_cost': item['EXT_COST'],
                            'description': item['DESCR'],
                            'item_code': item['ITEM_NO'],
                            'item_name': item['DESCR'],
                            'price': item['EXT_PRC'],
                            'qty': item['QTY_SOLD']
                        }
                    ], 
                    'customer_number': item['CUST_NO'],
                    'total_quantity': item['QTY_SOLD'],
                    'ticket_location': item['STR_ID'],
                    'ticket_number': item['TKT_NO'],
                    'ticket_type': item['TKT_TYP'],
                    'ticket_date': item['BUS_DAT'],
                    'customer_name': item['NAM'],
                    'post_date': item['BUS_DAT'],
                    'line_type': item['LIN_TYP'],
                }
            else: 
                item_data = {
                    'exact_cost': item['EXT_COST'],
                    'description': item['DESCR'],
                    'item_code': item['ITEM_NO'],
                    'item_name': item['DESCR'],
                    'price': item['EXT_PRC'],
                    'qty': item['QTY_SOLD']
                }
                ticket_data[item['TKT_NO']]['total_quantity'] += item['QTY_SOLD']
                ticket_data[item['TKT_NO']]['items'].append(item_data)
            
    tickets = list(ticket_data.values())
    fetched_tickets.extend(tickets)

    conn.close()
    return fetched_tickets.extend(tickets)

def create_counterpoint_sales_ticket(ticket):
    is_return = any(item['qty'] < 0 for item in ticket['items'])
    if is_return:
        if frappe.db.exists('CounterPoint Returns', {'ticket_number': ticket['ticket_number']}):
            return

        counterpoint_return = frappe.new_doc('CounterPoint Returns')
        counterpoint_return.update({
            'ticket_location': ticket['ticket_location'],
            'ticket_number': ticket['ticket_number'],
            'customer_name': ticket['customer_name'],
            'posting_date': ticket['post_date'],
            'customer': ticket['customer_number'],
            'ticket_date': ticket['ticket_date']
        })
        counterpoint_sales = frappe.new_doc('CounterPoint Sales')
        counterpoint_sales.update({
            'ticket_location': ticket['ticket_location'],
            'total_quantity': ticket['total_quantity'],
            'ticket_number': ticket['ticket_number'],
            'customer_name': ticket['customer_name'],
            'customer': ticket['customer_number'],
            'ticket_date': ticket['ticket_date'],
            'ticket_type': ticket['ticket_type'],
            'posting_date': ticket['post_date'],
            'line_type': ticket['line_type']
        })
        for item in ticket['items']:
            if item['qty'] < 0:
                counterpoint_return.append('items', {
                    'item': item['item_code'],
                    'item_name': item['item_name'],
                    'qty': item['qty'],
                    'cost': item['exact_cost'],
                    'price': item['price']
                })
            else:
                counterpoint_sales.append('items', {
                    'item': item['item_code'],
                    'item_name': item['item_name'],
                    'qty': item['qty'],
                    'cost': item['exact_cost'],
                    'price': item['price']
                })

        counterpoint_return.insert()

        if any(item['qty'] > 0 for item in ticket['items']) and not frappe.db.exists('CounterPoint Sales', {'ticket_number': ticket['ticket_number']}):
            counterpoint_sales.insert()
            create_sales_invoice_from_ticket(counterpoint_sales)

    else:
        if frappe.db.exists('CounterPoint Sales', {'ticket_number': ticket['ticket_number']}):
            counterpoint_sales = frappe.get_doc('CounterPoint Sales', {'ticket_number': ticket['ticket_number']})
            create_sales_invoice_from_ticket(counterpoint_sales)
            return

        counterpoint_sales = frappe.new_doc('CounterPoint Sales')
        counterpoint_sales.update({
            'ticket_location': ticket['ticket_location'],
            'total_quantity': ticket['total_quantity'],
            'ticket_number': ticket['ticket_number'],
            'customer_name': ticket['customer_name'],
            'customer': ticket['customer_number'],
            'ticket_date': ticket['ticket_date'],
            'ticket_type': ticket['ticket_type'],
            'posting_date': ticket['post_date'],
            'line_type': ticket['line_type']
        })

        for item in ticket['items']:
            counterpoint_sales.append('items', {
                'item': item['item_code'],
                'item_name': item['item_name'],
                'qty': item['qty'],
                'cost': item['exact_cost'],
                'price': item['price'],     
            })

        counterpoint_sales.insert()
        create_sales_invoice_from_ticket(counterpoint_sales)
            
def create_sales_invoice_from_ticket(ticket):
	fields = ['customer', 'customer_name', 'ticket_number', 'ticket_location']
	skip = False
	temp = ''
	current_ticket = frappe.get_doc('CounterPoint Sales', ticket.name)

	for item in current_ticket.items:
		if not item:
			temp += f'->Missing item data for {item}\n'
			skip = True

		if item.qty <= 0:
			temp += f'-> Item {item.item} has invalid quantity: {item.qty}\n'
			skip = True

		if not frappe.db.exists('Item', item.item):
			temp += f'-> Item {item.item} does not exist in the system.\n'
			try:
				temp += f'-> Attempting to upload Item {item.item}.\n'
				upload_item(item.item)
				item_doc = frappe.get_doc('Item', item.item)
				is_whole_num = frappe.db.get_value('UOM', {'name': item_doc.stock_uom}, ['must_be_whole_number'])

				if is_whole_num == 1 and not item.qty.is_integer():
					temp += f'-> Fractional quantity {item.qty} not allowed for item {item.item}.\n'
					skip = True

			except Exception as e:
				temp += f'-> Something went wrong when uploading {item.item}.\n'
				skip = True
				continue

		else:
			item_doc = frappe.get_doc('Item', item.item)
			is_whole_num = frappe.db.get_value('UOM', {'name': item_doc.stock_uom}, ['must_be_whole_number'])

			if is_whole_num == 1 and not item.qty.is_integer():
				temp += f'-> Fractional quantity {item.qty} not allowed for item {item.item}.\n'
				skip = True

	for key in fields:
		if not current_ticket.get(key):
			temp += f'-> Missing value for {key}.\n'
			skip = True

	if skip:
		frappe.log_error(title="create_sales_invoice_from_ticket", message=temp)
		current_ticket.ticket_error = 1
		current_ticket.save() 
	
	sales_inv_exists = frappe.db.exists('Sales Invoice', {'custom_ticket': ticket.get('ticket_number')})

	if sales_inv_exists:
		current_ticket.sales_invoice_created = 1
		current_ticket.save()
		si = frappe.get_doc('Sales Invoice', {'custom_ticket': ticket.get('ticket_number')})

	else:
		formatted_posting_date = current_ticket.posting_date.split()[0]
		ticket_customer_id = current_ticket.customer
		ticket_customer_name = current_ticket.customer_name
		cus_in_sys = frappe.db.exists('Customer', ticket_customer_id)
		sales_invoice_customer = ''
		
		if not cus_in_sys:
			new_cus = frappe.new_doc('Customer')
			new_cus.update({
				'customer_name': ticket_customer_id,
				'customer_details': ticket_customer_name,
				'customer_type': 'Individual',
				'territory': 'All Territories'
			})
			new_cus.insert()
			sales_invoice_customer = new_cus.name

		else:
			sales_invoice_customer = frappe.db.get_value('Customer', ticket_customer_id, 'name')

		warehouse = frappe.db.get_value('Store Location Mapping Table', {'store_location': current_ticket.ticket_location}, ['warehouse'])

		si = frappe.new_doc('Sales Invoice')
		si.update({
			'set_posting_time': 1,
			'posting_date': formatted_posting_date,
			'posting_time': time(23, 59),
			'customer': sales_invoice_customer,
			'update_stock': 1,
			'custom_ticket': current_ticket.ticket_number,
			'due_date': datetime.datetime.now() + datetime.timedelta(1),
			'set_warehouse': warehouse
		})
		
		for item in current_ticket.items:
			si.append('items', {
				'item_code': item.item,
				'warehouse': warehouse,
				'qty': float(item.qty),
				'uom': frappe.db.get_value('Item', item.item, 'stock_uom'),
				'rate': float(item.price),
				'price_list_rate': float(item.price),
			})

		try:
			si.insert()
			current_ticket.sales_invoice_created = 1
			current_ticket.save() 

		except Exception as e:
			frappe.log_error(title="create_sales_invoice_from_ticket", message=frappe.get_traceback())
			return

	check_and_submit_invoice(si)     
	
def check_and_submit_invoice(si):
	ticket_exists = frappe.db.exists('CounterPoint Sales', f'TK-{si.custom_ticket}')
	if ticket_exists:
		frappe.db.savepoint('sp')
		ticket_doc = frappe.get_doc('CounterPoint Sales', f'TK-{si.custom_ticket}')
		if ticket_doc.total_quantity > 0:
			s_inv= frappe.get_doc("Sales Invoice",si.name)
			if s_inv.docstatus == 0:
				try:
					s_inv.submit()
					frappe.db.commit()
				except frappe.exceptions.ValidationError as e:
					frappe.db.rollback()
					customer = frappe.get_doc('Customer', s_inv.customer)
					customer.credit_limit = []
					customer.save()
					try:
						s_inv.submit()
						frappe.db.commit()
					except Exception as e:
						frappe.db.rollback()
						frappe.log_error(title="check_and_submit_invoice", message=frappe.get_traceback())
						return
				except Exception as e:
					frappe.db.rollback()
					frappe.log_error(title="check_and_submit_invoice", message=frappe.get_traceback())
					return