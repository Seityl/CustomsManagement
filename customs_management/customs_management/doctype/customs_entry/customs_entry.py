# Copyright (c) 2023, Sudeep Kulkarni and contributors
# For license information, please see license.txt

import json
import re
import html
from xml.dom import minidom
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

import frappe
from frappe import _
from frappe.utils.data import flt
from frappe.utils import nowdate, nowtime
from frappe.model.document import Document

from erpnext.setup.utils import get_exchange_rate

from customs_management.api import add_tofob
from customs_management.api import create_attachment

class CustomsEntry(Document):
	def before_save(self):
		try:
			self.update_additional_charges_table()
			let_selections = list({item.reference_document for item in self.items})
			
			if let_selections:
				self.recalculate_charges(let_selections)
			
			self.update_tariff_number_summary_table()
			self.update_consolidation_table()
			self.update_tax_table()
			
			purchases_list = json.loads(self.purchases_list)
			create_attachment(self, 'Customs Entry', self.name, self.doctype, purchases_list)
		
		except json.JSONDecodeError:
			frappe.throw(_("Invalid JSON format in purchases_list. Please check the data."))

		except Exception as e:
			frappe.log_error(frappe.get_traceback(), _("Customs Entry Before Save Error"))
			frappe.throw(_("Error saving Customs Entry: {0}").format(str(e)))

	def on_submit(self):
		try:
			settings = frappe.get_doc('Customs Management Settings')
			landed_cost_voucher = frappe.new_doc('Landed Cost Voucher')

			landed_cost_voucher.update({
				'company': self.company,
				'distribute_charges_based_on': settings.distribute_charges_based_on,	 
				'customs_entry': self.name
			})

			for doc in self.consolidation:
				try:
					purchase_receipt_doc = frappe.get_doc('Purchase Receipt', {'name' : doc.reference_document})

					landed_cost_voucher.append('purchase_receipts', {
						'receipt_document_type' : doc.reference_doctype,
						'receipt_document' : doc.reference_document,
						'supplier': purchase_receipt_doc.supplier,
						'grand_total': purchase_receipt_doc.grand_total
					})

				except frappe.DoesNotExistError:
					frappe.throw(_("Purchase Receipt {0} not found").format(doc.reference_document))
				
				except Exception as e:
					frappe.log_error(frappe.get_traceback(), _("Landed Cost Voucher Creation Error"))

			for item in self.items:
				try:
					item_description = frappe.db.get_value('Item', {'name' : item.item}, ['description'])
					
					landed_cost_voucher.append('items', {
						'item_code': item.item,
						'purchase_receipt_item': item.item_id,
						'description': item_description,
						'qty': item.qty,
						'uom': item.uom,
						'rate': item.rate,
						'amount': item.amount,
						'receipt_document_type': item.reference_doctype,
						'receipt_document': item.reference_document,
						'cost_center': item.cost_center,
					})

				except Exception as e:
					frappe.log_error(frappe.get_traceback(), _("Item Processing Error"))
					frappe.throw(_("Error processing item {0}: {1}").format(item.item_code, str(e)))

			for charge in self.additional_charges:
				landed_cost_voucher.append('taxes',{
						'expense_account' : charge.expense_account,
						'description' : charge.description,
						'amount' : charge.amount
				})

			landed_cost_voucher.insert()
			
			if settings.auto_submit_created_landed_cost_voucher:
				landed_cost_voucher.submit()
				
			for item in self.consolidation:
				frappe.db.set_value(item.reference_doctype, item.reference_document, 'custom_customs_entry_created', '1')

		except Exception as e:
			frappe.log_error(frappe.get_traceback(), _("Customs Entry Submit Error"))
			frappe.throw(_("Failed to submit Customs Entry: {0}").format(str(e)))

	def set_item_factors(self):
		if not self.total_amount_for_split:
			frappe.throw(_("Total amount for split is zero. Cannot calculate item weights."))

		total = flt(self.total_amount_for_split, 9)
		cumulative_weight = 0

		for idx, item in enumerate(self.items):
			item.item_weight = flt((item.rate * item.qty) / total, 9)
			
			# For last item, adjust to ensure sum = 1
			if idx == len(self.items) - 1:
				item.item_weight = flt(1 - cumulative_weight, 6)

			else:
				cumulative_weight += item.item_weight
				item.item_weight = flt(item.item_weight, 6)

		total_weight = sum(flt(item.item_weight, 6) for item in self.items)

		if abs(total_weight - 1) > 0.0001:
			frappe.msgprint(f"Warning: Item weights sum to {total_weight:.6f}")

	def recalculate_charges(self, selections):
		try:
			if not self.conversion_rate or self.conversion_rate <= 0:
				frappe.throw(_("Conversion rate must be greater than zero"))

			self.clear_charges()

			conversion_rate = self.conversion_rate
			freight = self.get_freight()
			insurance = self.get_insurance()

			totals = {
				'total_base_amount_for_split': 0,
				'total_amount_for_split': 0,
				'total_items_qty': 0,
				'total_amount': 0,
				'total_amount_company_currency': 0
			}

			for pr in selections:
				try:
					self.process_purchase_receipt(pr, conversion_rate, freight, insurance)
					totals = self.update_overall_totals(frappe.get_doc('Purchase Receipt', pr), totals)

				except Exception as e:
					frappe.log_error(frappe.get_traceback(), _("Purchase Receipt Processing Error"))
					frappe.throw(_("Error processing {0}: {1}").format(pr, str(e)))


			self.total_amount_for_split = totals['total_amount_for_split']
			self.total_base_amount_for_split = totals['total_base_amount_for_split']
			self.total_item_qty = totals['total_items_qty']
			# self.total_amount = totals['total_amount']
			# self.total_amount_company_currency = totals['total_amount_company_currency']

			self.set_item_factors()

			# Add dummy data to dummy table to render custom table
			self.append('tariff_breakdown', {'sr_no': 1})

		except Exception as e:
			frappe.log_error(frappe.get_traceback(), _("Recalculate Charges Error"))
			frappe.throw(_("Error recalculating charges: {0}").format(str(e)))

	def clear_charges(self):
		self.total_amount_company_currency = 0
		self.total_base_amount_for_split = 0
		self.total_amount_for_split = 0
		self.total_amount = 0

		self.tariff_number_summary = []
		self.tariff_breakdown = []
		self.consolidation = []
		self.tax_info = []
		self.items = []

	@frappe.whitelist()
	def get_receipt_item_data(self, selections):
		try:
			if isinstance(selections, str):
				selections = frappe.parse_json(selections)
				
			self.recalculate_charges(selections)

		except Exception as e:
			frappe.log_error(frappe.get_traceback(), _("Purchase Receipt Processing Error"))

	def get_freight(self):
		freight_accounts = [
			'USD - Freight and Forwarding Charges - USD - JP',
			'GBP - Freight and Forwarding Charges - GBP - JP'
		]
		return next((row.amount for row in self.additional_charges if row.expense_account in freight_accounts), 0)

	def get_insurance(self):
		insurance_accounts = [
			'USD - Freight Insurance Charges - USD - JP',
			'GBP - Freight Insurance Charges - GBP - JP'
		]
		return next((row.amount for row in self.additional_charges if row.expense_account in insurance_accounts), 0)

	def get_suppliers_document_name(self):
		return frappe.db.get_value('Purchase Receipt', self.consolidation[0].reference_document, 'supplier_name') or ''

	def get_suppliers_document_invoice_nbr(self):
		return frappe.db.get_value('Purchase Receipt', self.consolidation[0].reference_document, 'custom_invoice_number') or ''

	def get_suppliers_document_city(self):
		supplier = frappe.db.get_value('Purchase Receipt', self.consolidation[0].reference_document, 'supplier')
		supplier_address = frappe.db.get_value('Supplier', supplier, 'supplier_primary_address') or frappe.db.get_value('Dynamic Link', {'link_doctype': 'Supplier', 'link_name': supplier}, 'parent')

		if supplier_address:
			city = frappe.db.get_value('Address', supplier_address, 'city')
			return city

	def get_suppliers_document_country(self):
		supplier = frappe.db.get_value('Purchase Receipt', self.consolidation[0].reference_document, 'supplier')
		supplier_address = frappe.db.get_value('Supplier', supplier, 'supplier_primary_address') or frappe.db.get_value('Dynamic Link', {'link_doctype': 'Supplier', 'link_name': supplier}, 'parent')

		if supplier_address:
			country = frappe.db.get_value('Address', supplier_address, 'country')
			return country

	def get_suppliers_document_street(self):
		supplier = frappe.db.get_value('Purchase Receipt', self.consolidation[0].reference_document, 'supplier')
		supplier_address = frappe.db.get_value('Supplier', supplier, 'supplier_primary_address') or frappe.db.get_value('Dynamic Link', {'link_doctype': 'Supplier', 'link_name': supplier}, 'parent')

		if supplier_address:
			address_line1 = frappe.db.get_value('Address', supplier_address, 'address_line1')
			return address_line1

	def get_suppliers_document_date(self):
		return str(frappe.db.get_value('Purchase Receipt', self.consolidation[0].reference_document, 'posting_date').strftime('%m/%d/%y')) or ''

	def get_total_number_of_items(self):
		return str(len({item.customs_tariff_number for item in self.items if item.customs_tariff_number}))

	def get_exporter_name(self):
		soup = BeautifulSoup(frappe.db.get_value('Purchase Receipt', self.consolidation[0].reference_document, 'shipping_address_display'), "html.parser")
		raw_text = soup.get_text()
		exporter_name_text = html.unescape(raw_text)
		return re.sub(r'\s+', ' ', exporter_name_text).strip()

	def get_ref_num(self):
		return frappe.db.get_value('Purchase Receipt', self.consolidation[0].reference_document, 'custom_invoice_number')

	def get_export_country(self):
		return frappe.db.get_value('Country', self.country_of_origin, 'code').upper()

	def get_total_cost(self):
		return str(self.get_freight() + self.get_insurance())

	def get_total_cif(self):
		return str(self.total_amount_company_currency + self.get_freight() + self.get_insurance())
		
	def get_main_tariff(self):
		return self.items[0].customs_tariff_number.replace('.', '')[:-1]

	def get_main_tariff_precision(self):
		return str(frappe.db.get_value('Customs Tariff Number', self.items[0].customs_tariff_number, 'custom_precision'))

	def get_country_code(self):
		code = frappe.db.get_value('Country', self.country_of_origin, 'code')
		if code:
			return code.upper()
			
	def get_commercial_description(self, tariff_code):
		matching_descriptions = []

		for item in self.items:
			if item.customs_tariff_number == tariff_code:
				matching_descriptions.append(item.description)
					
		return ", ".join(matching_descriptions)

	def get_suppliers(self):
		unique_suppliers = []
		for item in self.items:
			s = frappe.db.get_value('Purchase Receipt', item.reference_document, 'supplier')
			if s and s not in unique_suppliers:
				unique_suppliers.append(s)
		return str(unique_suppliers)

	def get_suppliers_link_code(self, supplier=None):
		unique_suppliers = []
		for item in self.items:
			s = frappe.db.get_value('Purchase Receipt', item.reference_document, 'supplier')
			if s and s not in unique_suppliers:
				unique_suppliers.append(s)
		try:
			if supplier:
				return str(unique_suppliers.index(supplier) + 1)
		
			return str(1)

		except ValueError:
			return str(1)
			
	@frappe.whitelist()
	def get_exchange_rate(self):
		try:
			company_currency = frappe.get_value('Company', {'name': self.company}, ['default_currency'])

			if not company_currency:
				frappe.throw(_("Default currency not set for company {0}").format(self.company))
       
			exchange_rate = get_exchange_rate(self.currency, company_currency)
			self.conversion_rate = exchange_rate
			self.update_default_additional_charges()

		except Exception as e:
			frappe.log_error(frappe.get_traceback(), _("Exchange Rate Error"))
			frappe.throw(_("Error fetching exchange rate: {0}").format(str(e)))

	@frappe.whitelist()
	def get_default_additional_charges(self):
		try:
			settings = frappe.get_doc('Customs Management Settings')
			self.additional_charges = []

			for i in settings.customs_entry_additional_charges:
				self.append('additional_charges', {
					'expense_account': i.expense_account,
					'description': i.description,
					'amount': i.amount
				})

		except Exception as e:
			frappe.log_error(frappe.get_traceback(), _("Default Charges Error"))
			frappe.throw(_("Error loading default charges: {0}").format(str(e)))

	def process_purchase_receipt(self, pr_name, conversion_rate, freight, insurance):
		try:
			purchase_receipt = frappe.get_doc('Purchase Receipt', pr_name)

		except frappe.DoesNotExistError:
			frappe.throw(_("Purchase Receipt {0} not found").format(pr_name))
		
		if purchase_receipt.supplier_address:
			duty_exempt = frappe.db.get_value('Address', {'name': purchase_receipt.supplier_address}, 'duty_exempt') or False

		else:
			duty_exempt = False

		# Parse miscellaneous charges if available
		misc_charges = {}

		if purchase_receipt.other_charges_calculation:
			try:
				soup = BeautifulSoup(purchase_receipt.other_charges_calculation, 'html.parser')
				rows = soup.find_all('tr')[1:]
				misc_index = None

				for i, th in enumerate(soup.find_all('th')):
					if th.text.strip() == 'Miscellaneous Expenses':
						misc_index = i

				for row in rows:
					cols = row.find_all('td')
					item_code = cols[0].text.strip()
					miscellaneous_expenses = cols[misc_index].text.strip() if misc_index is not None else 0
					misc_charges[item_code] = miscellaneous_expenses

			except Exception as e:
				frappe.log_error(frappe.get_traceback(), _("HTML Parsing Error"))
				frappe.throw(_("Error parsing charges for {0}").format(pr_name))

		for item in purchase_receipt.items:
			try:
				tariff_number = frappe.get_doc('Customs Tariff Number', 
					frappe.db.get_value('Item', {'item_code': item.item_code}, 'customs_tariff_number'))
				
                # LEGACY: Calculate insurance and freight for each item using the item cost and total cost of invoice.
				invoice_total = purchase_receipt.grand_total
				item_invoice_weight = round((item.amount / invoice_total), 6)
				item_freight = round((freight * item_invoice_weight), 3)
				item_insurance = round((insurance * item_invoice_weight), 3)

				# Parse miscellaneous charge for this item
				item_misc = misc_charges.get(item.item_code, 0)
				cleaned_misc = re.sub(r'[^0-9.,]+', '', str(item_misc)).replace(',', '')

				try:
					item_misc = round((float(cleaned_misc)), 3)
					
				except ValueError:
					item_misc = 0.0

				additional_charges = item_insurance + item_freight
				base_additional_charges = round((additional_charges * conversion_rate), 3)

				amount = round((item.amount + additional_charges + item_misc), 3)
				base_amount = round((amount * conversion_rate), 3)

				if duty_exempt:
					duty_percent = 0
					duty = 0
					base_duty = 0

				else:
					duty_percent = tariff_number.custom_duty_percentage
					duty = round(((amount / 100) * duty_percent), 3)
					base_duty = round((duty * conversion_rate), 3)

				surcharge_percent = tariff_number.custom_surcharge_percentage
				surcharge = round(((amount / 100) * surcharge_percent), 3)
				base_surcharge = round((surcharge * conversion_rate), 3)

				service_charge_percent = tariff_number.custom_service_charge_percentage
				service_charge = round(((amount / 100) * service_charge_percent), 3)
				base_service_charge = round((service_charge * conversion_rate), 3)

				excise_percent = tariff_number.custom_excise_percentage
				excise = round(((amount / 100) * excise_percent), 3)
				base_excise = round((excise * conversion_rate), 3)

				taxable_amount = round((amount + duty + surcharge + service_charge + excise), 3)
				base_taxable_amount = round((taxable_amount * conversion_rate), 3)
				vat_percent = tariff_number.custom_vat_percentage
				vat = round(((taxable_amount / 100) * vat_percent), 3)
				base_vat = round((vat * conversion_rate), 3)

				self.append('items', {
					'reference_doctype': 'Purchase Receipt',
					'reference_document': item.parent,
					'item': item.item_code,
					'item_name': item.item_name,
					'description': item.description,
					'item_id': item.name,
					'customs_tariff_number': tariff_number.tariff_number,
					'supplier_invoice_no': purchase_receipt.custom_invoice_number,
					'qty': item.qty,
					'stock_qty': item.stock_qty,
					'uom': item.uom,
					'rate': item.rate,
					'base_rate': item.base_rate,
					'miscellaneous': item_misc,
					'amount': amount,
					'base_amount': base_amount,
					'duty_exempt': 1 if duty_exempt else 0,
					'cost_center': item.cost_center,
					'ref_document_currency': purchase_receipt.currency,
					'ref_document_conversion_rate': purchase_receipt.conversion_rate,
					'tariff_desc': tariff_number.description,
					'additional_charges': additional_charges,
					'base_additional_charges': base_additional_charges,
					'taxable_amount': taxable_amount,
					'base_taxable_amount': base_taxable_amount,
					'duty_percent': duty_percent,
					'duty_amount': duty,
					'base_duty_amount': base_duty,
					'vat_percent': vat_percent,
					'vat_amount': vat,
					'base_vat_amount': base_vat,
					'service_charge_percent': service_charge_percent,
					'service_charge_percentage': service_charge,
					'base_service_charge_percentage': base_service_charge,
					'surcharge_percent': surcharge_percent,
					'surcharge_percentage': surcharge,
					'base_surcharge_percentage': base_surcharge,
					'excise_percent': excise_percent,
					'excise_percentage': excise,
					'base_excise_percentage': base_excise				
				})

			except frappe.DoesNotExistError:
				frappe.throw(_("Customs Tariff Number {0} not found").format(tariff_number))
				
			except Exception as e:
				frappe.log_error(frappe.get_traceback(), _("Item Processing Error"))
				frappe.throw(_("Error processing item {0}: {1}").format(item.item_code, str(e)))

	def update_overall_totals(self, pr, totals):
		try:
			if not pr:
				frappe.throw(_("Invalid Purchase Receipt document provided"))

			totals['total_amount_for_split'] += pr.net_total
			totals['total_base_amount_for_split'] += pr.base_net_total
			totals['total_items_qty'] += pr.total_qty
			# totals['total_amount'] += pr.net_total
			# totals['total_amount_company_currency'] += pr.base_net_total

			return totals

		except Exception as e:
			frappe.log_error(frappe.get_traceback(), _("Update Totals Error"))
			frappe.throw(_("Error updating totals for {0}: {1}").format(pr.name, str(e)))
		
	def update_additional_charges_table(self): 
		try:
			if not self.additional_charges:
				frappe.throw(_("Additional charges table missing from document"))

			for charge in self.additional_charges:
				if not charge.expense_account:
					frappe.throw(_("Expense account missing in additional charge row"))

			for charge in self.additional_charges:
				charge.custom_foreign_currency = self.currency
				charge.exchange_rate = self.conversion_rate
				charge.base_amount = charge.amount * self.conversion_rate

		except Exception as e:
			frappe.log_error(frappe.get_traceback(), _("Additional Charges Update Error"))
			frappe.throw(_("Error updating additional charges: {0}").format(str(e)))

	def update_tariff_number_summary_table(self):
		try:
			self.tariff_number_summary = []
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
							'total_base_amount': 0.0
						}

					tariff_numbers[tariff_number]['items'].append(item)
					tariff_numbers[tariff_number]['total_amount'] += item.amount
					tariff_numbers[tariff_number]['total_base_amount'] += item.base_amount

			for tariff_number, data in tariff_numbers.items():
				duty_percent = data['tariff_doc'].custom_duty_percentage
				total_amount = data['total_amount']
				total_base_amount = data['total_base_amount']

				self.append('tariff_number_summary', {
					'customs_tariff_number': tariff_number,
					'description': data['tariff_doc'].description,
					'duty_percentage': duty_percent,
					'amount': total_amount,
					'base_amount': total_base_amount,
					'duty_amount': flt((total_amount / 100) * duty_percent, 3),
					'base_duty_amount': flt((total_base_amount / 100) * duty_percent, 3)
				})

		except Exception as e:
			frappe.log_error(frappe.get_traceback(), _("Tariff Summary Error"))
			frappe.throw(_("Error updating tariff summary: {0}").format(str(e)))

	def update_consolidation_table(self):
		try:
			self.consolidation = []
			purchase_receipts = set()

			total = 0
			base_total = 0

			if not self.items:
				frappe.throw(_("No items found to consolidate"))

			for item in self.items:
				if not item.reference_document:
					frappe.throw(_("Item {0} has no reference document").format(item.item_code))

				purchase_receipts.add(item.reference_document)

			total = 0.0
			base_total = 0.0

			for pr in purchase_receipts:
				try:
					total += flt(frappe.db.get_value('Purchase Receipt', pr, 'grand_total'))
					base_total += flt(frappe.db.get_value('Purchase Receipt', pr, 'base_grand_total'))

				except Exception as e:
					frappe.log_error(frappe.get_traceback(), _("Consolidation Data Error"))
					frappe.throw(_("Error getting totals for {0}: {1}").format(pr, str(e)))

			consolidation_data = []

			for pr in purchase_receipts:
				try:
					pr_doc = frappe.get_doc('Purchase Receipt', pr)
					fob = flt(pr_doc.grand_total)
					percentage = fob / total if total != 0 else 0

					mass = flt(self.mass_kg * percentage, 3) if self.mass_kg else 0

					freight = flt(self.get_freight() * percentage, 3)
					insurance = flt(self.get_insurance() * percentage, 3)
					additional_cost = freight + insurance
					total_cost = fob + additional_cost

					# TODO: Add XCD (Base) fields for base amounts rather than converting
					consolidation_data.append({
						'reference_doctype': 'Purchase Receipt',
						'reference_document': pr,
						'supplier_name': pr_doc.supplier_name,
						'fob_price': fob,
						'base_fob_price': round((fob * self.conversion_rate), 2),
						'additional_cost': (additional_cost),
						'freight_cost': round((freight * self.conversion_rate), 2),
						'insurance_cost': round((insurance * self.conversion_rate), 2),
						'total_cost': total_cost,
						'mass_kg': mass
					})

				except Exception as e:
					frappe.log_error(frappe.get_traceback(), _("PR Consolidation Error"))
					frappe.throw(_("Error processing {0}: {1}").format(pr, str(e)))

			consolidation_data.sort(key=lambda x: x['fob_price'], reverse=True)
			for data in consolidation_data:
				self.append('consolidation', data)

		except Exception as e:
			frappe.log_error(frappe.get_traceback(), _("Consolidation Table Error"))
			frappe.throw(_("Error updating consolidation table: {0}").format(str(e)))

	def update_tax_table(self):
		try:
			self.tax_info = []
			invoice_groups = {}

			for item in self.items:
				if item.reference_document not in invoice_groups:
					invoice_groups[item.reference_document] = {
						'invoice': frappe.db.get_value('Purchase Receipt', item.reference_document, 'custom_invoice_number') or 'N/A',
						'duty': 0,
						'vat': 0,
						'service': 0,
						'surcharge': 0,
						'excise': 0,
						'base_duty': 0,
						'base_vat': 0,
						'base_service': 0,
						'base_surcharge': 0,
						'base_excise': 0,
					}

				invoice_groups[item.reference_document]['duty'] += item.duty_amount or 0
				invoice_groups[item.reference_document]['surcharge'] += item.surcharge_percentage or 0
				invoice_groups[item.reference_document]['service'] += item.service_charge_percentage or 0
				invoice_groups[item.reference_document]['vat'] += item.vat_amount or 0
				invoice_groups[item.reference_document]['excise'] += item.excise_percentage or 0

				invoice_groups[item.reference_document]['base_duty'] += item.base_duty_amount or 0
				invoice_groups[item.reference_document]['base_surcharge'] += item.base_surcharge_percentage or 0
				invoice_groups[item.reference_document]['base_service'] += item.base_service_charge_percentage or 0
				invoice_groups[item.reference_document]['base_vat'] += item.base_vat_amount or 0
				invoice_groups[item.reference_document]['base_excise'] += item.base_excise_percentage or 0

			for invoice, group in invoice_groups.items():
				self.append('tax_info', {
					'invoice': group['invoice'],
					'duty': group['duty'],
					'base_duty': group['base_duty'],
					'tax_description': f'{invoice} - Surcharge',
					'surcharge': group['surcharge'],
					'base_surcharge': group['base_surcharge'],
					'service': group['service'],
					'base_service': group['base_service'],
					'vat': group['vat'],
					'base_vat': group['base_vat'],
					'excise': group['excise'],
					'base_excise': group['base_excise']
				})

		except Exception as e:
			frappe.log_error(
				message=f'{e}',
				title='[Customs Management] Error in update_tax_table()',
			)
			frappe.throw(f'Something went wrong: {e}')

	def update_default_additional_charges(self):
		try:
			if not self.currency:
				frappe.throw(_("Currency not set in document"))

			self.additional_charges = []
			currency = self.currency.upper()

			charge_map = {
				'USD': {
					'freight': 'USD - Freight and Forwarding Charges - USD - JP',
					'insurance': 'USD - Freight Insurance Charges - USD - JP'
				},
				'GBP': {
					'freight': 'GBP - Freight and Forwarding Charges - GBP - JP',
					'insurance': 'GBP - Freight Insurance Charges - GBP - JP'
				}
			}

			# Get charge accounts or default to USD
			accounts = charge_map.get(currency, charge_map['USD'])

			for charge_type in ['freight', 'insurance']:
				self.append('additional_charges', {
					'expense_account': accounts[charge_type],
					'description': charge_type.title(),
					'account_currency': currency,
					'exchange_rate': self.conversion_rate,
					'amount': 0.0,
					'base_amount': 0.0
				})

		except Exception as e:
			frappe.log_error(frappe.get_traceback(), _("Default Charges Error"))
			frappe.throw(_("Error setting default charges: {0}").format(str(e)))

