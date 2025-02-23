frappe.ui.form.on('Material Request',{
    refresh	: function(frm) {
        console.log("Material request script")
        frm.add_custom_button(('Split Material list'), function() {
            frappe.confirm('Are you sure you want to proceed? Current Material Request will be split and then deleted.',
              () => {
                frappe.call({
                  method : 'customs_management.api.split_mat_req',
                  freeze:true,
                  freeze_message:"Generating Material List...",
                  args: {
                      name:frm.doc.name,
                      
                  },
                  callback:function(resp){
                      console.log(resp)
                      if (resp.message){
                          frappe.show_alert("Material List Created Successfully",5)
                      }
                  }
              })
              }, () => {
                  // action to perform if No is selected
              })
           
        })

        frappe.call({
          method : 'customs_management.api.check_picklists',
          args: {
              material_request:frm.doc.name,
          },
          callback: (r) => {
              if(r.message['message'] == true && frm.doc.status !== 'Transferred') {
                frm.add_custom_button(("Update Ordered %"), () => {
                  frappe.confirm(
                      '<b>Are you sure you want to proceed?</b><br>Selecting "Yes" will check if all stock entries linked to this material request have been submitted and set document status to "Transferred".<br>Select "No" to cancel.',
                      () => {
                        //   frappe.call({
                        //       method : 'customs_management.api.update_ordered_percentage',
                        //       freeze:true,
                        //       freeze_message:"Updating Percentage...",
                        //       args: {
                        //           material_request:frm.doc.name,
                        //       },
                        //       callback: (r) => {
                        //           if(r.message['status'] == 'success') {
                        //               frappe.show_alert({
                        //                   message: r.message['message'],
                        //                   indicator:'green'
                        //               }, 5);
                        //               frm.reload_doc();
                        //           } else if(r.message['status'] == 'error') {
                        //               frappe.show_alert({
                        //                   message: r.message['message'],
                        //                   indicator:'red'
                        //               }, 15);
                        //           }
                        //       }
                        //   })
                      }, () => {
                              // Action to perform if No is selected
                          }
                      );
                });
              } else if(r.message['status'] == 'error') {
                  frappe.show_alert({
                      message: r.message['message'],
                      indicator:'red'
                  }, 15);
              }
          }
        })
        // frm.add_custom_button(("Create Picklist"),()=>{
        //     frappe.call({
        //         method : 'customs_management.api.create_pick_list_frm_matrq',
        //         freeze:true,
        //         freeze_message:"Generating Pick List...",
        //         args: {
        //             doc:frm.doc,
                    
        //         },
        //         callback:function(resp){
        //             console.log(resp)
        //             if (resp.message){
        //                 frappe.show_alert("Pick List Created Successfully",5)
        //             }
        //         }
        //     })
        // })
        
        // if (frm.doc.docstatus === 1) {
        //     frm.add_custom_button(("Update Ordered %"), () => {
        //         frappe.confirm(
        //             '<b>Are you sure you want to proceed?</b><br>Selecting "Yes" will check if all stock entries linked to this material request have been submitted and set document status to "Transferred".<br>Select "No" to cancel.',
        //             () => {
        //                 frappe.call({
        //                     method : 'customs_management.api.update_ordered_percentage',
        //                     freeze:true,
        //                     freeze_message:"Updating Percentage...",
        //                     args: {
        //                         material_request:frm.doc.name,
        //                     },
        //                     callback: (r) => {
        //                         if(r.message['status'] == 'success') {
        //                             frappe.show_alert({
        //                                 message: r.message['message'],
        //                                 indicator:'green'
        //                             }, 5);
        //                             frm.reload_doc();
        //                         } else if(r.message['status'] == 'error') {
        //                             frappe.show_alert({
        //                                 message: r.message['message'],
        //                                 indicator:'red'
        //                             }, 15);
        //                         }
        //                     }
        //                 })
        //             }, () => {
        //                     // Action to perform if No is selected
        //                 }
        //             );
        //         }
        //     );
        
        // }
    }


})
