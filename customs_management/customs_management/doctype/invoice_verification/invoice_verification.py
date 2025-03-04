# Copyright (c) 2023, Sudeep Kulkarni and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils.data import flt
from erpnext.setup.utils import get_exchange_rate
import re
from customs_management.api import create_attachment

def sort_func_tariff(val):
    # print("val-->",val,bool(re.match(r'^\d+(\.\d+)?$', val)))
    if val and bool(re.match(r'^\d+(\.\d+)?$', val)):
        return float(val)
    else:
        return float('inf')
	
def sort_func_item(val):
    # print("val-->",val,bool(re.match(r'^\d+(\.\d+)?$', val.get("customs_tariff_number"))))
    if val.get("customs_tariff_number") and bool(re.match(r'^\d+(\.\d+)?$', val.get("customs_tariff_number"))):
        print("enters if con")
        return float(val.get("customs_tariff_number"))
    else:
        print("enters else")
        return float('inf')
	
def consolidate_by_item(data):
	dic={}
	for i in data:
		if i.get('item_code') in dic:
			dic[i.get('item_code')]['qty']+=i.get('qty')
			dic[i.get('item_code')]['rate']+=i.get('rate')
			dic[i.get('item_code')]['amount']+=i.get('amount')
		else:
			dic[i.get('item_code')]=i
	print("consolidated items tariff app items",dic)
	return list(dic.values())

class InvoiceVerification(Document):
	def before_save(self):
		total=0.0
		for item in self.items:
			total += item.amount
		self.db_set("total",total)

		tax=0.0
		for taxes in self.additional_charges:
			tax+=taxes.amount
		# self.db_get("total_taxes_and_charges",tax)
		self.total_taxes_and_charges = tax
		
		create_attachment(self,self.reference_document,self.name,self.doctype)


	
	@frappe.whitelist()
	def get_items_by_purchase_invoice(self):
		self.grand_total = None
		self.item_count = None
		# self.additional_charges = None
		self.total_item_qty = None
		self.items = None
		self.tariff_number_summary = None
		
		if self.reference_doctype == "Purchase Invoice":

			self.grand_total = None
			self.item_count = None
			# self.additional_charges = None
			self.total_item_qty = None
			self.items = None
			self.tariff_number_summary = None

			purchase_invoice = frappe.get_doc('Purchase Invoice', {"name" : self.reference_document})
			print("========================", purchase_invoice)
			self.currency=purchase_invoice.currency
			self.suppliers_name=purchase_invoice.supplier_name
			self.invoice_number=purchase_invoice.custom_invoice_number
			source_table = purchase_invoice.get('items')
			source_table_data = []

			duty_exempt = 0
			address = frappe.db.get_value('Address',{'name':purchase_invoice.supplier_address},['duty_exempt'])
			if address:
				duty_exempt = 1

			for row in source_table:
				item_det,des = frappe.db.get_value('Item', {'item_code' : row.item_code},['customs_tariff_number','description'])
				item_tariff_number = item_det
				item_description = des
				source_table_data.append({
					'item_code':row.item_code,
					'item_name' : row.item_name,
					'description' : item_description,
					'customs_tariff_number' : item_tariff_number,
					'qty' : row.qty,
					'uom': row.uom,
					'rate' : row.base_rate,
					'amount' : row.base_amount,
					'duty_exempt' : duty_exempt,
					'cost_center' : row.cost_center,
					
				})
			
			# print('data*********************',source_table_data,purchase_invoice)

			source_table_data.sort(key=sort_func_item)
			source_table_data=consolidate_by_item(source_table_data)
			for data in source_table_data:
				# child_table_row = self.append("target_child_table")
				# child_table_row.field1 = row.get("field1")
				# if data.get('customs_tariff_number'):
				ctr = self.append('items')
				ctr.item = data.get('item_code')
				ctr.item_name = data.get('item_name')
				ctr.description = data.get('description')
				ctr.customs_tariff_number = data.get('customs_tariff_number')
				ctr.qty = data.get('qty')
				ctr.uom = data.get('uom')
				ctr.rate = data.get('rate')
				ctr.amount = data.get('amount')
				ctr.duty_exempt = data.get('duty_exempt')
				ctr.cost_center = data.get('cost_center')

			cus = []
			for entries in self.items:
				cus.append(entries.customs_tariff_number)
			print("=================",cus)
			customs_tariff_number = list(set(cus))
			print("=================", customs_tariff_number)

			dc = {}
			duty_ex=0

			if self.reference_doctype=="Purchase Invoice":
				doc=frappe.get_doc("Purchase Invoice",self.reference_document)
				if doc.supplier_address:
					sa=frappe.get_doc("Address",doc.supplier_address)
					if sa.duty_exempt:
						duty_ex=1
					else:
						su=frappe.get_doc("Supplier",doc.supplier)
						if su.customs_duty_exempt:
							duty_ex=1
				else:
					su=frappe.get_doc("Supplier",doc.supplier)
					if su.customs_duty_exempt:
						duty_ex=1

			for ct in customs_tariff_number:
				amt = 0.0
				for ent in self.items:
					if ct == ent.customs_tariff_number:
						amt += ent.amount
						dc.update({
							ct : amt
						})

			if duty_exempt == 0:
				
				customs_tariff_number.sort(key=sort_func_tariff)
				for num in customs_tariff_number:
					if num:
						tns = self.append('tariff_number_summary')
						ctn = frappe.get_doc('Customs Tariff Number', num)
						tns.customs_tariff_number = num
						tns.duty_percentage = ctn.custom_duty_percentage
						tns.duty_amount = (flt(ctn.custom_duty_percentage) * flt(dc.get(num))) / 100	
						print("duty amt ==================",(ctn.custom_duty_percentage) , dc.get(num)) 
				if len(customs_tariff_number)==0:
					frappe.throw("Items dont have tariff number")
			
			item_count = 0
			for i in self.items:
				item_count += 1
			gt = frappe.get_doc('Purchase Invoice', self.reference_document)
			self.grand_total = gt.grand_total
			self.total_item_qty = gt.total_qty
			self.item_count = item_count
			
			# self.save()
			print("After Save -----------------")
			return "Method Called ======="
		
		
