import datetime
import frappe
import json
import re
import os
from frappe.exceptions import TimestampMismatchError
from bs4 import BeautifulSoup
from erpnext.setup.utils import get_exchange_rate
from erpnext.stock.doctype.stock_reconciliation.stock_reconciliation import get_items
import requests

@frappe.whitelist()
def update_bin_stock(item_data):
  item_data = item_data
  item_not_exists = []
  warehouse_not_exists = []

  try:
    stock_entry = frappe.new_doc('Stock Entry')
    stock_entry.stock_entry_type = 'Material Transfer'
    
    for item in item_data:
      item = item
      item_exists = frappe.db.exists('Item', item['item_code'])
        
      if item_exists:
        for bin_location in item['bins']:
          warehouse = bin_location + ' - JP'
          warehouse_exists = frappe.db.exists('Warehouse', warehouse)
  
          if warehouse_exists: 
            item_qty = get_item_stock(item['item_code'], warehouse)

            if item_qty >= 25:
              stock_entry.append('items', {
                'item_code': item['item_code'],
                  's_warehouse': 'Virtual L4 - JP',
                  't_warehouse': warehouse,
                  'qty': 25
                })
          else:
              warehouse_not_exists.append(bin_location)
              continue
      else:
        item_not_exists.append(item["item_code"])
        continue
    
    stock_entry.insert()
    if len(item_not_exists) == 0 and len(warehouse_not_exists) == 0:
      return f'Stock Entry Was Created Successfully'
    elif len(item_not_exists) == 0 and len(warehouse_not_exists) != 0:
      return f'Stock Entry Was Created Successfully. but these warehouses do not exist on the system: {warehouse_not_exists}'
    elif len(item_not_exists) != 0 and len(warehouse_not_exists) == 0:
      return f'Stock Entry Was Created Successfully. but these items do not exist on the system: {item_not_exists}'
    else:
      return f'Stock Entry Was Created Successfully. but these items do not exist on the system: {item_not_exists}\n and these warehouses do not exist on the system: {warehouse_not_exists}'
        
  except Exception as e:
    return e


def get_item_stock(item_code, warehouse):
  # Raw SQL query to fetch stock from the Bin table
  stock = frappe.db.sql("""
    SELECT actual_qty
    FROM `tabBin`
    WHERE item_code = %s AND warehouse = %s
  """, (item_code, warehouse), as_dict=True)

  # Extract the actual_qty from the result
  if stock:
    return stock[0].get("actual_qty")
  else:
    return 0
  
@frappe.whitelist()
def send_outstanding_material_request_emails():
    message = ''

    from_date = frappe.utils.getdate('2024-01-01')
    to_date = frappe.utils.add_to_date(None, days=-3, as_string=False, as_datetime=True)

    outstanding_material_requests = frappe.get_list("Material Request", filters=[[
        'status', 'in', ['Pending','In Transit','Partially Ordered', 'Draft']],[
        "creation", "between", [from_date, to_date]]], fields = ["name", "status", "owner", "creation"]
    )
        
    owners = []
    associated_material_requests = {}

    for material_request in outstanding_material_requests:
        for key, value in material_request.items():
            if key == "owner" and value not in owners:
                owners.append(value)
            if key == "creation":
                    material_request[key] = str(value)

        for owner in owners:
            values = {}
            
            for key, value in material_request.items():
                if key == "name":
                    values["Name"] = value
                    
                if key == "status":
                    values["Status"] = value
                    
                if key == "creation":
                    values["Date Created"] = value
                    
            associated_material_requests.setdefault(owner, []).append(values)

    message = message + "The following employees have material requests that have been outstanding for 3 or more days: \n\n"

    n = 1

    for person, values in associated_material_requests.items():
        message = message + str(n) + ". " + person + "\n"
        n = n + 1
        
    message = message + "\n"+ "* " * 25 + "\n\n"

    for person, values in associated_material_requests.items():
            message = message + "Outstanding material requests from - " + person + "\n\n"
            for material_request in values:
                message = message + "- " * 25 + "\n"
                for key, value in material_request.items():
                    message = message + key + ": " + value + "\n"
            message = message + "\n"+ "* " * 25 + "\n\n"
                
    # recipients = ['inventory@jollys.local', 'supervisor@jollys.local', 'jeriel@jollys.local', 'jprevost@jollysonline.com', 'ecyrille@jollysonline.com', 'cdgrant@jollysonline.com']

    frappe.sendmail(
        recipients = ['jeriel@jollys.local', 'jprevost@jollysonline.com', 'ecyrille@jollysonline.com', 'cdgrant@jollysonline.com'],
        subject = 'Outstanding Material Requests',
        message = message,
        header = 'Outstanding Material Requests'
    )

@frappe.whitelist()
def my_function(name='SC014',customs_entry='CE-TSCW16719757-#00001',tariff_count=False):
    print("name",name,customs_entry)
    receipts_list=[]
    tariff_list=[]
    counter=0
    receipts=frappe.db.get_all("Consolidation",{"parent":customs_entry},["reference_document","reference_doctype"],order_by='fob_price2 desc')
    # return receipts
    for receipt in receipts:
        purchase_det=frappe.get_doc(receipt.get("reference_doctype"),receipt.get("reference_document"))
        supplier=purchase_det.supplier
        supplier_name=purchase_det.supplier_name
        address_name=frappe.db.get_value("Dynamic Link",{"link_title":supplier_name},['parent'])
        address=frappe.db.get_value("Address",{"name":address_name},["address_line1","city","country"])
        frn_curr_sym=frappe.db.get_value("Currency",{"name":purchase_det.currency},["symbol"])
        
        total_cmp=0
        total_frn=0
        
        # country=frappe.db.get_value("Country",{"name":address[2]},["code"])
        sup_country=""
        if address:
            sup_country=address[2]
            print("supplier",receipt.get("reference_document"),supplier,supplier_name,address_name,address[2])
        else:
            print("supplier",receipt.get("reference_document"),supplier,supplier_name,address_name,address)
        items=frappe.db.get_all("Customs Entry Tariff Application Item",{"parent":name,"reference_document":receipt.get("reference_document"),"reference_doctype":receipt.get("reference_doctype")},["*"])
 
        misc_charges_recp=frappe.db.get_all("Purchase Taxes and Charges",{"parent":purchase_det.name},['tax_amount'])
        total_misc_charges=0
        total_qty=0
        charge_factor=0
        for i in misc_charges_recp:
            total_misc_charges+=float(i.get('tax_amount')) 
        for i in items:
            total_qty+=float(i.qty)
        if total_qty>0:
            charge_factor=total_misc_charges/total_qty
        print(f'===,misc_charges_recp {misc_charges_recp},total_misc_charges {total_misc_charges},total_qty {total_qty},charge_factor {charge_factor}')

        # print("items",items)
        tariff_data={}
        for entries in items:
            entries.update({"misc_charge":round(charge_factor,4)})
            total_cmp+=entries.get('amount')
            total_frn+=entries.get('base_amount')
            # print("entries",entries)
            if entries.customs_tariff_number:
                    # utn.append(ent.customs_tariff_number)
                if entries.customs_tariff_number not in tariff_data:
                    tariff_data.update({entries.customs_tariff_number:[entries]})
                    print("new tariff added")
                    counter+=1
                    tariff_list.append(entries.customs_tariff_number)
                else:
                    tariff_data[entries.customs_tariff_number].append(entries)
        tariff_keys=list(tariff_data.keys())
        tariff_keys.sort(key=lambda x: float(x) if x else float('inf'))

        receipts_list.append({
            receipt.get("reference_document"):{
                            "data":tariff_data,
                            "doctype":receipt.get("reference_doctype"),
                            "supplier_name":supplier_name,
                            "supplier_country":sup_country,
                            "cur_cmp":total_cmp,
                            "cur_frn":total_frn,
                            "cur_pur": purchase_det.currency,
                            "frn_curr_sym":frn_curr_sym ,
                            "no_of_itm":len(items),
                            "invoice_number":purchase_det.custom_invoice_number,  
                            "tariff_keys":tariff_keys, 
                            }
                        })
    print("counter",counter)
    if tariff_count:
        return len(list(set(tariff_list))) if len(list(set(tariff_list))) >0 else 1
    return receipts_list

    # print("tariff_data",tariff_data)
    # for i in tariff_data:
    #     print(f"{i}")
    #     for j in tariff_data.get(i):
    #         print(f"{j.name},{j.customs_tariff_number}")
    #     print()
    # return "hello world"


@frappe.whitelist()
def my_function1(name):
    print("name",name)
    # return receipts

    items=frappe.db.get_all("Customs Entry Tariff Application Item",{"parent":name},["*"])
    print("items",items)
    tariff_data={}
    for entries in items:
        # print("entries",entries)
        if entries.customs_tariff_number:
                # utn.append(ent.customs_tariff_number)
            if entries.customs_tariff_number not in tariff_data:
                tariff_data.update({entries.customs_tariff_number:[entries]})
            else:
                tariff_data[entries.customs_tariff_number].append(entries)
 
    return tariff_data

    print("tariff_data",tariff_data)
    for i in tariff_data:
        print(f"{i}")
        for j in tariff_data.get(i):
            print(f"{j.name},{j.customs_tariff_number}")
        print()
    return "hello world"

@frappe.whitelist()
def get_tax_info(name='SC008',document="MAT-PRE-2023-00015",doc="Purchase Receipt"):
    duty=0
    vat=0
    service=0
    surcharge=0
    excise=0
    markup=0
    items=frappe.db.get_all("Customs Entry Tariff Application Item",{"parent":name,"reference_document":document},["*"])
    purchase_det=frappe.get_doc(doc,document)
    supplier=purchase_det.supplier
    supplier_name=purchase_det.supplier_name
    print("supplier",supplier,supplier_name)
    print("puchase===============================================",purchase_det.name)
    # print("items",items)
    for item in items:
        print("item",item.get("name"),item.get("customs_tariff_number"))
        duty_per,vat_per,ser_per,sur_per,excise_per,markup_per=frappe.db.get_value("Customs Tariff Number",{"name":item.get("customs_tariff_number")},["custom_duty_percentage","custom_vat_percentage","custom_service_charge_percentage","custom_surcharge_percentage","custom_excise_percentage","custom_markup_percentage"])
        print(duty_per,vat_per,ser_per,sur_per,excise_per,markup_per)
        duty+=item.get('amount')*(duty_per/100)
        # vat+=item.get('amount')*(vat_per/100)
        service+=item.get('amount')*(ser_per/100)
        surcharge+=item.get('amount')*(sur_per/100)
        excise+=item.get('amount')*(excise_per/100)
        markup+=item.get('amount')*(markup_per/100)

        bs_amt=item.get('amount') if item.get('amount') else 0
        vat_total=item.get('amount')*(duty_per/100)+item.get('amount')*(ser_per/100)+item.get('amount')*(sur_per/100)+item.get('amount')*(excise_per/100)+bs_amt
        print(f"duty {item.get('amount')*(duty_per/100)}  + service {item.get('amount')*(ser_per/100)}  + surcharge {item.get('amount')*(sur_per/100)}  + exicse {item.get('amount')*(excise_per/100)}  + bs_amount {bs_amt}")
        vat+=vat_total*(vat_per/100)
        print(f"item-{item.get('item')} {vat_total}*{vat_per}/100 == vat")
    total=duty+vat+service+surcharge+excise

    print("->",[{"abbr":"DT","desc":"DUTY","val":duty},
        {"abbr":"VAT","desc":"VALUE ADDED TAX","val":vat},
        {"abbr":"SR","desc":"SERVICE","val":service},
        {"abbr":"SC","desc":"SURCHARGE","val":surcharge},
        {"abbr":"EX","desc":"EXCISE","val":excise},
        {"abbr":"MK","desc":"MARKUP","val":markup}
        ])
    return [
            {"abbr":"DT","desc":"DUTY","val":duty},
            {"abbr":"VAT","desc":"VALUE ADDED TAX","val":vat},
            {"abbr":"SR","desc":"SERVICE","val":service},
            {"abbr":"SC","desc":"SURCHARGE","val":surcharge},
            {"abbr":"EX","desc":"EXCISE","val":excise},
            {"abbr":"","desc":"TOTAL TAXES","val":total}
           ]


