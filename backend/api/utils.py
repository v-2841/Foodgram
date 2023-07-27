from django.http import HttpResponse
from rest_framework.pagination import PageNumberPagination
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter


class LimitPageNumberPagination(PageNumberPagination):
    page_size_query_param = 'limit'


def generate_pdf(data):
    response = HttpResponse(content_type='application/pdf')
    response[
        'Content-Disposition'] = 'attachment; filename="exported_data.pdf"'

    # Создаем объект "canvas" для рисования на PDF
    c = canvas.Canvas(response, pagesize=letter)

    # Рисуем информацию из сериализатора на PDF
    y_position = 700
    for key, value in data.items():
        c.drawString(100, y_position, f"{key}: {value}")
        y_position -= 20

    # Закрываем объект "canvas"
    c.save()
    return response