def prettify(elem):
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent='  ')

def build_export_release(doc):
    export_release = ET.Element('Export_release')
    
    date_exit = ET.SubElement(export_release, 'Date_of_exit')
    date_exit.text = nowdate()

    time_exit = ET.SubElement(export_release, 'Time_of_exit')
    time_exit.text = nowtime()
    
    office_code = ET.SubElement(export_release, 'Actual_office_of_exit_code')
    office_code.text = doc.office_code

    office_name = ET.SubElement(export_release, 'Actual_office_of_exit_name')
    ET.SubElement(office_name, 'null')

    exit_ref = ET.SubElement(export_release, 'Exit_reference')
    ET.SubElement(exit_ref, 'null')
    
    comments = ET.SubElement(export_release, 'Comments')
    ET.SubElement(comments, 'null')
    
    return export_release

def build_property(doc, settings):
    property_elem = ET.Element('Property')
    
    sad_flow = ET.SubElement(property_elem, 'Sad_flow')
    sad_flow.text = settings.sad_flow
    
    nbers = ET.SubElement(property_elem, 'Nbers')

    ET.SubElement(nbers, 'Number_of_loading_lists')
    
    total_items = ET.SubElement(nbers, 'Total_number_of_items')
    total_items.text = doc.get_total_number_of_items()
    
    total_packages = ET.SubElement(nbers, 'Total_number_of_packages')
    total_packages.text = str(doc.number_of_packages)
    
    place_decl = ET.SubElement(property_elem, 'Place_of_declaration')
    place_decl.text = doc.incoterm
    
    date_decl = ET.SubElement(property_elem, 'Date_of_declaration')
    date_decl.text = nowdate()
    
    selected_page = ET.SubElement(property_elem, 'Selected_page')
    selected_page.text = settings.selected_page
    
    return property_elem

