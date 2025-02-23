# Copyright (c) 2023, Sudeep Kulkarni and contributors
# For license information, please see license.txt

from erpnext.setup.utils import get_exchange_rate
import frappe
from frappe.model.document import Document
from frappe.utils.data import flt

class CustomsManagementSettings(Document):
	@frappe.whitelist()
	def get_exchange(self):
		resp = []
		for acc in self.tariff_management_additional_charges:
			account = frappe.get_doc('Account', acc.expense_account)
			print("Account ===============", account)
			company_currency = frappe.get_doc('Company', acc.company)
			ex_rate=1
			# if acc.amount:
			accur = account.account_currency if account.account_currency else company_currency.default_currency
			ex_rate = get_exchange_rate(accur, company_currency.default_currency)
			acc.base_amount = flt(ex_rate) * flt(acc.amount)
			resp.append(accur)
			resp.append(ex_rate)
			resp.append(acc.base_amount)
				# resp.append(account.currency)

			print("LIST ===============", resp)
			return resp
	