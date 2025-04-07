// Copyright (c) 2025, Jollys Pharmacy Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Invoice Verification', {
    before_save: async function (frm) {
        if (!frm.is_new()) {
            let validated = await frm.trigger('update_item_tariff_numbers');
            frappe.validated = validated;
        }
    },

    onload: function(frm) {
        if (!frm.is_new()) {
            frm.toggle_enable('reference_document', false);
        }
        // Hides Add Row button from items tables
        frm.get_field('items').grid.cannot_add_rows = true;
        // Hides Delete button from items tables
        frm.set_df_property('items', 'cannot_delete_rows', 1);
        
        frm.set_query('reference_document', () => {
            return {
                filters: {
                    custom_invoice_verification_created: 0,
                    custom_invoice_number: ['is', 'set'],
                    docstatus: 1
                }
            };
        });
    },
    
    refresh: function (frm) {
        if (!frm.is_new()) {
            frm.toggle_enable('reference_document', false);
        }
        
        // Hides check boxes on child tables
        $('.row-check').hide();

        if (!frm.is_new()) {
            if (frm.is_dirty()) {
                frm.reload_doc().then(() => {
                    if (frm.is_dirty()) {
                        frm.save()
                    }
                });
            }
        }

        if (!frm.doc.__islocal) {
            frm.add_custom_button(__("Go to Split up"), function () {
                frappe.set_route(`app/print/Invoice Verification/${frm.doc.name}`);
            });
        }

        // Custom HTML Tariff Number Summary Table

        let description_cache = {};  // Cache to store fetched tariff number descriptions

        frm.fields_dict.tariff_number_summary.grid.update_footer = function() { 
            let total_duty_amount = 0;
            let table_rows_array = [];  // Store table rows as objects instead of concatenating strings

            let fetch_tariff_desc = (tariff_number, callback) => {
                // Check cache first
                if (description_cache[tariff_number]) {
                    callback(description_cache[tariff_number]);
                } else {
                    frappe.call({
                        method: "frappe.client.get_value",
                        freeze: true,
                        freeze_message: 'Loading Tariff Number Summary...',
                        args: {
                            doctype: "Customs Tariff Number",
                            filters: { name: tariff_number },
                            fieldname: "description"
                        },
                        callback: function(response) {
                            let description = response.message ? response.message.description : "No Description";
                            description_cache[tariff_number] = description;  // Store in cache
                            callback(description);
                        }
                    });
                }
            };

            let row_count = frm.doc.tariff_number_summary.length;
            let processed_rows = 0;

            let processRow = (row) => {
                fetch_tariff_desc(row.customs_tariff_number, function(description) {
                    total_duty_amount += row.duty_amount || 0;
                    
                    // Store row as an object for sorting later
                    table_rows_array.push({
                        customs_tariff_number: row.customs_tariff_number || '',
                        description: description || '',
                        duty_percentage: row.duty_percentage.toFixed(2) || '0.00',
                        duty_amount: row.duty_amount || 0  // Store as number for sorting
                    });

                    processed_rows++;

                    // Once all rows are processed, sort and render the table
                    if (processed_rows === row_count) {
                        // Sort by highest total duty amount
                        table_rows_array.sort((a, b) => b.duty_amount - a.duty_amount);
                        renderTable();
                    }
                });
            };

            // Process each row asynchronously
            frm.doc.tariff_number_summary.forEach(row => {
                processRow(row);
            });

            // Function to render the table with sorted data
            let renderTable = () => {
                $(frm.fields_dict.tariff_number_summary.grid.wrapper).hide();
                let parent = $(frm.fields_dict.tariff_number_summary.grid.wrapper).parent();
                parent.find('.custom-tariff_number_summary-display-wrapper').remove();
                
                let table_rows = table_rows_array.map(row => `
                    <tr>
                        <td>${row.customs_tariff_number}</td>
                        <td>${row.description}</td>
                        <td>${row.duty_percentage} %</td>
                        <td>$ ${row.duty_amount.toFixed(2)}</td>
                    </tr>
                `).join('');

                parent.append(`
                    <div class="custom-tariff_number_summary-display-wrapper" style="overflow-x: auto; width: 100%; margin-top: 15px; background-color: var(--card-bg, #fff);">
                        <h4 style="font-weight: bold; margin-bottom: 10px; color: var(--text-color, #333);">Tariff Number Summary</h4>
                        <table class="table table-bordered custom-tariff_number_summary-display" 
                            style="min-width: 800px; border-radius: 10px; width: 100%; 
                                    border: 3px solid var(--border-color, #dee2e6); 
                                    background-color: var(--card-bg, #fff); color: var(--text-color, #333);">
                            <thead style="background-color: var(--header-bg, #f8f9fa); color: var(--header-text, #333);">
                                <tr style="font-weight: bold; border-bottom: 3px solid var(--border-color, #dee2e6);">
                                    <th>Tariff Number</th>
                                    <th>Description</th>
                                    <th>Duty %</th>
                                    <th>Duty Amount</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${table_rows}
                                <tr style="font-weight: bold; border-top: 3px solid var(--border-color, #dee2e6);">
                                    <td colspan="3" style="text-align: right;">Total :</td>
                                    <td>$ ${total_duty_amount.toFixed(2)}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                `);
            };
        };

        frm.fields_dict.tariff_number_summary.grid.update_footer();
    },
    
    reference_document: function (frm) {
        if (frm.doc.reference_document) {
            frappe.call({
                method: "get_items",
                doc: frm.doc,
                callback: function (r) {
                    frm.refresh_field('items');
                    frm.refresh_field('currency');
                    frm.refresh_field('item_count');
                    frm.refresh_field('total_item_qty');
                    frm.refresh_field('tariff_number_summary');
                    // $('.row-check').hide();
                }
            });
        }
    },
    
    date_item_tariff_numbers: function (frm) {
        return new Promise((resolve, reject) => {
            frappe.call({
                method: "update_item_tariff_numbers",
                doc: frm.doc,
                freeze: true,
                freeze_message: "Updating item tariff numbers...",
                callback: function (r) {
                    let d = new frappe.ui.Dialog({
                        title: '<b>Add Tariff Number</b>',
                        fields: [
                            {
                                label: 'Tariff Number',
                                fieldname: 'tariff_number',
                                fieldtype: 'Data',
                                reqd: 1
                            },
                            {
                                label: 'Description',
                                fieldname: 'description',
                                fieldtype: 'Data',
                                reqd: 1
                            },
                            {
                                label: '',
                                fieldname: 'section_break1',
                                fieldtype: 'Section Break',
                            },
                            {
                                label: 'Precision',
                                fieldname: 'custom_precision',
                                fieldtype: 'Int',
                                default: '00',
                                reqd: 1
                            },
                            {
                                label: 'Markup Percentage',
                                fieldname: 'custom_markup_percentage',
                                fieldtype: 'Percent',
                            },
                            {
                                label: 'Surcharge Percentage',
                                fieldname: 'custom_surcharge_percentage',
                                fieldtype: 'Percent',
                            },
                            {
                                label: 'Excise Percentage',
                                fieldname: 'custom_excise_percentage',
                                fieldtype: 'Percent',
                            },
                            {
                                label: '',
                                fieldname: 'column_break1',
                                fieldtype: 'Column Break',
                            },
                            {
                                label: 'Duty Percentage',
                                fieldname: 'custom_duty_percentage',
                                fieldtype: 'Percent',
                            },
                            {
                                label: 'VAT Percentage',
                                fieldname: 'custom_vat_percentage',
                                fieldtype: 'Percent',
                                default: 15,
                                reqd: 1
                            },
                            {
                                label: 'Service Charge Percentage',
                                fieldname: 'custom_service_charge_percentage',
                                fieldtype: 'Percent',
                            }
                        ],
                        size: 'small',
                        primary_action_label: '<b>Add</b>',
                        primary_action(values) {
                            frappe.call({
                                method: "create_tariff_number",
                                doc: frm.doc,
                                args: { 'values' : values },
                                freeze: true,
                                freeze_message: "Creating tariff number...",
                                callback: function (r) {
                                    if (r.message['status'] === 'success') {
                                        frappe.show_alert({
                                            message: r.message['message'],
                                            indicator:'green'
                                        }, 10);
                                        d.hide();
                                        frm.trigger('update_item_tariff_numbers');     
                                    }
                                }
                            });
                        }
                    });
                    if (r.message['status'] === 'error') {
                        frappe.show_alert({
                            message: r.message['message'],
                            indicator: 'red'
                        }, 10);
                        d.set_value('tariff_number', r.message['customs_tariff_number']);
                        d.show();
                        resolve(false);
                    } else {
                        d.hide();
                        frm.trigger('reference_document');
                        resolve(true);
                    }
                }
            });
        });
    },
});

