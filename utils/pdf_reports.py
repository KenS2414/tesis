from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def generate_gradebook_pdf(subject, student_data):
    """Return bytes of a simple gradebook PDF for `subject` and iterable `student_data`.
    `student_data` should be iterable of (student, grade list, average) tuples.
    """
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    width, height = letter
    y = height - 72
    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, y, f"Libreta de Notas: {subject.name}")
    y -= 28
    if getattr(subject, 'category', None):
        c.setFont("Helvetica", 10)
        c.drawString(72, y, f"Categoría: {subject.category}")
        y -= 20

    c.setFont("Helvetica-Bold", 12)
    c.drawString(72, y, "Estudiante")
    c.drawString(300, y, "Nota")
    c.drawString(380, y, "Comentario")
    y -= 16
    c.setFont("Helvetica", 10)
    for student, grades, avg in student_data:
        for grade in grades:
            if y < 72:
                c.showPage()
                y = height - 72
            name = f"{student.first_name} {student.last_name}"
            c.drawString(72, y, name)
            # Use 'value' or 'score'
            score_val = getattr(grade, 'value', getattr(grade, 'score', None))
            score = "" if score_val is None else str(score_val)
            c.drawString(300, y, score)
            comment = grade.comment or ""
            c.drawString(380, y, comment[:60])
            y -= 14
        if y < 72:
            c.showPage()
            y = height - 72
        c.setFont("Helvetica-Bold", 10)
        avg_str = f"{avg:.2f}" if avg is not None else "N/A"
        c.drawString(72, y, f"Promedio Actual: {avg_str}")
        c.setFont("Helvetica", 10)
        y -= 20

    c.showPage()
    c.save()
    buf.seek(0)
    return buf.read()


def generate_payment_pdf(payment, student):
    """Return bytes of a simple payment receipt PDF for `payment` and `student`."""
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    width, height = letter
    y = height - 72
    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, y, "Payment Receipt")
    y -= 28
    c.setFont("Helvetica", 12)
    c.drawString(72, y, f"Student: {student.first_name} {student.last_name}")
    y -= 18
    c.drawString(72, y, f"Amount: {payment.amount}")
    y -= 18
    c.drawString(72, y, f"Status: {payment.status}")
    y -= 18
    c.drawString(72, y, f"Payment ID: {payment.id}")
    y -= 18
    c.showPage()
    c.save()
    buf.seek(0)
    return buf.read()
