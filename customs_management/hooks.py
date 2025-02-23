from . import __version__ as app_version

app_name = "customs_management"
app_title = "Customs Management"
app_publisher = "Sudeep Kulkarni"
app_description = "Customs Management"
app_email = "asoral@dexiss.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "public/css/custom.css"
# app_include_js = "/assets/customs_management/js/customs_management.js"

# include js, css files in header of web template
# web_include_css = "/assets/customs_management/css/customs_management.css"
# web_include_js = "/assets/customs_management/js/customs_management.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "customs_management/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"HD Ticket": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {"Customs Tariff Number" : "public/js/custom_Customs Tariff Number.js",
              "Pick List" : "public/js/custom_Pick List.js",
              "Sales Order": "public/js/custom_Sales Order.js",
              "Sales Invoice": "public/js/custom_Sales Invoice.js",
              "Material Request": "public/js/custom_Material Request.js",
              "Overtime Request":"public/js/custom_Otr.js",
              "Salary Slip":"public/js/Salary Slip.js",
              }
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
jinja = {
	"methods": [
        # "customs_management.customs_management.doctype.customs_entry.customs_entry.get_unique_invoice",
        # "customs_management.customs_management.doctype.customs_entry.customs_entry.get_document_count",
        # "customs_management.customs_management.doctype.customs_entry.customs_entry.get_currency_symbol",
        "customs_management.api.my_function",
        "customs_management.api.my_function1",
        "customs_management.api.get_tax_info",
        "customs_management.api.additional_charges",
        "customs_management.api.additional_curr",
        "customs_management.api.tariff_application_data",
        "customs_management.api.get_asycuda_no",
        "customs_management.api.custom_entry_print_data",
        "customs_management.api.add_tofob",
    ]
	# "filters": "customs_management.utils.jinja_filters"
}


# Installation
# ------------

# before_install = "customs_management.install.before_install"
# after_install = "customs_management.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "customs_management.uninstall.before_uninstall"
# after_uninstall = "customs_management.uninstall.after_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "customs_management.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
#	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
#	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
#	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
#	"*": {
#		"on_update": "method",
#		"on_cancel": "method",
#		"on_trash": "method"
#	}
# }

doc_events = {
	"Pick List": {
		"before_save": "customs_management.api.sort_pick_list",
		# "on_submit": "customs_management.api.create_grouping",
		
	},
    "Purchase Receipt":{
        "on_submit": "customs_management.api.create_tariffapp",
        "on_update_after_submit": "customs_management.api.create_tariffapp",
    },
    "Purchase Invoice":{
        "on_submit": "customs_management.api.create_tariffapp",
        "on_update_after_submit": "customs_management.api.create_tariffapp",
    },
    "Salary Slip":{
        "before_save": "customs_management.api.calculate_working_salaryslip",
        
    },
     "Stock Entry":{
        "on_submit": "customs_management.api.set_stock_status",
        
    },
    "Landed Cost Voucher":{
        "on_submit":"customs_management.api.fix_taxes_and_charges"
    }
	
}

# Scheduled Tasks
# ---------------

scheduler_events = {
#	"all": [
#		"customs_management.tasks.all"
#	],
#	"daily": [
#		"customs_management.tasks.daily"
#	],
#	"hourly": [
#		"customs_management.tasks.hourly"
#	],
#	"weekly": [
#		"customs_management.tasks.weekly"
#	],
#	"monthly": [
#		"customs_management.tasks.monthly"
#	],
	"cron": {
        "*/3 * * * *": [
            # "customs_management.api.create_sales_invoice",
            # "customs_management.api.schedule_create_sales_invoice",
            # "customs_management.api.schedule_create_sales_invoice_from_ticket"

        ],
        "0 0 * * *": [
            "customs_management.api.send_outstanding_material_request_emails"
        ],
        # "0 14 * * *": [
        #   "customs_management.api.schedule_reorder_item"
        # ]
    }
}

# Testing
# -------

# before_tests = "customs_management.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
#	"frappe.desk.doctype.event.event.get_events": "customs_management.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
#	"Task": "customs_management.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["customs_management.utils.before_request"]
# after_request = ["customs_management.utils.after_request"]

# Job Events
# ----------
# before_job = ["customs_management.utils.before_job"]
# after_job = ["customs_management.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
#	{
#		"doctype": "{doctype_1}",
#		"filter_by": "{filter_by}",
#		"redact_fields": ["{field_1}", "{field_2}"],
#		"partial": 1,
#	},
#	{
#		"doctype": "{doctype_2}",
#		"filter_by": "{filter_by}",
#		"partial": 1,
#	},
#	{
#		"doctype": "{doctype_3}",
#		"strict": False,
#	},
#	{
#		"doctype": "{doctype_4}"
#	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
#	"customs_management.auth.validate"
# ]