def build_identification(doc, settings):
	identification = ET.Element('Identification')

	office_segment = ET.SubElement(identification, 'Office_segment')

	clearance_code = ET.SubElement(office_segment, 'Customs_clearance_office_code')
	clearance_code.text = doc.office_code

	type_group = ET.SubElement(identification, 'Type')

	decl_type = ET.SubElement(type_group, 'Type_of_declaration')
	decl_type.text = settings.declaration_type

	proc_code = ET.SubElement(type_group, 'Declaration_gen_procedure_code')
	proc_code.text = settings.declaration_type

	transit_doc = ET.SubElement(type_group, 'Type_of_transit_document')
	ET.SubElement(transit_doc, 'null')

	manifest_ref = ET.SubElement(identification, 'Manifest_reference_number')
	manifest_ref.text = doc.manifest_reference_number

	registration = ET.SubElement(identification, 'Registration')

	serial_number = ET.SubElement(registration, 'Serial_number')
	
	ET.SubElement(serial_number, 'null')

	ET.SubElement(registration, 'Number')

	reg_date = ET.SubElement(registration, 'Date')
	reg_date.text = nowdate()

	assessment = ET.SubElement(identification, 'Assessment')

	serial_number = ET.SubElement(assessment, 'Serial_number')

	ET.SubElement(serial_number, 'null')

	ET.SubElement(assessment, 'Number')

	assess_date = ET.SubElement(assessment, 'Date')
	assess_date.text = nowdate()

	receipt = ET.SubElement(identification, 'Receipt')

	serial_number = ET.SubElement(receipt, 'Serial_number')

	ET.SubElement(serial_number, 'null')

	ET.SubElement(receipt, 'Number')

	receipt_date = ET.SubElement(receipt, 'Date')
	receipt_date.text = nowdate()

	return identification

