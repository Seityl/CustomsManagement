import frappe

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