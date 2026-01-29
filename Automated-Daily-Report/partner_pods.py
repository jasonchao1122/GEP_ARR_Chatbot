"""
GEP Partner Pod/Category Mapping
Fetched from FY26 Targets spreadsheet (Priority and Pod columns)
"""

# Partner classifications (from FY26 Targets sheet)
# Format: partner_name: (pod, priority)
PARTNER_DATA = {
    # Accounting
    'BQE Software, Inc': ('Accounting', 'P1'),
    'Collective': ('Accounting', 'Anchor'),
    'CustomBooks Gusto Integration': ('Accounting', 'P2'),
    'Formations': ('Accounting', 'P2'),
    'Freshbooks': ('Accounting', 'Anchor'),
    'Heard': ('Accounting', 'P2'),
    'Lettuce Financial Labs': ('Accounting', 'P2'),
    'Xero Payroll': ('Accounting', 'Anchor'),
    
    # Banking
    'Chase': ('Banking', 'Anchor'),
    'Citizens': ('Banking', 'P1'),
    'US Bancorp': ('Banking', 'Anchor'),
    
    # HRIS
    'HR for Health': ('HRIS', 'P1'),
    'HiBob Payroll': ('HRIS', 'Anchor'),
    'Lattice Payroll': ('HRIS', 'Anchor'),
    'Remote.com - Production Oct/2023': ('HRIS', 'P2'),
    'guHRoo': ('HRIS', 'P2'),
    
    # VSaaS (Vertical SaaS)
    'Archy - Deprecated': ('VSaaS', 'P2'),
    'CleanCloud': ('VSaaS', 'P2'),
    'Dolce': ('VSaaS', 'P2'),
    'GoCo': ('VSaaS', 'P1'),
    'Groundcloud Prod 2': ('VSaaS', 'P2'),
    'RockSpoon, Inc': ('VSaaS', 'P2'),
    'Studio Designer': ('VSaaS', 'P1'),
    'Thryv, Inc.': ('VSaaS', 'P1'),
    'Vagaro Embedded Payroll': ('VSaaS', 'Anchor'),
    'busybusy': ('VSaaS', 'P2'),
    
    # Partners not in FY26 sheet - default to Other
    'Hour Timesheet LLC. Prod 2': ('Other', 'P2'),
    'Hourly.io': ('Other', 'P2'),
    'Goldfish [EMB TEST]': ('Other', 'P2'),
}

# Pod display order
POD_ORDER = [
    'Accounting',
    'Banking',
    'HRIS',
    'VSaaS',
    'Other',
]

# Priority sort order
PRIORITY_ORDER = {
    'Anchor': 1,
    'P1': 2,
    'P2': 3,
}

def get_partner_pod(partner_name):
    """Get the pod/category for a partner name"""
    data = PARTNER_DATA.get(partner_name, ('Other', 'P2'))
    return data[0]

def get_partner_priority(partner_name):
    """Get the priority for a partner name"""
    data = PARTNER_DATA.get(partner_name, ('Other', 'P2'))
    return data[1]

def get_priority_sort_key(priority):
    """Get sort key for priority (lower is higher priority)"""
    return PRIORITY_ORDER.get(priority, 99)

def group_partners_by_pod(partner_list):
    """
    Group a list of partners by pod
    
    Args:
        partner_list: List of partner dictionaries with 'name' key
    
    Returns:
        Dictionary with pod names as keys, list of partners as values
    """
    pods = {pod: [] for pod in POD_ORDER}
    
    for partner in partner_list:
        pod = get_partner_pod(partner.get('name', ''))
        if pod not in pods:
            pods[pod] = []
        pods[pod].append(partner)
    
    # Remove empty pods
    return {pod: partners for pod, partners in pods.items() if partners}