@frappe.whitelist()
def additional_charges(custom_entry="CE-test222-01",foreign=True):
    add_info=frappe.db.get_all("Landed Cost Taxes and Charges",{"parent":custom_entry},["amount","base_amount"])
    total=0
    for info in add_info:
        if foreign:
            total+=info.get("amount")
        else:
            total+=info.get("base_amount")
    return total

@frappe.whitelist()
def additional_curr(custom_entry="CE-test222-01"):
    add_info=frappe.db.get_value("Landed Cost Taxes and Charges",{"parent":custom_entry},["account_currency"])
    return add_info


@frappe.whitelist()
def tariff_application_data(name='TAF-01001',doct="Purchase Receipt",docu='MAT-PRE-2023-00036',tariff_count=False):
    print("name",name,docu)
    receipts_list=[]
    tariff_list=[]
    counter=0
    
    # return receipts
    
    purchase_det=frappe.get_doc(doct,docu)
    supplier=purchase_det.supplier
    supplier_name=purchase_det.supplier_name
    address_name=frappe.db.get_value("Dynamic Link",{"link_title":supplier_name},['parent'])
    address=frappe.db.get_value("Address",{"name":address_name},["address_line1","city","country"])
    frn_curr_sym=frappe.db.get_value("Currency",{"name":purchase_det.currency},["symbol"])
    
    total_cmp=0
    total_frn=0
    
    # country=frappe.db.get_value("Country",{"name":address[2]},["code"])
    sup_country=""
    if address:
        sup_country=address[2]
        print("supplier",docu,supplier,supplier_name,address_name,address[2])
    else:
        print("supplier",docu,supplier,supplier_name,address_name,address)
    items=frappe.db.get_all("Tariff Application Item",{"parent":name},["*"])
    print("items",items)
    print("len",len(items))
    tariff_data={}
    for entries in items:
        total_cmp+=entries.get('amount')
        # total_frn+=entries.get('base_amount')
        # print("entries",entries)
        if entries.customs_tariff_number:
                # utn.append(ent.customs_tariff_number)
            if entries.customs_tariff_number not in tariff_data:
                tariff_data.update({entries.customs_tariff_number:[entries]})
                print("new tariff added")
                counter+=1
                tariff_list.append(entries.customs_tariff_number)
            else:
                tariff_data[entries.customs_tariff_number].append(entries)
    tariff_keys=list(tariff_data.keys())
    tariff_keys.sort()
    print("tariff_data",tariff_data,tariff_keys)
    receipts_list.append({
        docu:{
                "data":tariff_data,
                "doctype":doct,
                "supplier_name":supplier_name,
                "supplier_country":sup_country,
                "cur_cmp":total_cmp,
                "cur_frn":total_frn,
                "cur_pur": purchase_det.currency,
                "frn_curr_sym":frn_curr_sym ,
                "no_of_itm":len(items),
                "invoice_number":purchase_det.custom_invoice_number,  
                "tariff_keys":tariff_keys, 
            }
     })
    print("counter",counter)
    if tariff_count:
        return len(list(set(tariff_list)))
    return receipts_list

    print("recipts list",receipts_list)
    # print("tariff_data",tariff_data)
    for i in tariff_data:
        print(f"{i}")
        for j in tariff_data.get(i):
            print(f"{j.name},{j.customs_tariff_number}")
        print()
    return "hello world"

@frappe.whitelist()
def get_asycuda_no(ce,tariff):
    print("ce",ce,tariff)
    data=frappe.get_value("Customs Entry Tariff Application Item Display",{"parent":ce,"tariff_group":tariff},['sr_no'])
    print("get_asycuda_no data",data)
    print("\n\n\n")
    return data if data else "no data"

def sort_li(item):
    print("sort_li",item)
    print("itgrouyp",item.item_group)
    return item.warehouse

@frappe.whitelist()
def sort_pick_list(self,method):

    if self and not self.locations:
        print("No locations found for self.locations")
        return
    for ind,i in enumerate(sorted(self.locations, key=sort_li), start=1):
        # print("locations",ind,i)
        print("group",i.item_group,i.idx)
        i.idx=ind
    # frappe.throw("hello world")
    # return "hello world"
        
@frappe.whitelist()
def create_grouping(self='',value=''):
    self=frappe.get_doc('Pick List',self)
    print("create grouping")
    print("self",self,value)
    print(type(self))

    groups={}
    for i in self.locations:
        if i.item_group not in groups:
            groups[i.item_group]=[{
                "item_code":i.item_code,
                "item_name":i.item_name,
                "description":i.description,
                "item_group":i.item_group,
                "warehouse":i.warehouse,
                "qty":i.qty,
                "stock_qty":i.stock_qty,
                "picked_qty":i.picked_qty,
                "uom":i.uom,
                "conversion_factor":i.conversion_factor,
                "stock_uom":i.stock_uom
            }]
        else:
            groups[i.item_group].append({
                "item_code":i.item_code,
                "item_name":i.item_name,
                "description":i.description,
                "item_group":i.item_group,
                "warehouse":i.warehouse,
                "qty":i.qty,
                "stock_qty":i.stock_qty,
                "picked_qty":i.picked_qty,
                "uom":i.uom,
                "conversion_factor":i.conversion_factor,
                "stock_uom":i.stock_uom
            })
    print("groups",groups)
    for i in groups:
        print(f"{i}:")
        doc = frappe.get_doc({
            'doctype': 'Pick List',
        })
        doc.company=self.company
        doc.parent_warehouse=  "KG Warehouse - JP"
        doc.purpose=self.purpose
        if self.purpose=="Material Transfer for Manufacture":
            print("purpose Material Transfer for Manufacture")
            doc.work_order=self.work_order
            doc.for_qty=self.for_qty
        elif self.purpose== "Material Transfer":
            doc.material_request=self.material_request
            doc.for_qty=self.for_qty
            print("purpose Material Transfer",self.for_qty)
        elif self.purpose=="Delivery":
            print("purpose Delivery")
            doc.customer=self.customer
        # doc.scan_mode=self.scan_mode
        # doc.prompt_qty=self.prompt_qty
        for j in groups[i]:
            print(j)
            doc.append("locations",{
                "item_code":j.get("item_code"),
                "item_name":j.get("item_name"),
                "description":j.get("description"),
                "item_group":j.get("item_group"),
                "warehouse":j.get("warehouse"),
                "qty":j.get("qty"),
                "stock_qty":j.get("stock_qty"),
                "picked_qty":j.get("picked_qty"),
                "uom":j.get("uom"),
                "conversion_factor":j.get("conversion_factor"),
                "stock_uom":j.get("stock_uom")
            })
        doc.insert()    
    return "pick list split success"
    # frappe.throw("hello world trash ur sumbit")

@frappe.whitelist()
def create_grouping_salesorder(self,values,doctype):
    print("doctype--",doctype)
    
    self=frappe.get_doc(doctype,self)
    print("create grouping")
    print("self",self,values)
    print(type(self))
    values=json.loads(values)
    groups={}
    for i in self.items:
        if i.item_group not in groups:
            groups[i.item_group]=[{
                "item_code":i.item_code,
                "item_name":i.item_name,
                "description":i.description,
                "item_group":i.item_group,
                "warehouse":i.warehouse,
                "qty":i.qty,
                "stock_qty":i.stock_qty,
                "picked_qty":i.picked_qty,
                "uom":i.uom,
                "conversion_factor":i.conversion_factor,
                "stock_uom":i.stock_uom
            }]
        else:
            groups[i.item_group].append({
                "item_code":i.item_code,
                "item_name":i.item_name,
                "description":i.description,
                "item_group":i.item_group,
                "warehouse":i.warehouse,
                "qty":i.qty,
                "stock_qty":i.stock_qty,
                "picked_qty":i.picked_qty,
                "uom":i.uom,
                "conversion_factor":i.conversion_factor,
                "stock_uom":i.stock_uom
            })
    print("groups",groups)
    for i in groups:
        print(f"{i}:")
        if values.get(i) == 0 and values.get('all') == 0:
            print("no")
            continue
        doc = frappe.get_doc({
            'doctype': 'Pick List',
        })
        doc.company=self.company
        doc.purpose="Delivery"
        doc.custom_item_group=i
        # doc.parent_warehouse=self.parent_warehouse
        # if self.purpose=="Material Transfer for Manufacture":
        #     print("purpose Material Transfer for Manufacture")
        #     doc.work_order=self.work_order
        #     doc.for_qty=self.for_qty
        # elif self.purpose== "Material Transfer":
        #     doc.material_request=self.material_request
        #     doc.for_qty=self.for_qty
        #     print("purpose Material Transfer",self.for_qty)
        # elif self.purpose=="Delivery":
        #     print("purpose Delivery")
        doc.customer=self.customer
        # doc.scan_mode=self.scan_mode
        # doc.prompt_qty=self.prompt_qty
        for j in groups[i]:
            print(j)
            doc.append("locations",{
                "item_code":j.get("item_code"),
                "item_name":j.get("item_name"),
                "description":j.get("description"),
                "item_group":j.get("item_group"),
                "warehouse":j.get("warehouse"),
                "qty":j.get("qty"),
                "stock_qty":j.get("stock_qty"),
                "picked_qty":j.get("picked_qty"),
                "uom":j.get("uom"),
                "conversion_factor":j.get("conversion_factor"),
                "stock_uom":j.get("stock_uom")
            })
        doc.insert()    
    return True
    
# create grouping based on both warehouse and item group
@frappe.whitelist()
def create_grouping_picklist(self, doctype):
    # print("doctype--",doctype)
    
    self = frappe.get_doc(doctype,self)
    # print("create grouping")
    # print("self",self,values)
    # print(type(self))
    # values=json.loads(values)
    # frappe.msgprint(values)

    groups = {}
    
    for i in self.locations:
        key = i.item_group

        if key not in groups:
            groups[key] = [{
                "item_code": i.item_code,
                "item_name": i.item_name,
                "description": i.description,
                "item_group": i.item_group,
                "warehouse": i.warehouse,
                "qty": i.qty,
                "stock_qty": i.stock_qty,
                "picked_qty": i.picked_qty,
                "uom": i.uom,
                "conversion_factor": i.conversion_factor,
                "stock_uom": i.stock_uom,
                "material_request": i.material_request,
                "material_request_item": i.material_request_item
            }]

        else:
            groups[key].append({
                "item_code": i.item_code,
                "item_name": i.item_name,
                "description": i.description,
                "item_group": i.item_group,
                "warehouse": i.warehouse,
                "qty": i.qty,
                "stock_qty": i.stock_qty,
                "picked_qty": i.picked_qty,
                "uom": i.uom,
                "conversion_factor": i.conversion_factor,
                "stock_uom": i.stock_uom,
                "material_request": i.material_request,
                "material_request_item": i.material_request_item
            })
    # print("groups",groups)

    for itm in groups:
        # print(f"\n\n{itm}")
        doc  =  frappe.get_doc({
            'doctype': 'Pick List',
            'company': self.company,
            'purpose': self.purpose,
            'material_request': self.material_request,
            'custom_target_warehouse': self.custom_target_warehouse or None,
            'custom_item_group': itm,
            'customer': self.customer
        })
        # doc.company = self.company
        # doc.purpose = self.purpose
        # doc.material_request = self.material_request
        # if self.custom_target_warehouse:
        #   doc.custom_target_warehouse  =  self.custom_target_warehouse
        # doc.custom_item_group = itm
        # doc.customer = self.customer
        for j in groups.get(itm):
            # print(f'\t-{j.get("item_code")}\t{j.get("warehouse")}\t{j.get("item_group")}')
            doc.append("locations",{
                "item_code":j.get("item_code"),
                "item_name":j.get("item_name"),
                "description":j.get("description"),
                "item_group":j.get("item_group"),
                "warehouse":j.get("warehouse"),
                "qty":j.get("qty"),
                "stock_qty":j.get("stock_qty"),
                "picked_qty":j.get("picked_qty"),
                "uom":j.get("uom"),
                "conversion_factor":j.get("conversion_factor"),
                "stock_uom":j.get("stock_uom"),
                "material_request":j.get("material_request"),
                "material_request_item":j.get("material_request_item")
            })
        # for k in doc.locations:
        #     print("preview",k.__dict__)
        doc.insert()  

    if self.docstatus == 0:
        self.delete() 

    elif self.docstatus == 1:
        self.docstatus = 2
        self.save()
        self.delete()
    return True