def build_traders(doc, settings):
	traders = ET.Element('Traders')

	exporter = ET.SubElement(traders, 'Exporter')

	ET.SubElement(exporter, 'Exporter_code')

	exporter_name = ET.SubElement(exporter, 'Exporter_name')
	exporter_name.text = doc.get_exporter_name()

	consignee = ET.SubElement(traders, 'Consignee')

	consignee_code = ET.SubElement(consignee, 'Consignee_code')
	consignee_code.text = settings.declarant_reference_no

	consignee_name = ET.SubElement(consignee, 'Consignee_name')
	consignee_name.text = settings.declarant_reference_address

	financial = ET.SubElement(traders, 'Financial')

	financial_code = ET.SubElement(financial, 'Financial_code')
	financial_code.text = settings.declarant_reference_no

	financial_name = ET.SubElement(financial, 'Financial_name')
	financial_name.text = settings.declarant_reference_address

	return traders

def build_declarant(doc, settings):
    declarant = ET.Element('Declarant')

    decl_code = ET.SubElement(declarant, 'Declarant_code')
    decl_code.text = settings.declarant_reference_no
    
    decl_name = ET.SubElement(declarant, 'Declarant_name')
    decl_name.text = settings.declarant_reference_address

    rep = ET.SubElement(declarant, 'Declarant_representative')
    rep.text = settings.declarant_representative

    ref = ET.SubElement(declarant, 'Reference')

    ref_num = ET.SubElement(ref, 'Number')
    ref_num.text = doc.get_ref_num()

    return declarant

