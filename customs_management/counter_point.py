import frappe
import datetime

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

def update_as_done(ticket_name):
    ticket_doc=frappe.get_doc("CounterPoint Sales_",ticket_name)
    ticket_doc.sales_invoice_created=1
    ticket_doc.save()

@frappe.whitelist()
def create_sales_invoice():
    check_and_submit()
    return_invoice()
    print("--x--"*40)
    print("start creating sales")
    fields=['customer','customer_name','qty','cost','ticket','cost','price','ticket_location']
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

                              
        print()
        print()
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
    return "sales invoice created"