def create_log(i,message):
    print("create log()()(())",i,message,i.get('name'))
    log_exists=frappe.db.exists("Counter Point Sales Log",i.get('name'))
    print("log_exists=",log_exists)
    if log_exists:
        print("log exists")
        log=frappe.get_doc("Counter Point Sales Log",i.get('name'))
    else:
        print("log does not exits")
        log=frappe.get_doc({"doctype":"Counter Point Sales Log"})
        log.name=i.get('name')
    log.ticket_name=i.get('name')
    log.ticket=i.get('ticket')
    log.item=i.get('item')
    log.error=message
    if log_exists:
        log.save()
    else:
        log.insert()
    frappe.db.commit()

def create_sales_log(i,message):
    print("create log()()(())",i,message,i.get('name'))
    log_exists=frappe.db.exists("Counter Point Sales Log",i.get('name'))
    if log_exists:
        print("log exists")
        log=frappe.get_doc("Counter Point Sales Log",i.get('name'))
    else:
        print("log does not exits")
        log=frappe.get_doc({"doctype":"Counter Point Sales Log"})
        log.name=i.get('name')

    log.ticket=i.get('custom_ticket')

    log.error=message
    if log_exists:
        log.save()
    else:
        log.insert()
    frappe.db.commit()

# for checking created sales invoice and if no more tickets of it exist it will be submitted
def check_and_submit():
    print("--x--"*40)
    print("creating check and submit")
    sales_list=frappe.db.get_all("Sales Invoice",{'docstatus':0},['name','custom_ticket'],limit=20)
    print("sales_list",sales_list)
    for ticket in sales_list:
        print("ticket--",ticket)
        tickets=frappe.db.get_all("CounterPoint Sales_",filters={'qty':['>','0'],'ticket':ticket.get('custom_ticket'),'sales_invoice_created':0},fields=['name','item','qty'],limit=1,order_by='ticket')
        print("tickets",tickets)
        if not tickets:
            print("submit",tickets)
            s_inv=frappe.get_doc("Sales Invoice",ticket.get('name'))
            try:
                # pass
                print("submitting",ticket)
                s_inv.submit()
            except Exception as e:
                print("sales invoice submit error",e)
                create_sales_log(ticket,f"Sales Invoice submit error: {str(e)}")
               
            print()
        else:
            print("tickets remainng",tickets)
            print()
    frappe.db.commit()
    
def return_invoice():
    print("--x--"*40)
    print("creating return")
    tickets=frappe.db.get_all("CounterPoint Sales_",filters={'qty':['<','0'],'sales_invoice_created':0,'line_type':'R'},fields=['*'],limit=20,order_by='ticket')
    dic={}
    for i in tickets:   
        print(i)
        print()
        if i.get('ticket') in dic:
            dic[i.get('ticket')].append(i)
        else:
            dic[i.get('ticket')]=[i]
    print("dic",dic)

    # this is to consolidate multiple items as one in a ticket group
    for i in dic:   
        print()
        print()
        print("summup")
        print(f"{i}:")
        temp_dic={}
        for j in dic.get(i):
            print("-->",j.get("name"),j.get("item"),j.get("qty"),j.get("ticket"))
            key=j.get('item')
            if key in temp_dic:                
                print(f"temp_dic[{key}]['qyt]",temp_dic[key]['qty'])
                temp_dic[key]['qty']+=j.get('qty')
            else:
                temp_dic[key]=j
            print(f"temp_dic",temp_dic)
            # print("list",list(temp_dic.values()))
            dic[i]=list(temp_dic.values())

    print("dic after summup",dic)
    for ticket in dic:
        # pass
        # check if sales invoice exists for which we will be returning the items to 
        if frappe.db.exists("Sales Invoice", {"custom_ticket": ticket}):
            sinv_name=frappe.db.get_value("Sales Invoice",{"custom_ticket":ticket},['name'])
            ex_sales_invoice=frappe.get_doc("Sales Invoice",sinv_name)
            print("sales invoice exists",ex_sales_invoice.name)
            # create sales invoice
            sales_invoice=frappe.get_doc({"doctype":"Sales Invoice"})
            sales_invoice.is_return=1
            sales_invoice.customer=ex_sales_invoice.customer
            sales_invoice.custom_ticket=ticket
            # sales_invoice.name=f'{ticket}'
            sales_invoice.return_against=ex_sales_invoice.name
            for data in dic.get(ticket):
                print("for ticket ----->",ticket)
                # check the items exsist in order to create a return for them 
                if frappe.db.get_value("Sales Invoice Item",{'item_code':data.get('item'),'parent':ex_sales_invoice.name},['name']):
                    print(f"{data.get('item')} found in {ex_sales_invoice}")
                    # item_rate=frappe.db.get_value("Sales Invoice Item",{'item_code':data.get('item'),'parent':ex_sales_invoice.name},['rate'])
                    # if data.get('price')*-1 > item_rate:
                    #     create_log(data,f"Return Invoice: {data.get('item')} price is greater than item in {ex_sales_invoice.name}")
                else:
                    print("not found")
                    continue
                


                warehouse=frappe.db.get_value("Store Location Mapping Table",{"store_location":data.get("ticket_location")},['warehouse'])
                sales_invoice.append("items",{
                    "item_code":data.get('item'),
                    "item_name":data.get('item_name'),
                    "qty":float(data.get('qty')) if data.get('qty') else 0,
                    "rate":float(data.get('price')) if data.get('price') else 0,
                    "warehouse":warehouse,
                    # "uom":"EACH",
                    "amount":(float(data.get('price')))*float(data.get('qty')) if data.get('price') and data.get('qty') else 0
                })
                print("data.get('price')",data.get('price'))
                ret_tick=frappe.get_doc("CounterPoint Sales_",data.get('name'))
                ret_tick.sales_invoice_created=1
                ret_tick.save()
            print("sales_invoice.items",sales_invoice.items)
            for i in sales_invoice.items:
                print("sales inv dic",i.__dict__)
                print(i.rate)
                print()
            print("sales invoice submit",sales_invoice.name)
            if sales_invoice.items:
                sales_invoice.save()
                sales_invoice.submit()

def update_as_error(ticket_name):
    ticket_doc=frappe.get_doc("CounterPoint Sales_",ticket_name)
    ticket_doc.ticket_error=1
    ticket_doc.save()
    frappe.db.commit()

def update_as_done(ticket_name):
    ticket_doc=frappe.get_doc("CounterPoint Sales_",ticket_name)
    ticket_doc.sales_invoice_created=1
    ticket_doc.save()
    frappe.db.commit()

@frappe.whitelist()
def create_sales_invoice():
    check_and_submit()
    return_invoice()
    print("--x--"*40)
    print("start creating sales")
    fields=['customer','customer_name','qty','cost','ticket','cost','price','ticket_location']
    print("create_sales_invoice"*40)
    dic={}
    tickets=frappe.db.get_all("CounterPoint Sales_",{'sales_invoice_created':0,'ticket_error':0},['*'],limit=200,order_by='ticket')
    for i in tickets:
        update_countsales=True
        skip=False
        print("tick",i.get('name'),i.get('customer'),i.get('item'),i.get('ticket'))
        print("ticket",i)
        temp=''
        if not frappe.db.exists('Item',i.get('item')):
            print('item does not exists')
            # create_log(i,f"Item {i.get('item')} does not exists")
            temp+=f"->Item {i.get('item')} does not exists \n"
            skip=True
        else:
            print("uom qty",i.get("qty"),type(i.get("qty")))
            # if item exists check its uom and does it allow fraction dont need to handle other way around if int float allows int
            if not i.get('qty').is_integer():
                print("yes qty is float",i.get('item'),i.get('qty'))
                item_doc=frappe.get_doc('Item',i.get('item'))
                whole_no=frappe.db.get_value("UOM",{"name":item_doc.stock_uom},['must_be_whole_number'])
                print(f"whole number",whole_no)
                if whole_no == 1:
                    temp+=f"->Item {i.get('item')} UOM does not allow {i.get('qty')} fractional data as qty please update UOM and its settings \n"
                    skip=True

        for key in fields:
            print(f"error loop {key} : {i.get(key)}")
            if i.get(key) == None or i.get(key) == "":
                skip=True
                print(f"ERROR -------- {key} : {i.get(key)}")
                temp+=f"->{key} field blank \n"
                print("temp",temp)
        
        sinv_name=frappe.db.get_value("Sales Invoice",{"custom_ticket":i.get('ticket')},['name'])
        check_item_negative=frappe.db.get_value("Sales Invoice Item",{'item_code':i.get("item"),'parent':sinv_name},['name'])
        # if item qty is less than zero and also the item is not in the sales table then skip we cant have item with negative qty
        # if i.get('qty')<=0 and not check_item_negative:
        if i.get('qty')<=0:
            print("if i.get('qty')<=0 and not item_name:",i.get('qty'))
            temp+=f"->item:{i.get('item')} has {i.get('qty')} qty which cannot be applicable as there is no sales invoice with this item to make the modification on\n"
            # update_countsales=False
            # return_invoice()
            skip=True

        if skip:
            create_log(i,temp)
            update_as_error(i.get('name'))
            continue

        # if update_countsales:
        #     update_as_done(i.get('name'))

        if i.get('ticket') in dic:
            dic[i.get('ticket')].append(i)
        else:
            dic[i.get('ticket')]=[i]


    # this is to consolidate multiple items as one in a ticket group
    for i in dic:   
        print()
        print()
        print("summup")
        print(f"{i}:")
        temp_dic={}
        for j in dic.get(i):
            print("-->",j.get("name"),j.get("item"),j.get("qty"),j.get("ticket"))
            key=j.get('item')
            if key in temp_dic:                
                print(f"temp_dic[{key}]['qyt]",temp_dic[key]['qty'])
                temp_dic[key]['qty']+=j.get('qty')
            else:
                temp_dic[key]=j
            print(f"temp_dic",temp_dic)
            # print("list",list(temp_dic.values()))
            dic[i]=list(temp_dic.values())

    # for i in dic:   
    #     print()
    #     print()
    #     print("preivew")
    #     print(f"{i}:")
    #     for j in dic.get(i):
    #         print("-->",j.get("name"),j.get("item"),j.get("qty"),j.get("ticket"))


    # for every ticket
    for i in dic:
        print()
        print()
        sales_inv_exists=frappe.db.exists('Sales Invoice',{"custom_ticket": i})
        sinv_name1=frappe.db.get_value("Sales Invoice",{"custom_ticket":i},['name'])
        if sales_inv_exists:
            sales_invoice=frappe.get_doc("Sales Invoice",sinv_name1)
            
        else:
            sales_invoice=frappe.get_doc({"doctype":"Sales Invoice"})
            sales_invoice.custom_ticket=i
            sales_invoice.update_stock=1
            sales_invoice.due_date=datetime.datetime.now() + datetime.timedelta(1)
            sales_invoice.set_posting_time = 1
            posting_date = dic.get(i)[0].get('posting_date') if dic.get(i) else None
            converted_posting_date = datetime.datetime.strptime(posting_date, "%Y-%m-%dT%H:%M:%S.%fZ")
            formatted_posting_date = converted_posting_date.strftime("%Y-%m-%d")
            sales_invoice.posting_date = formatted_posting_date
        one_cust=dic.get(i)[0] if dic.get(i) else None
        ticket_customer_id=one_cust.get('customer')
        ticket_customer_name=one_cust.get('customer_name')
        print(f"ticket customer {ticket_customer_id} name{ticket_customer_name}")
        cus_in_sys=frappe.db.get_value("Customer",ticket_customer_id)
        if not cus_in_sys:
            print("cust not in sys")
            new_cus=frappe.get_doc({"doctype":"Customer"})
            new_cus.customer_name=ticket_customer_id
            new_cus.customer_details=ticket_customer_name

            new_cus.customer_type='Individual'
            new_cus.customer_group='Individual'
            new_cus.territory='All Territories'
            new_cus.insert()
            sales_invoice.customer=new_cus.name
        else:
            print("cust in sys")
            sales_invoice.customer=cus_in_sys
        print(f"cus_in_sys {cus_in_sys}")
        print("i-->",i)
        # for every item in ticket
        for j in dic.get(i):
            if sales_invoice.docstatus == 1:
                create_log(j,f"Sales Invoice:'{sales_invoice.name}' is already submitted and cannot add or delete item:'{j.get('item')}' in order to allow this change cancel the sales invoice")
                update_as_error(j.get('name'))
                continue
            
            print(f"j {j},i {i}")
            # this is for existsing item
            # check if everytime before adding is there a item alerady present in sales table if yes then modify its qty if it is negative then reduce its qty
            item_name=frappe.db.get_value("Sales Invoice Item",{'item_code':j.get("item"),'parent':sinv_name1})
            warehouse=frappe.db.get_value("Store Location Mapping Table",{"store_location":j.get("ticket_location")},['warehouse'])
            sales_invoice.set_warehouse=warehouse
            if item_name:
                # before adding to table if item exists lets check to update its qty 
                modification_item=frappe.get_doc('Sales Invoice Item',item_name)
                if j.get('qty')<0:
                    pass
                    # if item qty less than 0 but no such item exists from before than skip
                
                    # print(f"qty less than zero {item_name}")
                    # # if not item_name:
                    # #     print(f"item is {item_name} not there in sytem to begin with")
                    # #     continue
                    # print("modification item",modification_item,modification_item.item_code,modification_item.qty,j.get('qty'),modification_item.qty+j.get('qty'))
                    # # sales_invoice.is_return=1
                    # if modification_item.qty+j.get('qty') <= 0: 
                    #     print("child item modification is less than = 0")
                    #     modification_item.delete()                   
                    # else:
                    #     sales_invoice.append("items",{
                    #     "idx":modification_item.idx,
                    #     "item_code":j.get('item'),
                    #     "item_name":j.get('item_name'),
                    #     "qty":modification_item.qty+float(j.get('qty')) if j.get('qty') else 0,
                    #     "rate":float(j.get('price')) if j.get('price') else 0,
                    #     # "uom":"EACH",
                    #     "amount":float(j.get('price'))*(modification_item.qty+float(j.get('qty'))) if j.get('price') and j.get('qty') else 0
                    #     })
                    #     modification_item.delete() 
                
                    # continue
                else:
                    update_as_done(j.get('name'))
                    print("item already exists in child table modify qty",modification_item,modification_item.qty)
                    # modification_item.qty=modification_item.qty+j.get('qty')
                    # modification_item.qty=2
                    print("Modification item name",modification_item.name,modification_item.__dict__)
                    sales_invoice.append("items",{
                        "idx":modification_item.idx,
                        "item_code":j.get('item'),
                        "item_name":j.get('item_name'),
                        "qty":modification_item.qty+float(j.get('qty')) if j.get('qty') else 0,
                        "rate":float(j.get('price')) if j.get('price') else 0,
                        "warehouse":warehouse,
                        # "uom":"EACH",
                        "amount":float(j.get('price'))*(modification_item.qty+float(j.get('qty'))) if j.get('price') and j.get('qty') else 0
                         })
                    modification_item.delete()  
                    # modification_item.save()
                    frappe.db.commit()
                continue
            # this is for new item
            update_as_done(j.get('name'))
            sales_invoice.append("items",{
                "item_code":j.get('item'),
                "item_name":j.get('item_name'),
                "qty":float(j.get('qty')) if j.get('qty') else 0,
                "rate":float(j.get('price')) if j.get('price') else 0,
                "warehouse":warehouse,
                # "uom":"EACH",
                "amount":float(j.get('price'))*float(j.get('qty')) if j.get('price') and j.get('qty') else 0
            })
            print("-->",j.get('name'),j.get('customer'),j.get('item'),j.get('ticket'))
            print()
        if sales_inv_exists:
            # pass
            sales_invoice.save()
        else:
            sales_invoice.insert()
        frappe.db.commit()
    return "sales invoice created"