def build_general_information(doc, settings):
	general_info = ET.Element('General_information')

	country = ET.SubElement(general_info, 'Country')

	first_dest = ET.SubElement(country, 'Country_first_destination')
	first_dest.text = doc.get_country_code()

	trading_country = ET.SubElement(country, 'Trading_country')
	ET.SubElement(trading_country, 'null')

	export_elem = ET.SubElement(country, 'Export')

	export_country = ET.SubElement(export_elem, 'Export_country_code')
	export_country.text = doc.get_country_code()

	ET.SubElement(export_elem, 'Export_country_region')

	destination = ET.SubElement(country, 'Destination')

	dest_country = ET.SubElement(destination, 'Destination_country_code')
	dest_country.text = settings.destination_country_code

	ET.SubElement(destination, 'Destination_country_region')

	value_details = ET.SubElement(general_info, 'Value_details')
	value_details.text = str(doc.total_amount_for_split)

	ET.SubElement(general_info, 'CAP')

	add_info = ET.SubElement(general_info, 'Additional_information')
	ET.SubElement(add_info, 'null')

	comments = ET.SubElement(general_info, 'Comments_free_text')
	ET.SubElement(comments, 'null')

	return general_info

def build_transport(doc):
	transport = ET.Element('Transport')

	means = ET.SubElement(transport, 'Means_of_transport')

	departure_info = ET.SubElement(means, 'Departure_arrival_information')

	identity = ET.SubElement(departure_info, 'Identity')
	identity.text = doc.transportation_service

	nationality = ET.SubElement(departure_info, 'Nationality')
	ET.SubElement(nationality, 'null')

	border_info = ET.SubElement(means, 'Border_information')

	border_identity = ET.SubElement(border_info, 'Identity')
	border_identity.text = doc.transportation_service

	nationality = ET.SubElement(border_identity, 'Nationality')
	ET.SubElement(nationality, 'null')

	inland_mode = ET.SubElement(means, 'Inland_mode_of_transport')
	inland_mode.text = doc.mode_of_transport

	delivery_terms = ET.SubElement(transport, 'Delivery_terms')

	dt_code = ET.SubElement(delivery_terms, 'Code')
	dt_code.text = doc.incoterm

	dt_place = ET.SubElement(delivery_terms, 'Place')
	ET.SubElement(dt_place, 'null')

	ET.SubElement(delivery_terms, 'Situation')

	border_office = ET.SubElement(transport, 'Border_office')

	bo_code = ET.SubElement(border_office, 'Code')
	bo_code.text = doc.office_code

	place_of_loading = ET.SubElement(transport, 'Place_of_loading')

	pl_code = ET.SubElement(place_of_loading, 'Code')
	ET.SubElement(pl_code, 'null')

	pl_name = ET.SubElement(place_of_loading, 'Name')
	pl_name.text = doc.port_location

	ET.SubElement(place_of_loading, 'Country')

	loc_goods = ET.SubElement(transport, 'Location_of_goods')
	loc_goods.text = doc.port_location

	return transport

