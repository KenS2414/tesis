from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def generate_gradebook_pdf(subject, grades):
    """Return bytes of a simple gradebook PDF for `subject` and iterable `grades`.
    `grades` should be iterable of (student, grade) tuples where `student` has
    first_name/last_name and `grade` has score/comment.
    """
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    width, height = letter
    y = height - 72
    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, y, f"Gradebook: {subject.name}")
    y -= 28
    if getattr(subject, 'category', None):
        c.setFont("Helvetica", 10)
        c.drawString(72, y, f"Category: {subject.category}    Credits: {getattr(subject, 'credits', '')}")
        y -= 20

    c.setFont("Helvetica-Bold", 12)
    c.drawString(72, y, "Student")
    c.drawString(300, y, "Score")
    c.drawString(380, y, "Comment")
    y -= 16
    c.setFont("Helvetica", 10)
    for student, grade in grades:
        if y < 72:
            c.showPage()
            y = height - 72
        name = f"{student.first_name} {student.last_name}"
        c.drawString(72, y, name)
        score = "" if grade.score is None else str(grade.score)
        c.drawString(300, y, score)
        comment = grade.comment or ""
        c.drawString(380, y, comment[:60])
        y -= 14

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
