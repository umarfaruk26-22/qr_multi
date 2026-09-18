import csv
import io
import re
from datetime import datetime, date
from database.connection import get_db_connection

def validate_phone(phone_str):
    """Simple phone cleaner and validator."""
    if not phone_str:
        return False
    # Check if there are at least 7 digits
    digits = re.sub(r'\D', '', str(phone_str))
    return len(digits) >= 7

def validate_email(email_str):
    """Simple email regex validator."""
    if not email_str:
        return False
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return bool(re.match(email_regex, str(email_str).strip()))

def parse_date_safe(date_val):
    """Safely parse date string into YYYY-MM-DD or None."""
    if not date_val:
        return None
    val = str(date_val).strip()
    if not val:
        return None
    for fmt in ('%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%m/%d/%Y'):
        try:
            return datetime.strptime(val, fmt).date()
        except ValueError:
            pass
    return None


def create_lead(employee_id, data, ip_address='', user_agent='', source='direct_web'):
    """
    Creates a new visitor lead record.
    Mandatory: name, phone, email
    Optional: dob, anniversary, city
    """
    if not employee_id:
        raise ValueError("Employee ID is required.")

    name = str(data.get('name', '')).strip()
    phone = str(data.get('phone', '')).strip()
    email = str(data.get('email', '')).strip().lower()
    
    if not name:
        raise ValueError("Full Name is required.")
    if not phone:
        raise ValueError("Mobile Number is required.")
    if not email:
        raise ValueError("Email Address is required.")
        
    if not validate_phone(phone):
        raise ValueError("Please provide a valid mobile number.")
    if not validate_email(email):
        raise ValueError("Please provide a valid email address.")

    dob = parse_date_safe(data.get('dob'))
    anniversary = parse_date_safe(data.get('anniversary'))
    city = str(data.get('city', '')).strip() or None

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Verify employee exists and is active
        cursor.execute("SELECT id, first_name, last_name, slug FROM employees WHERE id = %s AND is_deleted = 0", (employee_id,))
        emp = cursor.fetchone()
        if not emp:
            raise ValueError("Invalid employee profile.")

        cursor.execute(
            """
            INSERT INTO visitor_leads (
                employee_id, name, phone, email, dob, anniversary, city, source, ip_address, user_agent
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                employee_id, name, phone, email, dob, anniversary, city,
                source or 'direct_web', ip_address or '', user_agent or ''
            )
        )
        conn.commit()
        lead_id = cursor.lastrowid
        
        return {
            'id': lead_id,
            'employee_id': employee_id,
            'employee_name': f"{emp['first_name']} {emp['last_name']}".strip(),
            'employee_slug': emp['slug'],
            'name': name,
            'phone': phone,
            'email': email,
            'dob': dob.isoformat() if dob else None,
            'anniversary': anniversary.isoformat() if anniversary else None,
            'city': city
        }
    finally:
        cursor.close()
        conn.close()


def get_leads(search='', employee_id=None, page=1, per_page=20):
    """
    Retrieves paginated visitor leads with joined employee profile info.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        conditions = []
        params = []

        if employee_id:
            try:
                emp_id_int = int(employee_id)
                conditions.append("vl.employee_id = %s")
                params.append(emp_id_int)
            except (ValueError, TypeError):
                pass

        if search:
            s = f"%{search.strip()}%"
            conditions.append("(vl.name LIKE %s OR vl.phone LIKE %s OR vl.email LIKE %s OR vl.city LIKE %s OR e.first_name LIKE %s OR e.last_name LIKE %s)")
            params.extend([s, s, s, s, s, s])

        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

        # Total Count
        count_sql = f"""
            SELECT COUNT(*) AS total 
            FROM visitor_leads vl
            JOIN employees e ON vl.employee_id = e.id
            {where_clause}
        """
        cursor.execute(count_sql, tuple(params))
        total = cursor.fetchone()['total']

        # Pagination
        page = max(1, int(page))
        per_page = max(1, int(per_page))
        offset = (page - 1) * per_page
        pages = max(1, (total + per_page - 1) // per_page)

        query_sql = f"""
            SELECT 
                vl.id,
                vl.employee_id,
                vl.name,
                vl.phone,
                vl.email,
                vl.dob,
                vl.anniversary,
                vl.city,
                vl.source,
                vl.ip_address,
                vl.created_at,
                e.first_name AS emp_first_name,
                e.last_name AS emp_last_name,
                e.slug AS emp_slug,
                e.designation AS emp_designation,
                e.profile_image AS emp_image
            FROM visitor_leads vl
            JOIN employees e ON vl.employee_id = e.id
            {where_clause}
            ORDER BY vl.created_at DESC
            LIMIT %s OFFSET %s
        """
        exec_params = list(params) + [per_page, offset]
        cursor.execute(query_sql, tuple(exec_params))
        leads = cursor.fetchall()

        return {
            'leads': leads,
            'total': total,
            'page': page,
            'pages': pages,
            'per_page': per_page
        }
    finally:
        cursor.close()
        conn.close()


def get_lead_summary():
    """
    Returns aggregated KPIs and per-employee breakdown of visitor leads.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Total leads
        cursor.execute("SELECT COUNT(*) AS total FROM visitor_leads")
        total_leads = cursor.fetchone()['total']

        # Leads today
        cursor.execute("SELECT COUNT(*) AS today_count FROM visitor_leads WHERE DATE(created_at) = CURDATE()")
        today_leads = cursor.fetchone()['today_count']

        # Leads this month
        cursor.execute("SELECT COUNT(*) AS month_count FROM visitor_leads WHERE YEAR(created_at) = YEAR(CURDATE()) AND MONTH(created_at) = MONTH(CURDATE())")
        month_leads = cursor.fetchone()['month_count']

        # Unique employees visited
        cursor.execute("SELECT COUNT(DISTINCT employee_id) AS visited_employees FROM visitor_leads")
        visited_employees_count = cursor.fetchone()['visited_employees']

        # Employee breakdown ("Kitne logo ne kisko visit kiya")
        cursor.execute(
            """
            SELECT 
                e.id AS employee_id,
                e.first_name,
                e.last_name,
                e.slug,
                e.designation,
                e.profile_image,
                e.is_active,
                COUNT(vl.id) AS lead_count,
                MAX(vl.created_at) AS last_lead_at
            FROM employees e
            LEFT JOIN visitor_leads vl ON e.id = vl.employee_id
            WHERE e.is_deleted = 0
            GROUP BY e.id, e.first_name, e.last_name, e.slug, e.designation, e.profile_image, e.is_active
            ORDER BY lead_count DESC, e.first_name ASC
            """
        )
        employee_breakdown = cursor.fetchall()

        return {
            'total_leads': total_leads,
            'today_leads': today_leads,
            'month_leads': month_leads,
            'visited_employees_count': visited_employees_count,
            'employee_breakdown': employee_breakdown
        }
    finally:
        cursor.close()
        conn.close()


def get_recent_leads(limit=10):
    """
    Returns the most recent visitor leads for admin dashboard widgets.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT 
                vl.id,
                vl.employee_id,
                vl.name,
                vl.phone,
                vl.email,
                vl.city,
                vl.created_at,
                e.first_name AS emp_first_name,
                e.last_name AS emp_last_name,
                e.slug AS emp_slug
            FROM visitor_leads vl
            JOIN employees e ON vl.employee_id = e.id
            ORDER BY vl.created_at DESC
            LIMIT %s
            """,
            (limit,)
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def delete_lead(lead_id):
    """
    Deletes a single visitor lead.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM visitor_leads WHERE id = %s", (lead_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        cursor.close()
        conn.close()


def export_leads_csv(employee_id=None, search=''):
    """
    Exports visitor leads into CSV format string.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        conditions = []
        params = []

        if employee_id:
            try:
                emp_id_int = int(employee_id)
                conditions.append("vl.employee_id = %s")
                params.append(emp_id_int)
            except (ValueError, TypeError):
                pass

        if search:
            s = f"%{search.strip()}%"
            conditions.append("(vl.name LIKE %s OR vl.phone LIKE %s OR vl.email LIKE %s OR vl.city LIKE %s OR e.first_name LIKE %s OR e.last_name LIKE %s)")
            params.extend([s, s, s, s, s, s])

        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

        query_sql = f"""
            SELECT 
                vl.id AS Lead_ID,
                vl.created_at AS Visited_Date_Time,
                CONCAT(e.first_name, ' ', e.last_name) AS Visited_Employee,
                e.designation AS Employee_Designation,
                vl.name AS Visitor_Name,
                vl.phone AS Visitor_Phone,
                vl.email AS Visitor_Email,
                vl.dob AS Date_Of_Birth,
                vl.anniversary AS Anniversary_Date,
                vl.city AS City,
                vl.source AS Visit_Source,
                vl.ip_address AS IP_Address
            FROM visitor_leads vl
            JOIN employees e ON vl.employee_id = e.id
            {where_clause}
            ORDER BY vl.created_at DESC
        """
        cursor.execute(query_sql, tuple(params))
        rows = cursor.fetchall()

        output = io.StringIO()
        # UTF-8 BOM for Microsoft Excel auto-detect
        output.write('\ufeff')

        if rows:
            formatted_rows = []
            for r in rows:
                formatted_rows.append({
                    'Lead_ID': r['Lead_ID'],
                    'Visited_Date_Time': r['Visited_Date_Time'].strftime('%Y-%m-%d %H:%M:%S') if r['Visited_Date_Time'] else '',
                    'Visited_Employee': r['Visited_Employee'] or '',
                    'Employee_Designation': r['Employee_Designation'] or '',
                    'Visitor_Name': r['Visitor_Name'] or '',
                    'Visitor_Phone': str(r['Visitor_Phone'] or ''),
                    'Visitor_Email': r['Visitor_Email'] or '',
                    'Date_Of_Birth': r['Date_Of_Birth'].strftime('%d-%b-%Y') if r['Date_Of_Birth'] else '',
                    'Anniversary_Date': r['Anniversary_Date'].strftime('%d-%b-%Y') if r['Anniversary_Date'] else '',
                    'City': r['City'] or '',
                    'Visit_Source': 'QR Scan' if r['Visit_Source'] == 'qr_scan' else 'Direct Web',
                    'IP_Address': r['IP_Address'] or ''
                })

            writer = csv.DictWriter(output, fieldnames=list(formatted_rows[0].keys()))
            writer.writeheader()
            for row in formatted_rows:
                writer.writerow(row)
        else:
            writer = csv.writer(output)
            writer.writerow(['Lead_ID', 'Visited_Date_Time', 'Visited_Employee', 'Employee_Designation', 'Visitor_Name', 'Visitor_Phone', 'Visitor_Email', 'Date_Of_Birth', 'Anniversary_Date', 'City', 'Visit_Source'])

        return output.getvalue()
    finally:
        cursor.close()
        conn.close()