def build_financial(doc, settings):
	financial = ET.Element('Financial')

	transaction = ET.SubElement(financial, 'Financial_transaction')

	code1 = ET.SubElement(transaction, 'code1')
	code1.text = doc.currency

	code2 = ET.SubElement(transaction, 'code2')
	code2.text = str(doc.conversion_rate)

	bank = ET.SubElement(financial, 'Bank')

	ET.SubElement(bank, 'Code')

	ET.SubElement(bank, 'Name')

	branch = ET.SubElement(bank, 'Branch')
	ET.SubElement(branch, 'null')

	bank_ref = ET.SubElement(bank, 'Reference')
	ET.SubElement(bank_ref, 'null')

	terms = ET.SubElement(financial, 'Terms')

	term_code = ET.SubElement(terms, 'Code')
	ET.SubElement(term_code, 'null')

	term_desc = ET.SubElement(terms, 'Description')
	ET.SubElement(term_desc, 'null')

	total_invoice = ET.SubElement(financial, 'Total_invoice')
	total_invoice.text = str(doc.total_amount_company_currency)

	deffered_payment_reference = ET.SubElement(financial, 'Deffered_payment_reference')
	ET.SubElement(deffered_payment_reference, 'null')

	mop = ET.SubElement(financial, 'Mode_of_payment')
	mop.text = settings.mode_of_payment

	amounts = ET.SubElement(financial, 'Amounts')

	ET.SubElement(amounts, 'Total_manual_taxes')

	global_taxes = ET.SubElement(amounts, 'Global_taxes')
	global_taxes.text = '0.0'

	totals_taxes = ET.SubElement(amounts, 'Totals_taxes')
	totals_taxes.text = '0.0'

	guarantee = ET.SubElement(financial, 'Guarantee')

	guarantee_name = ET.SubElement(guarantee, 'Name')
	ET.SubElement(guarantee_name, 'null')

	guarantee_amount = ET.SubElement(guarantee, 'Amount')
	guarantee_amount.text = '0.0'

	guarantee_date = ET.SubElement(guarantee, 'Date')
	guarantee_date.text = nowdate()

	excluded_country = ET.SubElement(amounts, 'Excluded_country')

	excluded_country_code = ET.SubElement(excluded_country, 'Code')
	ET.SubElement(excluded_country_code, 'null')

	excluded_country_name = ET.SubElement(excluded_country, 'Name')
	ET.SubElement(excluded_country_name, 'null')

	return financial

def build_warehouse():
    warehouse = ET.Element('Warehouse')
    ET.SubElement(warehouse, 'Identification')
    ET.SubElement(warehouse, 'Delay')
    return warehouse

def build_transit(doc):
	transit = ET.Element('Transit')

	principal = ET.SubElement(transit, 'Principal')

	princ_code = ET.SubElement(principal, 'Code')
	ET.SubElement(princ_code, 'null')

	princ_name = ET.SubElement(principal, 'Name')
	ET.SubElement(princ_name, 'null')

	princ_representative = ET.SubElement(principal, 'Representative')
	ET.SubElement(princ_representative, 'null')

	signature = ET.SubElement(transit, 'Signature')

	sig_place = ET.SubElement(signature, 'Place')
	ET.SubElement(sig_place, 'null')

	sig_date = ET.SubElement(signature, 'Date')
	sig_date.text = nowdate()

	destination = ET.SubElement(transit, 'Destination')

	dest_office = ET.SubElement(destination, 'Office')
	ET.SubElement(dest_office, 'null')

	dest_country = ET.SubElement(destination, 'Country')
	ET.SubElement(dest_country, 'null')

	seals = ET.SubElement(transit, 'Seals')
	
	ET.SubElement(seals, 'Number')

	seals_identity = ET.SubElement(seals, 'Identity')
	ET.SubElement(seals_identity, 'null')

	ET.SubElement(transit, 'Result_of_control')

	ET.SubElement(transit, 'Time_limit')

	ET.SubElement(transit, 'Officer_name')

	return transit

def build_valuation(doc, settings):
	valuation = ET.Element('Valuation')

	working_mode = ET.SubElement(valuation, 'Calculation_working_mode')
	working_mode.text = settings.calculation_working_mode

	weight_elem = ET.SubElement(valuation, 'Weight')

	ET.SubElement(weight_elem, 'Gross_weight')

	total_cost = ET.SubElement(valuation, 'Total_cost')
	total_cost.text = doc.get_total_cost()

	total_cif = ET.SubElement(valuation, 'Total_CIF')
	total_cif.text = doc.get_total_cif()

	gs_invoice = ET.SubElement(valuation, 'Gs_Invoice')

	inv_amount = ET.SubElement(gs_invoice, 'Amount_foreign_currency')
	inv_amount.text = str(doc.total_amount_for_split)

	inv_currency = ET.SubElement(gs_invoice, 'Currency_code')
	inv_currency.text = doc.currency

	inv_rate = ET.SubElement(gs_invoice, 'Currency_rate')
	inv_rate.text = str(doc.conversion_rate)

	gs_external = ET.SubElement(valuation, 'Gs_external_freight')

	ext_amount = ET.SubElement(gs_external, 'Amount_foreign_currency')
	ext_amount.text = str(doc.get_freight())

	ext_currency = ET.SubElement(gs_external, 'Currency_code')
	ext_currency.text = doc.currency

	ext_rate = ET.SubElement(gs_external, 'Currency_rate')
	ext_rate.text = str(doc.conversion_rate)

	gs_internal = ET.SubElement(valuation, 'Gs_internal_freight')

	ext_amount = ET.SubElement(gs_internal, 'Amount_foreign_currency')
	ext_amount.text = str(doc.get_freight())

	ext_currency = ET.SubElement(gs_internal, 'Currency_code')
	ext_currency.text = doc.currency

	ext_rate = ET.SubElement(gs_internal, 'Currency_rate')
	ext_rate.text = str(doc.conversion_rate)

	gs_insurance = ET.SubElement(valuation, 'Gs_insurance')

	ext_amount = ET.SubElement(gs_insurance, 'Amount_foreign_currency')
	ext_amount.text = str(doc.get_insurance())

	ext_currency = ET.SubElement(gs_insurance, 'Currency_code')
	ext_currency.text = doc.currency

	ext_rate = ET.SubElement(gs_insurance, 'Currency_rate')
	ext_rate.text = str(doc.conversion_rate)

	gs_other_cost = ET.SubElement(valuation, 'Gs_other_cost')

	ext_amount = ET.SubElement(gs_other_cost, 'Amount_foreign_currency')
	ext_amount.text = '0'

	ext_currency = ET.SubElement(gs_other_cost, 'Currency_code')
	ext_currency.text = doc.currency

	ext_rate = ET.SubElement(gs_other_cost, 'Currency_rate')
	ext_rate.text = str(doc.conversion_rate)

	gs_decuction = ET.SubElement(valuation, 'Gs_decuction')

	ext_amount = ET.SubElement(gs_decuction, 'Amount_foreign_currency')
	ext_amount.text = '0'

	ext_currency = ET.SubElement(gs_decuction, 'Currency_code')
	ext_currency.text = doc.currency

	ext_rate = ET.SubElement(gs_decuction, 'Currency_rate')
	ext_rate.text = str(doc.conversion_rate)

	total = ET.SubElement(valuation, 'Total')

	total_invoice = ET.SubElement(total, 'Total_invoice')
	total_invoice.text = str(doc.total_amount_for_split)

	total_weight = ET.SubElement(total, 'Total_weight')
	total_weight.text = str(doc.mass_kg)

	return valuation

