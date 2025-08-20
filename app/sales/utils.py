import platform
from django.conf import settings
from django.core.exceptions import ValidationError

if platform.system() == "Windows":
    import win32print
    import win32con

# else:
#     raise ValidationError("Printing is only supported on Windows")

# from escpos.printer import Usb
# from django.conf import settings
# from django.core.exceptions import ValidationError

# def print_invoice(sale):
#     """
#     Print a receipt for the given sale using a USB POS printer with ESC/POS.
#     Args:
#         sale: Sale object containing sale details and items.
#     Raises:
#         ValidationError: If printer connection or printing fails.
#     """
#     try:
#         # Initialize USB printer (adjust vendor_id/product_id for Xprinter XP80T)
        
#         printer = Usb(
#             idVendor=getattr(settings, 'PRINTER_VENDOR_ID', 0x2D37),  # Xprinter VID
#             idProduct=getattr(settings, 'PRINTER_PRODUCT_ID', 0x0001),  # Replace with your printer's PID (find via lsusb or Device Manager)
#             timeout=1000
#         )

#         # Header
#         printer.set(align='center')
#         printer.text("Feni Pet Clinic & Pet Shop\n")
#         printer.text(f"Receipt #{sale.id}\n")
#         printer.text(f"Date: {sale.created_at.strftime('%Y-%m-%d %H:%M')}\n")
#         printer.text(f"Cashier: {sale.created_by.username}\n")
#         printer.text("-" * 32 + "\n")

#         # Items
#         printer.set(align='left')
#         printer.text("Item             Qty   Price   Total\n")
#         printer.text("-" * 32 + "\n")
#         for item in sale.sale_items.all():
#             name = item.product.name[:12].ljust(12)  # Truncate for 80mm paper
#             qty = str(item.quantity).rjust(4)
#             price = f"{item.sale_price:.2f}".rjust(7)
#             total = f"{item.quantity * item.sale_price:.2f}".rjust(7)
#             printer.text(f"{name} {qty} {price} {total}\n")

#         # Totals
#         printer.text("-" * 32 + "\n")
#         printer.set(align='right')
#         printer.text(f"Subtotal: ৳ {sale.subtotal:.2f}\n")
#         if sale.discount_amount > 0:
#             printer.text(f"Discount: -৳ {sale.discount_amount:.2f}\n")
#         printer.text(f"Total:    ৳ {sale.total_amount:.2f}\n")
#         printer.text("\nThank you for shopping with us!\n")

#         # Cut paper
#         printer.cut()
#         printer.close()

#     except Exception as e:
#         raise ValidationError(f"Failed to print receipt: {str(e)}")


def print_invoice(sale):
    """
    Print a receipt for the given sale using a USB POS printer with ESC/POS on Windows.
    Args:
        sale: Sale object containing sale details and items.
    Raises:
        ValidationError: If printer connection or printing fails, or if not on Windows.
    """

    if platform.system() != "Windows":
        raise ValidationError("Printing is only supported on Windows")
    
    try:
        printer_name = "POS-80C"
        hprinter = win32print.OpenPrinter(printer_name)
        hjob = win32print.StartDocPrinter(hprinter, 1, (f"Receipt_{sale.id}", None, "RAW"))
        win32print.StartPagePrinter(hprinter)

        lines = []

        # Header
        lines.append(b"\x1B\x40")  # Initialize
        lines.append(b"\x1B\x61\x01")  # Center
        lines.append("Feni Pet Clinic & Pet Shop\n".encode('utf-8'))
        lines.append(f"Receipt #{sale.id}\n".encode('utf-8'))
        lines.append(f"Date: {sale.created_at.strftime('%Y-%m-%d %H:%M')}\n".encode('utf-8'))
        lines.append(f"Cashier: {sale.created_by.username}\n".encode('utf-8'))
        lines.append(b"-" * 32 + b"\n")

        # Items
        lines.append(b"\x1B\x61\x00")  # Left
        lines.append("Item           Qty  Price  Total\n".encode('utf-8'))
        lines.append(b"-" * 32 + b"\n")

        for item in sale.sale_items.all():
            name = item.product.name[:12].ljust(12)
            qty = str(item.quantity).rjust(3)
            price = f"{item.sale_price:.2f}".rjust(6)
            total = f"{item.quantity * item.sale_price:.2f}".rjust(6)
            line = f"{name} {qty} {price} {total}\n"
            lines.append(line.encode('utf-8'))

        # Totals
        lines.append(b"-" * 32 + b"\n")
        lines.append(b"\x1B\x61\x02")  # Right
        lines.append(f"Subtotal: BDT {sale.subtotal:.2f}\n".encode('utf-8'))
        if sale.discount_amount > 0:
            lines.append(f"Discount: -BDT {sale.discount_amount:.2f}\n".encode('utf-8'))
        lines.append(f"Total:    BDT {sale.total_amount:.2f}\n".encode('utf-8'))

        # Footer
        lines.append("\nThank you for shopping with us!\n".encode('utf-8'))
        lines.append(b"\x1D\x56\x00")  # Cut

        receipt = b''.join(lines)
        win32print.WritePrinter(hprinter, receipt)

        win32print.EndPagePrinter(hprinter)
        win32print.EndDocPrinter(hprinter)
        win32print.ClosePrinter(hprinter)

    except Exception as e:
        raise ValidationError(f"Failed to print receipt: {str(e)}")