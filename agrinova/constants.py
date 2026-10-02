"""Shared constants for AgriNova."""

TAMIL_NADU_DISTRICTS = [
    ('Ariyalur', 'Ariyalur'),
    ('Chengalpattu', 'Chengalpattu'),
    ('Chennai', 'Chennai'),
    ('Coimbatore', 'Coimbatore'),
    ('Cuddalore', 'Cuddalore'),
    ('Dharmapuri', 'Dharmapuri'),
    ('Dindigul', 'Dindigul'),
    ('Erode', 'Erode'),
    ('Kallakurichi', 'Kallakurichi'),
    ('Kanchipuram', 'Kanchipuram'),
    ('Kanyakumari', 'Kanyakumari'),
    ('Karur', 'Karur'),
    ('Krishnagiri', 'Krishnagiri'),
    ('Madurai', 'Madurai'),
    ('Mayiladuthurai', 'Mayiladuthurai'),
    ('Nagapattinam', 'Nagapattinam'),
    ('Namakkal', 'Namakkal'),
    ('Nilgiris', 'Nilgiris'),
    ('Perambalur', 'Perambalur'),
    ('Pudukkottai', 'Pudukkottai'),
    ('Ramanathapuram', 'Ramanathapuram'),
    ('Ranipet', 'Ranipet'),
    ('Salem', 'Salem'),
    ('Sivaganga', 'Sivaganga'),
    ('Tenkasi', 'Tenkasi'),
    ('Thanjavur', 'Thanjavur'),
    ('Theni', 'Theni'),
    ('Thoothukudi', 'Thoothukudi'),
    ('Tiruchirappalli', 'Tiruchirappalli'),
    ('Tirunelveli', 'Tirunelveli'),
    ('Tirupathur', 'Tirupathur'),
    ('Tiruppur', 'Tiruppur'),
    ('Tiruvallur', 'Tiruvallur'),
    ('Tiruvannamalai', 'Tiruvannamalai'),
    ('Tiruvarur', 'Tiruvarur'),
    ('Vellore', 'Vellore'),
    ('Viluppuram', 'Viluppuram'),
    ('Virudhunagar', 'Virudhunagar'),
]

# Regions for matching proximity scoring
TAMIL_NADU_REGIONS = {
    'North': [
        'Chennai', 'Tiruvallur', 'Kanchipuram', 'Chengalpattu', 'Vellore',
        'Ranipet', 'Tirupathur', 'Krishnagiri', 'Dharmapuri', 'Tiruvannamalai',
        'Viluppuram', 'Kallakurichi',
    ],
    'West': [
        'Coimbatore', 'Tiruppur', 'Erode', 'Salem', 'Namakkal', 'Karur',
        'Nilgiris', 'Dindigul', 'Theni',
    ],
    'Central': [
        'Tiruchirappalli', 'Thanjavur', 'Tiruvarur', 'Nagapattinam',
        'Mayiladuthurai', 'Ariyalur', 'Perambalur', 'Pudukkottai',
        'Sivaganga', 'Madurai',
    ],
    'South': [
        'Tirunelveli', 'Tenkasi', 'Thoothukudi', 'Kanyakumari',
        'Ramanathapuram', 'Virudhunagar',
    ],
}

UNIT_CHOICES = [
    ('kg', 'Kilogram (kg)'),
    ('quintal', 'Quintal'),
    ('ton', 'Ton'),
]

ORDER_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('confirmed', 'Confirmed'),
    ('shipped', 'Shipped'),
    ('delivered', 'Delivered'),
    ('cancelled', 'Cancelled'),
]

PAYMENT_STATUS_CHOICES = [
    ('unpaid', 'Unpaid'),
    ('paid_test', 'Paid (Test Mode)'),
]
