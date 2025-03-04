frappe.ui.form.on('Material Request',{
    refresh: function(frm) {
        frm.add_custom_button(('Split Material Request'), function() {
            frappe.confirm('Are you sure you want to proceed? Current Material Request will be split and then deleted.',
                () => {
                    frappe.call({
                        method: 'customs_management.api.split_mat_req',
                        freeze: true,
                        freeze_message: 'Splitting Material Request...',
                        args: { name: frm.doc.name }
                    });
                }, () => {
                    // action to perform if No is selected
                }
            );
        });
    }
});