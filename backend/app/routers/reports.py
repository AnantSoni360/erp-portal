from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
import io
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from app.database import get_db
from app.models import MaterialMaster, InwardTransaction, ContractorTransaction, Contractor
from app.calculation import calculate_stock_status

router = APIRouter(prefix="/reports", tags=["Reports & Analytics"])

@router.get("/stock/excel")
def export_stock_excel(
    category: str = "All",
    stock_status: str = "All",
    db: Session = Depends(get_db)
):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Current Stock Ledger"

    # Brand Header (Royal Blue)
    royal_blue_fill = PatternFill(start_color="1D4ED8", end_color="1D4ED8", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    title_font = Font(name="Calibri", size=16, bold=True, color="1D4ED8")
    subtitle_font = Font(name="Calibri", size=10, italic=True, color="64748B")

    ws.merge_cells("A1:I1")
    ws["A1"] = "MMTPL – Store & Inventory Management System"
    ws["A1"].font = title_font

    ws.merge_cells("A2:I2")
    ws["A2"] = "Current Stock & Inventory Ledger Report (Generated from Live Central Database)"
    ws["A2"].font = subtitle_font

    headers = [
        "Item ID", "Material / Specification", "Category", "Unit",
        "Booked Inward", "Issued", "Returned", "Book Balance", "Stock Status"
    ]

    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=4, column=col_num)
        cell.value = header
        cell.fill = royal_blue_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")

    # Fetch materials
    inward_sub = db.query(
        InwardTransaction.item_id,
        func.sum(InwardTransaction.quantity).label("inw")
    ).filter(
        InwardTransaction.status == "Book",
        InwardTransaction.check_status == "OK"
    ).group_by(InwardTransaction.item_id).subquery()

    issued_sub = db.query(
        ContractorTransaction.item_id,
        func.sum(ContractorTransaction.issued_qty).label("iss"),
        func.sum(ContractorTransaction.returned_qty).label("ret")
    ).filter(
        ContractorTransaction.status == "Posted",
        ContractorTransaction.check_status == "OK"
    ).group_by(ContractorTransaction.item_id).subquery()

    query = db.query(
        MaterialMaster,
        func.coalesce(inward_sub.c.inw, 0.0).label("inward_qty"),
        func.coalesce(issued_sub.c.iss, 0.0).label("issued_qty"),
        func.coalesce(issued_sub.c.ret, 0.0).label("returned_qty")
    ).outerjoin(
        inward_sub, MaterialMaster.item_id == inward_sub.c.item_id
    ).outerjoin(
        issued_sub, MaterialMaster.item_id == issued_sub.c.item_id
    )

    if category != "All":
        query = query.filter(MaterialMaster.category == category)

    materials = query.all()

    thin_border = Border(
        left=Side(style='thin', color='E2E8F0'),
        right=Side(style='thin', color='E2E8F0'),
        top=Side(style='thin', color='E2E8F0'),
        bottom=Side(style='thin', color='E2E8F0')
    )

    row_num = 5
    for mat, inw, iss, ret in materials:
        bal = (mat.opening_stock or 0.0) + inw - iss + ret
        st = calculate_stock_status(bal, mat.reorder_level, mat.name, mat.unit)
        if stock_status != "All" and st != stock_status:
            continue

        row = [
            mat.item_id,
            mat.name,
            mat.category,
            mat.unit,
            round(inw, 2),
            round(iss, 2),
            round(ret, 2),
            round(bal, 2),
            st
        ]
        for col_num, val in enumerate(row, 1):
            cell = ws.cell(row=row_num, column=col_num)
            cell.value = val
            cell.border = thin_border
            if col_num in [5, 6, 7, 8]:
                cell.alignment = Alignment(horizontal="right")
            elif col_num in [1, 4, 9]:
                cell.alignment = Alignment(horizontal="center")
            else:
                cell.alignment = Alignment(horizontal="left")
        row_num += 1

    # Adjust column widths
    ws.column_dimensions['A'].width = 12
    ws.column_dimensions['B'].width = 38
    ws.column_dimensions['C'].width = 24
    ws.column_dimensions['D'].width = 10
    ws.column_dimensions['E'].width = 15
    ws.column_dimensions['F'].width = 12
    ws.column_dimensions['G'].width = 12
    ws.column_dimensions['H'].width = 15
    ws.column_dimensions['I'].width = 14

    stream = io.BytesIO()
    wb.save(stream)
    stream.seek(0)

    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=MMTPL_Stock_Report.xlsx"}
    )


@router.get("/stock/pdf")
def export_stock_pdf(
    category: str = "All",
    db: Session = Depends(get_db)
):
    stream = io.BytesIO()
    doc = SimpleDocTemplate(
        stream,
        pagesize=landscape(letter),
        leftMargin=30,
        rightMargin=30,
        topMargin=30,
        bottomMargin=30
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        textColor=colors.HexColor('#1D4ED8'),
        spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor('#64748B'),
        spaceAfter=15
    )

    elements = [
        Paragraph("MMTPL – Store & Inventory Management ERP Portal", title_style),
        Paragraph(f"Current Stock Ledger Summary | Category Filter: {category}", subtitle_style),
        Spacer(1, 10)
    ]

    # Query items (top 100 for PDF performance)
    inward_sub = db.query(
        InwardTransaction.item_id,
        func.sum(InwardTransaction.quantity).label("inw")
    ).filter(
        InwardTransaction.status == "Book",
        InwardTransaction.check_status == "OK"
    ).group_by(InwardTransaction.item_id).subquery()

    issued_sub = db.query(
        ContractorTransaction.item_id,
        func.sum(ContractorTransaction.issued_qty).label("iss"),
        func.sum(ContractorTransaction.returned_qty).label("ret")
    ).filter(
        ContractorTransaction.status == "Posted",
        ContractorTransaction.check_status == "OK"
    ).group_by(ContractorTransaction.item_id).subquery()

    query = db.query(
        MaterialMaster,
        func.coalesce(inward_sub.c.inw, 0.0).label("inward_qty"),
        func.coalesce(issued_sub.c.iss, 0.0).label("issued_qty"),
        func.coalesce(issued_sub.c.ret, 0.0).label("returned_qty")
    ).outerjoin(
        inward_sub, MaterialMaster.item_id == inward_sub.c.item_id
    ).outerjoin(
        issued_sub, MaterialMaster.item_id == issued_sub.c.item_id
    )

    if category != "All":
        query = query.filter(MaterialMaster.category == category)

    materials = query.limit(100).all()

    data = [["Item ID", "Specification", "Category", "Unit", "Inward", "Issued", "Returned", "Balance", "Status"]]
    for mat, inw, iss, ret in materials:
        bal = (mat.opening_stock or 0.0) + inw - iss + ret
        st = calculate_stock_status(bal, mat.reorder_level, mat.name, mat.unit)
        spec = (mat.name[:32] + "..") if len(mat.name) > 34 else mat.name
        cat = (mat.category[:18] + "..") if len(mat.category) > 20 else mat.category
        data.append([
            mat.item_id,
            spec,
            cat,
            mat.unit,
            str(round(inw, 1)),
            str(round(iss, 1)),
            str(round(ret, 1)),
            str(round(bal, 1)),
            st
        ])

    table = Table(data, colWidths=[65, 190, 110, 45, 55, 50, 55, 60, 60])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1D4ED8')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')])
    ]))

    elements.append(table)
    doc.build(elements)
    stream.seek(0)

    return StreamingResponse(
        stream,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=MMTPL_Stock_Report.pdf"}
    )
