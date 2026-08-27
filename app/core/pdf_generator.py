import io
import os
from datetime import datetime, timezone
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Try to import arabic_reshaper and python-bidi
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    HAS_ARABIC_SUPPORT = True
except ImportError:
    HAS_ARABIC_SUPPORT = False

# Register Cross-Platform Arabic / Unicode Fonts if available
FONT_REGULAR = "Helvetica"
FONT_BOLD = "Helvetica-Bold"

candidate_fonts = [
    # Windows paths
    (r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\arialbd.ttf", "DemianaArabic", "DemianaArabicBold"),
    (r"C:\Windows\Fonts\tahoma.ttf", r"C:\Windows\Fonts\tahomabd.ttf", "DemianaTahoma", "DemianaTahomaBold"),
    (r"C:\Windows\Fonts\seguiemj.ttf", None, "DemianaSegoe", "DemianaSegoeBold"),
    # Linux / Docker paths
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "DemianaDejaVu", "DemianaDejaVuBold"),
    ("/usr/share/fonts/truetype/msttcorefonts/arial.ttf", "/usr/share/fonts/truetype/msttcorefonts/arialbd.ttf", "DemianaLinuxArial", "DemianaLinuxArialBold"),
    ("/usr/share/fonts/truetype/freefont/FreeSans.ttf", "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf", "DemianaFreeSans", "DemianaFreeSansBold"),
]

for reg_path, bold_path, reg_name, bold_name in candidate_fonts:
    if os.path.exists(reg_path):
        try:
            pdfmetrics.registerFont(TTFont(reg_name, reg_path))
            FONT_REGULAR = reg_name
            if bold_path and os.path.exists(bold_path):
                pdfmetrics.registerFont(TTFont(bold_name, bold_path))
                FONT_BOLD = bold_name
            else:
                FONT_BOLD = reg_name
            break
        except Exception:
            continue

def ar(text: str) -> str:
    """Helper to reshape and format Arabic text for ReportLab rendering."""
    if not text:
        return ""
    text_str = str(text)
    if HAS_ARABIC_SUPPORT:
        try:
            reshaped = arabic_reshaper.reshape(text_str)
            return get_display(reshaped)
        except Exception:
            return text_str
    return text_str


