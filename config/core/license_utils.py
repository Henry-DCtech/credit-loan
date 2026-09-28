import secrets
import string
from datetime import timedelta
from django.utils import timezone

def generate_crp_license(years=1, org_name=""):
    """
    Generates CRP-XXXX-XXXX-XXXX
    years: 1,2,3 etc
    """
    chars = string.ascii_uppercase + string.digits
    # avoid confusing chars like O,0,I,1
    chars = chars.replace("O","").replace("0","").replace("I","").replace("1","")
    
    def block():
        return ''.join(secrets.choice(chars) for _ in range(4))
    
    key = f"CRP-{block()}-{block()}-{block()}"
    
    issued = timezone.now()
    expiry = issued + timedelta(days=365*years)
    
    return {
        "license_key": key,
        "issued_date": issued,
        "expiry_date": expiry,
        "org_name": org_name,
        "years": years
    }

# Example:
# data = generate_crp_license(years=1, org_name="First Bank")
# print(data)