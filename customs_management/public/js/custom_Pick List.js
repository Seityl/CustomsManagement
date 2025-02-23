
frappe.ui.form.on('Pick List', {
    refresh:function(frm){
        // if (frm.doc.docstatus==1){
        //     frm.add_custom_button(('Split Picklist'), function() {
        //         let d = new frappe.ui.Dialog({
        //             title: 'Split based on',
        //             fields: [
        //                 {
        //                     label: 'Field',
        //                     fieldname: 'field',
        //                     fieldtype: 'Select',
        //                     options: ['Item Group']
        //                 },
    
        //             ],
        //             size: 'small', // small, large, extra-large 
        //             primary_action_label: 'Create Pick Lists',
        //             primary_action(values) {
        //                 console.log(values);
        //                 frappe.call({
        //                     method : 'customs_management.api.create_grouping',
        //                     args: {
        //                         self:frm.doc.name,
        //                         values:values
        //                     },
        //                     callback:function(resp){
        //                         console.log(resp)
        //                     }
        //                 })
        //                 d.hide();
        //             }
        //         });
                
        //         d.show();
                
        //         console.log('rrrrrrrrrrrrrrrrrrrr refresh')
        //     })
        // }

        // new dialogue box with check box selection
        // if (frm.doc.docstatus==1){
        //     frm.add_custom_button(('Split Picklist'), function() {
        //         // console.log("frm.doc.doctype",frm.doc.doctype)
        //         let groups=[]
        //         for (let data of frm.doc.locations){
        //             // console.log("data.item_group",data,data.item_group)
        //             if (!groups.includes(data.item_group)){
        //                 groups.push(data.item_group)
        //             }
        //         }
        //         let group_data=[]
        //         group_data.push({
        //             label: 'All' ,
        //             fieldname: 'all' ,
        //             fieldtype: 'Check',
        //             default:1,
        //         })
        //         for (let data of groups){
        //             group_data.push({
        //                 label: data ,
        //                 fieldname: data ,
        //                 fieldtype: 'Check',
        //             })
        //         }
        //         console.log("groups",groups)
        //         let d = new frappe.ui.Dialog({
        //             title: 'Split based on',
        //             fields: group_data,
        //             size: 'small', // small, large, extra-large 
        //             primary_action_label: 'Create Pick Lists',
        //             primary_action(values) {
        //                 console.log("values",values);
        //                 frappe.call({
        //                     method : 'customs_management.api.create_grouping_picklist',
        //                     freeze:true,
        //                     freeze_message:"Generating Pick List...",
        //                     args: {
        //                         self:frm.doc.name,
        //                         values:values,
        //                         doctype:frm.doc.doctype
        //                     },
        //                     callback:function(resp){
        //                         console.log(resp)
        //                         if (resp.message){
        //                             frappe.show_alert("Pick List Created Successfully",5)
        //                         }
        //                     }
        //                 })
        //                 d.hide();
        //             }
        //         });
                
        //         d.show();
                
        //         console.log('rrrrrrrrrrrrrrrrrrrr refresh')
        //     })
        // }


        if (frm.doc.workflow_state === 'Draft'){
            frm.add_custom_button(('Split Picklist'), function() {
              frappe.confirm('Are you sure you want to proceed? Current Pick List will be split and then deleted.',
                () => {
                  frappe.call({
                    method : 'customs_management.api.create_grouping_picklist',
                    freeze:true,
                    freeze_message:"Generating Pick Lists...",
                    args: {
                        self:frm.doc.name,
                        // values:[{'all':1}],
                        doctype:frm.doc.doctype
                    },
                    callback:function(resp){
                        console.log(resp)
                        if (resp.message){
                            frappe.show_alert("Pick Lists Created Successfully",5)
                        }
                    }
                })
                }, () => {
                    // action to perform if No is selected
                })
            })
        }

        // frm.trigger('custom_edit_item')
    },

    // custom_edit_item:function(frm){
    //     console.log("edit pick item")
    //     if (frm.doc.custom_edit_item == 1){
    //         console.log("inside if")
    //         // add row button
    //         frm.fields_dict["locations"].grid.wrapper
    //         .find(".grid-add-row")
    //         .show();
    //         // row edit button
    //         frm.fields_dict["locations"].grid.wrapper
    //         .find(".btn-open-row")
    //         .show();
    //     }else{
    //         console.log("outside if")
    //         // add row button
    //         frm.fields_dict["locations"].grid.wrapper
    //         .find(".grid-add-row")
    //         .hide();
    //         // row edit button
    //         frm.fields_dict["locations"].grid.wrapper
    //         .find(".btn-open-row")
    //         .hide();

    //     }
    // }
})
