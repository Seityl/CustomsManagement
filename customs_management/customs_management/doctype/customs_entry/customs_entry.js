// Copyright (c) 2023, Sudeep Kulkarni and contributors
// For license information, please see license.txt

frappe.ui.form.on('Customs Entry', {
	onload_post_render: function(frm) {
		if(frm.doc.__islocal) {
			frappe.call({
				method: 'get_default_additional_charges',
                freeze: true,
                freeze_message: 'Loading Default Additional Charges...',
				doc: frm.doc,
			});
		}
	},

    onload: function(frm) {
        // Hides Add Row button from additional_charges tables
        frm.get_field('additional_charges').grid.cannot_add_rows = true;
        // Hides Delete button from additional_charges tables
        frm.set_df_property('additional_charges', 'cannot_delete_rows', 1);
    },
    
	refresh: function(frm) {
        // Hides check boxes on child tables
        $('.row-check').hide();
        
		if(!frm.doc.__islocal) {
			frm.add_custom_button('Split up', function() {
				frappe.set_route(`app/print/Customs Entry/${frm.doc.name}`);
			});
		}

		if(frm.doc.docstatus == 0) {
			frm.add_custom_button('Get Items From', function() {
				var d = new frappe.ui.form.MultiSelectDialog({
					doctype: 'Purchase Receipt',
					target: frm,
					setters: {
						supplier_name: undefined,
						custom_invoice_number: undefined,
						grand_total: undefined,
					},
					add_filters_group: 1,
					get_query() {
						return {
							filters: {
								docstatus: ['=', 1],
								custom_customs_entry_created: ['=','0'],
								status: ['not in', ['Closed', 'Completed', 'Return Issued']]
							}
						}
					},
					size: 'large',
					action(selections) {
						if (selections) {
							frm.doc.purchases_list = JSON.stringify(selections)
							frm.refresh_field('purchases_list')
							frappe.call({
								method: 'get_receipt_item_data',
								doc: frm.doc,
								args: {
									selections: selections,
								},
								freeze: true,
								freeze_message: 'Loading Purchase Receipt Items...',
								callback: function (r) {
                                    frm.refresh();
                                    frm.dirty();
                                    frm.save();
								}
							});
						}
						d.dialog.hide();
					}
				});
			});
		}

		if(frm.doc.workflow_state == 'Approved' || frm.doc.workflow_state == 'Download XML') {
			frm.add_custom_button(__('Download XML'), function () {
				var w = window.open(
					frappe.urllib.get_full_url(
						'/api/method/customs_management.customs_management.doctype.customs_entry.customs_entry.generate_xml_file?' +
						'xml=' +
						encodeURIComponent(frm.doc.name) +
						'&name=' +
						encodeURIComponent(frm.doc.name)
					)
				);
				if(!w) {
					frappe.msgprint(__('Please enable pop-ups'));
					return;
				}
			});
		}

        // Custom HTML Item Details Table
        frm.fields_dict.items.grid.update_footer = function() {
            let table_rows = '';
            let row_count = frm.doc.items.length;
            let processed_rows = 0;

            // Function to render the table with subtle theme-aware styling
            let renderTable = (table_rows) => {
                // Hide the original grid wrapper and remove previous custom wrappers
                $(frm.fields_dict.items.grid.wrapper).hide();
                let parent = $(frm.fields_dict.items.grid.wrapper).parent();
                parent.find('.custom-items-display-wrapper').remove();

                parent.append(`
                    <div class="custom-items-display-wrapper" style="overflow-x: auto; width: 100%; margin-top: 15px; background-color: var(--card-bg, #fff);">
                        <h4 style="font-weight: bold; margin-bottom: 10px; color: var(--text-color, #333);">Item Details</h4>
                        <table class="table table-bordered custom-items-display" 
                            style="border-radius: 10px; border: 3px solid var(--border-color, #dee2e6); width: 100%; background-color: var(--card-bg, #fff); color: var(--text-color, #333);">
                            <thead style="background-color: var(--header-bg, #f8f9fa); color: var(--header-text, #333);">
                                <tr style="font-weight: bold; border-bottom: 3px solid var(--border-color, #dee2e6);">
                                    <th>Reference Doctype</th>
                                    <th>Reference Document</th>
                                    <th>Item</th>
                                    <th>Item ID</th>
                                    <th>Description</th>
                                    <th>Tariff Number</th>
                                    <th>Duty Exempt</th>
                                    <th>Factor</th>
                                    <th>Rate</th>
                                    <th>Base Rate (XCD)</th>
                                    <th>CIF</th>
                                    <th>Base CIF (XCD)</th>
                                    <th>Invoice Currency</th>
                                    <th>Invoice Conversion Rate</th>
                                    <th>Invoice Number</th>
                                    <th>Cost Center</th>
                                    <th>UOM</th>
                                    <th>Qty</th>
                                    <th>Stock Qty</th>
                                    <th>Additional Charges</th>
                                    <th>Base Additional Charges (XCD)</th>
                                    <th>Miscellaneous</th>
                                    <th>Taxable Amount</th>
                                    <th>Base Taxable Amount (XCD)</th>
                                    <th>Duty %</th>
                                    <th>Duty Amount</th>
                                    <th>Base Duty Amount (XCD)</th>
                                    <th>VAT %</th>
                                    <th>VAT Amount</th>
                                    <th>Base VAT Amount (XCD)</th>
                                    <th>Service %</th>
                                    <th>Service Amount</th>
                                    <th>Base Service Amount (XCD)</th>
                                    <th>Surcharge %</th>
                                    <th>Surcharge Amount</th>
                                    <th>Base Surcharge Amount (XCD)</th>
                                    <th>Excise %</th>
                                    <th>Excise Amount</th>
                                    <th>Base Excise Amount (XCD)</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${table_rows}
                            </tbody>
                        </table>
                    </div>
                `);
            };

            // Function to process each row
            let processRow = (row) => {
                table_rows += `
                    <tr>
                        <td>${row.reference_doctype || ''}</td>
                        <td>${row.reference_document || ''}</td>
                        <td>${row.item || ''}</td>
                        <td>${row.item_id || ''}</td>
                        <td>${row.description || ''}</td>
                        <td>${row.customs_tariff_number || ''}</td>
                        <td>${row.duty_exempt ? 'Yes' : 'No'}</td>
                        <td>${row.item_weight || '0.00'}</td>
                        <td>${row.rate || '0.00'}</td>
                        <td>${row.base_rate || '0.00'}</td>
                        <td>${row.amount || '0.00'}</td>
                        <td>${row.base_amount || '0.00'}</td>
                        <td>${row.ref_document_currency || ''}</td>
                        <td>${row.ref_document_conversion_rate || '0.00'}</td>
                        <td>${row.supplier_invoice_no || ''}</td>
                        <td>${row.cost_center || ''}</td>
                        <td>${row.uom || ''}</td>
                        <td>${row.qty || '0'}</td>
                        <td>${row.stock_qty || '0'}</td>
                        <td>${row.additional_charges || '0.00'}</td>
                        <td>${row.base_additional_charges || '0.00'}</td>
                        <td>${row.miscellaneous || '0.00'}</td>
                        <td>${row.taxable_amount || '0.00'}</td>
                        <td>${row.base_taxable_amount || '0.00'}</td>
                        <td>${row.duty_percent || '0'}</td>
                        <td>${row.duty_amount || '0.00'}</td>
                        <td>${row.base_duty_amount || '0.00'}</td>
                        <td>${row.vat_percent || '0'}</td>
                        <td>${row.vat_amount || '0.00'}</td>
                        <td>${row.base_vat_amount || '0.00'}</td>
                        <td>${row.service_charge_percent || '0'}</td>
                        <td>${row.service_charge_percentage || '0.00'}</td>
                        <td>${row.base_service_charge_percentage || '0.00'}</td>
                        <td>${row.surcharge_percent || '0'}</td>
                        <td>${row.surcharge_percentage || '0.00'}</td>
                        <td>${row.base_surcharge_percentage || '0.00'}</td>
                        <td>${row.excise_percent || '0'}</td>
                        <td>${row.excise_percentage || '0.00'}</td>
                        <td>${row.base_excise_percentage || '0.00'}</td>
                    </tr>
                `;

                processed_rows++;

                // Once all rows are processed, render the table
                if (processed_rows === row_count) {
                    renderTable(table_rows);
                }
            };

            // Process each row
            frm.doc.items.forEach(row => {
                processRow(row);
            });
        };

        frm.fields_dict.items.grid.update_footer();

        let description_cache = {};  // Cache to store fetched tariff number descriptions

        frm.fields_dict.tariff_breakdown.grid.update_footer = function() {
            // Group items by tariff number
            let groups = {};
            frm.doc.items.forEach(row => {
                let tariff_number = row.customs_tariff_number || 'Unknown';
                if (!groups[tariff_number]) {
                    groups[tariff_number] = [];
                }
                groups[tariff_number].push(row);
            });
        
            // Get all unique tariff numbers
            let tariffNumbers = Object.keys(groups);
            let table_rows = "";
            let processedGroups = 0;
        
            // Function to fetch tariff description for a tariff number
            let fetch_tariff_desc = (tariff_number, callback) => {
                if (description_cache[tariff_number]) {
                    callback(description_cache[tariff_number]);
                } else {
                    frappe.call({
                        method: "frappe.client.get_value",
                        freeze: true,
                        freeze_message: 'Loading Tariff Breakdown...',
                        args: {
                            doctype: "Customs Tariff Number",
                            filters: { name: tariff_number },
                            fieldname: "description"
                        },
                        callback: function(response) {
                            let description = response.message ? response.message.description : "No Description";
                            description_cache[tariff_number] = description;
                            callback(description);
                        }
                    });
                }
            };
        
            // Iterate over each unique tariff number group
            tariffNumbers.forEach(tariff_number => {
                fetch_tariff_desc(tariff_number, function(tariff_desc) {
                    // Add group header row
                    table_rows += `
                        <tr style="font-weight: bold; border-top: 3px solid var(--border-color, #dee2e6); background-color: var(--group-bg, #e9ecef); color: var(--group-text, #333); padding: 5px 0;">
                            <td colspan="5" style="text-align: center;">
                                DUTY GROUP - ${tariff_number} - ${tariff_desc}
                            </td>
                        </tr>
                    `;
                    let groupSubtotal = 0;
                    // Process each item in the current group
                    groups[tariff_number].forEach(row => {
                        let item_code = row.item || '';
                        let description = row.description || '';
                        let qty = row.qty || 0;
                        let uom = row.uom || '';
                        let base_amount = row.base_amount || 0;
                        groupSubtotal += base_amount;
                        table_rows += `
                            <tr>
                                <td>${item_code}</td>
                                <td>${description}</td>
                                <td>${qty}</td>
                                <td>${uom}</td>
                                <td style="text-align: right;">$ ${base_amount.toFixed(2)}</td>
                            </tr>
                        `;
                    });
                    // Add subtotal row for this group
                    table_rows += `
                        <tr style="font-weight: bold; border-top: 2px solid var(--border-color, #dee2e6);">
                            <td colspan="4" style="text-align: right;">SUBTOTAL :</td>
                            <td style="text-align: right;">$ ${groupSubtotal.toFixed(2)}</td>
                        </tr>
                    `;
                    processedGroups++;
                    if (processedGroups === tariffNumbers.length) {
                        renderTable(table_rows);
                    }
                });
            });
        
            // Function to render the final table
            let renderTable = (table_rows) => {
                $(frm.fields_dict.tariff_breakdown.grid.wrapper).hide();
                let parent = $(frm.fields_dict.tariff_breakdown.grid.wrapper).parent();
                parent.find('.custom-items-breakdown-display-wrapper').remove();
                parent.append(`
                    <div class="custom-items-breakdown-display-wrapper" style="overflow-x: auto; width: 100%; margin-top: 15px; background-color: var(--card-bg, #fff);">
                        <h4 style="font-weight: bold; margin-bottom: 10px; color: var(--text-color, #333);">Tariff Breakdown</h4>
                        <table class="table table-bordered custom-items-breakdown-display" 
                            style="min-width: 800px; border-radius: 10px; width: 100%; border: 5px solid var(--border-color, #dee2e6); background-color: var(--card-bg, #fff); color: var(--text-color, #333);">
                            <thead style="background-color: var(--header-bg, #f8f9fa); color: var(--header-text, #333);">
                                <tr style="font-weight: bold;">
                                    <th>Item Code</th>
                                    <th>Description</th>
                                    <th>Quantity</th>
                                    <th>UOM</th>
                                    <th style="text-align: right;">Amount (XCD)</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${table_rows}
                            </tbody>
                        </table>
                    </div>
                `);
            };
        };
        
        frm.fields_dict.tariff_breakdown.grid.update_footer();

        // Custom HTML Tariff Number Summary Table
        frm.fields_dict.tariff_number_summary.grid.update_footer = function() { 
            let total_base_duty_amount = 0;
            let table_rows = '';
            
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
                    total_base_duty_amount += row.base_duty_amount || 0;
                    
                    table_rows += `
                        <tr>
                            <td>${row.customs_tariff_number || ''}</td>
                            <td>${description || ''}</td>
                            <td>${row.duty_percentage.toFixed(2) || '0.00'} %</td>
                            <td>$ ${row.base_duty_amount.toFixed(2) || '$ 0.00'}</td>
                        </tr>
                    `;

                    processed_rows++;

                    // Once all rows are processed, render the table
                    if (processed_rows === row_count) {
                        renderTable(table_rows);
                    }
                });
            };

            // Process each row asynchronously
            frm.doc.tariff_number_summary.forEach(row => {
                processRow(row);
            });

            // Function to render the table with subtle styling for light and dark themes
            let renderTable = (table_rows) => {
                $(frm.fields_dict.tariff_number_summary.grid.wrapper).hide();
                let parent = $(frm.fields_dict.tariff_number_summary.grid.wrapper).parent();
                parent.find('.custom-tariff_number_summary-display-wrapper').remove();
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
                                    <th>Duty Amount (XCD)</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${table_rows}
                                <tr style="font-weight: bold; border-top: 3px solid var(--border-color, #dee2e6);">
                                    <td colspan="3" style="text-align: right;">Total :</td>
                                    <td>$ ${total_base_duty_amount.toFixed(2)}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                `);
            };
        };

        frm.fields_dict.tariff_number_summary.grid.update_footer();

        // Custom HTML Consolidation Table
        frm.fields_dict.consolidation.grid.update_footer = function() { 
            let base_total_fob = 0;
            let base_total_freight = 0;
            let base_total_insurance = 0;
            let base_total_cost = 0;
            let base_total_mass = 0;

            let table_rows = '';

            let fetch_invoice_no = (reference_document, callback) => {
                frappe.call({
                    method: "frappe.client.get_value",
                    freeze: true,
                    freeze_message: 'Loading Consolidation...',
                    args: {
                        doctype: "Purchase Receipt",
                        filters: { name: reference_document },
                        fieldname: "custom_invoice_number"
                    },
                    callback: function(response) {
                        let invoice_no = response.message ? response.message.custom_invoice_number : "N/A";
                        callback(invoice_no);
                    }
                });
            };

            let row_count = frm.doc.consolidation.length;
            let processed_rows = 0;

            frm.doc.consolidation.forEach(row => {
                base_total_fob += row.base_fob_price || 0;
                base_total_freight += row.freight_cost || 0;
                base_total_insurance += row.insurance_cost || 0;
                base_total_cost += row.total_cost || 0;
                base_total_mass += row.mass_kg || 0;

                fetch_invoice_no(row.reference_document, function(invoice_no) {
                    table_rows += `
                        <tr>
                            <td>${invoice_no}</td>
                            <td>${row.supplier_name || ''}</td>
                            <td>$ ${row.base_fob_price.toFixed(2) || '$ 0.00'}</td>
                            <td>$ ${row.freight_cost.toFixed(2) || '$ 0.00'}</td>
                            <td>$ ${row.insurance_cost.toFixed(2) || '$ 0.00'}</td>
                            <td>$ ${row.total_cost.toFixed(2) || '$ 0.00'}</td>
                            <td>${row.mass_kg.toFixed(2) || '0.00'} kg</td>
                        </tr>
                    `;

                    processed_rows++;

                    if (processed_rows === row_count) {
                        renderTable(table_rows);
                    }
                });
            });

            let renderTable = (table_rows) => {
                // Hide the original grid wrapper
                $(frm.fields_dict.consolidation.grid.wrapper).hide();
                let parent = $(frm.fields_dict.consolidation.grid.wrapper).parent();
                parent.find('.custom-consolidation-display-wrapper').remove();
                parent.append(`
                    <div class="custom-consolidation-display-wrapper" style="overflow-x: auto; width: 100%; margin-top: 15px; background-color: var(--card-bg, #fff);">
                        <h4 style="font-weight: bold; margin-bottom: 10px; color: var(--text-color, #333);">Consolidation</h4>
                        <table class="table table-bordered custom-consolidation-display" 
                            style="min-width: 800px; border-radius: 10px; width: 100%; 
                                border: 3px solid var(--border-color, #dee2e6); 
                                background-color: var(--card-bg, #fff); color: var(--text-color, #333);">
                            <thead style="background-color: var(--header-bg, #f8f9fa); color: var(--header-text, #333);">
                                <tr style="font-weight: bold; border-bottom: 3px solid var(--border-color, #dee2e6);">
                                    <th>Invoice No</th>
                                    <th>Supplier Name</th>
                                    <th>FOB Price (XCD)</th>
                                    <th>Freight Cost (XCD)</th>
                                    <th>Insurance Cost (XCD)</th>
                                    <th>Total Cost (XCD)</th>
                                    <th>Mass (kg)</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${table_rows}
                                <tr style="font-weight: bold; border-top: 3px solid var(--border-color, #dee2e6);">
                                    <td colspan="2" style="text-align: right;">Total :</td>
                                    <td>$ ${base_total_fob.toFixed(2)}</td>
                                    <td>$ ${base_total_freight.toFixed(2)}</td>
                                    <td>$ ${base_total_insurance.toFixed(2)}</td>
                                    <td>$ ${base_total_cost.toFixed(2)}</td>
                                    <td>${base_total_mass.toFixed(2)} kg</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                `);
            };
        };

        frm.fields_dict.consolidation.grid.update_footer();

        // Custom HTML Tax Info Table
        frm.fields_dict.tax_info.grid.update_footer = function() { 
            let table_rows = '';

            let total_base_duty = 0, total_base_vat = 0, total_base_service = 0, total_base_surcharge = 0, total_base_excise = 0;

            // Loop through each tax_info row and build the table rows
            frm.doc.tax_info.forEach(row => {
                total_base_duty += Number(row.base_duty) || 0;
                total_base_vat += Number(row.base_vat) || 0;
                total_base_service += Number(row.base_service) || 0;
                total_base_surcharge += Number(row.base_surcharge) || 0;
                total_base_excise += Number(row.base_excise) || 0;

                table_rows += `
                    <tr>
                        <td>${row.invoice || ''}</td>
                        <td style="text-align: right;">$ ${Number(row.base_duty).toFixed(2)}</td>
                        <td style="text-align: right;">$ ${Number(row.base_vat).toFixed(2)}</td>
                        <td style="text-align: right;">$ ${Number(row.base_service).toFixed(2)}</td>
                        <td style="text-align: right;">$ ${Number(row.base_surcharge).toFixed(2)}</td>
                        <td style="text-align: right;">$ ${Number(row.base_excise).toFixed(2)}</td>
                    </tr>
                `;
            });

            // Build the totals row; spanning first column with label "Total :"
            let totalsRow = `
                <tr style="font-weight: bold; border-top: 3px solid var(--border-color, #dee2e6);">
                    <td style="text-align: right;">Total :</td>
                    <td style="text-align: right;">$ ${total_base_duty.toFixed(2)}</td>
                    <td style="text-align: right;">$ ${total_base_vat.toFixed(2)}</td>
                    <td style="text-align: right;">$ ${total_base_service.toFixed(2)}</td>
                    <td style="text-align: right;">$ ${total_base_surcharge.toFixed(2)}</td>
                    <td style="text-align: right;">$ ${total_base_excise.toFixed(2)}</td>
                </tr>
            `;

            // Append the totals row to table_rows
            table_rows += totalsRow;

            // Render the complete table with subtle styling
            let renderTable = (table_rows) => {
                // Hide the original grid wrapper
                $(frm.fields_dict.tax_info.grid.wrapper).hide();

                // Remove any existing custom display wrapper
                let parent = $(frm.fields_dict.tax_info.grid.wrapper).parent();
                parent.find('.custom-tax-info-display-wrapper').remove();

                // Append the new custom HTML table
                parent.append(`
                    <div class="custom-tax-info-display-wrapper" style="overflow-x: auto; width: 100%; margin-top: 15px; background-color: var(--card-bg, #fff);">
                        <h4 style="font-weight: bold; margin-bottom: 10px; color: var(--text-color, #333);">Tax Info</h4>
                        <table class="table table-bordered custom-tax-info-display" 
                            style="min-width: 800px; border-radius: 10px; width: 100%; border: 3px solid var(--border-color, #dee2e6); background-color: var(--card-bg, #fff); color: var(--text-color, #333);">
                            <thead style="background-color: var(--header-bg, #f8f9fa); color: var(--header-text, #333);">
                                <tr style="font-weight: bold; border-bottom: 3px solid var(--border-color, #dee2e6);">
                                    <th>Invoice No.</th>
                                    <th>Duty (XCD)</th>
                                    <th>VAT (XCD)</th>
                                    <th>Service (XCD)</th>
                                    <th>Surcharge (XCD)</th>
                                    <th>Excise (XCD)</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${table_rows}
                            </tbody>
                        </table>
                    </div>
                `);
            };

            // Render the table after processing all rows
            renderTable(table_rows);
        };

        // Call the function to render Tax Info table on refresh
        frm.fields_dict.tax_info.grid.update_footer();
	},

	currency: function(frm) {
		frappe.call({
			method: "get_exchange_rate",
			doc: frm.doc,
			freeze: true,
			freeze_message: "Loading Currency...",
			callback: function(r) {
				frm.refresh_field("conversion_rate");
				frm.refresh_field("additional_charges");
			}
		});
    }
});