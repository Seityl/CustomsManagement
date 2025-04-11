from __future__ import unicode_literals

import re
import json
import requests
from requests_oauthlib import OAuth1Session
from datetime import datetime, timedelta, timezone

import frappe
from frappe import _
from frappe.utils.data import flt

from erpnext.setup.utils import get_exchange_rate

class WooCommerceError(frappe.ValidationError): 
	pass

def make_woocommerce_log(title, status, method, message=None, exception=False, name=None, request_data={}):
	if not name:
		name = frappe.db.get_value('WooCommerce Log', {'status': 'Queued'})
		
		if name:
			""" if name not provided by log calling method then fetch existing queued state log"""
			log = frappe.get_doc("WooCommerce Log", name)
		
		else:
			""" if queued job is not found create a new one."""
			log = frappe.get_doc({"doctype":"WooCommerce Log"}).insert(ignore_permissions=True)
		
		if exception:
			frappe.db.rollback()
			log = frappe.get_doc({"doctype":"WooCommerce Log"}).insert(ignore_permissions=True)
			
		log.message = message if message else frappe.get_traceback()
		log.title = title[0:140]
		log.method = method
		log.status = status
		log.request_data= json.dumps(request_data)
		
		log.save(ignore_permissions=True)
		frappe.db.commit()

def clear_woocommerce_logs():
	woocommerce_logs = frappe.get_all('WooCommerce Log', fields=['name'])

	if woocommerce_logs:
		for woocommerce_log in woocommerce_logs:
			frappe.delete_doc('WooCommerce Log', woocommerce_log['name'], ignore_permissions=True)

		frappe.msgprint("Cleared Logs")
	else:
		frappe.msgprint("No Logs Found")

def get_woocommerce_settings():
    settings = frappe.get_single('WooCommerce Sync')
    if settings.woocommerce_url:
        settings.api_secret = settings.get_password(fieldname='api_secret')
        return settings
    else:
        frappe.throw(_('woocommerce store URL is not configured on WooCommerce Sync'), WooCommerceError)

def get_request(path, data=None):
    woocommerce_settings = get_woocommerce_settings()

    woocommerce_url = woocommerce_settings.woocommerce_url
    api_key = woocommerce_settings.api_key
    api_secret = woocommerce_settings.api_secret
    woocommerce = OAuth1Session(client_key=api_key, client_secret=api_secret) 

    api_endpoint = f'{woocommerce_url}{path}'
    r = woocommerce.get(api_endpoint)
    
    if r.status_code != requests.codes.ok:
        make_woocommerce_log(title=f'WooCommerce get error {r.status_code}', 
            status='Error', 
            method='get_request', 
            message=f'{r.url}:{r.json()}',
            request_data=data, 
            exception=True
        )
        return r.json()
    else: 
        make_woocommerce_log(title='SUCCESS: GET', status='Success', method='get_request', message=str(r.json()), request_data=data, exception=True)
        return r.json()

def get_item_weight(id):
    return flt(get_request(f'wp-json/wc/v3/products/{id}')['weight'])

def get_order_tracking_number(id):
    order = get_request(f'wp-json/wc/v3/orders/{str(id)}/notes')
    for note in order:
        content = note.get('note', '')
        match = re.search(r'Tracking Number is:\s*(\d+)', content)
        if match:
            return match.group(1)

def get_orders():
    """Returns list of orders completed today"""
    today = datetime.now(timezone.utc).date()
    after = datetime.combine(today, datetime.min.time()).isoformat()
    before = datetime.combine(today + timedelta(days=1), datetime.min.time()).isoformat()
    orders = get_request( f'wp-json/wc/v3/orders?status=completed&after={after}&before={before}')
    return [order['id'] for order in orders]

def get_order_info(id):
    out = frappe._dict()

    out['total_item_qty'] = 0
    out['order_number'] = id
    out['item_count'] = 0

    order = get_request(f'wp-json/wc/v3/orders/{str(id)}')

    out['currency'] = order['currency']
    
    out['items'] = []
    for item in order['line_items']:
        item_data = frappe._dict({
            'item_code': item['sku'],
            'amount': flt(item['subtotal']) + flt(item['subtotal_tax'])
        })
        out['items'].append(item_data)
        out['item_count'] += 1
        out['total_item_qty'] += item['quantity']

    return out

