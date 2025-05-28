GENDER_CHOICES = [
    ('M', 'Male'),
    ('F', 'Female'),
    ('O', 'Other'),
]

STATUS_CHOICES = [
    ('active', 'Active'),
    ('inactive', 'Inactive'),
    ('pending', 'Pending'),
]

CLIENT_STATUS_CHOICES = [
    ('lead', 'Lead'),
    ('interested', 'Interested'),
    ('converted', 'Converted'),
    ('inactive', 'Inactive'),
]

ROLE_PREFIXES = {
    'admin': 'AD',
    'trainer': 'TR',
    'dietitian': 'DT',
    'manager': 'MG',
    'sales': 'SL',
}
