# Copyright (c) 2023, Sudeep Kulkarni and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils.data import flt, getdate, today, unique, nowdate

from erpnext.setup.utils import get_exchange_rate
from erpnext.stock.get_item_details import get_price_list_rate

from customs_management.api import create_attachment

class ShipmentClearing(Document):
    def before_save(self):
        self.update_bank_and_handler_charges()
        self.update_default_additional_charges()

        self.get_exempt_invoice()
        create_attachment(self, self.customs_entry, self.name, self.doctype)
    
    def on_submit(self):
        self.link_to_landed_cost_vouchers()
        self.generate_price_revision()

        # doc = frappe.get_doc('Customs Entry', self.customs_entry)
        # items = doc.items

        # for i in items:
        #     for pr in self.price_revision_items:
        #         if i.item == pr.item:
        #             print('iiiiiiiiiiiiiiiiiiiiii',i.description)
        #             if pr.current_price != pr.updated_price and pr.price_approved == 1:
        #                 item_price = frappe.new_doc("Item Price")
        #                 item_price.item_code = pr.item
        #                 item_price.item_name = pr.item_name
        #                 item_price.item_description = i.description
        #                 item_price.uom = pr.uom
        #                 item_price.price_list = self.sales_pricelist
        #                 item_price.price_list_rate = pr.updated_price
        #                 if self.sales_pricelist == "Standard Selling":
        #                     item_price.selling = 1
        #                 if self.sales_pricelist == "Standard Buying":
        #                     item_price.buying = 1
                        
        #                 item_price.save()
        
    def link_to_landed_cost_vouchers(self):
        landed_cost_voucners = frappe.db.get_all('Landed Cost Voucher', filters={'customs_entry': self.customs_entry}, fields=['name'])
        for landed_cost_voucner in landed_cost_voucners:
            frappe.db.set_value('Landed Cost Voucher', landed_cost_voucner, 'shipment_clearing', self.name)

    @frappe.whitelist()
    def get_markup_summary(self, item_tariff_number=None, custom_markup_percentage=None):
        if not self.customs_entry:
            return
        
        customs_entry_doc = frappe.get_doc('Customs Entry', self.customs_entry)

        self.markup_summary = []
        self.items = []

        markup_items = []

        for item in customs_entry_doc.items:
            existing_item = next((entry for entry in markup_items if entry['item_code'] == item.item), None)

            if existing_item:
                existing_item['qty'] += item.qty
                
            else:
                markup_items.append({
                    'item_code': item.item,
                    'qty': item.qty,
                    'reference_doctype' : item.reference_doctype,
                    'reference_document': item.reference_document,
                    'customs_tariff_number': item.customs_tariff_number,
                    'description': item.description,
                    'uom': item.uom
                })

        for markup_item in markup_items:
            if item_tariff_number == markup_item['customs_tariff_number']:
                markup_per = custom_markup_percentage

            else:
                markup_per = frappe.db.get_value('Customs Tariff Number', {'tariff_number': markup_item['customs_tariff_number']}, 'custom_markup_percentage')
                
            self.append('markup_summary', {
                'item_code' : markup_item['item_code'],
                'tariff_number' : markup_item['customs_tariff_number'],
                'description' : markup_item['description'],
                'markup_per' : markup_per
            })
        
        for item in customs_entry_doc.items:
            data = item.__dict__
            del data['name']
            self.append('items', data)

    def get_port_charge(self):
        for row in self.additional_charges:
            if row.description and row.description.lower() == 'port charges':
                return row.base_amount

    def get_transport_charge(self):
        for row in self.additional_charges:
            if row.description and row.description.lower() == 'rental and transportation charges':
                return row.base_amount

    def get_bank_charge(self):
        for row in self.additional_charges:
            if row.description and row.description.lower() == 'bank expense':
                return row.base_amount

    def get_handler_charge(self):
        for row in self.additional_charges:
            if row.description and row.description.lower() == 'handler expense':
                return row.base_amount
    
    def get_misc_charge(self):
        for row in self.additional_charges:
            if row.description and row.description.lower() == 'misc charges':
                return row.base_amount

    def get_item_price(self, item):
        today = nowdate()
        item_price_data = frappe.db.sql(
            """
            SELECT price_list_rate
            FROM `tabItem Price`
            WHERE item_code = '{0}' 
            AND price_list = '{1}'
            AND valid_from <= '{2}'
            AND (valid_upto IS NULL OR valid_upto >= '{3}')
            ORDER BY valid_from DESC
            LIMIT 1
            """.format(item.item, self.sales_pricelist, today, today),
            as_dict=True
        )
        print('item_price_data', item_price_data)
        if item_price_data:
            price_list_rate = item_price_data[0].get('price_list_rate')
            return price_list_rate + ((item.vat_percent / 100) * price_list_rate)

        else:
            return 0.00
            
    @frappe.whitelist()
    def generate_price_revision(self):
        try:
            settings = frappe.get_doc('Customs Management Settings')

            self.price_revision_items = []
            markup_rates = {}

            for markup_item in self.markup_summary:
                try:
                    if markup_item.item_code not in markup_rates:
                        markup_rates[markup_item.item_code] = markup_item.markup_per

                except Exception as e:
                    frappe.log_error(frappe.get_traceback(), 
                        "Error processing markup_summary for item: {0}".format(markup_item.item_code))
                    frappe.msgprint(_("Error processing markup_summary for item: {0}. Continuing...").format(item.item))
                    continue

            for item in self.items:
                inland_charges = sum(
                    item.item_weight * charge_func() 
                    for charge_func in [
                        self.get_transport_charge, 
                        self.get_handler_charge, 
                        self.get_port_charge, 
                        self.get_bank_charge, 
                        self.get_misc_charge
                    ]
                )

                landed_cost = sum([
                    item.base_service_charge_percentage,
                    item.base_surcharge_percentage,
                    item.base_excise_percentage,
                    item.base_duty_amount,
                    item.base_amount,
                    inland_charges
                ])

                base = landed_cost + item.base_vat_amount

                markup_percent = markup_rates.get(item.item, 0)
                markup_value = round((base * (markup_percent / 100)), 2)

                case_price = (base + markup_value) / item.qty
                each_price = (base + markup_value) / item.stock_qty

                current_item_price = self.get_item_price(item)
                diff_percentage = abs(((each_price - flt(current_item_price)) / flt(current_item_price)) * 100)

                if(diff_percentage < settings.threshold):
                    updated_case_price = case_price
                    updated_each_price = each_price
                    price_approved = True

                else:
                    updated_case_price = 0
                    updated_each_price = 0
                    price_approved = False
                    
                self.append('price_revision_items', {
                    'item': item.item,
                    'description': item.description,
                    'qty': item.qty,
                    'stock_qty': item.stock_qty,
                    'uom': item.uom,
                    'base': base,
                    'markup_percent': markup_percent,
                    'markup_value': markup_value,
                    'current_price': current_item_price,
                    'diff_percentage': diff_percentage,
                    'each_price': each_price,
                    'case_price': case_price,
                    'updated_case_price': updated_case_price,
                    'updated_each_price': updated_each_price,
                    'price_approved': price_approved
                })

        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Error in generate_price_revision")
            frappe.throw(_("Error generating price revision: {0}").format(str(e)))

    def get_exempt_invoice(self):
        rd=[]
        self.exempt_invoices=[]
        for i in self.items:
            if i.reference_document not in rd:
                rd.append(i.reference_document)
                if i.reference_doctype=="Purchase Receipt":

                    doc=frappe.get_doc("Purchase Receipt",i.reference_document)
                    sup=frappe.get_doc("Supplier",doc.supplier)
                    if sup.customs_duty_exempt:
                        pinv=frappe.db.sql("""select distinct(parent) as pin from `tabPurchase Invoice Item` pi where pi.purchase_receipt='{0}' and pi.docstatus=1""".format(doc.name),as_dict=1)
                        for j in pinv:
                            pdoc=frappe.get_doc("Purchase Invoice",j.get("pin"))
                            self.append('exempt_invoices',{
                                'purchase_invoice' : pdoc.name,
                                'amount' :pdoc.total,
                                'qty' : pdoc.total_qty
                            })

                if i.reference_doctype=="Purchase Invoice":
                    doc=frappe.get_doc("Purchase Invoice",i.reference_document)
                    sup=frappe.get_doc("Supplier",doc.supplier)
                    if sup.customs_duty_exempt:
                        self.append('exempt_invoices',{
                            'purchase_invoice' : doc.name,
                            'amount' :doc.total,
                            'qty' : doc.total_qty
                        })
        
    @frappe.whitelist()
    def get_exchange(self, account_name=None, amount=None):
        out = {}

        if not account_name or not amount:
            return

        account = frappe.get_doc('Account', account_name)
        company = frappe.get_doc('Company', self.company)
        account_currency = account.account_currency if account.account_currency else company.default_currency
        exchange_rate = get_exchange_rate(account_currency, company.default_currency) or 1
        base_amount = flt(exchange_rate) * flt(amount)
        out['account_currency'] = account_currency
        out['exchange_rate'] = exchange_rate
        out['base_amount'] = base_amount

        return out

    @frappe.whitelist()
    def get_default_additional_charges(self):
        try:
            settings = frappe.get_doc('Customs Management Settings')
            self.additional_charges = []

            for i in settings.shipment_clearing_additional_charges:
                self.append('additional_charges', {
                    'expense_account': i.expense_account,
                    'account_currency': i.account_currency,
                    'exchange_rate': get_exchange_rate(self.custom_entry_currency, i.account_currency),
                    'description': i.description,
                    'amount': 0.0,
                    'base_amount': 0.0,
                    'custom_foreign_currency': self.custom_entry_currency
                })

        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Error in get_default_additional_charges")
            frappe.throw(_("Error setting default additional charges: {0}").format(str(e)))

    @frappe.whitelist()
    def update_default_additional_charges(self):
        for row in self.additional_charges:
            row.exchange_rate = get_exchange_rate(self.custom_entry_currency, row.account_currency)
            row.base_amount = row.amount * row.exchange_rate
            row.custom_foreign_currency = self.custom_entry_currency

    @frappe.whitelist()
    def update_bank_and_handler_charges(self):
        # total = 0
        # total = frappe.db.get_value('Customs Entry', self.customs_entry, 'total_base_amount_for_split')
        doc = frappe.get_doc('Customs Entry', self.customs_entry)
        total = 0.0
        # Iterate over each row in the consolidation child table
        for row in doc.consolidation:
            # If the base_fob_price field is not already set, calculate it using fob_price and conversion_rate
            total += flt(row.base_fob_price)
            # for item in self.items:
            #     total += (item.base_amount or 0)
                        # + (item.base_duty_amount or 0) + (item.base_surcharge_percentage or 0) + \
                        # (item.base_service_charge_percentage or 0) + (item.base_excise_percentage or 0) + (item.base_vat_amount or 0)
                    
        self.handler_percentage_value = round(total * (self.handler_percentage / 100), 2)
        self.bank_percentage_value = round(total * (self.bank_percentage / 100), 2)
        self.total_charges_amount = self.handler_percentage_value + self.bank_percentage_value

    @frappe.whitelist()
    def initialize_additional_charges(self):
        try:
            settings_doc = frappe.get_doc('Customs Management Settings')
            accounts = settings_doc.tariff_accounts[0]

            # Initialize a dictionary with default values for each tariff charge type.
            data = {
                'Customs Duty': {
                    'amount': 0,
                    'base_amount': 0,
                    'description': 'Customs Duty',
                    'custom_foreign_currency': self.custom_entry_currency,
                    'account': accounts.duty_account,
                },
                'VAT': {
                    'amount': 0,
                    'base_amount': 0,
                    'description': 'VAT',
                    'custom_foreign_currency': self.custom_entry_currency,
                    'account': accounts.vat_account,
                },
                'Service charge': {
                    'amount': 0,
                    'base_amount': 0,
                    'description': 'Service Charge',
                    'custom_foreign_currency': self.custom_entry_currency,
                    'account': accounts.service_charge_account,
                },
                'Surcharge': {
                    'amount': 0,
                    'base_amount': 0,
                    'description': 'Surcharge',
                    'custom_foreign_currency': self.custom_entry_currency,
                    'account': accounts.surcharge_account,
                },
                'Excise': {
                    'amount': 0,
                    'base_amount': 0,
                    'description': 'Excise',
                    'custom_foreign_currency': self.custom_entry_currency,
                    'account': accounts.excise_account,
                },
                'Bank': {
                    'amount': 0,
                    'base_amount': self.bank_percentage_value,
                    'description': 'Bank Expense',
                    'custom_foreign_currency': self.custom_entry_currency,
                    'account': accounts.bank_expense_account,
                },
                'Handler': {
                    'amount': 0,
                    'base_amount': self.handler_percentage_value,
                    'description': 'Handler Expense',
                    'custom_foreign_currency': self.custom_entry_currency,
                    'account': accounts.handler_expense_account,
                }
            }

            # Mapping of invoice and company currency fields for accumulation
            accumulation_fields = {
                'Customs Duty': {'invoice': 'duty_amount', 'company': 'base_duty_amount'},
                'VAT': {'invoice': 'vat_amount', 'company': 'base_vat_amount'},
                'Service charge': {'invoice': 'service_charge_percentage', 'company': 'base_service_charge_percentage'},
                'Surcharge': {'invoice': 'surcharge_percentage', 'company': 'base_surcharge_percentage'},
                'Excise': {'invoice': 'excise_percentage', 'company': 'base_excise_percentage'},
            }

            # Loop through each item and update the dictionary with amounts.
            for item in self.items:
                for key, fields in accumulation_fields.items():
                    data[key]['amount'] += getattr(item, fields['invoice'], 0) or 0
                    data[key]['base_amount'] += getattr(item, fields['company'], 0) or 0

            # Get exchange rate using the reference currency from the first item if available.
            ref_currency = self.items[0].ref_document_currency if self.items else self.custom_entry_currency
            exchange_rate = get_exchange_rate(ref_currency, 'XCD')

            # Append rows to additional_charges only if base_amount and account are valid.
            for key, d in data.items():
                if not d.get('account'):
                    frappe.msgprint(
                        _("Skipping due to missing account ({0}) for {1}").format(
                            d.get('account'), key
                        )
                    )
                    continue

                if key in ['Bank', 'Handler']:
                    self.append('additional_charges', {
                        'expense_account': d['account'],
                        'description': d['description'],
                        'amount': round(d['base_amount'] / exchange_rate, 2),
                        'base_amount': round(d['base_amount'], 2),
                        'account_currency': 'XCD',
                        'exchange_rate': exchange_rate,
                        'custom_foreign_currency': self.custom_entry_currency,
                    })

                else:
                    self.append('additional_charges', {
                        'expense_account': d['account'],
                        'description': d['description'],
                        'amount': round(d['amount'], 2),
                        'base_amount': round(d['base_amount'], 2),
                        'account_currency': 'XCD',
                        'exchange_rate': 1,
                        'custom_foreign_currency': self.custom_entry_currency,
                    })

        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Error in get_tariff_account_items")
            frappe.throw(_("Error getting tariff account items: {0}").format(str(e)))