def get_orders_entry_info(order_ids):
    out = frappe._dict()
    for id in order_ids:
        out[id]['total_item_qty'] = 0
        out[id]['order_number'] = id
        out[id]['item_count'] = 0

        order = get_request(f'wp-json/wc/v3/orders/{str(id)}')

        out[id]['currency'] = order['currency']
        
        shipping_country = frappe.db.get_value('Country', {'code': order['shipping']['country']}).upper() or None
        exchange_rate = get_exchange_rate(order['currency'], 'XCD')

        fields = [
            order['shipping']['first_name'],
            order['shipping']['last_name'],
            order['shipping']['company'],
            order['shipping']['address_1'],
            order['shipping']['address_2'],
            order['shipping']['city'],
            order['shipping']['state'],
            order['shipping']['postcode'],
            shipping_country
        ]
        out[id]['Consignee_name'] = ' '.join([v.upper() for v in fields if v])

        out[id]['Year'] =  datetime.strptime(order['date_completed'], '%Y-%m-%dT%H:%M:%S').year
        out[id]['Number'] = id

        out[id]['Country_first_destination'] = order['shipping']['country']

        out[id]['Destination_country_code'] = order['shipping']['country']
        out[id]['Destination_country_name'] = shipping_country

        out[id]['Total_cost'] = order['total']
        out[id]['Total_CIF'] = round((flt(order['total']) * exchange_rate), 2)

        out[id]['Gs_Invoice_Amount_national_currency'] = 0
        out[id]['Gs_Invoice_Amount_foreign_currency'] = 0

        out[id]['Gs_internal_freight_Amount_national_currency'] = 0
        out[id]['Gs_internal_freight_Amount_foreign_currency'] = 0

        for shipping in order['shipping_lines']:
            out[id]['Gs_internal_freight_Amount_national_currency'] += round((flt(shipping['total']) * exchange_rate), 2)
            out[id]['Gs_internal_freight_Amount_foreign_currency'] += flt(shipping['total'])

        out[id]['Total_invoice'] = 0
        out[id]['Total_weight'] = 0

        out[id]['items'] = []
        for item in order['line_items']:
            print(item)
            item_data = frappe._dict({
                'description': item['name'],
                'item_code': item['sku'],
                'qty': item['quantity'],
                'amount': flt(item['subtotal']) + flt(item['subtotal_tax'])
            })
            out[id]['items'].append(item_data)
            out[id]['Gs_Invoice_Amount_national_currency'] += round((flt(item['total']) + flt(item['total_tax'])) * exchange_rate, 2)
            out[id]['Gs_Invoice_Amount_foreign_currency'] += round((flt(item['total']) + flt(item['total_tax'])), 2)
            out[id]['Total_invoice'] += round((flt(item['total']) + flt(item['total_tax'])), 2)
            out[id]['Total_weight'] += get_item_weight(item['product_id'])

            out[id]['item_count'] += 1
            out[id]['total_item_qty'] += item['quantity']

        out[id]['Marks1_of_packages'] =  f"{order['shipping']['first_name']} {order['shipping']['last_name']} {get_order_tracking_number(id)}"

        out[id]['Commercial_Description'] = ' '.join(
            [item['name'] for item in order['line_items'][:3] if item.get('name')]
        ).upper()

        out[id]['Gross_weight_itm'] =  out[id]['Total_weight']
        out[id]['Net_weight_itm'] =  out[id]['Total_weight']

        out[id]['Total_cost_itm'] = order['total']
        out[id]['Total_CIF_itm'] = round((flt(order['total']) * exchange_rate), 2)

        out[id]['Statistical_value'] = round((flt(order['total']) * exchange_rate), 2)

        out[id]['Item_Invoice_Amount_national_currency'] = round((out[id]['Total_invoice'] * exchange_rate), 2)
        out[id]['Item_Invoice_Amount_foreign_currency'] = out[id]['Total_invoice']

        out[id]['item_internal_freight_Amount_national_currency'] = round((flt(order['total']) / exchange_rate), 2)
        out[id]['item_internal_freight_Amount_foreign_currency'] = order['total']

    return out

def is_local_order(id):
    order = get_request(f'wp-json/wc/v3/orders/{str(id)}')
    if not order or 'shipping' not in order or not order['shipping']['country']:
        return False
    shipping_country = order['shipping']['country'].strip().upper()
    return shipping_country == 'DM' or shipping_country == 'DOMINICA'

def sync_orders():
    orders = get_orders()
    if not orders:
        return

    for id in orders:
        if is_local_order(id):
            continue

        try:
            create_order_verification(id)

        except frappe.exceptions.DoesNotExistError:
            frappe.log_error(title="sync_orders", message=frappe.get_traceback())
            continue

        except Exception as e:
            frappe.log_error(title="sync_orders", message=frappe.get_traceback())
            continue

def create_order_verification(id):
    order = get_order_info(id)
    order_verification = frappe.new_doc('Order Verification')
    order_verification.update({
        'currency': order.currency,
        'item_count': order.item_count,
        'order_number': order.order_number,
        'total_item_qty': order.total_item_qty
    })
    for item in order['items']:
        doc = frappe.get_doc('Item', item.item_code)
        order_verification.append('items', {
            'amount': item.amount,
            'item': doc.item_code,
            'description': doc.description,
            'customs_tariff_number': doc.customs_tariff_number
        })

    tariff_numbers = {}

    for item in order_verification.items:
        print('itemamount: ',item.amount)
        if item.customs_tariff_number:
            tariff_number = item.customs_tariff_number

            try:
                tariff_doc = frappe.get_doc('Customs Tariff Number', tariff_number)

            except frappe.DoesNotExistError:
                frappe.throw(_("Customs Tariff Number {0} not found").format(tariff_number))

            if tariff_number not in tariff_numbers:
                tariff_numbers[tariff_number] = {
                    'tariff_doc': tariff_doc,
                    'items': [],
                    'total_amount': 0.0,
                }

            tariff_numbers[tariff_number]['items'].append(item)
            tariff_numbers[tariff_number]['total_amount'] += item.amount

    for tariff_number, data in tariff_numbers.items():
        duty_percent = data['tariff_doc'].custom_duty_percentage
        total_amount = data['total_amount']

        order_verification.append('tariff_number_summary', {
            'customs_tariff_number': tariff_number,
            'description': data['tariff_doc'].description,
            'duty_percentage': duty_percent,
            'amount': total_amount,
            'duty_amount': flt((total_amount / 100) * duty_percent, 3),
        })

    order_verification.insert()
    frappe.db.commit()