@frappe.whitelist()
def reset():
    tickets=frappe.db.get_all("CounterPoint Sales_",{'sales_invoice_created':1},['*'])
    print("tickets",tickets)
    for i in tickets:
        print("reset",i.get('name'))
        doc=frappe.get_doc("CounterPoint Sales_",i.get('name'))
        doc.sales_invoice_created=0
        doc.save()
    return 'done'




# @frappe.whitelist()
# def create_tariffapp(self,method):
#     if self.is_return:
#         return
    
#     print(self,method,type(self))
#     # self=json.loads(self)
#     print("create_tairffapp  "*80)
#     # tariff=frappe.get_doc({"doctype":"Tariff Application"})
#     # tariff.company="Jollys Pharmacy Limited"
#     # tariff.reference_doctype="Purchase Receipt"
#     # tariff.reference_document="MAT-PRE-2023-00034"
#     # tariff.currency="USD"
#     # get_items_by_purchase_invoice(tariff)
#     # get_default_additional_charges(tariff)
#     # tariff.insert()
#     print("self.",self.custom_invoice_number)
#     if self.custom_invoice_number:
#         if self.doctype == "Purchase Invoice" and self.update_stock == 0:
#         # can throw a message to say wont be created coz of updatestock 1
#             frappe.msgprint(
#                 msg='This invoice update stock is 1 should be 0 to generate tariff application record',
#                 title='Error',
#             )
#             return
#         tariff=frappe.get_doc({"doctype":"Tariff Application"})
#         tariff.company=self.company
#         tariff.reference_doctype=self.doctype
#         tariff.reference_document=self.name
#         tariff.currency=self.currency
#         get_items_by_purchase_invoice(tariff)
#         get_default_additional_charges(tariff)
#         tariff.insert()


@frappe.whitelist()
def sales_xml(name):
    print("name")
    return "prime"

@frappe.whitelist()
def custom_entry_print_data(name='SC014',tariff_count=False):
    customs_entry=name
    print("name",name,customs_entry)
    receipts_list=[]
    tariff_list=[]
   
    receipts=frappe.db.get_all("Consolidation",{"parent":customs_entry,"parenttype":"Customs Entry"},["reference_document","reference_doctype"],order_by='fob_price2 desc')
    # return receipts
    for receipt in receipts:
        purchase_det=frappe.get_doc(receipt.get("reference_doctype"),receipt.get("reference_document"))
        supplier=purchase_det.supplier
        supplier_name=purchase_det.supplier_name
        address_name=frappe.db.get_value("Dynamic Link",{"link_title":supplier_name},['parent'])
        address=frappe.db.get_value("Address",{"name":address_name},["address_line1","city","country"])
        frn_curr_sym=frappe.db.get_value("Currency",{"name":purchase_det.currency},["symbol"])
        taxes_charges = purchase_det.total_taxes_and_charges
        
        total_cmp=0
        total_frn=0

        misc_exp={}
        # misc charges
        if (purchase_det.other_charges_calculation):
            soup = BeautifulSoup(purchase_det.other_charges_calculation, 'html.parser')

            # Find all table rows (excluding the header row)
            rows = soup.find_all('tr')[1:]
            print("xox"*100)
            print("soup th",soup.find_all('th'),('Miscellaneous Expenses' in soup.find_all('th')))
            msc_index=None
            for i,th in enumerate(soup.find_all('th')):
                print("th",i,th.text.strip())
                if th.text.strip() == 'Miscellaneous Expenses':
                    print("exists",i)
                    msc_index=i
            # print("rows",rows)
            
            for row in rows:
                cols = row.find_all('td')
                print("cols",cols)
                item = cols[0].text.strip()
                taxable_amount = cols[1].text.strip()
                miscellaneous_expenses = cols[msc_index].text.strip() if msc_index else 0
                misc_exp.update({item:miscellaneous_expenses})

            print(misc_exp)
        
        # country=frappe.db.get_value("Country",{"name":address[2]},["code"])
        sup_country=""
        if address:
            sup_country=address[2]
            print("supplier",receipt.get("reference_document"),supplier,supplier_name,address_name,address[2])
        else:
            print("supplier",receipt.get("reference_document"),supplier,supplier_name,address_name,address)
        items=frappe.db.get_all("Customs Entry Tariff Application Item",{"parent":name,"reference_document":receipt.get("reference_document"),"reference_doctype":receipt.get("reference_doctype")},["*"])
        # print("items",items)
        # frappe.throw("manual error")
        misc_charges_recp=frappe.db.get_all("Purchase Taxes and Charges",{"parent":purchase_det.name},['tax_amount'])
        total_misc_charges=0
        total_qty=0
        charge_factor=0
        for i in misc_charges_recp:
            total_misc_charges+=float(i.get('tax_amount')) 
        for i in items:
            total_qty+=float(i.qty)
        if total_qty>0:
            charge_factor=total_misc_charges/total_qty
        print(f'===,misc_charges_recp {misc_charges_recp},total_misc_charges {total_misc_charges},total_qty {total_qty},charge_factor {charge_factor}')

        # print("items",items)
        tariff_data={}
        for entries in items:
            entries.update({"misc_charge":round(charge_factor,4)})
            total_cmp+=entries.get('amount')
            total_frn+=entries.get('base_amount')
            # print("entries",entries)
            print("tariff_data",tariff_data.keys(),entries.customs_tariff_number)
            if entries.customs_tariff_number:
                    # utn.append(ent.customs_tariff_number)
                if entries.customs_tariff_number not in tariff_data:
                    tariff_data.update({entries.customs_tariff_number:[entries]})
                    print("new tariff added")
                    
                    tariff_list.append(entries.customs_tariff_number)
                else:
                    tariff_data[entries.customs_tariff_number].append(entries)
        tariff_keys=list(tariff_data.keys())
        # tariff_keys.sort()
        tariff_keys.sort(key=lambda x: float(x) if x else float('inf'))
        receipts_list.append({
            receipt.get("reference_document"):{
                            "data":tariff_data,
                            "doctype":receipt.get("reference_doctype"),
                            "supplier_name":supplier_name,
                            "supplier_country":sup_country,
                            "cur_cmp":total_cmp,
                            "cur_frn":total_frn,
                            "cur_pur": purchase_det.currency,
                            "frn_curr_sym":frn_curr_sym ,
                            "no_of_itm":len(items),
                            "invoice_number":purchase_det.custom_invoice_number,  
                            "tariff_keys":tariff_keys, 
                            "taxes_charges":taxes_charges,
                            "misc_exp":misc_exp,
                            "frn_fob":purchase_det.grand_total,
                            }
                        })
  

    tariff_list.sort()
    print("tariff_list",tariff_list)
    print("len",len(list(set(tariff_list))))
    if tariff_count:
        return len(list(set(tariff_list))) if len(list(set(tariff_list))) >0 else 1
    return receipts_list

@frappe.whitelist()
def add_tofob(misc,tot):
    x=0
    f=tot
    if misc:
        x=misc.split(" ")
        x[1]=x[1].replace(",","")
        # tot.replace(",","")
        print(f"before additon {float(x[1])}+{float(tot)}",)
        f=float(x[1])+float(tot)
    print("xxxdfdf",x)
    return round(f,2)

# @frappe.whitelist()
# def get_tax_info(name='SC008',document="MAT-PRE-2023-00015",doc="Purchase Receipt"):
#     duty=0
#     vat=0
#     service=0
#     surcharge=0
#     excise=0
#     markup=0
#     items=frappe.db.get_all("Customs Entry Tariff Application Item",{"parent":name,"reference_document":document},["*"])
#     purchase_det=frappe.get_doc(doc,document)
#     supplier=purchase_det.supplier
#     supplier_name=purchase_det.supplier_name
#     print("supplier",supplier,supplier_name)
#     print("puchase===============================================",purchase_det.name)
#     # print("items",items)
#     for item in items:
#         print("item",item.get("name"),item.get("customs_tariff_number"))
#         duty_per,vat_per,ser_per,sur_per,excise_per,markup_per=frappe.db.get_value("Customs Tariff Number",{"name":item.get("customs_tariff_number")},["custom_duty_percentage","custom_vat_percentage","custom_service_charge_percentage","custom_surcharge_percentage","custom_excise_percentage","custom_markup_percentage"])
#         print(duty_per,vat_per,ser_per,sur_per,excise_per,markup_per)
#         duty+=item.get('amount')*(duty_per/100)
#         # vat+=item.get('amount')*(vat_per/100)
#         service+=item.get('amount')*(ser_per/100)
#         surcharge+=item.get('amount')*(sur_per/100)
#         excise+=item.get('amount')*(excise_per/100)
#         markup+=item.get('amount')*(markup_per/100)