def build_item(doc, settings, supplier_link_code, tariff_code, item_price):
	item_elem = ET.Element('Item')

	suppliers_link = ET.SubElement(item_elem, 'Suppliers_link')
	ET.SubElement(suppliers_link, 'Suppliers_link_code').text = supplier_link_code

	packages = ET.SubElement(item_elem, 'Packages')

	number_of_packages = ET.SubElement(packages, 'Number_of_packages')
	number_of_packages.text = str(doc.number_of_packages)

	marks1 = ET.SubElement(packages, 'Marks1_of_packages')
	marks1.text = settings.marks1

	marks2 = ET.SubElement(packages, 'Marks2_of_packages')
	ET.SubElement(marks2, 'null')

	kind_of_packages_code = ET.SubElement(packages, 'Kind_of_packages_code')
	kind_of_packages_code.text = doc.package_type.upper()
	
	tarification = ET.SubElement(item_elem, 'Tarification')

	tarification_data = ET.SubElement(tarification, 'Tarification_data')
	ET.SubElement(tarification_data, 'null')

	hs_code = ET.SubElement(tarification, 'HScode')
	
	commodity_code = ET.SubElement(hs_code, 'Commodity_code')
	commodity_code.text = tariff_code.replace(".", "")

	precision_1 = ET.SubElement(hs_code, 'Precision_1')
	precision_1.text = doc.get_main_tariff_precision()
	
	precision2 = ET.SubElement(hs_code, 'Precision_2')
	ET.SubElement(precision2, 'null')
	
	precision3 = ET.SubElement(hs_code, 'Precision_3')
	ET.SubElement(precision3, 'null')
	
	precision4 = ET.SubElement(hs_code, 'Precision_4')
	ET.SubElement(precision4, 'null')

	preference_code = ET.SubElement(tarification, 'Preference_code')
	ET.SubElement(preference_code, 'null')

	extended_customs_procedure = ET.SubElement(tarification, 'Extended_customs_procedure')
	extended_customs_procedure.text = settings.extended_customs_procedure

	national_customs_procedure = ET.SubElement(tarification, 'National_customs_procedure')
	national_customs_procedure.text = settings.national_customs_procedure

	quota_code = ET.SubElement(tarification, 'Quota_code')
	ET.SubElement(quota_code, 'null')

	supplementary_unit = ET.SubElement(tarification, 'Supplementary_unit')

	supplementary_unit_code = ET.SubElement(supplementary_unit, 'Supplementary_unit_code')
	supplementary_unit_code.text = settings.supplementary_unit_code

	supplementary_unit_name = ET.SubElement(supplementary_unit, 'Supplementary_unit_name')
	supplementary_unit_name.text = settings.supplementary_unit_name
	
	suppplementary_unit_quantity = ET.SubElement(supplementary_unit, 'Suppplementary_unit_quantity')
	suppplementary_unit_quantity.text = str(doc.total_item_qty)

	item_price = ET.SubElement(tarification, 'Item_price')
	item_price.text = item_price

	valuation_method_code = ET.SubElement(tarification, 'Valuation_method_code')
	ET.SubElement(valuation_method_code, 'null')

	ET.SubElement(tarification, 'Attached_doc_item')

	ai_code = ET.SubElement(tarification, 'A.I._code')
	ET.SubElement(ai_code, 'null')

	goods_description = ET.SubElement(item_elem, 'Goods_description')

	country_of_origin_code = ET.SubElement(goods_description, 'Country_of_origin_code')
	country_of_origin_code.text = doc.get_country_code()
	
	ET.SubElement(goods_description, 'Country_of_origin_region')

	commercial_description = ET.SubElement(goods_description, 'Commercial_Description')
	commercial_description.text = doc.get_commercial_description(tariff_code)

	previous_doc = ET.SubElement(item_elem, 'Previous_doc')

	summary_declaration = ET.SubElement(previous_doc, 'Summary_declaration')
	summary_declaration.text = doc.bill_of_lading

	summary_declaration_sl = ET.SubElement(previous_doc, 'Summary_declaration_sl')
	ET.SubElement(summary_declaration_sl, 'null')

	ET.SubElement(previous_doc, 'Previous_document_reference')

	previous_warehouse_code = ET.SubElement(previous_doc, 'Previous_warehouse_code')
	ET.SubElement(previous_warehouse_code, 'null')

	licence_number = ET.SubElement(item_elem, 'Licence_number')
	ET.SubElement(licence_number, 'null')

	ET.SubElement(item_elem, 'Amount_deducted_from_licence')

	ET.SubElement(item_elem, 'Quantity_deducted_from_licence')

	free_text_1 = ET.SubElement(item_elem, 'Free_text_1')
	ET.SubElement(free_text_1, 'null')

	ET.SubElement(item_elem, 'Free_text_2')

	taxation = ET.SubElement(item_elem, 'Taxation')
	ET.SubElement(taxation, 'Item_taxes_amount')
	ET.SubElement(taxation, 'Item_taxes_guaranted_amount')
	ET.SubElement(taxation, 'Item_taxes_mode_of_payment')
	ET.SubElement(taxation, 'Counter_of_normal_mode_of_payment')
	ET.SubElement(taxation, 'Displayed_item_taxes_amount')

	for _ in range(8):
		taxation_line = ET.SubElement(taxation, 'Taxation_line')
		duty_tax_code = ET.SubElement(taxation_line, 'Duty_tax_code')
		ET.SubElement(duty_tax_code, 'null')
		ET.SubElement(taxation_line, 'Duty_tax_Base')
		ET.SubElement(taxation_line, 'Duty_tax_rate')
		ET.SubElement(taxation_line, 'Duty_tax_amount')
		duty_tax_mp = ET.SubElement(taxation_line, 'Duty_tax_MP')
		ET.SubElement(duty_tax_mp, 'null')
		duty_tax_type = ET.SubElement(taxation_line, 'Duty_tax_Type_of_calculation')
		ET.SubElement(duty_tax_type, 'null')
		
	valuation_item = ET.SubElement(item_elem, 'Valuation_item')

	weight_itm = ET.SubElement(valuation_item, 'Weight_itm')

	gross_weight_itm = ET.SubElement(weight_itm, 'Gross_weight_itm')
	gross_weight_itm.text = str(doc.mass_kg)

	net_weight_itm = ET.SubElement(weight_itm, 'Net_weight_itm')
	net_weight_itm.text = str(doc.mass_kg)

	ET.SubElement(valuation_item, 'Total_CIF_itm').text = f"{doc.total_base_amount_for_split:.2f}"

	ET.SubElement(valuation_item, 'Statistical_value').text = f"{doc.total_base_amount_for_split:.2f}"

	ET.SubElement(valuation_item, 'Alpha_coeficient_of_apportionment')

	item_invoice = ET.SubElement(valuation_item, 'Item_Invoice')

	ET.SubElement(item_invoice, 'Amount_foreign_currency').text = f"{doc.total_amount_for_split:.2f}"

	ET.SubElement(item_invoice, 'Currency_code').text = doc.currency

	ET.SubElement(item_invoice, 'Currency_rate').text = f"{doc.conversion_rate:.4f}"

	cost_sections = [
		('item_external_freight', doc.get_freight()),
		('item_internal_freight', 0),
		('item_insurance', doc.get_insurance()),
		('item_other_cost', 0),
		('item_deduction', 0)
	]

	for section, value in cost_sections:
		elem = ET.SubElement(valuation_item, section)
		ET.SubElement(elem, 'Amount_foreign_currency').text = f"{value:.1f}"
		ET.SubElement(elem, 'Currency_code').text = doc.currency
		ET.SubElement(elem, 'Currency_rate').text = f"{doc.conversion_rate:.4f}"

	return item_elem

