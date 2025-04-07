frappe.listview_settings['Invoice Verification'] = {
    hide_name_column: true,
    has_indicator_for_draft: true,

    get_indicator: function(doc) {
        const status_colors = {
            "Unverified": "yellow",           
            "Verified": "green"
        };
        console.log(status_colors)
      return [__(doc.status), status_colors[doc.status], "status,=,"+doc.status];
    }
}