#         bs_amt=item.get('amount') if item.get('amount') else 0
#         vat_total=item.get('amount')*(duty_per/100)+item.get('amount')*(ser_per/100)+item.get('amount')*(sur_per/100)+item.get('amount')*(excise_per/100)+bs_amt
#         print(f"duty {item.get('amount')*(duty_per/100)}  + service {item.get('amount')*(ser_per/100)}  + surcharge {item.get('amount')*(sur_per/100)}  + exicse {item.get('amount')*(excise_per/100)}  + bs_amount {bs_amt}")
#         vat+=vat_total*(vat_per/100)
#         print(f"item-{item.get('item')} {vat_total}*{vat_per}/100 == vat")
#     total=duty+vat+service+surcharge+excise

#     print("->",[{"abbr":"DT","desc":"DUTY","val":duty},
#         {"abbr":"VAT","desc":"VALUE ADDED TAX","val":vat},
#         {"abbr":"SR","desc":"SERVICE","val":service},
#         {"abbr":"SC","desc":"SURCHARGE","val":surcharge},
#         {"abbr":"EX","desc":"EXCISE","val":excise},
#         {"abbr":"MK","desc":"MARKUP","val":markup}
#         ])
#     return [
#             {"abbr":"DT","desc":"DUTY","val":duty},
#             {"abbr":"VAT","desc":"VALUE ADDED TAX","val":vat},
#             {"abbr":"SR","desc":"SERVICE","val":service},
#             {"abbr":"SC","desc":"SURCHARGE","val":surcharge},
#             {"abbr":"EX","desc":"EXCISE","val":excise},
#             {"abbr":"","desc":"TOTAL TAXES","val":total}
#            ]


@frappe.whitelist()
def split_mat_req(name):
    doc = frappe.get_doc("Material Request", name)
    try:
        if doc.material_request_type != 'Material Transfer':
            frappe.throw('Only able to split purpose "Material Transfer" by warehouse.')

        if doc.material_request_type == 'Material Transfer':
            locations = []
        
            for item in doc.items:
                if item.warehouse not in locations:
                    locations.append(item.warehouse)
            
            if len(locations) == 1:
                frappe.throw('Material request is already split by warehouse.')

            else:
                for location in locations:
                    new_material_request = frappe.new_doc('Material Request')
                    new_material_request.update({
                        'material_request_type': 'Material Transfer',
                        'schedule_date': doc.items[0].schedule_date,
                        'transaction_date': doc.transaction_date,
                        'set_warehouse': location
                    })
                    for item in doc.items:
                        if item.warehouse == location:
                            new_material_request.append("items", {
                                "item_code": item.item_code,
                                "schedule_date": item.schedule_date,
                                "qty": item.qty,
                                "warehouse": item.warehouse,
                                "uom": item.uom,
                            })
                            
                    new_material_request.insert()
                    
                if doc.docstatus == 1:
                    doc.docstatus = 2
                    doc.save()
                
                doc.delete()
                frappe.msgprint(msg='Material Transfer has been Successfully Split.', title='Success')

    except Exception as e:
        frappe.msgprint(msg=f'Something has went wrong during the splitting process. {e}', title='Error')

@frappe.whitelist()
def create_attachment(self,target='MAT-PRE-2024-00067',dest_name="TAF-15001",dest_doctype='Tariff Application',purchase_list=[]):
    print("create_attachment",target,dest_name,dest_doctype,purchase_list)
    # remove existing attachments
    rec_to_del=frappe.db.get_all("File",{'attached_to_name':dest_name,'attached_to_doctype':dest_doctype},['name'])
    if rec_to_del:
        rec_to_del=list(map(lambda x:x.get('name'),rec_to_del))
    for i in rec_to_del:
        frappe.get_doc("File",i).delete()

    print("rec_to_del",rec_to_del)
    # return 'helo'
    # add new file attachment
    existing_doc=[]
    
    if target=="Customs Entry":
        for i in purchase_list:
            existing_doc.extend(frappe.db.get_all('File',{'attached_to_name':i},['*']))
          
    else:
        existing_doc=frappe.db.get_all('File',{'attached_to_name':target},['*'])
    print("existing_doc summary",existing_doc)
    for i in existing_doc:
        new_file=frappe.get_doc({'doctype':"File"})
        new_file.file_name=i.file_name
        new_file.file_url=i.file_url
        new_file.attached_to_name=dest_name
        new_file.file_size=i.file_size
        new_file.attached_to_doctype=dest_doctype
        new_file.is_private=i.is_private
        new_file.folder=i.folder
        new_file.content_hash=i.content_hash
        new_file.file_type=i.file_type
        new_file.insert()


@frappe.whitelist()
def calculate_working_salaryslip(self,method):
    print("salary slip",self,method,self.start_date,self.end_date)
    # working hours salary slip
    data=frappe.db.get_all("Attendance",filters=[[ 'attendance_date', 'between', [self.start_date, self.end_date]],["employee","=",self.employee],["docstatus","=","1"]],pluck="working_hours")
    total=0
    if data:
        total=round(sum(data),1)
    print("total",total)
    # ot hours
    ot_total_hrs=0
    ot_data=frappe.db.get_all("Overtime Request",filters=[[ 'date', 'between', [self.start_date, self.end_date]],["employee","=",self.employee],["docstatus","=","1"]],pluck="overtime_hours")
    if ot_data:
        ot_total_hrs=round(sum(ot_data),1)
    print("ot_total_hrs",ot_total_hrs)
    # ot amt
    total_ot_amt=0
    ot_amt=frappe.db.get_all("Overtime Request",filters=[[ 'date', 'between', [self.start_date, self.end_date]],["employee","=",self.employee],["docstatus","=","1"]],pluck="overtime_amount")
    if ot_amt:
        total_ot_amt=round(sum(ot_amt),1)
    print("total_ot_amt",total_ot_amt)
    

    ot_flag=frappe.db.get_value("Employee Grade",self.grade,["is_overtime_paid"])
    print("ot flag",ot_flag)
    if ot_flag:
        self.overtime=ot_total_hrs
        self.overtime_amount=total_ot_amt
    self.custom_hours_worked=total-ot_total_hrs


    print("data",data)


@frappe.whitelist()
def check_holiday(date):
    val = frappe.db.get_value('Holiday', {"holiday_date": date}, 'description') 
    print("val",val)
    return True if val else False

@frappe.whitelist()
def calc_overtime(frm):
    frm=json.loads(frm)
    if not (frm.get("employee") and frm.get("date")):
        return {"status":False,"data":"Employee and Date are needed to fetch overtime amount"}
    print("calc_overtime function",{"attendance_date":frm.get("date"),"employee":frm.get("employee")})
    attendance_data= frappe.db.get_value("Attendance",{"attendance_date":frm.get("date"),"employee":frm.get("employee")},["shift","working_hours"])
    print("shift name, wrk hours",attendance_data)
    shift_hrs=0
    if (attendance_data):
        shift = frappe.get_doc("Shift Type",attendance_data[0])
        shift_hrs=shift.end_time-shift.start_time
        shift_hrs=shift_hrs.seconds // 3600
        print("final data",(attendance_data[1])-shift_hrs)
    print("shift hrs",shift_hrs)
    return {"status":True,"data":(attendance_data[1])-shift_hrs if shift_hrs > 0 else 0}

# chiranjeevi@dexciss.com
# "sbadole@dexciss.com"
@frappe.whitelist()
def send_email_picklist():
    print("Send email picklist")
    frappe.sendmail(recipients="ssutar@dexciss.com",
		subject="Test email from method ",
		message= "test email form send email method picklist"
    )

@frappe.whitelist()
def create_pick_list_frm_matrq(doc):
    doc=json.loads(doc)
    print("doc",doc.items)
    new_doc=frappe.get_doc({"doctype":"Pick List"})
    new_doc.purpose="Material Transfer"
    new_doc.material_request=doc.get("name")
    for item in doc.get('items'):
        new_doc.append("locations",{
            "item_code":item.get("item_code"),
            "item_name":item.get("item_name"),
            "description":item.get("description"),
            "item_group":item.get("item_group"),
            "item_code":item.get("item_code"),
            "item_code":item.get("item_code"),
            "item_code":item.get("item_code"),
        })
    
    return "hsdfkll"

@frappe.whitelist()
def get_uom_price_rev(doctype, txt, searchfield, start, page_len, filters):
    print("filters",filters,doctype,txt,searchfield)
    rev_uom=frappe.db.get_value("Price Revision",{"name":filters.get('cdn')},['uom'])
    print("rev_uom",rev_uom)
    curr_uom_cf=frappe.db.get_value("UOM Conversion Detail",{"parent":filters.get("item"),"parenttype":"Item","uom":rev_uom},['idx'])
    print("cf",curr_uom_cf)
    uoms=[]
    if curr_uom_cf == 1:
        uoms=frappe.db.get_all("UOM Conversion Detail",{"parent":filters.get("item"),"parenttype":"Item","idx":["=",curr_uom_cf]},pluck="uom")    
    else:
        uoms=frappe.db.get_all("UOM Conversion Detail",{"parent":filters.get("item"),"parenttype":"Item","idx":["<",curr_uom_cf]},pluck="uom")
    data=[]
    for i in uoms:
        data.append([i])
    
    print("uoms",uoms,data)
    return data

@frappe.whitelist()
def conversion_uom_pricerevision(row):
    # markup_per=frappe.db.get_value("Markup Summary",{"item_code":row.get("item"),"parent":row.get("parent"),"parenttype":"Shipment Clearing"},['markup_'])
    row=json.loads(row)
    curr_uom_cf=1
    new_uom_cf=1
    qty,rev_uom,cp,up=frappe.db.get_value("Price Revision",{"name":row.get('name')},['qty','uom','calculated_price','updated_price'])
    print(f"qty {qty}  rev_uom {rev_uom}  cp {cp}  up {up}")
    curr_uom_cf=frappe.db.get_value("UOM Conversion Detail",{"parent":row.get("item"),"parenttype":"Item","uom":rev_uom},['conversion_factor'])
    new_uom_cf=frappe.db.get_value("UOM Conversion Detail",{"parent":row.get("item"),"parenttype":"Item","uom":row.get("uom")},['conversion_factor'])
    print("row",row,curr_uom_cf,new_uom_cf)
    if not new_uom_cf:
        return False
    final_qty=(qty*curr_uom_cf)/new_uom_cf
    unit_price_act=cp/curr_uom_cf
    unit_price_updt=up/curr_uom_cf
    newly_calc_price=unit_price_act*new_uom_cf
    newly_calc_updt_price=unit_price_updt*new_uom_cf
    # new_updt_price=newly_calc_price(newly_calc_price*(markup_per/100))
    return final_qty,newly_calc_price,newly_calc_updt_price
    
@frappe.whitelist()
def set_stock_status(self,method):
    print("set_stock_status")
    if self.pick_list:
        frappe.db.set_value("Pick List",self.pick_list,"workflow_state","Stock Entry")


@frappe.whitelist()
def upload_purchase_order(purchase_order): 
    n8n_url = 'http://10.0.10.188:5678/webhook/upload-purchase-order'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'ABC123!'
    }

    if not purchase_order:
        return 'Please Provide a Purchase Order Number'
    
    payload = json.dumps({'purchase_order': purchase_order})
    
    req = requests.post(n8n_url, data=payload, headers=headers)

    return req.json()["msg"]

