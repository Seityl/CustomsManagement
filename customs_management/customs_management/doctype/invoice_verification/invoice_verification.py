#  Copyright (c) 2025, Jollys Pharmacy Ltd. and contributors
#  For license information, please see license.txt

import re

import frappe
from frappe import _
from frappe.utils.data import flt
from frappe.model.document import Document

from customs_management.api import create_attachment
	
class InvoiceVerification(Document):
	def before_save(self):
		create_attachment(self, self.reference_document, self.name, self.doctype)
	
	def on_submit(self):
		self.update_purchase_receipt()
		self.update_status('Verified')

	def before_insert(self):
		if frappe.db.exists('Invoice Verification', {'reference_document': self.reference_document}):
			frappe.throw(_(f'Invoice Verification for Purchase Receipt {self.reference_document} has already been created.'))
		self.get_items()
        
	def update_status(self, status:str):
		self.db_set('status', status)

	def consolidate_items(self, purchase_receipt, duty_exempt):
		out = []
		item_dict = frappe._dict()

		for item in purchase_receipt.items:
			item_tariff_number = frappe.db.get_value('Item', {'item_code' : item.item_code}, ['customs_tariff_number'])

			if item.item_code in item_dict:
				existing_item = item_dict.item_code
				existing_item.qty += item.qty
				existing_item.rate += item.rate
				existing_item.amount += item.amount

			else:
				new_item = {
					'item_code': item.item_code,
					'item_name': item.item_name,
					'recept_item_id': item.name,
					'description': item.description,
					'customs_tariff_number': item_tariff_number,
					'qty': item.qty,
					'uom': item.uom,
					'rate': item.rate,
					'amount': item.amount,
					'duty_exempt': duty_exempt,
					'cost_center': item.cost_center
				}
				out.append(new_item)
				item_dict.item_code = [new_item]

		return out

	def reset_fields(self):
		# self.grand_total = None
		self.total_item_qty = 0
		self.item_count = 0
		# self.total_taxes_and_charges = None
		self.currency = 'XCD'

	def reset_child_tables(self):
		self.items = []
		# self.additional_charges = None
		self.tariff_number_summary = []

	def update_purchase_receipt(self):
		frappe.db.set_value(self.reference_doctype, self.reference_document, 'custom_invoice_verification_created', '1')
        
	def update_totals(self):
		total_item_qty = 0
		item_count = len(self.items)
        
		for item in self.items:
			total_item_qty += item.qty
            
		self.total_item_qty = total_item_qty
		self.item_count = item_count

	def update_tariff_number_summary_table(self):
		try:
			tariff_numbers = {}
			for item in self.items:
				if not item.duty_exempt and item.customs_tariff_number:
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

				self.append('tariff_number_summary', {
					'customs_tariff_number': tariff_number,
					'description': data['tariff_doc'].description,
					'duty_percentage': duty_percent,
					'amount': total_amount,
					'duty_amount': flt((total_amount / 100) * duty_percent, 3),
				})

		except Exception as e:
			frappe.log_error(frappe.get_traceback(), _("Tariff Summary Error"))
			frappe.throw(_("Error updating tariff summary: {0}").format(str(e)))

	@frappe.whitelist()
	def get_items(self):
		self.reset_fields()
		self.reset_child_tables()

		purchase_receipt = frappe.get_doc('Purchase Receipt', {'name': self.reference_document})
		duty_exempt = frappe.db.get_value('Address', {'name': purchase_receipt.supplier_address}, ['duty_exempt']) or 0
		
		self.update({
			'currency': purchase_receipt.currency,
			'suppliers_name': purchase_receipt.supplier_name,
			'invoice_number': purchase_receipt.custom_invoice_number
		})

		source_table_data = self.consolidate_items(purchase_receipt, duty_exempt)
		source_table_data.sort(key=sort_by_tariff_number)

		for item in source_table_data:
			self.append('items', {
				'item': item.get('item_code'),
				'item_name': item.get('item_name'),
				'recept_item_id': item.get("recept_item_id"),
				'description': item.get('description'),
				'customs_tariff_number': item.get('customs_tariff_number'),
				'qty': item.get('qty'),
				'uom': item.get('uom'),
				'rate': item.get('rate'),
				'amount': item.get('amount'),
				'duty_exempt': duty_exempt,
				'cost_center': item.get('cost_center')
			})

		self.update_tariff_number_summary_table()
		self.update_totals()
		# self.save()
	
	@frappe.whitelist()
	def update_item_tariff_numbers(self):
		for item in self.items:
			current_tariff = frappe.db.get_value('Item', {'name': item.item}, ['customs_tariff_number'])
			
			if item.customs_tariff_number != current_tariff:
				if not frappe.db.exists('Customs Tariff Number', item.customs_tariff_number):
					html_msg = (
						'<div class="alert alert-danger">'
						f"Customs Tariff Number does not exist:<br><br>{item.customs_tariff_number}<br><br>"
						"Please add it using the dialog!"
						"</div>"
					)
					return {'status': 'error', 'message': html_msg, 'customs_tariff_number': item.customs_tariff_number}

				frappe.db.savepoint('sp')

				try:
					frappe.db.set_value('Item', item.item, 'customs_tariff_number', item.customs_tariff_number)
					frappe.db.set_value('Invoice Verification Item', item.name, 'customs_tariff_number', item.customs_tariff_number)
					frappe.db.commit()

				except Exception as e:
					frappe.db.rollback()
					frappe.log_error(frappe.get_traceback(), _("update_item_tariff_numbers"))
					frappe.throw(str(e))

		return {'status': 'success'}
	
	@frappe.whitelist()
	def create_tariff_number(self, values):
		tariff_number = frappe.new_doc('Customs Tariff Number')
		tariff_number.update({
			'tariff_number': values['tariff_number'],
			'description': values['description'],
			'custom_precision': values['custom_precision'],
			'custom_markup_percentage': values['custom_markup_percentage'],
			'custom_surcharge_percentage': values['custom_surcharge_percentage'],
			'custom_duty_percentage': values['custom_duty_percentage'],
			'custom_vat_percentage': values['custom_vat_percentage'],
			'custom_service_charge_percentage': values['custom_service_charge_percentage'],
			'custom_excise_percentage': values['custom_excise_percentage']
		})

		frappe.db.savepoint('sp')

		try:
			tariff_number.insert()
			frappe.db.commit()

		except Exception as e:
			frappe.db.rollback()
			frappe.log_error(frappe.get_traceback(), _("create_tariff_number"))
			frappe.throw(_("Error in create_tariff_number: {0}").format(str(e)))

		html_msg = (
			'<div class="alert alert-success">'
			f"Customs Tariff Number added successully:<br><br>{values['tariff_number']}<br><br>"
			"</div>"
		)
		return {'status': 'success', 'message': html_msg}

	# def send_notification(self):
	# 	recipients = frappe.db.get_list('Employee', {'department': 'Tariff - JP'})
	# 	for recipient in recipients:
			
	# 	return recipients
	
def sort_by_tariff_number(item):
	if item.get('customs_tariff_number') and bool(re.match(r'^\d+(\.\d+)?$', item.get('customs_tariff_number'))):
		return float(item.get('customs_tariff_number'))
	else:
		return float('inf')

def is_local_purchase_receipt(pr):
	supplier = frappe.db.get_value('Purchase Receipt', pr.name, 'supplier')
	supplier_address = frappe.db.get_value('Supplier', supplier, 'supplier_primary_address')
	address_country = frappe.db.get_value('Address', supplier_address, 'country')

	if address_country != 'Dominica':
		return False
		
	return True

def create_invoice_verification(doc, method):
	if not is_local_purchase_receipt(doc):
		if not doc.custom_invoice_number:
			return

		invoice_verification = frappe.new_doc('Invoice Verification')
		invoice_verification.reference_document = doc.name
		invoice_verification.insert()
		
		frappe.db.commit()
