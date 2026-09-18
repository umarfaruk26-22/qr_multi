from database.connection import query_db

ALLOWED_EVENTS = {
    'profile_view',
    'qr_scan',
    'whatsapp_click',
    'google_review_click',
    'instagram_click',
    'facebook_click',
    'linkedin_click',
    'youtube_click',
    'website_click'
}

def record_event(employee_id, event_type, device_type='desktop', referrer='', ip_address='', user_agent=''):
    """
    Records an analytics event into the database.
    """
    if event_type not in ALLOWED_EVENTS:
        return False
        
    try:
        query_db(
            """
            INSERT INTO analytics (employee_id, event_type, device_type, referrer, ip_address, user_agent)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                employee_id,
                event_type,
                (device_type or 'desktop')[:50],
                (referrer or '')[:255],
                (ip_address or '')[:100],
                (user_agent or '')[:500]
            ),
            commit=True
        )
        return True
    except Exception as e:
        print(f"Error logging analytics event: {e}")
        return False


def get_global_analytics_summary():
    """
    Retrieves global platform statistics for dashboard cards.
    """
    stats = {
        'total_views': 0,
        'total_scans': 0,
        'total_whatsapp': 0,
        'total_reviews': 0,
        'total_social': 0
    }
    
    rows = query_db(
        """
        SELECT event_type, COUNT(*) as count 
        FROM analytics 
        GROUP BY event_type
        """
    )
    
    for row in (rows or []):
        evt = row['event_type']
        cnt = row['count']
        if evt == 'profile_view':
            stats['total_views'] = cnt
        elif evt == 'qr_scan':
            stats['total_scans'] = cnt
        elif evt == 'whatsapp_click':
            stats['total_whatsapp'] = cnt
        elif evt == 'google_review_click':
            stats['total_reviews'] = cnt
        elif evt in ('instagram_click', 'facebook_click', 'linkedin_click', 'youtube_click', 'website_click'):
            stats['total_social'] += cnt
            
    return stats


def get_employee_analytics(employee_id):
    """
    Retrieves analytics metrics for a specific employee.
    """
    metrics = {
        'profile_views': 0,
        'qr_scans': 0,
        'whatsapp_clicks': 0,
        'google_review_clicks': 0,
        'instagram_clicks': 0,
        'facebook_clicks': 0,
        'linkedin_clicks': 0,
        'youtube_clicks': 0,
        'website_clicks': 0,
        'total_clicks': 0
    }
    
    rows = query_db(
        """
        SELECT event_type, COUNT(*) as count 
        FROM analytics 
        WHERE employee_id = %s 
        GROUP BY event_type
        """,
        (employee_id,)
    )
    
    for row in (rows or []):
        evt = row['event_type']
        cnt = row['count']
        if evt == 'profile_view':
            metrics['profile_views'] = cnt
        elif evt == 'qr_scan':
            metrics['qr_scans'] = cnt
        elif evt == 'whatsapp_click':
            metrics['whatsapp_clicks'] = cnt
            metrics['total_clicks'] += cnt
        elif evt == 'google_review_click':
            metrics['google_review_clicks'] = cnt
            metrics['total_clicks'] += cnt
        elif evt == 'instagram_click':
            metrics['instagram_clicks'] = cnt
            metrics['total_clicks'] += cnt
        elif evt == 'facebook_click':
            metrics['facebook_clicks'] = cnt
            metrics['total_clicks'] += cnt
        elif evt == 'linkedin_click':
            metrics['linkedin_clicks'] = cnt
            metrics['total_clicks'] += cnt
        elif evt == 'youtube_click':
            metrics['youtube_clicks'] = cnt
            metrics['total_clicks'] += cnt
        elif evt == 'website_click':
            metrics['website_clicks'] = cnt
            metrics['total_clicks'] += cnt
            
    return metrics


def get_recent_activity_logs(limit=25):
    """
    Retrieves recent activity logs across all employees.
    """
    return query_db(
        """
        SELECT a.id, a.employee_id, a.event_type, a.device_type, a.referrer, a.created_at,
               e.first_name, e.last_name, e.slug
        FROM analytics a
        JOIN employees e ON a.employee_id = e.id
        ORDER BY a.created_at DESC
        LIMIT %s
        """,
        (limit,)
    )