def build_suppliers_documents(doc, settings):
    suppliers_docs = ET.Element('Suppliers_documents')

    suppliers_document_itmlink = ET.SubElement(suppliers_docs, 'Suppliers_document_itmlink')
    suppliers_document_itmlink.text = ''
    
    if doc.consolidation:
        suppliers_document_code = ET.SubElement(suppliers_docs, 'Suppliers_document_code')
        suppliers_document_code.text = ''
		
        suppliers_document_name = ET.SubElement(suppliers_docs, 'Suppliers_document_name')
        suppliers_document_name.text = doc.get_suppliers_document_name()

        suppliers_document_country = ET.SubElement(suppliers_docs, 'Suppliers_document_country')
        suppliers_document_country.text = doc.get_suppliers_document_country()

        suppliers_document_city = ET.SubElement(suppliers_docs, 'Suppliers_document_city')
        suppliers_document_city.text = doc.get_suppliers_document_city()

        suppliers_document_street = ET.SubElement(suppliers_docs, 'Suppliers_document_street')
        suppliers_document_street.text = doc.get_suppliers_document_street()

        suppliers_document_telephone = ET.SubElement(suppliers_docs, 'Suppliers_document_telephone')
        suppliers_document_telephone.text = ''

        suppliers_document_fax = ET.SubElement(suppliers_docs, 'Suppliers_document_fax')
        suppliers_document_fax.text = ''

        suppliers_document_zip_code = ET.SubElement(suppliers_docs, 'Suppliers_document_zip_code')
        suppliers_document_zip_code.text = ''

        suppliers_document_invoice_nbr = ET.SubElement(suppliers_docs, 'Suppliers_document_invoice_nbr')
        suppliers_document_invoice_nbr.text = doc.get_suppliers_document_invoice_nbr()

        suppliers_document_invoice_amt = ET.SubElement(suppliers_docs, 'Suppliers_document_invoice_amt')
        suppliers_document_invoice_amt.text = ''

        suppliers_document_type_code = ET.SubElement(suppliers_docs, 'Suppliers_document_type_code')
        suppliers_document_type_code.text = settings.suppliers_document_type_code

        suppliers_document_date = ET.SubElement(suppliers_docs, 'Suppliers_document_date')
        suppliers_document_date.text = doc.get_suppliers_document_date()

        suppliers_document_c75_nbr = ET.SubElement(suppliers_docs, 'Suppliers_document_c75_nbr')
        suppliers_document_c75_nbr.text = ''

        suppliers_document_c75_date = ET.SubElement(suppliers_docs, 'Suppliers_document_c75_date')
        suppliers_document_c75_date.text = ''
		
        return suppliers_docs

@frappe.whitelist()
def generate_xml_file(name):
	"""
	Generate the XML file for a given Customs Entry by automatically deriving 
	and filling out the fields as per the legacy PHP file. The resulting XML is
	returned as a downloadable file.
	"""
	doc = frappe.get_doc('Customs Entry', name)
	settings = frappe.get_doc('Customs Management Settings')

	root = ET.Element('ASYCUDA')

	root.append(build_export_release(doc))

	ET.SubElement(root, 'Assessment_notice')
	ET.SubElement(root, 'Global_taxes')

	root.append(build_property(doc, settings))
	root.append(build_identification(doc, settings))
	root.append(build_traders(doc, settings))
	root.append(build_declarant(doc, settings))
	root.append(build_general_information(doc, settings))
	root.append(build_transport(doc))
	root.append(build_financial(doc, settings))
	root.append(build_warehouse())
	root.append(build_transit(doc))
	root.append(build_valuation(doc, settings))

	items_container = ET.Element('Items')

	for tariff_summary in doc.tariff_number_summary:
		for item in doc.items:
			processed_tariff = item.customs_tariff_number

			if processed_tariff == tariff_summary.customs_tariff_number:
				supplier_for_tariff = frappe.db.get_value('Purchase Receipt', item.reference_document, 'supplier')
				tariff_code = processed_tariff
				item_price = tariff_summary.base_amount
				break

		if supplier_for_tariff:
			supplier_link_code = doc.get_suppliers_link_code(supplier_for_tariff)
			items_container.append(build_item(doc, settings, supplier_link_code, tariff_code, item_price))
			
	root.append(items_container)
	root.append(build_suppliers_documents(doc, settings))

	xml_str = prettify(root)

	file_name = f'{name}.xml'
	frappe.local.response.filename = file_name
	frappe.local.response.filecontent = xml_str
	frappe.local.response.type = 'download'

	return xml_str