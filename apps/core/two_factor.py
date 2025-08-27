# apps/core/two_factor.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django_otp.models import Device
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_otp.plugins.otp_static.models import StaticDevice, StaticToken
from django_otp.util import random_hex
import qrcode
import qrcode.image.svg
from io import BytesIO
import base64


@login_required
def setup_2fa(request):
    """Setup two-factor authentication for the user"""
    user = request.user
    
    # Check if user already has 2FA enabled
    if user.is_verified():
        messages.info(request, 'Two-factor authentication is already enabled for your account.')
        return redirect('accounts:profile')
    
    if request.method == 'POST':
        # Generate TOTP device
        device = TOTPDevice.objects.create(
            user=user,
            name='default',
            confirmed=False
        )
        
        # Generate QR code
        qr_url = device.config_url
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_url)
        qr.make(fit=True)
        
        # Create QR code image
        factory = qrcode.image.svg.SvgPathImage
        img = qr.make_image(image_factory=factory)
        
        # Convert to base64 for display
        buffer = BytesIO()
        img.save(buffer)
        qr_code_svg = buffer.getvalue().decode()
        
        # Generate backup codes
        static_device = StaticDevice.objects.create(
            user=user,
            name='backup'
        )
        
        backup_codes = []
        for _ in range(10):
            token = StaticToken.objects.create(
                device=static_device,
                token=random_hex(length=8)
            )
            backup_codes.append(token.token)
        
        context = {
            'qr_code_svg': qr_code_svg,
            'backup_codes': backup_codes,
            'device': device,
        }
        
        return render(request, 'accounts/2fa_setup.html', context)
    
    return render(request, 'accounts/2fa_enable.html')


@login_required
@require_http_methods(["POST"])
def verify_2fa_setup(request):
    """Verify the 2FA setup with user-provided token"""
    user = request.user
    token = request.POST.get('token', '').strip()
    
    # Get unconfirmed TOTP device
    device = TOTPDevice.objects.filter(user=user, confirmed=False).first()
    
    if not device:
        return JsonResponse({'success': False, 'error': 'No setup in progress'})
    
    if device.verify_token(token):
        device.confirmed = True
        device.save()
        
        messages.success(request, 'Two-factor authentication has been successfully enabled!')
        return JsonResponse({'success': True, 'redirect': '/accounts/profile/'})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid token. Please try again.'})


@login_required
def disable_2fa(request):
    """Disable two-factor authentication"""
    user = request.user
    
    if request.method == 'POST':
        password = request.POST.get('password')
        
        if not user.check_password(password):
            messages.error(request, 'Incorrect password.')
            return render(request, 'accounts/2fa_disable.html')
        
        # Delete all devices
        Device.objects.filter(user=user).delete()
        
        messages.success(request, 'Two-factor authentication has been disabled.')
        return redirect('accounts:profile')
    
    return render(request, 'accounts/2fa_disable.html')


@login_required
def regenerate_backup_codes(request):
    """Regenerate backup codes"""
    user = request.user
    
    if request.method == 'POST':
        # Delete existing backup codes
        try:
            static_device = StaticDevice.objects.get(user=user, name='backup')
            StaticToken.objects.filter(device=static_device).delete()
        except StaticDevice.DoesNotExist:
            static_device = StaticDevice.objects.create(user=user, name='backup')
        
        # Generate new backup codes
        backup_codes = []
        for _ in range(10):
            token = StaticToken.objects.create(
                device=static_device,
                token=random_hex(length=8)
            )
            backup_codes.append(token.token)
        
        context = {'backup_codes': backup_codes}
        return render(request, 'accounts/2fa_backup_codes.html', context)
    
    return redirect('accounts:profile')


def get_2fa_status(user):
    """Get 2FA status for a user"""
    totp_devices = TOTPDevice.objects.filter(user=user, confirmed=True)
    static_devices = StaticDevice.objects.filter(user=user)
    
    return {
        'enabled': totp_devices.exists(),
        'totp_devices': totp_devices.count(),
        'backup_codes_available': any(
            device.token_set.filter(token__isnull=False).exists() 
            for device in static_devices
        ),
        'backup_codes_count': sum(
            device.token_set.filter(token__isnull=False).count() 
            for device in static_devices
        )
    }
