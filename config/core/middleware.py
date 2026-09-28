from django.shortcuts import render
from django.utils import timezone
from .models import BankLicense

class LicenseCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Don't check admin, login, static
        exempt = ['/admin', '/login', '/logout', '/license', '/static', '/media']
        if any(request.path.startswith(x) for x in exempt):
            return self.get_response(request)

        try:
            lic = BankLicense.objects.first()
            if not lic or not lic.is_valid():
                return render(request, 'license_expired.html', {
                    'bank': lic.bank_name if lic else 'Unknown',
                    'valid_until': lic.valid_until if lic else 'Expired',
                    'key': lic.license_key if lic else 'NO KEY'
                })
        except:
            # If table not created yet, allow
            pass

        return self.get_response(request)