#=========================================================================================================================================		
	
		elif self.reference_doctype == "Purchase Receipt":

			self.grand_total = None
			self.item_count = None
			# self.additional_charges = None
			self.total_item_qty = None
			self.items = None
			self.tariff_number_summary = None

			purchase_invoice = frappe.get_doc('Purchase Receipt', {"name" : self.reference_document})
			print("========================", purchase_invoice)
			self.currency=purchase_invoice.currency
			self.suppliers_name=purchase_invoice.supplier_name
			self.invoice_number=purchase_invoice.custom_invoice_number
			print("self.currency",self.currency)
			source_table = purchase_invoice.get('items')
			source_table_data = []

			print('purchase invoice items______________________',source_table)
			
			duty_exempt = 0
			address = frappe.db.get_value('Address',{'name':purchase_invoice.supplier_address},['duty_exempt'])
			if address:
				duty_exempt = 1

			for row in source_table:
				print("ppppppppppppppppppppppp",row.name)
				item_det,des = frappe.db.get_value('Item', {'item_code' : row.item_code},['customs_tariff_number','description'])
			
				item_tariff_number = item_det
				item_description = des
				# if address.duty_exempt == 1:
				source_table_data.append({
					'item_code':row.item_code,
					'item_name' : row.item_name,
					'recept_item_id':row.name,
					'description' : item_description,
					'customs_tariff_number' : item_tariff_number,
					'qty' : row.qty,
					'uom' : row.uom,
					'rate' : row.rate,
					'amount' : row.amount,
					'duty_exempt': duty_exempt,
					'cost_center' : row.cost_center
				})
			source_table_data=consolidate_by_item(source_table_data)
			print('purchase receipt data***************************',source_table_data)

			source_table_data.sort(key=sort_func_item)
			for data in source_table_data:
				# if data.get('customs_tariff_number'):
				# child_table_row = self.append("target_child_table")
				# child_table_row.field1 = row.get("field1")
				ctr = self.append('items')
				print("----------------------------))))))))))))))))",data.get("name"))
				ctr.item = data.get('item_code')
				ctr.item_name = data.get('item_name')
				ctr.recept_item_id = data.get("recept_item_id")
				ctr.description = data.get('description')
				ctr.customs_tariff_number = data.get('customs_tariff_number')
				ctr.qty = data.get('qty')
				ctr.uom = data.get('uom')
				ctr.rate = data.get('rate')
				ctr.amount = data.get('amount')
				ctr.duty_exempt = data.get('duty_exempt')
				ctr.cost_center = data.get('cost_center')

			cus = []
			for entries in self.items:
				cus.append(entries.customs_tariff_number)
			print("=================",cus)
			customs_tariff_number = list(set(cus))
			print("=================", customs_tariff_number)

			dc = {}
			duty_ex=0
			if self.reference_doctype=="Purchase Receipt":
				doc=frappe.get_doc("Purchase Receipt",self.reference_document)
				if doc.supplier_address:
					sa=frappe.get_doc("Address",doc.supplier_address)
					if sa.duty_exempt:
						duty_ex=1
					else:
						su=frappe.get_doc("Supplier",doc.supplier)
						if su.customs_duty_exempt:
							duty_ex=1
				else:
					su=frappe.get_doc("Supplier",doc.supplier)
					if su.customs_duty_exempt:
						duty_ex=1


			for ct in customs_tariff_number:
				amt = 0.0
				for ent in self.items:
					if ct == ent.customs_tariff_number:
						amt += ent.amount
						dc.update({
							ct : amt
						})

			company_currency = frappe.get_doc('Company', self.company)
			curr_ex_rate=1
			curr_ex_rate=get_exchange_rate(self.currency,company_currency.default_currency)
			customs_tariff_number.sort(key=sort_func_tariff)
			print("curr enx",curr_ex_rate)

			if duty_exempt == 0:
				for num in customs_tariff_number:
					if num:
						tns = self.append('tariff_number_summary')
						ctn = frappe.get_doc('Customs Tariff Number', num)
						tns.customs_tariff_number = num
						tns.duty_percentage = ctn.custom_duty_percentage
						tns.duty_amount = (flt(ctn.custom_duty_percentage)* flt(dc.get(num))) / 100
						tns.base_duty_amount = round(tns.duty_amount/curr_ex_rate,2)
						tns.duty_calculated_on=dc.get(num)	
						print("duty amt ==================",(ctn.custom_duty_percentage) , dc.get(num))
				if len(customs_tariff_number)==0:
					frappe.throw("No Item Have Tarrif Number")
			
			item_count = 0
			for i in self.items:
				item_count += 1
			gt = frappe.get_doc('Purchase Receipt', self.reference_document)
			self.grand_total = gt.grand_total
			self.total_item_qty = gt.total_qty
			self.item_count = item_count
			
			# self.save()
			print("After Save -----------------")
			return "Method Called ======="
		
		else:
			frappe.throw("Please Enter Reference Document")

	def on_submit(self):
		# self.items = None
		if len(self.additional_charges)>0:
			
			landed_cost_voucher = frappe.new_doc('Landed Cost Voucher')
			landed_cost_voucher.company  = self.company
			landed_cost_voucher.distribute_charges_based_on = self.distribute_charges_based_on
			
			print("ON SUBMIT ============================", landed_cost_voucher, landed_cost_voucher.company)

			if self.reference_doctype == 'Purchase Invoice':
				supp = frappe.get_doc('Purchase Invoice', {'name' : self.reference_document})
				print("----------------------",supp, supp.supplier)
			else:
				supp = frappe.get_doc('Purchase Receipt', {'name' : self.reference_document})
				print("----------------------",supp, supp.supplier)
			
			source_table = self.get('items')
			for row in source_table:
				item_det= frappe.db.get_value('Item', {'name' : row.item},["customs_tariff_number"])
				desc =  frappe.db.get_value('Item', {'name' : row.item},["description"])
				# child_id=frappe.get_doc()
				print('desc_______________________________0000000000',row.recept_item_id)
				item_tariff_number = item_det
				item_description = desc

				landed_cost_voucher.append('items',{
					'item_code' : row.item,
					'purchase_receipt_item':row.recept_item_id,
					'description' : item_description,
					'qty' : row.qty,
					'uom' : row.uom,
					'rate' : row.rate,
					'amount' : row.amount,
					'receipt_document' : self.reference_document,
					'receipt_document_type' : self.reference_doctype,
					'cost_center' : row.cost_center,
					
			 	})
				# print("---------eeeeeeeeeeeeeeeeee",landed_cost_voucher.items)

			landed_cost_voucher.append('purchase_receipts',{
					'receipt_document_type' : self.reference_doctype,
					'receipt_document' : self.reference_document,
					'supplier' : supp.supplier,
					'grand_total' : self.grand_total
				})

			print("Afetr Purchase receipt")

			print("After Items")
			# landed_cost_voucher.invoice_verification=self.name
			for row in self.additional_charges:
				landed_cost_voucher.append('taxes',{
						'expense_account' : row.expense_account,
						'description' : row.description,
						'amount' : row.amount
				})
			
			landed_cost_voucher.insert()
			print("After Taxes")
			
			landed_cost_voucher.save()
			print("---------eeeeeeeeeeeeeeeeee",landed_cost_voucher.items)
			cms=frappe.get_doc("Customs Management Settings")
			if cms.auto_submit_created_landed_cost_voucher:
				landed_cost_voucher.submit()

		#add check (tariff application created)box tick in purchase receipt/invoice on submit
		frappe.db.set_value(self.reference_doctype, self.reference_document, 'custom_invoice_verification_created', '1')

			
			
	@frappe.whitelist()
	def get_exchange(self,exca,amt):
		resp = []
		# for acc in self.additional_charges:
		account = frappe.get_doc('Account', exca)
		print("Account ===============", account)
		company_currency = frappe.get_doc('Company', self.company)
		# freight to be usd from supplier req by cust
		ex_rate=1
		# if acc.amount:
		accur = account.account_currency if account.account_currency else company_currency.default_currency
		# ex_rate = get_exchange_rate(accur, company_currency.default_currency)
		# freight to be usd from supplier req by cust
		ex_rate = get_exchange_rate("USD", company_currency.default_currency)
		base_amount = flt(ex_rate) * flt(amt)
		resp.append(accur)
		resp.append(ex_rate)
		resp.append(base_amount)
		# print('acc.base_amount---------------------------------',acc.base_amount,ex_rate,accur)
			# resp.append(account.currency)

		print("LIST ===============", resp)
		return resp
	
	@frappe.whitelist()
	def get_default_additional_charges(self):
		doc=frappe.get_doc("Customs Management Settings")
		if len(doc.tariff_management_additional_charges)>0:
			self.additional_charges=[]
			

		for j in doc.tariff_management_additional_charges:
			company_currency = frappe.get_doc('Company', self.company)
			account = frappe.get_doc('Account', j.expense_account)
			ex_rate=1
			accur = account.account_currency if account.account_currency else company_currency.default_currency
			# ex_rate = get_exchange_rate(accur, company_currency.default_currency)
			# all freight charges to be in usd
			ex_rate = get_exchange_rate("USD",company_currency.default_currency)
			self.append("additional_charges",{
				"expense_account":j.expense_account,
				"description":j.description,
				"amount":j.amount,
				"base_amount":flt(ex_rate) * flt(j.amount),
				# "account_currency":accur,
				# all freight charges to be in usd
				"account_currency":"USD",
				"exchange_rate":ex_rate
			})
		

	@frappe.whitelist()
	def get_tarif_application(self):
		lis=[]
		
		if self.reference_doctype=="Purchase Receipt":
			doc=frappe.db.get_all("Purchase Receipt",{"docstatus":1,"company":self.company},["name"],order_by="creation desc")
			print("doc data",doc)
			for j in doc:
				lis.append(j.get("name"))
			print('doc&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&',doc)

		if self.reference_doctype=="Purchase Invoice":
			doc=frappe.db.get_all("Purchase Invoice",{"docstatus":1,"company":self.company,"update_stock":1},["name"],order_by="creation desc")
			for j in doc:
				lis.append(j.get("name"))
		print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&",lis)
		return lis

	@frappe.whitelist()
	def update_tariff(self):
		for i in self.items:
			if i.customs_tariff_number == frappe.db.get_value("Item",{"name":i.item},['customs_tariff_number']):
				print(f"{i.item} {i.customs_tariff_number} existing is the same")
			else:
				print(f"{i.item} {i.customs_tariff_number} changed needs to be changed")
				if frappe.db.exists("Customs Tariff Number",i.customs_tariff_number):
					print("do the changes in item")
					frappe.db.set_value('Item', i.item, 'customs_tariff_number', i.customs_tariff_number)
				else:
					frappe.throw(f"The tariff no : {i.customs_tariff_number} does not exists in the system Please add it first")
			
		return True




