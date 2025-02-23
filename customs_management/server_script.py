import frappe
from datetime import datetime
import time

@frappe.whitelist()
def clock_in_out():
    # employee_id = frappe.form_dict['employee_id']
    employee_id='JE10516'

    current_date = frappe.utils.today()
        
    start_of_day = f'{current_date} 00:00:00'
        
    end_of_day = f'{current_date} 23:59:59'

    try:
        employee_exists = bool(frappe.db.exists('Employee', employee_id))
        
        if employee_exists:
            emp=frappe.get_doc("Employee",employee_id)
            
            existing_check_ins = frappe.db.get_list('Employee Checkin',  filters=[['time', 'between', [start_of_day, end_of_day]], ['employee', '=', employee_id]], fields=['log_type'])
            
            check_in = {}
            print("emp def shift",emp.default_shift)
            in_or_out = ''
            if len(existing_check_ins) == 0:
                check_in = frappe.new_doc('Employee Checkin')
                check_in.employee = employee_id
                check_in.log_type = 'IN'
                check_in.time = frappe.utils.now()
                check_in.shift=emp.default_shift
                employee_checkin = check_in.insert()
                # check_in.save(ignore_permissions=True)
                in_or_out = 'in'
            elif existing_check_ins[-1]['log_type'] == 'IN':
                check_in = frappe.new_doc('Employee Checkin')
                check_in.employee = employee_id
                check_in.log_type = 'OUT'
                check_in.shift=emp.default_shift
                employee_checkin = check_in.insert()
                # check_in.save(ignore_permissions=True)
                check_in.time = frappe.utils.now()
                in_or_out = 'out'
            elif existing_check_ins[-1]['log_type'] == 'OUT':
                check_in = frappe.new_doc('Employee Checkin')
                check_in.employee = employee_id
                check_in.log_type = 'IN'
                check_in.time = frappe.utils.now()
                check_in.shift=emp.default_shift
                employee_checkin = check_in.insert()
                # check_in.save(ignore_permissions=True)
                in_or_out = 'in'
            
            employee_name = frappe.db.get_value('Employee', employee_id, ['employee_name'])
            frappe.response['data'] = f'{employee_name} has clocked {in_or_out} for {check_in.time}'
        else:
            frappe.response['msg'] = 'Invalid Employee ID.'
    except Exception as e:
        frappe.response['msg'] = f'Something went wrong, please try again. {e}'

@frappe.whitelist()
def create_check_in():
    check_in=frappe.get_doc({
    'doctype': 'Employee Checkin',
    })
    # check_in = frappe.new_doc('Employee Checkin')
    check_in.employee='JE10516'
    check_in.time =datetime.now()
    check_in.insert()
    print("unsaved",check_in.meta.__dict__)
 