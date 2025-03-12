frappe.listview_settings['Costing'] = {
    hide_name_column: true
}

function extend_listview_event(doctype, event, callback) {
    if (!frappe.listview_settings[doctype]) {
        frappe.listview_settings[doctype] = {};
    }

    const old_event = frappe.listview_settings[doctype][event];
    frappe.listview_settings[doctype][event] = function (listview) {
        if (old_event) {
            old_event(listview);
        }
        callback(listview);
    };
}

extend_listview_event("Costing", "refresh", function (listview) {
    $(document).ready(function() {
        $('span[data-filter="workflow_state,=,Draft"]').each(function() {
            $(this).removeClass('red').addClass('gray');
        });
    });
    $(document).ready(function() {
        $('span[data-filter="workflow_state,=,Costed"]').each(function() {
            $(this).removeClass('gray').addClass('yellow');
        });
    });
    $(document).ready(function() {
        $('span[data-filter="workflow_state,=,Approved"]').each(function() {
            $(this).removeClass('gray').addClass('green');
        });
    });
    $(document).ready(function() {
        $('span[data-filter="workflow_state,=,Priced"]').each(function() {
            $(this).removeClass('gray').addClass('blue');
        });
    });
    $(document).ready(function() {
        $('span[data-filter="workflow_state,=,Cancelled"]').each(function() {
            $(this).removeClass('gray').addClass('red');
        });
    });
});