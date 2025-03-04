
frappe.ui.form.on('Pick List', {
    refresh: function(frm) {
        if(frm.doc.workflow_state === 'Draft') {
            frm.add_custom_button(('Split Picklist'), function() {
                frappe.confirm('Are you sure you want to proceed? Current Pick List will be split and then deleted.',
                    () => {
                        frappe.call({
                            method: 'customs_management.api.create_grouping_picklist',
                            freeze: true,
                            freeze_message:'Generating Pick Lists...',
                            args: {
                                self: frm.doc.name,
                                doctype: frm.doc.doctype
                            },
                            callback:function(resp) {
                                if(resp.message) {
                                    frappe.show_alert('Pick Lists Created Successfully',5)
                                }
                            }
                        });
                    }, () => {
                        // action to perform if No is selected
                    }
                );
            });
        }
    }
});