# fixtures = [{
#   'doctype': 'Custom Field',
#   'filters': {
#   'name': ['in', ('Company-custom_code')]
#    }
# }]

# fixtures = [{
#   'doctype': 'Custom Field',
#   'filters': {
#     'name': ['in', 'Company-custom_code' ,'Item-custom_commodity_code']
#    }
# }]

fixtures = [
		{"dt":"Custom Field", "filters": [["name", "in",(
            "Company-custom_code",
            "Landed Cost Taxes and Charges-custom_type",
            "Purchase Receipt-custom_tariff_application_created",
            "Purchase Invoice-custom_tariff_application_created",
            "Purchase Receipt-custom_customs_entry_created",
            "Purchase Invoice-custom_customs_entry_created",
            "Customs Tariff Number-custom_tariff_details",
            "Customs Tariff Number-custom_duty_percentage",
            "Customs Tariff Number-custom_service_charge_percentage",
            "Customs Tariff Number-custom_column_break_hi4h3",
            "Customs Tariff Number-custom_vat_percentage",
            "Customs Tariff Number-custom_custom_cost_details",
            "Customs Tariff Number-custom_surcharge_percentage",
            "Customs Tariff Number-custom_column_break_lsdr6",
            "Customs Tariff Number-custom_markup_percentage",
            "Customs Tariff Number-custom_excise_percentage",
            "Pick List-custom_item_group",
            "Purchase Receipt-custom_invoice_number",
            "Purchase Invoice-custom_invoice_number",
            "Customs Tariff Number-custom_precision",
            "Sales Invoice-custom_ticket",
            "Sales Invoice-custom_customs_clearence_office",
            "Sales Invoice-custom_declaration_procedure",
            "Sales Invoice-custom_extended_customs",
            "Sales Invoice-custom_country_first_destination",
            "Sales Invoice-custom_country_of_origin",
            "Sales Invoice-custom_column_break_evlqw",
            "Sales Invoice-custom_transport_service",
            "Sales Invoice-custom_number_of_packages",
            "Sales Invoice-custom_package_type",
            "Sales Invoice-custom_gross_weight",
            "Sales Invoice-custom_export",
            "Sales Invoice-custom_national_customs_procedure",
            "Sales Invoice-custom_invoice_number",
            "Sales Invoice-custom_xml",
            "Pick List-custom_edit_item",
            "Salary Structure-custom_salary_slip_based_on_worked_hours",
            "Salary Structure Assignment-custom_hourly_rate",
            "Salary Structure Assignment-custom_company_currency",
            "Salary Slip-custom_hours_worked",
            "Employee Grade-custom_hd_multiplier",
            "Overtime Request-custom_manual_ot_type",
            "Overtime Request-custom_ot_multiplier_type",

            "Landed Cost Taxes and Charges-custom_foreign_currency",

            "Material Request-custom_auto_reorder"
        )]]},

        {"dt":"Property Setter", "filters": [["name", "in",(
            "Purchase Receipt-main-title_field",
            "Purchase Receipt-main-show_title_field_in_link",
            "Purchase Invoice-main-title_field",
            "Purchase Invoice-main-show_title_field_in_link",
            "Tariff Application-main-default_print_format",
            "Shipment Clearing-main-default_print_format",
        )]]}
]

# fixtures = [“Workflow”,“Workflow State”,“Print Format”,“Notification”,“Workflow Action Master”,
#   {
#     “dt”: “Custom Field”,
#     “filters”: [
#             [
#             “name”, “in”, [“Purchase Order-registration_type”,
#             “Purchase Order-mode_of_transport”,
#             “Purchase Order-supplier_gstin”,
#             “Purchase Order-place_of_supply”,
#             “Purchase Order-company_gstin”,
#             “Purchase Order-remarks”,
#             “Purchase Order-authorised_signatory”,
#             “Sales Order-remarks”,
#             “Sales Invoice-authorised_signatory”,
#             “Sales Invoice-remarks”,
#             “Address-cin_no”,
#             “Purchase Receipt-authorised_signatory”,
#             “Purchase Receipt-mode_of_transport”,
#             “Delivery Note-authorised_signatory”,
#             ]
#           ]
#     ]
#   }
# ]

# override_doctype_dashboards = {
# 	"Sales Order": "nextproject.nextproject.custom_sales_order_dashboard.get_data",
# 	"Project": "nextproject.nextproject.custom_project_dashboard.get_data",
# 	"Task": "nextproject.nextproject.custom_task_dashboard.get_data",
# 	"Sales Invoice":"nextproject.nextproject.custom_sales_invoice_dashboard.get_data",
#     "HD Ticket":"nextproject.custom_hd_ticket_dashboard.get_data"
# }
