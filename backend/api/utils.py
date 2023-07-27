import os
from datetime import datetime

from django.conf import settings
from django.http import HttpResponse
from rest_framework.pagination import PageNumberPagination
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4


class LimitPageNumberPagination(PageNumberPagination):
    page_size_query_param = 'limit'


def shopping_cart_serializer_to_print_data(data):
    result_data = []
    for ingredient in data:
        result_data.append(
            ingredient['specification']['name']
            + ' - ' + str(ingredient['amount'])
            + ', ' + ingredient['specification']['measurement_unit'])
    result_data.sort()
    return result_data


def generate_pdf(data):
    response = HttpResponse(content_type='application/pdf')
    response[
        'Content-Disposition'] = 'attachment; filename="shopping_cart.pdf"'
    font_path = os.path.join(settings.BASE_DIR, 'fonts', 'arial.ttf')
    pdfmetrics.registerFont(TTFont('Arial', font_path))
    top_margin = 42.52  # 15 mm
    bottom_margin = 56.69  # 20 mm
    left_margin = 85.04  # 30 mm
    right_margin = 28.35  # 10 mm
    line_spacing = 10
    width = A4[0] - (left_margin + right_margin)
    height = A4[1] - (top_margin + bottom_margin)
    c = canvas.Canvas(response, pagesize=(width, height))
    header_font_size = 18
    font_size = 12
    c.setFont("Arial", header_font_size)
    c.drawString(left_margin, height - top_margin, 'Список покупок от '
                 + f'{datetime.today().strftime("%d.%m.%Y")} г.')
    c.setFont("Arial", font_size)
    y_position = height - top_margin - header_font_size - line_spacing
    for item in data:
        c.drawString(left_margin, y_position, "\u25A1")
        x_offset = left_margin + 15
        c.drawString(x_offset, y_position, item)
        y_position -= font_size + line_spacing
    c.save()
    return response