def generate_reception_gate_pdf(
    period_name: str,
    start_date_str: str,
    end_date_str: str,
    approved_retreatants: list
) -> io.BytesIO:
    """
    Generates official gate reception check-in sheet with checkboxes for pen verification.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=20,
        leftMargin=20,
        topMargin=25,
        bottomMargin=20
    )
    story = []
    styles = getSampleStyleSheet()

    # Title & Header Styles
    title_style = ParagraphStyle(
        'MainTitle',
        parent=styles['Heading1'],
        fontName=FONT_BOLD,
        fontSize=17,
        leading=22,
        alignment=1, # Center
        textColor=colors.HexColor('#4A2E18')
    )
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontName=FONT_REGULAR,
        fontSize=12,
        leading=16,
        alignment=1,
        textColor=colors.HexColor('#7A5C3D')
    )
    meta_style = ParagraphStyle(
        'Meta',
        parent=styles['Normal'],
        fontName=FONT_BOLD,
        fontSize=10,
        leading=14,
        alignment=1,
        textColor=colors.HexColor('#1E293B')
    )

    story.append(Paragraph(ar("دير القديسة دميانة العامر ببراري بلقاس"), title_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph(ar("بيت الخلوة – كشف استقبال وبوابة النزيلات الرسمي"), subtitle_style))
    story.append(Spacer(1, 8))
    
    meta_text = f"الفترة: {period_name}  |  تاريخ البداية: {start_date_str}  |  المغادرة: {end_date_str}  |  إجمالي المقبولات: {len(approved_retreatants)}"
    story.append(Paragraph(ar(meta_text), meta_style))
    story.append(Spacer(1, 14))

    # Table Header and Rows
    table_data = [
        [
            ar("م"),
            ar("رقم الحجز"),
            ar("الاسم بالكامل"),
            ar("المحافظة"),
            ar("الكنيسة / الإبراشية"),
            ar("رقم الهاتف"),
            ar("الحالة"),
            ar("القلاية / الغرفة"),
            ar("توقيع الحضور")
        ]
    ]

    for idx, item in enumerate(approved_retreatants, start=1):
        church_dio = f"{item.get('church', '')} - {item.get('diocese', '')}".strip(" -")
        table_data.append([
            str(idx),
            item.get("booking_reference", ""),
            ar(item.get("full_name", "")),
            ar(item.get("governorate", "")),
            ar(church_dio),
            item.get("phone_number", ""),
            ar(item.get("attendance_status", "مقبولة")),
            ar(item.get("room_or_cell_number", "")),
            "[   ]"  # Box for physical pen check
        ])

    col_widths = [25, 95, 160, 85, 155, 95, 70, 75, 60]
    t = Table(table_data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8B5A2B')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), FONT_REGULAR),
        ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
        ('FONTSIZE', (0, 0), (-1, 0), 9.5),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 7),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#FFFBF5'), colors.HexColor('#F5EFEB')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D1C7BD')),
        ('FONTSIZE', (0, 1), (-1, -1), 8.5),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        ('TOPPADDING', (0, 1), (-1, -1), 4),
    ]))

    story.append(t)
    story.append(Spacer(1, 16))

    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontName=FONT_REGULAR,
        fontSize=8.5,
        leading=11,
        alignment=1,
        textColor=colors.HexColor('#64748B')
    )
    now_str = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    story.append(Paragraph(ar(f"تم استخراج التقرير آلياً من نظام بيت الخلوة بدير القديسة دميانة في: {now_str}"), footer_style))

    doc.build(story)
    buffer.seek(0)
    return buffer


def generate_final_period_summary_pdf(
    period_name: str,
    start_date_str: str,
    end_date_str: str,
    capacity: int,
    stats: dict,
    retreatants_list: list
) -> io.BytesIO:
    """
    Generates official final retreat period summary report.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )
    story = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'MainTitle',
        parent=styles['Heading1'],
        fontName=FONT_BOLD,
        fontSize=17,
        leading=22,
        alignment=1,
        textColor=colors.HexColor('#4A2E18')
    )
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontName=FONT_REGULAR,
        fontSize=12,
        leading=16,
        alignment=1,
        textColor=colors.HexColor('#7A5C3D')
    )

    story.append(Paragraph(ar("دير القديسة دميانة العامر ببراري بلقاس"), title_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph(ar("التقرير الإحصائي الختامي لفترة الخلوة"), subtitle_style))
    story.append(Spacer(1, 14))

    # Summary Stat Box
    summary_data = [
        [ar("الفترة"), ar(period_name), ar("تاريخ البدء"), start_date_str],
        [ar("المغادرة"), end_date_str, ar("السعة الاستيعابية"), str(capacity)],
        [ar("المقبولات"), str(stats.get("approved_count", 0)), ar("الحاضرات فعلياً"), str(stats.get("checked_in_count", 0))],
        [ar("الاعتذارات"), str(stats.get("cancelled_count", 0)), ar("غياب دون اعتذار (No Show)"), str(stats.get("no_show_count", 0))],
    ]
    summary_table = Table(summary_data, colWidths=[110, 155, 125, 140])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8F4EE')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D1C7BD')),
        ('FONTNAME', (0, 0), (-1, -1), FONT_REGULAR),
        ('FONTNAME', (0, 0), (0, -1), FONT_BOLD),
        ('FONTNAME', (2, 0), (2, -1), FONT_BOLD),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2C1810')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 9.5),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 18))

    # Retreatants Table
    list_header = [[ar("م"), ar("رقم الحجز"), ar("الاسم"), ar("المحافظة"), ar("الكنيسة"), ar("حالة الحضور")]]
    for idx, r in enumerate(retreatants_list, start=1):
        list_header.append([
            str(idx),
            r.get("booking_reference", ""),
            ar(r.get("full_name", "")),
            ar(r.get("governorate", "")),
            ar(r.get("church", "")),
            ar(r.get("attendance_status", "مكتمل"))
        ])

    ret_table = Table(list_header, colWidths=[30, 95, 155, 95, 100, 60], repeatRows=1)
    ret_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6B4423')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), FONT_REGULAR),
        ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2D8CC')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#FFFFFF'), colors.HexColor('#FBF8F4')]),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(ret_table)
    story.append(Spacer(1, 22))

    sign_style = ParagraphStyle(
        'Sign',
        parent=styles['Normal'],
        fontName=FONT_BOLD,
        fontSize=10.5,
        alignment=2, # Right
        textColor=colors.HexColor('#4A2E18')
    )
    story.append(Paragraph(ar("الأم المسؤولة عن بيت الخلوة: ......................................."), sign_style))

    doc.build(story)
    buffer.seek(0)
    return buffer
