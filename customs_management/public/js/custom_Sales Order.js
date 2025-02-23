
frappe.ui.form.on('Sales Order', {
    refresh:function(frm){
        if (frm.doc.docstatus==1){
            frm.add_custom_button(('Split Picklist'), function() {
                // console.log("frm.doc.doctype",frm.doc.doctype)
                let groups=[]
                for (let data of frm.doc.items){
                    // console.log("data.item_group",data,data.item_group)
                    if (!groups.includes(data.item_group)){
                        groups.push(data.item_group)
                    }
                }
                let group_data=[]
                group_data.push({
                    label: 'All' ,
                    fieldname: 'all' ,
                    fieldtype: 'Check',
                    default:1,
                })
                for (let data of groups){
                    group_data.push({
                        label: data ,
                        fieldname: data ,
                        fieldtype: 'Check',
                    })
                }
                console.log("groups",groups)
                let d = new frappe.ui.Dialog({
                    title: 'Split based on',
                    fields: group_data,
                    size: 'small', // small, large, extra-large 
                    primary_action_label: 'Create Pick Lists',
                    primary_action(values) {
                        console.log("values",values);
                        frappe.call({
                            method : 'customs_management.api.create_grouping_salesorder',
                            freeze:true,
                            freeze_message:"Generating Pick List...",
                            args: {
                                self:frm.doc.name,
                                values:values,
                                doctype:frm.doc.doctype
                            },
                            callback:function(resp){
                                console.log(resp)
                                if (resp.message){
                                    frappe.show_alert("Pick List Created Successfully",5)
                                }
                            }
                        })
                        d.hide();
                    }
                });
                
                d.show();
                
                console.log('rrrrrrrrrrrrrrrrrrrr refresh')
            })
        }
    }
})