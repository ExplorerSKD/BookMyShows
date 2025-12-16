import qrcode
import base64
from io import BytesIO
from django import template

register = template.Library()

@register.simple_tag
def generate_qr(value):
    """
    Generates a QR code for the given value and returns it as a base64 string.
    Usage: <img src="data:image/png;base64,{% generate_qr 'some_value' %}">
    """
    if not value:
        return ""
        
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(str(value))
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return img_str