@frappe.whitelist()
def upload_item(item): 
    n8n_url = 'http://10.0.10.188:5678/webhook/test-upload-item'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': '4w`aZgww.}{-Y]A'
    }

    if not item:
        return 'Please Provide an Item number'
    
    payload = json.dumps({'item': item})
    
    req = requests.post(n8n_url, data=payload, headers=headers)

    return req.json()["msg"]

@frappe.whitelist()
def upload_supplier(supplier): 
    n8n_url = 'http://10.0.10.188:5678/webhook/upload-supplier'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'ABC123!'
    }
    1
    if not supplier:
        return 'Please Provide a Supplier Number'
    
    payload = json.dumps({'supplier': supplier})
    
    req = requests.post(n8n_url, data=payload, headers=headers)

    return req.json()["msg"]


@frappe.whitelist()
def reset():
    tickets=frappe.db.get_all("CounterPoint Sales_",{'sales_invoice_created':1},['*'])
    print("tickets",tickets)
    for i in tickets:
        print("reset",i.get('name'))
        doc=frappe.get_doc("CounterPoint Sales_",i.get('name'))
        doc.sales_invoice_created=0
        doc.save()
    return 'done'

def create_ticket_log(ticket_name, message):
  print("create log()()(())",ticket_name ,message)
  log_exists = frappe.db.exists("CounterPoint Sales Log",ticket_name)
  if log_exists:
      print("log exists")
      log = frappe.get_doc("CounterPoint Sales Log", ticket_name)
  else:
      print("log does not exits")
      log = frappe.get_doc({"doctype":"CounterPoint Sales Log"})
      log.name = ticket_name
  log.ticket = ticket_name
  log.error = message
  if log_exists:
      log.save()
  else:
      log.insert()

def create_return_log(return_name, message):
  print("create log()()(())",return_name ,message)
  log_exists = frappe.db.exists("CounterPoint Returns Log",return_name)
  if log_exists:
      print("log exists")
      log = frappe.get_doc("CounterPoint Returns Log", return_name)
  else:
      print("log does not exits")
      log = frappe.get_doc({"doctype":"CounterPoint Returns Log"})
      log.name = return_name
  log.counterpoint_return = return_name
  log.error = message
  if log_exists:
      log.save()
  else:
      log.insert()

@frappe.whitelist()
def create_counterpoint_sales_ticket():
  data = frappe.request.data

  if not data:
    frappe.log_error(message='Failed to receive data for ticket creation.', title='Data Not Found')
    raise('Failed to receive data for ticket creation.')

  ticket = json.loads(data) 

  is_return = any(item['qty'] < 0 for item in ticket['items'])

  if is_return:
    return_exists = frappe.db.exists('CounterPoint Returns', {'ticket_number': ticket['ticket_number']})

    if return_exists:
      return {'message': f'Sales Return already created.'}

    counterpoint_return = frappe.new_doc('CounterPoint Returns')
    counterpoint_return.ticket_number = ticket['ticket_number']
    counterpoint_return.customer = ticket['customer_number']
    counterpoint_return.customer_name = ticket['customer_name']
    counterpoint_return.posting_date = ticket['posting_date']
    counterpoint_return.ticket_date = ticket['ticket_date']
    counterpoint_return.ticket_location = ticket['ticket_location']

    counterpoint_sales = frappe.new_doc('CounterPoint Sales')
    counterpoint_sales.ticket_number = ticket['ticket_number']
    counterpoint_sales.customer = ticket['customer_number']
    counterpoint_sales.customer_name = ticket['customer_name']
    counterpoint_sales.line_type = ticket['line_type']
    # counterpoint_sales.mode_of_payment = ticket['mode_of_payment']
    counterpoint_sales.posting_date = ticket['posting_date']
    counterpoint_sales.ticket_date = ticket['ticket_date']
    counterpoint_sales.ticket_type = ticket['ticket_type']
    counterpoint_sales.ticket_location = ticket['ticket_location']
    counterpoint_sales.total_quantity = ticket['total_quantity']

    for item in ticket['items']:
      if item['qty'] < 0:
        counterpoint_return.append('items', {
            'item': item['item_code'],
            'item_name': item['item_name'],
            'qty': item['qty'],
            'cost': item['exact_cost'],
            'price': item['price'],     
        })
      else:
        counterpoint_sales.append('items', {
            'item': item['item_code'],
            'item_name': item['item_name'],
            'qty': item['qty'],
            'cost': item['exact_cost'],
            'price': item['price'],     
        })

    counterpoint_return.insert()

    if any(item['qty'] > 0 for item in ticket['items']):
       counterpoint_sales.insert()
    
    return {'message': f'Sales Return has been succesfully created.'}
  else:

    ticket_exists = frappe.db.exists('CounterPoint Sales', {'ticket_number': ticket['ticket_number']})

    if ticket_exists:
      return {'message': f'Sales Ticket already created.'}
        
    counterpoint_sales = frappe.new_doc('CounterPoint Sales')
    counterpoint_sales.ticket_number = ticket['ticket_number']
    counterpoint_sales.customer = ticket['customer_number']
    counterpoint_sales.customer_name = ticket['customer_name']
    counterpoint_sales.line_type = ticket['line_type']
    # counterpoint_sales.mode_of_payment = ticket['mode_of_payment']
    counterpoint_sales.posting_date = ticket['posting_date']
    counterpoint_sales.ticket_date = ticket['ticket_date']
    counterpoint_sales.ticket_type = ticket['ticket_type']
    counterpoint_sales.ticket_location = ticket['ticket_location']
    counterpoint_sales.total_quantity = ticket['total_quantity']

    for item in ticket['items']:
      counterpoint_sales.append('items', {
          'item': item['item_code'],
          'item_name': item['item_name'],
          'qty': item['qty'],
          'cost': item['exact_cost'],
          'price': item['price'],     
      })

    counterpoint_sales.insert()
  
    return {'message': f'Sales Ticket has been succesfully created.'}

def create_material_receipt_from_return():
  fields = ['customer', 'customer_name', 'ticket_number', 'ticket_location']

  sales_returns = frappe.db.get_all("CounterPoint Returns", {'material_receipt_created': 0, 'return_error': 0}, ['*'], limit = 200, order_by = 'ticket_number')

  for sales_return in sales_returns:
    update_return = True
    skip = False
    temp = ''

    current_return = frappe.get_doc('CounterPoint Returns', sales_return.get('name'))
    
    for item in current_return.items:
      item_fields = ["item", "qty", "cost", "price"]

      for key in item_fields:
        print(f"error loop {key}: {item.get(key)}")
        if item.get(key) == None or item.get(key) == "":
          skip = True
          print(f"ERROR -------- {key} : {item.get(key)}")
          temp += f"->{key} field blank \n"
      
      if abs(item.get('qty')) <= 0:
        temp += f"->item:{item.get('item')} has {item.get('qty')} qty which cannot be applicable as there is no material receipt with this item to make the modification on\n"

        skip = True

      if not frappe.db.exists('Item', item.get('item')):
        print('Item does not exist')
        temp += f"->Item {item.get('item')} does not exist \n"
        skip = True
      else:
        if not item.get('qty').is_integer():
          item_doc = frappe.get_doc('Item', item.get('item'))
          is_whole_num = frappe.db.get_value("UOM", {"name": item_doc.stock_uom}, ['must_be_whole_number'])

          if is_whole_num == 1:
            temp += f"->Item {item.get('item')} UOM does not allow {item.get('qty')} fractional data as qty. Please update UOM and its settings \n"
            skip = True

    for key in fields:
      print(f"error loop {key}: {sales_return.get(key)}")
      if sales_return.get(key) == None or sales_return.get(key) == "":
        skip = True
        print(f"ERROR -------- {key} : {sales_return.get(key)}")
        temp += f"->{key} field blank \n"

    if skip:
      create_return_log(sales_return.get('name'), temp)
      print(sales_return, temp)
      return_doc = frappe.get_doc("CounterPoint Returns", sales_return.get('name'))
      return_doc.return_error = 1
      return_doc.save() 
      frappe.db.commit()
      continue
    
    if update_return:
      return_doc = frappe.get_doc("CounterPoint Returns", sales_return.get('name'))
      return_doc.material_receipt_created = 1
      return_doc.save()
      frappe.db.commit()


    mat_receipt_exists = frappe.db.exists('Stock Entry', {"custom_ticket": sales_return.get('ticket_number'), "stock_entry_type": 'Material Receipt'})
    mat_receipt_name = frappe.db.get_value("Stock Entry", {"custom_ticket": sales_return.get('ticket_number'), "stock_entry_type": 'Material Receipt'}, ['name'])

    if mat_receipt_exists:
      material_receipt = frappe.get_doc("Stock Entry", mat_receipt_name)
    else:
      material_receipt = frappe.get_doc({"doctype": "Stock Entry"})
      material_receipt.custom_ticket = sales_return.get('ticket_number')
      material_receipt.stock_entry_type = 'Material Receipt'
      material_receipt.to_warehouse = 'Return - JP'
      material_receipt.set_posting_time = 1
      posting_date = sales_return.get('posting_date') 
      converted_posting_date = datetime.datetime.strptime(posting_date, "%Y-%m-%dT%H:%M:%S.%fZ")
      formatted_posting_date = converted_posting_date.strftime("%Y-%m-%d")
      material_receipt.posting_date = formatted_posting_date
      
      for item in current_return.items: 
        
        material_receipt.append("items", {
          "item_code": item.get("item"),
          "qty": abs(float(item.get("qty")) if item.get("qty") else 0),
          "basic_rate": abs(float(item.get("price")) if item.get("price") else 0),
          "set_basic_rate_manually": 1,
          "basic_amount": abs(float(item.get("price")) * float(item.get("qty")) if item.get("price") and item.get("qty") else 0)
        })          

    if mat_receipt_exists:
      pass
    else:
      material_receipt.insert()
      material_receipt.submit()
  return "Material Receipt Created"

def create_stock_entry_from_return():
  fields = ['customer', 'customer_name', 'ticket_number', 'ticket_location']

  sales_returns = frappe.db.get_all("CounterPoint Returns", {'stock_entry_created': 0, 'material_receipt_created': 1, 'return_error': 0}, ['*'], limit = 200, order_by = 'ticket_number')

  for sales_return in sales_returns:
    update_return = True
    skip = False
    temp = ''

    current_return = frappe.get_doc('CounterPoint Returns', sales_return.get('name'))
    
    for item in current_return.items:
      item_fields = ["item", "qty", "cost", "price"]

      for key in item_fields:
        print(f"error loop {key}: {item.get(key)}")
        if item.get(key) == None or item.get(key) == "":
          skip = True
          print(f"ERROR -------- {key} : {item.get(key)}")
          temp += f"->{key} field blank \n"
      
      if abs(item.get('qty')) <= 0:
        temp += f"->item:{item.get('item')} has {item.get('qty')} qty which cannot be applicable as there is no stock entry with this item to make the modification on\n"

        skip = True

      if not frappe.db.exists('Item', item.get('item')):
        print('Item does not exist')
        temp += f"->Item {item.get('item')} does not exist \n"
        skip = True
      else:
        if not item.get('qty').is_integer():
          item_doc = frappe.get_doc('Item', item.get('item'))
          is_whole_num = frappe.db.get_value("UOM", {"name": item_doc.stock_uom}, ['must_be_whole_number'])

          if is_whole_num == 1:
            temp += f"->Item {item.get('item')} UOM does not allow {item.get('qty')} fractional data as qty. Please update UOM and its settings \n"
            skip = True

    for key in fields:
      print(f"error loop {key}: {sales_return.get(key)}")
      if sales_return.get(key) == None or sales_return.get(key) == "":
        skip = True
        print(f"ERROR -------- {key} : {sales_return.get(key)}")
        temp += f"->{key} field blank \n"

    if skip:
      create_return_log(sales_return.get('name'), temp)
      print(sales_return, temp)
      return_doc = frappe.get_doc("CounterPoint Returns", sales_return.get('name'))
      return_doc.return_error = 1
      return_doc.save() 
      frappe.db.commit()
      continue
    
    if update_return:
      return_doc = frappe.get_doc("CounterPoint Returns", sales_return.get('name'))
      return_doc.stock_entry_created = 1
      return_doc.save()
      frappe.db.commit()


    stock_entry_exists = frappe.db.exists('Stock Entry', {"custom_ticket": sales_return.get('ticket_number'), "stock_entry_type": 'Material Transfer'})
    stock_entry_name = frappe.db.get_value("Stock Entry", {"custom_ticket": sales_return.get('ticket_number'), "stock_entry_type": 'Material Transfer'}, ['name'])

    if stock_entry_exists:
      stock_entry = frappe.get_doc("Stock Entry", stock_entry_name)
    else:
      stock_entry = frappe.get_doc({"doctype": "Stock Entry"})
      stock_entry.custom_ticket = sales_return.get('ticket_number')
      stock_entry.stock_entry_type = 'Material Transfer'
      stock_entry.from_warehouse = 'Return - JP'
      stock_entry.set_posting_time = 1
      posting_date = sales_return.get('posting_date') 
      converted_posting_date = datetime.datetime.strptime(posting_date, "%Y-%m-%dT%H:%M:%S.%fZ")
      formatted_posting_date = converted_posting_date.strftime("%Y-%m-%d")
      stock_entry.posting_date = formatted_posting_date
      
      warehouse = frappe.db.get_value("Store Location Mapping Table", {"store_location": sales_return.get('ticket_location')}, ['warehouse'])

      stock_entry.to_warehouse = warehouse 
      
      for item in current_return.items: 
        
        stock_entry.append("items", {
          "item_code": item.get("item"),
          "qty": abs(float(item.get("qty")) if item.get("qty") else 0),
          "basic_rate": abs(float(item.get("price")) if item.get("price") else 0),
          "set_basic_rate_manually": 1,
          "basic_amount": abs(float(item.get("price")) * float(item.get("qty")) if item.get("price") and item.get("qty") else 0)
        })          

    if stock_entry_exists:
      pass
    else:
      stock_entry.insert()
      stock_entry.submit()
  return "Stock Entry Created"
  
from datetime import time

@frappe.whitelist()
def create_sales_invoice_from_ticket():
    print('Starting process to create sales invoices from tickets.')
    skipped = 0
    fields = ['customer', 'customer_name', 'ticket_number', 'ticket_location']
    tickets = frappe.db.get_all('CounterPoint Sales', 
        filters={'sales_invoice_created': 0, 'ticket_error': 0, 'posting_date': '2025-01-16T00:00:00.000Z'},
        fields=['*'],
        order_by = 'ticket_number',
    )
    print(f'Retrieved {len(tickets)} tickets for processing.')

    for ticket in tickets:
        print(f'\nProcessing ticket: {ticket.name}')
        skip = False
        temp = ''
        current_ticket = frappe.get_doc('CounterPoint Sales', ticket.name)

        for item in current_ticket.items:
            print(f'Checking item: {item.item} in ticket {current_ticket.name}')

            if not item:
                skip = True
                temp += f'->Missing item data for {item}\n'

            if item.qty <= 0:
                print(f'Invalid quantity for item {item.item}: {item.qty}')
                temp += f'-> Item {item.item} has invalid quantity: {item.qty}\n'
                skip = True

            if not frappe.db.exists('Item', item.item):
                print(f'Item {item.item} does not exist in the system.')
                temp += f'-> Item {item.item} does not exist in the system.\n'
                # try:
                #     print(f'Attempting to upload Item {item.item}.')
                #     temp += f'-> Attempting to upload Item {item.item}.\n'
                #     upload_item(item.item)

                # except Exception as e:
                #     print(f'Something went wrong when uploading Item {item.item}.')
                #     temp += f'-> Something went wrong when uploading {item.item}.\n'
                skip = True
                #     continue

            else:
                item_doc = frappe.get_doc('Item', item.item)
                is_whole_num = frappe.db.get_value('UOM', {'name': item_doc.stock_uom}, ['must_be_whole_number'])

                if is_whole_num == 1 and not item.qty.is_integer():
                    print(f'Item {item.item} has fractional quantity: {item.qty}, but its UOM requires whole numbers.')
                    temp += f'-> Fractional quantity {item.qty} not allowed for item {item.item}.\n'
                    skip = True

        for key in fields:
            print(f'Checking field {key} for ticket {current_ticket.name}: {current_ticket.get(key)}')
           
            if not current_ticket.get(key):
                skip = True
                print(f'Missing value for {key}.\n')
                temp += f'-> Missing value for {key}.\n'

        if skip:
            print(f'Skipping ticket {current_ticket.name} due to errors:\n{temp}')
            create_ticket_log(current_ticket.name, temp)
            current_ticket.ticket_error = 1
            current_ticket.save() 
            skipped += 1
            continue
        
        print(f'All validations passed for ticket {current_ticket.name}. Proceeding to create sales invoice.')
        sales_inv_exists = frappe.db.exists('Sales Invoice', {'custom_ticket': ticket.get('ticket_number')})

        if not sales_inv_exists:
            posting_date = current_ticket.posting_date 
            converted_posting_date = datetime.datetime.strptime(posting_date, '%Y-%m-%dT%H:%M:%S.%fZ')
            formatted_posting_date = converted_posting_date.strftime('%Y-%m-%d')
            ticket_customer_id = current_ticket.customer
            ticket_customer_name = current_ticket.customer_name
            cus_in_sys = frappe.db.exists('Customer', ticket_customer_id)
            sales_invoice_customer = ''
            
            if not cus_in_sys:
                print(f'Customer {ticket_customer_id} does not exist. Creating new customer.')
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
                print(f'Customer {ticket_customer_id} exists.')
                sales_invoice_customer = frappe.db.get_value('Customer', ticket_customer_id, 'name')

            warehouse = frappe.db.get_value('Store Location Mapping Table', {'store_location': current_ticket.ticket_location}, ['warehouse'])
            print(f'Creating Sales Invoice for ticket {current_ticket.name}.')
            si = frappe.new_doc('Sales Invoice')
            si.set_posting_time = 1
            si.posting_date = formatted_posting_date
            si.posting_time = time(23, 59)
            si.company = 'Jollys Pharmacy Limited'
            si.customer = sales_invoice_customer
            si.debit_to = '1310 - Debtors - JP',
            si.update_stock = 1
            si.is_pos = 0
            si.is_return = 0
            si.return_against = None
            si.currency = 'XCD'
            si.conversion_rate = 1
            si.naming_series = 'ACC-SINV-.YYYY.-'
            si.cost_center = 'Main - JP',
            si.custom_ticket = current_ticket.ticket_number
            si.due_date = datetime.datetime.now() + datetime.timedelta(1)
            si.set_warehouse = warehouse
            si.income_account = '4110 - Sales - JP',
            si.expense_account = '5111 - Cost of Goods Sold - JP',
            
            for item in current_ticket.items:
                print(f'Adding item {item.item} to Sales Invoice.')
                si.append('items', {
                    'item_code': item.item,
                    'item_name': frappe.db.get_value('Item', item.item, 'item_name'),
                    'description': frappe.db.get_value('Item', item.item, 'description'),
                    'warehouse': warehouse,
                    'target_warehouse': None,
                    'qty': float(item.qty),
                    'uom': frappe.db.get_value('Item', item.item, 'stock_uom'),
                    'stock_uom': frappe.db.get_value('Item', item.item, 'stock_uom'),
                    'rate': float(item.price),
                    'price_list_rate': float(item.price),
                    'income_account': '4110 - Sales - JP',
                    'expense_account': '5111 - Cost of Goods Sold - JP',
                    'discount_account': '6800 - Discount Expense - JP',
                    'discount_amount': 0,
                    'asset': None,
                    'cost_center': 'Main - JP',
                    'conversion_factor': 1,
                    'incoming_rate': 0,
                    'serial_and_batch_bundle': None,
                })

            try:
                si.insert()
                print(f'Sales Invoice {si.name} created successfully.')

            except Exception as e:
                print(f'Error creating Sales Invoice for ticket {current_ticket.name}: {str(e)}')
                create_sales_log(si, f'Error creating Sales Invoice: {str(e)}')
                continue
            
        else:
            print(f'Sales Invoice already created for ticket {current_ticket.name}. Continuing...')
            skipped += 1

    print('Finished processing tickets.')
    print(f'Skipped {skipped} / {len(tickets)}')

    try:
        schedule_check_and_inflate_stock_for_sales_invoices()

    except Exception as e:
        frappe.log_error(message=e, title='Error when scheduling schedule_check_and_submit_invoice()')
    
    return 'Sales Invoices Created'

def check_and_inflate_stock_for_sales_invoices(posting_date):
    print("Starting process to check and inflate stock.")
    si_list = frappe.db.get_all("Sales Invoice", 
        filters={'docstatus': 0, 'custom_ticket': ['!=', None], 'posting_date': '16-01-2025'},
        fields=['name'],
    )
    print(f"Number of Sales Invoices to process: {len(si_list)}")
    mr_items = []

    for si in si_list:
        doc = frappe.get_doc('Sales Invoice', si.name)
        print(f"\nProcessing Sales Invoice: {si.name}")

        for item in doc.items:
            is_stock_item = frappe.db.get_value('Item', item.item_code, 'is_stock_item')

            if not is_stock_item:
                print(f"Skipping Item : {item.item_code} - Not Stock Item")
                continue
            
            print(f"Checking Item : {item.item_code} - Warehouse : {item.warehouse}")
            most_recent_bin = frappe.get_all('Bin',
                filters = {'item_code':  item.item_code, 'warehouse': item.warehouse},
                fields = ['name', 'actual_qty'],
                order_by = 'creation',
                limit = 1
            )

            if not most_recent_bin:
                print(f"No Bin Found For : {item.item_code} - Warehouse : {item.warehouse}")
                item_exists = False 

                if len(mr_items) > 0:
                    for mr_item in mr_items:
                        if mr_item['item_code'] == item.item_code and mr_item['to_warehouse'] == item.warehouse:
                            mr_item['qty'] += item.qty
                            print(f"Adding {item.qty} To Item {mr_item['item_code']} For Warehouse {mr_item['to_warehouse']}")
                            item_exists = True 

                if not item_exists:
                    print(f"Appended {item.qty} To Item {item.item_code} For Warehouse {item.warehouse} to mr items")
                    mr_items.append({
                        'item_code': item.item_code,
                        'qty': item.qty,
                        'to_warehouse': item.warehouse
                    })

                continue
            
            most_recent_bin = most_recent_bin[0]

            if most_recent_bin.actual_qty < item.qty:
                print(f"Insufficient Quantity | Actual : {most_recent_bin.actual_qty} - Requires {item.qty}")
                required_qty = item.qty - most_recent_bin.actual_qty if most_recent_bin.actual_qty >= 0 else item.qty
                item_exists = False 

                if len(mr_items) > 0:
                    for mr_item in mr_items:
                        if mr_item['item_code'] == item.item_code and mr_item['to_warehouse'] == item.warehouse:
                            mr_item['qty'] += required_qty
                            print(f"Adding {required_qty} To Item {mr_item['item_code']} For Warehouse {mr_item['to_warehouse']}")
                            item_exists = True 

                if not item_exists:
                    print(f"Appended {required_qty} To Item {item.item_code} For Warehouse {item.warehouse} to mr items")
                    mr_items.append({
                        'item_code': item.item_code,
                        'qty': required_qty,
                        'to_warehouse': item.warehouse
                    })

            else:
                print(f"Sufficient Quantity | Actual : {most_recent_bin.actual_qty} - Requires {item.qty}")

    print(f"Creating Material Receipt")
    mr = frappe.get_doc({
        'doctype': 'Stock Entry',
        'stock_entry_type': 'Material Receipt',
        'set_posting_time': 1,
        'posting_date':  frappe.utils.getdate('16-01-2025'),
        'posting_time': time(23, 58)
    })
    for mr_item in mr_items:
        mr.append('items', {
            'item_code': mr_item['item_code'],
            't_warehouse': mr_item['to_warehouse'],
            'qty': mr_item['qty'],
            'uom': frappe.db.get_value('Item', mr_item['item_code'], 'stock_uom') 
        })
        print(f"Added Item {mr_item['item_code']} Qty {mr_item['qty']} To Warehouse {mr_item['to_warehouse']} To Material Receipt")

    try:
        mr.insert()
        print(f"Inserted Material Receipt")
        mr.save()
        mr.submit()
        print(f"Submitted Material Receipt")
        schedule_check_and_submit_invoice()

    except Exception as e:
        print(f'Something went wrong when inserting or submitting material receipt or scheduling schedule_check_and_submit_invoice(): {e}')
        frappe.log_error(message=e, title='Something went wrong when inserting or submitting material receipt or scheduling schedule_check_and_submit_invoice()')

    return 'Created and Submitted Material Receipt'

def check_and_submit_invoice():
    print("Starting process to check and submit invoices.")
    sales_list = frappe.db.get_all("Sales Invoice", 
        filters={'docstatus': 0, 'custom_ticket': ['!=', None]},
        fields=['*'],
    )
    print(f"Number of Sales Invoices to process: {len(sales_list)}")

    for sales_inv in sales_list:
        print(f"\nProcessing Sales Invoice: {sales_inv.name}")
        ticket_exists = frappe.db.exists('CounterPoint Sales', f'TK-{sales_inv.custom_ticket}')

        if ticket_exists:
            print(f"Ticket TK-{sales_inv.custom_ticket} exists for Sales Invoice {sales_inv.name}.")
            frappe.db.savepoint('sp')
            ticket_doc = frappe.get_doc('CounterPoint Sales', f'TK-{sales_inv.custom_ticket}')
            print(f"Ticket {ticket_doc.name} details: Total Quantity = {ticket_doc.total_quantity}")

            if ticket_doc.total_quantity > 0:
                s_inv= frappe.get_doc("Sales Invoice",sales_inv.name)

                if s_inv.docstatus == 0:
                    try:
                        print(f"Attempting to submit Sales Invoice {s_inv.name}.")
                        s_inv.submit()
                        frappe.db.commit()
                        print(f"Successfully submitted Sales Invoice {s_inv.name}.")

                    except frappe.exceptions.ValidationError as e:
                        frappe.db.rollback()
                        print(f"Unexpected error while submitting Sales Invoice {s_inv.name}: {str(e)}. Rolling back changes.")
                        create_sales_log(s_inv,f"Sales Invoice submit error: {str(e)}")
                        continue

                    except Exception as e:
                        frappe.db.rollback()
                        print(f"Unexpected error while submitting Sales Invoice {s_inv.name}: {str(e)}. Rolling back changes.")
                        create_sales_log(s_inv,f"Sales Invoice submit error: {str(e)}")
                        continue
                    
                else:
                    print(f"Skipping submission of Sales Invoice {s_inv.name}: Invalid docstatus {s_inv.docstatus}.")
                    create_sales_log(s_inv,f"Skipped submission of Sales Invoice {s_inv.name}: Invalid docstatus {s_inv.docstatus}.")
                    continue

            else:
                print(f"Skipping Sales Invoice {sales_inv.name}: Ticket {ticket_doc.name} has zero total quantity.")
                create_sales_log(s_inv,f"Skipped Sales Invoice {sales_inv.name}: Ticket {ticket_doc.name} has zero total quantity.")
                
        else:
            print(f"Ticket TK-{sales_inv.custom_ticket} does not exist. Skipping Sales Invoice {sales_inv.name}.")
            create_sales_log(s_inv,f"Ticket TK-{sales_inv.custom_ticket} does not exist. Skipped Sales Invoice {sales_inv.name}.")
            continue

    print("Finished processing Sales Invoices.")

def schedule_create_sales_invoice_from_ticket():
    frappe.enqueue(
    create_sales_invoice_from_ticket, # python function or a module path as string
    queue="default", # one of short, default, long
    timeout=86400, # pass timeout manually
    is_async=True, # if this is True, method is run in worker
    now=False, # if this is True, method is run directly (not in a worker) 
    job_name="Create Sales Invoices From Counterpoint Sales", # specify a job name
    )

def schedule_check_and_submit_invoice():
    frappe.enqueue(
    check_and_submit_invoice, # python function or a module path as string
    queue="default", # one of short, default, long
    timeout=86400, # pass timeout manually
    is_async=True, # if this is True, method is run in worker
    now=False, # if this is True, method is run directly (not in a worker) 
    job_name="Validate & Submit Generated Sales Invoices", # specify a job name
    )

def schedule_check_and_inflate_stock_for_sales_invoices():
    frappe.enqueue(
    check_and_inflate_stock_for_sales_invoices, # python function or a module path as string
    queue="default", # one of short, default, long
    timeout=86400, # pass timeout manually
    is_async=True, # if this is True, method is run in worker
    now=False, # if this is True, method is run directly (not in a worker) 
    job_name="Check & Inflate Stock to Submit Sales Invoices", # specify a job name
    posting_date='2025-01-15'
    )
    
# from customs_management.reorder import reorder_item
from erpnext.stock.reorder_item import reorder_item
def schedule_reorder_item():
    frappe.enqueue(
    reorder_item, # python function or a module path as string
    queue="default", # one of short, default, long
    timeout=86400, # pass timeout manually
    is_async=True, # if this is True, method is run in worker
    now=False, # if this is True, method is run directly (not in a worker) 
    job_name="RE-Order items", # specify a job name
    )

from frappe.utils.background_jobs import is_job_enqueued
from rq.job import Job, JobStatus
from frappe.utils.background_jobs import get_redis_conn
def schedule_create_sales_invoice():
    job_id=frappe.cache.get_value("job_create_sales_id")
    try:
        j=Job.fetch(job_id,connection=get_redis_conn())
    except Exception as e:
        print("error fetching job",e)
        j=None
    print("job_id", job_id)
    if j==None or j._status != "started" :
        queue=frappe.enqueue(
        create_sales_invoice, # python function or a module path as string
        queue="default", # one of short, default, long
        timeout=86400, # pass timeout manually
        is_async=True, # if this is True, method is run in worker
        now=False, # if this is True, method is run directly (not in a worker) 
        job_name="Create Sales Invoice background", # specify a job name
        )
        frappe.cache.set_value("job_create_sales_id", queue._id)
        print("job queue",queue._id)

def fix_taxes_and_charges(self,method):
    print("fix_taxes_and_charges",method)
    for item in self.taxes:
        if item.custom_foreign_currency != "XCD":
            ex_rate=get_exchange_rate(item.custom_foreign_currency,"XCD")
            if ex_rate:
                converted_amount= ex_rate*item.amount
                print(f"item:{item.name} ex_rate={ex_rate} converted_amount={converted_amount}")
                frappe.db.set_value("Landed Cost Taxes and Charges",item.name,'exchange_rate',ex_rate,update_modified=False)
                frappe.db.set_value("Landed Cost Taxes and Charges",item.name,'base_amount',converted_amount,update_modified=False)

@frappe.whitelist()
def fix_returns():
  try:
    errorenous_returns = frappe.db.get_all('CounterPoint Sales', {'ticket_error': 1, 'return_created': 0, 'sales_invoice_created': 0, 'is_return': 1}, ['*'])

    stock_entry = frappe.get_doc({"doctype": "Stock Entry"})
    stock_entry.stock_entry_type = 'Material Transfer'
    stock_entry.set_posting_time = 1
    posting_date = errorenous_returns[0].get('posting_date') 
    converted_posting_date = datetime.datetime.strptime(posting_date, "%Y-%m-%dT%H:%M:%S.%fZ")
    formatted_posting_date = converted_posting_date.strftime("%Y-%m-%d")
    stock_entry.posting_date = formatted_posting_date 

    for counterpoint_return in errorenous_returns:
        warehouse = frappe.db.get_value("Store Location Mapping Table", {"store_location": counterpoint_return.get('ticket_location')}, ['warehouse'])
        
        current_return = frappe.get_doc('CounterPoint Sales', counterpoint_return.name)

        for item in current_return.items:
            is_stock_item = bool(frappe.db.get_value('Item', item.get("item"), 'is_stock_item'))

            if not is_stock_item:
                continue
            
            if item.get("qty") < 0:
              stock_entry.append("items", {
                "item_code": item.get("item"),
                "qty": abs(float(item.get("qty")) if item.get("qty") else 0),
                "amount": abs(float(item.get("price")) if item.get("price") else 0),        
                "s_warehouse": "Return - JP",
                "t_warehouse": warehouse,
              })

    stock_entry.insert()
    frappe.db.commit()
    # material_receipt.submit()

    return stock_entry
  except Exception as e:
    return f'Something went wrong. {e}'
  # try:
  #   errorenous_returns = frappe.db.get_all('CounterPoint Sales', {'ticket_error': 1, 'return_created': 0, 'sales_invoice_created': 0, 'is_return': 1}, ['*'])

  #   material_receipt = frappe.get_doc({"doctype": "Stock Entry"})
  #   material_receipt.stock_entry_type = 'Material Receipt'
  #   material_receipt.set_posting_time = 1
  #   material_receipt.to_warehouse = 'Return - JP'
  #   posting_date = errorenous_returns[0].get('posting_date') 
  #   converted_posting_date = datetime.datetime.strptime(posting_date, "%Y-%m-%dT%H:%M:%S.%fZ")
  #   formatted_posting_date = converted_posting_date.strftime("%Y-%m-%d")
  #   material_receipt.posting_date = formatted_posting_date 

  #   for counterpoint_return in errorenous_returns:
  #       current_return = frappe.get_doc('CounterPoint Sales', counterpoint_return.name)

  #       for item in current_return.items:
  #           is_stock_item = bool(frappe.db.get_value('Item', item.get("item"), 'is_stock_item'))

  #           if not is_stock_item:
  #               continue
            
  #           if item.get("qty") < 0:
  #             material_receipt.append("items", {
  #               "item_code": item.get("item"),
  #               "qty": abs(float(item.get("qty")) if item.get("qty") else 0),
  #               "amount": abs(float(item.get("price")) if item.get("price") else 0)
  #             })

  #   material_receipt.insert()
  #   frappe.db.commit()
  #   # material_receipt.submit()

  #   return material_receipt
  # except Exception as e:
  #   return f'Something went wrong. {e}'

  # for stock_item in material_receipt.items:

@frappe.whitelist()
def expiration_sql():
    result = kg_stock_details = frappe.db.sql("""
        SELECT
            b.item_code,
            i.item_code,
            i.item_name,
            i.item_group,
            i.standard_rate,
            i.custom_expiration_date_1,
            i.custom_expiration_date_2,
            i.custom_expiration_date_3,
            i.custom_expiration_date_4,
            i.custom_expiration_date_5,                                                                                                                                        
            b.actual_qty,
            b.warehouse
            
        FROM `tabBin` b
        INNER JOIN `tabItem` i ON b.item_code = i.item_code 
        WHERE (( i.custom_expiration_date_1 > CURDATE() AND i.custom_expiration_date_1 <= DATE_ADD(CURDATE(), INTERVAL 3 MONTH)) OR
        ( i.custom_expiration_date_2 > CURDATE() AND i.custom_expiration_date_2 <= DATE_ADD(CURDATE(), INTERVAL 3 MONTH)) OR
        ( i.custom_expiration_date_3 > CURDATE() AND i.custom_expiration_date_3 <= DATE_ADD(CURDATE(), INTERVAL 3 MONTH)) OR
        ( i.custom_expiration_date_4 > CURDATE() AND i.custom_expiration_date_4 <= DATE_ADD(CURDATE(), INTERVAL 3 MONTH)) OR
        ( i.custom_expiration_date_5 > CURDATE() AND i.custom_expiration_date_5 <= DATE_ADD(CURDATE(), INTERVAL 3 MONTH)) )        
                                                                            
    """,
    as_dict = True
)

    return result    

@frappe.whitelist()
def category_list():
    result = frappe.db.sql("""SELECT DISTINCT item_group FROM `tabItem` WHERE item_group NOT IN (ADMAT, INTERNAL, PHARMACY, TESTS, SERVICES)""", as_dict = True)

    return result     

@frappe.whitelist()
def check_picklists(material_request): 
    try:
      pick_lists = frappe.get_all('Pick List', 
          filters = {'material_request': material_request}, 
          fields = ['name', 'workflow_state']
      )

      if pick_lists:
         return {'status': 'success',
              'message': all(pick_list.workflow_state == 'Stock Entry' for pick_list in pick_lists)}
    
    except Exception as e:
        return {
              'status': 'error',
              'message': f'An error occurred {e}.'
          }
@frappe.whitelist()
def update_ordered_percentage(material_request):
    current_per_ordered = frappe.db.get_value('Material Request', material_request, 'per_ordered')
    current_status = frappe.db.get_value('Material Request', material_request, 'status')
    
    if(current_per_ordered < 100 and current_status.lower() != 'transferred'):
        try:
            pick_lists = frappe.get_all('Pick List', 
                filters = {'material_request': material_request}, 
                fields = ['name']
            )

            if not pick_lists:
                return {
                    'status': 'error',
                    'message': f'No pick lists are linked to material request {material_request}.'
                }

            stock_entries_completed = True
            
            for pick_list in pick_lists:
                pick_list_doc = frappe.get_doc('Pick List', pick_list.name)
                
                if not (pick_list_doc.workflow_state == 'Stock Entry'):
                    stock_entries_completed = False

                if not (stock_entries_completed):
                    return {
                        'status': 'error',
                        'message': f'Error: Picklist {pick_list.name} is not submitted.'
                    }                            

            frappe.db.set_value('Material Request', material_request, 'per_ordered', 100)
            frappe.db.set_value('Material Request', material_request, 'status', 'Transferred')
            frappe.db.commit()
            
            return {
                'status': 'success',
                'message': f'Ordered percentage updated to 100%.'
            }                                       

        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error: {e}.'
            }
    
    return {
        'status': 'error',
        'message': f'Material Request is already transferred.'
    }
