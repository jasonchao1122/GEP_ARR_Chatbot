"""
GEP Partner Tier Mapping
Based on "GEP Partner Details - FY25 & 26" spreadsheet
"""

# Partner tier classifications
# Source: Authoritative list from GEP team (Jan 2026)
PARTNER_TIERS = {
    # Anchor Partners
    'Collective': 'Anchor',
    'Xero Payroll': 'Anchor',
    'Freshbooks': 'Anchor',
    'Chase': 'Anchor',
    'US Bancorp': 'Anchor',
    'HiBob Payroll': 'Anchor',
    'Lattice': 'Anchor',
    'Lattice Payroll': 'Anchor',
    'Vagaro Embedded Payroll': 'Anchor',
    
    # P1 Partners
    'BQE Software, Inc': 'P1',
    'GoCo': 'P1',
    'HR for Health': 'P1',
    'Studio Designer': 'P1',
    'Thryv, Inc.': 'P1',
    
    # P2 Partners
    'Lettuce Financial Labs': 'P2',
    'Hour Timesheet LLC. Prod 2': 'P2',
    'busybusy': 'P2',
    'CleanCloud': 'P2',
    'Heard': 'P2',
    'Formations': 'P2',
    'Accountingsuite': 'P2',
    'Rockspoon': 'P2',
    'Groundcloud Prod 2': 'P2',
    'Remote.com - Production Oct/2023': 'P2',
    'guHRoo': 'P2',
    'Archy - Deprecated': 'P2',
    '1-800Accountant - Deprecated': 'P2',
    'Hourly.io': 'P2',
}

# Filter sets
ANCHOR_PARTNERS = {k for k, v in PARTNER_TIERS.items() if v == 'Anchor'}
P1_PARTNERS = {k for k, v in PARTNER_TIERS.items() if v == 'P1'}
P2_PARTNERS = {k for k, v in PARTNER_TIERS.items() if v == 'P2'}

ANCHOR_AND_P1 = ANCHOR_PARTNERS | P1_PARTNERS


def get_partner_tier(partner_name):
    """Get the tier for a partner name"""
    return PARTNER_TIERS.get(partner_name, 'P2')


def is_anchor_or_p1(partner_name):
    """Check if partner is Anchor or P1"""
    return partner_name in ANCHOR_AND_P1


def filter_partners_by_tier(partner_dict, tiers=['Anchor', 'P1']):
    """
    Filter a dictionary of partners by tier
    
    Args:
        partner_dict: Dict with partner names as keys
        tiers: List of tier codes to include (e.g., ['Anchor', 'P1'])
    
    Returns:
        Filtered dictionary
    """
    return {
        name: data 
        for name, data in partner_dict.items() 
        if get_partner_tier(name) in tiers
    }

