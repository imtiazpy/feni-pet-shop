from django.utils.translation import gettext as _
from django.core.exceptions import ValidationError
from django.core.files import File
from io import BytesIO
from barcode import Code128
from barcode.writer import ImageWriter
import uuid
import base64
from PIL import Image, ImageDraw, ImageFont

def generate_barcode_image(self):
        """
        Generate a Code128 barcode image (38mm x 25mm at 300 DPI) with product name and price on top.
        Saves to barcode_image field and returns base64-encoded PNG.
        Returns:
            str: Base64-encoded PNG image.
        """
        if not self.barcode:
            self.barcode = f"BAR-{uuid.uuid4().hex[:10].upper()}"
        
        try:
            # Calculate dimensions (38mm x 25mm at 300 DPI)
            label_width_px = int(38 * 11.811)  # 449px
            label_height_px = int(25 * 11.811)  # 295px

            # Generate barcode
            writer = ImageWriter()
            writer_options = {
                'module_width': 0.4,  # 0.4mm for scannability
                'module_height': 15.0,  # Barcode height
                'quiet_zone': 2.54,  # 10px at 300 DPI (2.54mm)
                'font_size': 6,  # Disable default text
                'text_distance': 3,
                'background': 'white',
                'foreground': 'black',
                'dpi': 300,
            }
            barcode_obj = Code128(self.barcode, writer=writer)
            buffer = BytesIO()
            barcode_obj.write(buffer, options=writer_options)
            barcode_img = Image.open(buffer).convert('RGBA')

            # Create canvas
            canvas = Image.new('RGBA', (label_width_px, label_height_px), (255, 255, 255, 255))  # White background
            draw = ImageDraw.Draw(canvas)

            # Load font (Arial bold, 21pt ≈ 7px at 300 DPI)
            try:
                font = ImageFont.truetype("arialbd.ttf", 21)
            except IOError:
                font = ImageFont.load_default()

            # Text settings
            text_height = 30  # Top strip
            max_name_width = int(label_width_px * 0.6)  # 269px for name
            price_text = f"Price: {float(self.sale_price):.2f}"

            # Truncate product name with ellipsis
            name = self.name
            text_bbox = draw.textbbox((0, 0), name, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            if text_width > max_name_width:
                while text_width > max_name_width - draw.textlength("...", font=font):
                    name = name[:-1]
                    text_bbox = draw.textbbox((0, 0), name + "...", font=font)
                    text_width = text_bbox[2] - text_bbox[0]
                name = name + "..."

            # Draw text
            quiet_zone = 10  # 10px
            draw.text((quiet_zone, 5), name, font=font, fill=(0, 0, 0, 255))  # Left, 5px top padding
            price_bbox = draw.textbbox((0, 0), price_text, font=font)
            price_width = price_bbox[2] - price_bbox[0]
            draw.text((label_width_px - quiet_zone - price_width, 5), price_text, font=font, fill=(0, 0, 0, 255))  # Right

            # Place barcode
            barcode_width, barcode_height = barcode_img.size
            barcode_y = text_height  # Below text strip
            barcode_x = (label_width_px - barcode_width) // 2  # Center
            canvas.paste(barcode_img, (barcode_x, barcode_y))

            # Save to barcode_image field
            final_buffer = BytesIO()
            canvas.convert('RGB').save(final_buffer, format='PNG', dpi=(300, 300))
            filename = f"{self.slug.lower().replace(' ', '-')}-barcode.png"
            self.barcode_image.save(filename, File(final_buffer), save=False)

            # Return base64 for frontend
            base64_image = base64.b64encode(final_buffer.getvalue()).decode('utf-8')
            return f"data:image/png;base64,{base64_image}"

        except Exception as e:
            raise ValidationError(f"Failed to generate barcode: {str(e)}")