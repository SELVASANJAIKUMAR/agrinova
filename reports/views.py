"""
AgriNova Reports
Professional PDF reports for Admin.

Reports:
1. User Activity Report
2. Buy / Purchase Report
3. Sell / Listing Report
4. AI Chatbot Report
5. Price Forecast Report
6. Combined Report
"""

from io import BytesIO
from datetime import datetime

from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import render

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)

from orders.models import Order
from marketplace.models import Listing
from chatbot.models import ChatLog
from forecasting.models import PriceRecord


# ============================================================
# GENERAL HELPERS
# ============================================================

def get_styles():
    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="ReportTitle",
            parent=styles["Title"],
            fontSize=20,
            leading=24,
            alignment=TA_CENTER,
            spaceAfter=8,
        )
    )

    styles.add(
        ParagraphStyle(
            name="ReportSubtitle",
            parent=styles["Normal"],
            fontSize=9,
            leading=12,
            alignment=TA_CENTER,
            textColor=colors.grey,
            spaceAfter=15,
        )
    )

    styles.add(
        ParagraphStyle(
            name="SectionTitle",
            parent=styles["Heading2"],
            fontSize=13,
            leading=16,
            spaceBefore=10,
            spaceAfter=8,
        )
    )

    styles.add(
        ParagraphStyle(
            name="SmallText",
            parent=styles["Normal"],
            fontSize=7,
            leading=9,
        )
    )

    styles.add(
        ParagraphStyle(
            name="TinyText",
            parent=styles["Normal"],
            fontSize=6,
            leading=7,
        )
    )

    styles.add(
        ParagraphStyle(
            name="BodyTextReport",
            parent=styles["Normal"],
            fontSize=9,
            leading=13,
            spaceAfter=5,
        )
    )

    return styles


def paragraph(text, style):
    if text is None:
        text = "-"
    return Paragraph(str(text), style)


def make_table(data, widths, styles, small=False):
    converted = []

    cell_style = (
        styles["TinyText"]
        if small
        else styles["SmallText"]
    )

    for row in data:
        new_row = []

        for cell in row:
            if isinstance(cell, Paragraph):
                new_row.append(cell)
            else:
                new_row.append(
                    paragraph(cell, cell_style)
                )

        converted.append(new_row)

    table = Table(
        converted,
        colWidths=widths,
        repeatRows=1,
        hAlign="LEFT",
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#2F4F4F"),
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white,
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [
                        colors.white,
                        colors.HexColor("#F5F5F5"),
                    ],
                ),
            ]
        )
    )

    return table


def summary_boxes(items, styles):
    data = []

    for title, value in items:
        data.append(
            [
                Paragraph(
                    f"<b>{title}</b><br/>{value}",
                    styles["SmallText"],
                )
            ]
        )

    table = Table(
        [data],
        colWidths=[
            (180 * mm) / len(items)
        ] * len(items),
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.8,
                    colors.grey,
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "CENTER",
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    10,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    10,
                ),
            ]
        )
    )

    return table


def report_header_footer(canvas, doc):
    canvas.saveState()

    width, height = A4

    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawString(
        doc.leftMargin,
        height - 15 * mm,
        "AgriNova",
    )

    canvas.setFont("Helvetica", 7)
    canvas.drawRightString(
        width - doc.rightMargin,
        height - 15 * mm,
        "Agricultural Marketplace & AI Platform",
    )

    canvas.setFont("Helvetica", 7)

    canvas.drawString(
        doc.leftMargin,
        10 * mm,
        "AgriNova Admin Report",
    )

    canvas.drawRightString(
        width - doc.rightMargin,
        10 * mm,
        f"Page {doc.page}",
    )

    canvas.restoreState()


def create_pdf(filename, story):
    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=22 * mm,
        bottomMargin=18 * mm,
        title=filename,
        author="AgriNova",
    )

    document.build(
        story,
        onFirstPage=report_header_footer,
        onLaterPages=report_header_footer,
    )

    buffer.seek(0)

    response = HttpResponse(
        buffer.getvalue(),
        content_type="application/pdf",
    )

    response["Content-Disposition"] = (
        f'attachment; filename="{filename}"'
    )

    return response


def report_title(story, title, description, styles):
    story.append(
        Paragraph(
            title,
            styles["ReportTitle"],
        )
    )

    story.append(
        Paragraph(
            description,
            styles["ReportSubtitle"],
        )
    )


# ============================================================
# REPORT DASHBOARD
# ============================================================

def reports_dashboard(request):
    return render(
        request,
        "reports/dashboard.html",
    )


# ============================================================
# 1. USER REPORT
# ============================================================

def user_report(request):
    styles = get_styles()
    story = []

    User = get_user_model()

    users = User.objects.all().order_by("-date_joined")

    total_users = users.count()
    active_users = users.filter(
        is_active=True
    ).count()
    staff_users = users.filter(
        is_staff=True
    ).count()

    report_title(
        story,
        "User Activity Report",
        "Detailed report of registered AgriNova users and account activity.",
        styles,
    )

    story.append(
        summary_boxes(
            [
                ("Total Users", total_users),
                ("Active Users", active_users),
                ("Staff Users", staff_users),
            ],
            styles,
        )
    )

    story.append(Spacer(1, 10))

    story.append(
        Paragraph(
            "User Details",
            styles["SectionTitle"],
        )
    )

    data = [
        [
            "ID",
            "Username",
            "Email",
            "Date Joined",
            "Active",
        ]
    ]

    for user in users:
        joined = (
            user.date_joined.strftime("%d-%m-%Y")
            if user.date_joined
            else "-"
        )

        data.append(
            [
                user.id,
                user.username,
                user.email or "-",
                joined,
                "Yes" if user.is_active else "No",
            ]
        )

    story.append(
        make_table(
            data,
            [
                12 * mm,
                35 * mm,
                60 * mm,
                30 * mm,
                20 * mm,
            ],
            styles,
        )
    )

    story.append(Spacer(1, 12))

    story.append(
        Paragraph(
            "Summary",
            styles["SectionTitle"],
        )
    )

    story.append(
        Paragraph(
            f"AgriNova currently has {total_users} "
            f"registered users. {active_users} accounts "
            f"are active and {staff_users} users have "
            f"administrative privileges.",
            styles["BodyTextReport"],
        )
    )

    story.append(
        Paragraph(
            f"Report generated on "
            f"{datetime.now().strftime('%d-%m-%Y %H:%M')}.",
            styles["BodyTextReport"],
        )
    )

    return create_pdf(
        "AgriNova_User_Report.pdf",
        story,
    )


# ============================================================
# 2. BUY / PURCHASE REPORT
# ============================================================

def buy_report(request):
    styles = get_styles()
    story = []

    orders = (
        Order.objects
        .select_related("buyer")
        .prefetch_related(
            "items__listing__crop"
        )
        .order_by("-id")
    )

    total_orders = orders.count()

    total_purchase_value = (
        orders.aggregate(
            total=Sum("total_amount")
        )["total"]
        or 0
    )

    pending_orders = orders.filter(
        status="pending"
    ).count()

    completed_orders = orders.filter(
        status="completed"
    ).count()

    report_title(
        story,
        "Buy / Purchase Report",
        "Detailed buyer purchase, order and delivery information.",
        styles,
    )

    story.append(
        summary_boxes(
            [
                ("Total Orders", total_orders),
                (
                    "Purchase Value",
                    f"₹{total_purchase_value}",
                ),
                ("Pending Orders", pending_orders),
                (
                    "Completed Orders",
                    completed_orders,
                ),
            ],
            styles,
        )
    )

    story.append(Spacer(1, 12))

    # --------------------------------------------------------
    # ORDER DETAILS
    # --------------------------------------------------------

    story.append(
        Paragraph(
            "Purchase Order Details",
            styles["SectionTitle"],
        )
    )

    order_data = [
        [
            "Order",
            "Buyer",
            "Date",
            "Items",
            "Total",
            "Status",
        ]
    ]

    for order in orders:
        item_count = order.items.count()

        order_date = (
            order.created_at.strftime("%d-%m-%Y")
            if hasattr(order, "created_at")
            and order.created_at
            else "-"
        )

        order_data.append(
            [
                f"#{order.id}",
                getattr(
                    order.buyer,
                    "username",
                    "-",
                ),
                order_date,
                item_count,
                f"₹{order.total_amount}",
                getattr(
                    order,
                    "status",
                    "-",
                ),
            ]
        )

    story.append(
        make_table(
            order_data,
            [
                15 * mm,
                35 * mm,
                28 * mm,
                20 * mm,
                32 * mm,
                30 * mm,
            ],
            styles,
        )
    )

    story.append(Spacer(1, 15))

    # --------------------------------------------------------
    # DELIVERY ADDRESS
    # --------------------------------------------------------

    story.append(
        Paragraph(
            "Buyer Delivery Details",
            styles["SectionTitle"],
        )
    )

    delivery_data = [
        [
            "Order",
            "Buyer",
            "Mobile",
            "Complete Delivery Address",
        ]
    ]

    for order in orders:
        delivery_name = (
            getattr(
                order,
                "delivery_name",
                "-",
            )
            or "-"
        )

        delivery_phone = (
            getattr(
                order,
                "delivery_phone",
                "-",
            )
            or "-"
        )

        delivery_address = (
            getattr(
                order,
                "delivery_address",
                "-",
            )
            or "-"
        )

        delivery_city = (
            getattr(
                order,
                "delivery_city",
                "-",
            )
            or "-"
        )

        delivery_district = (
            getattr(
                order,
                "delivery_district",
                "-",
            )
            or "-"
        )

        delivery_state = (
            getattr(
                order,
                "delivery_state",
                "-",
            )
            or "-"
        )

        delivery_pincode = (
            getattr(
                order,
                "delivery_pincode",
                "-",
            )
            or "-"
        )

        complete_address = (
            f"{delivery_address}, "
            f"{delivery_city}, "
            f"{delivery_district}, "
            f"{delivery_state} - "
            f"{delivery_pincode}"
        )

        delivery_data.append(
            [
                f"#{order.id}",
                delivery_name,
                delivery_phone,
                complete_address,
            ]
        )

    story.append(
        make_table(
            delivery_data,
            [
                15 * mm,
                35 * mm,
                30 * mm,
                90 * mm,
            ],
            styles,
            small=True,
        )
    )

    story.append(Spacer(1, 15))

    # --------------------------------------------------------
    # PURCHASED ITEMS
    # --------------------------------------------------------

    story.append(
        Paragraph(
            "Purchased Product Details",
            styles["SectionTitle"],
        )
    )

    item_data = [
        [
            "Order",
            "Product",
            "Seller",
            "Quantity",
            "Unit Price",
            "Subtotal",
        ]
    ]

    for order in orders:

        for item in order.items.all():

            listing = getattr(
                item,
                "listing",
                None,
            )

            product_name = (
                listing.crop.name
                if listing and listing.crop
                else "-"
            )

            seller = "-"

            if listing is not None:
                seller_obj = getattr(
                    listing,
                    "seller",
                    None,
                )

                if seller_obj is not None:
                    seller = getattr(
                        seller_obj,
                        "username",
                        "-",
                    )

            quantity = getattr(
                item,
                "quantity",
                0,
            )

            unit_price = getattr(
                item,
                "unit_price",
                0,
            )

            try:
                subtotal = quantity * unit_price
            except Exception:
                subtotal = "-"

            item_data.append(
                [
                    f"#{order.id}",
                    product_name,
                    seller,
                    quantity,
                    f"₹{unit_price}",
                    f"₹{subtotal}",
                ]
            )

    if len(item_data) == 1:
        item_data.append(
            [
                "-",
                "No purchased products found",
                "-",
                "-",
                "-",
                "-",
            ]
        )

    story.append(
        make_table(
            item_data,
            [
                15 * mm,
                45 * mm,
                35 * mm,
                20 * mm,
                30 * mm,
                30 * mm,
            ],
            styles,
            small=True,
        )
    )

    story.append(Spacer(1, 12))

    story.append(
        Paragraph(
            "Purchase Summary",
            styles["SectionTitle"],
        )
    )

    story.append(
        Paragraph(
            f"This report contains {total_orders} "
            f"purchase orders with a total recorded "
            f"purchase value of ₹{total_purchase_value}. "
            f"The report also includes buyer delivery "
            f"information and individual purchased "
            f"product details.",
            styles["BodyTextReport"],
        )
    )

    return create_pdf(
        "AgriNova_Buy_Purchase_Report.pdf",
        story,
    )


# ============================================================
# 3. SELL / LISTING REPORT
# ============================================================

def sell_report(request):
    styles = get_styles()
    story = []

    listings = (
        Listing.objects
        .select_related(
            "seller",
            "crop",
        )
        .order_by("-id")
    )

    total_listings = listings.count()

    active_listings = listings.filter(
        is_active=True
    ).count()

    report_title(
        story,
        "Sell / Product Listing Report",
        "Detailed seller product listing and marketplace information.",
        styles,
    )

    story.append(
        summary_boxes(
            [
                ("Total Listings", total_listings),
                ("Active Listings", active_listings),
                (
                    "Inactive Listings",
                    total_listings - active_listings,
                ),
            ],
            styles,
        )
    )

    story.append(Spacer(1, 12))

    story.append(
        Paragraph(
            "Seller Listing Details",
            styles["SectionTitle"],
        )
    )

    data = [
        [
            "ID",
            "Seller",
            "Product",
            "Price",
            "Quantity",
            "District",
            "Status",
        ]
    ]

    for listing in listings:

        seller = getattr(
            listing.seller,
            "username",
            "-",
        )

        # Correct product field:
        # Listing -> CropCategory -> name
        product_name = (
            listing.crop.name
            if listing.crop
            else "-"
        )

        # Correct price field:
        # Listing.price_per_unit
        price = getattr(
            listing,
            "price_per_unit",
            0,
        )

        quantity = getattr(
            listing,
            "quantity",
            0,
        )

        district = getattr(
            listing,
            "district",
            "-",
        )

        is_active = getattr(
            listing,
            "is_active",
            True,
        )

        data.append(
            [
                listing.id,
                seller,
                product_name,
                f"₹{price}",
                quantity,
                district,
                (
                    "Active"
                    if is_active
                    else "Inactive"
                ),
            ]
        )

    story.append(
        make_table(
            data,
            [
                12 * mm,
                30 * mm,
                45 * mm,
                25 * mm,
                25 * mm,
                30 * mm,
                25 * mm,
            ],
            styles,
            small=True,
        )
    )

    story.append(Spacer(1, 12))

    story.append(
        Paragraph(
            "Seller Summary",
            styles["SectionTitle"],
        )
    )

    story.append(
        Paragraph(
            f"AgriNova currently contains "
            f"{total_listings} product listings. "
            f"{active_listings} listings are active "
            f"and available for marketplace activity.",
            styles["BodyTextReport"],
        )
    )

    return create_pdf(
        "AgriNova_Sell_Listing_Report.pdf",
        story,
    )


# ============================================================
# 4. AI CHATBOT REPORT
# ============================================================

def chatbot_report(request):
    styles = get_styles()
    story = []

    messages = (
        ChatLog.objects
        .select_related("user")
        .order_by("-id")
    )

    total_queries = messages.count()

    report_title(
        story,
        "AI Chatbot Query Report",
        "Detailed record of Agriculture Assistant interactions.",
        styles,
    )

    story.append(
        summary_boxes(
            [
                ("Total Queries", total_queries),
                (
                    "Unique Users",
                    messages.values(
                        "user"
                    ).distinct().count(),
                ),
            ],
            styles,
        )
    )

    story.append(Spacer(1, 12))

    story.append(
        Paragraph(
            "Chatbot Query Details",
            styles["SectionTitle"],
        )
    )

    data = [
        [
            "User",
            "Date",
            "Provider",
            "Query",
            "Response",
        ]
    ]

    for message in messages:

        username = (
            getattr(
                message.user,
                "username",
                "-",
            )
            if getattr(
                message,
                "user",
                None,
            )
            else "-"
        )

        date_value = getattr(
            message,
            "created_at",
            None,
        )

        date_text = (
            date_value.strftime(
                "%d-%m-%Y %H:%M"
            )
            if date_value
            else "-"
        )

        provider = (
            getattr(
                message,
                "provider",
                "-",
            )
            or "-"
        )

        query = (
            getattr(
                message,
                "message",
                None,
            )
            or getattr(
                message,
                "query",
                None,
            )
            or "-"
        )

        response_text = (
            getattr(
                message,
                "response",
                None,
            )
            or getattr(
                message,
                "answer",
                None,
            )
            or "-"
        )

        data.append(
            [
                username,
                date_text,
                provider,
                query,
                response_text,
            ]
        )

    story.append(
        make_table(
            data,
            [
                25 * mm,
                30 * mm,
                25 * mm,
                50 * mm,
                50 * mm,
            ],
            styles,
            small=True,
        )
    )

    story.append(Spacer(1, 12))

    story.append(
        Paragraph(
            "Chatbot Summary",
            styles["SectionTitle"],
        )
    )

    story.append(
        Paragraph(
            f"The AgriNova Agriculture Assistant "
            f"has recorded {total_queries} chatbot "
            f"interactions. These records can be "
            f"used by administrators to understand "
            f"user questions and assistant usage.",
            styles["BodyTextReport"],
        )
    )

    return create_pdf(
        "AgriNova_AI_Chatbot_Report.pdf",
        story,
    )


# ============================================================
# 5. PRICE FORECAST REPORT
# ============================================================

def forecast_report(request):
    styles = get_styles()
    story = []

    total_records = PriceRecord.objects.count()

    different_crops = (
        PriceRecord.objects
        .values("crop")
        .distinct()
        .count()
    )

    different_districts = (
        PriceRecord.objects
        .values("district")
        .distinct()
        .count()
    )

    synthetic_records = (
        PriceRecord.objects
        .filter(is_synthetic=True)
        .count()
    )

    market_records = (
        PriceRecord.objects
        .filter(is_synthetic=False)
        .count()
    )

    records = (
        PriceRecord.objects
        .select_related("crop")
        .order_by(
            "-date",
            "-id",
        )[:200]
    )

    report_title(
        story,
        "Price Forecast Report",
        "Historical and forecasting-related agricultural price data.",
        styles,
    )

    story.append(
        summary_boxes(
            [
                (
                    "Total Price Records",
                    total_records,
                ),
                (
                    "Different Crops",
                    different_crops,
                ),
                (
                    "Different Districts",
                    different_districts,
                ),
                (
                    "Demo / Synthetic",
                    synthetic_records,
                ),
            ],
            styles,
        )
    )

    story.append(Spacer(1, 10))

    story.append(
        summary_boxes(
            [
                ("Market Data", market_records),
                (
                    "Detailed Records",
                    min(total_records, 200),
                ),
            ],
            styles,
        )
    )

    story.append(Spacer(1, 12))

    story.append(
        Paragraph(
            "Latest Price Data Details",
            styles["SectionTitle"],
        )
    )

    story.append(
        Paragraph(
            "The summary statistics above cover all "
            "price records available in the AgriNova "
            "database. To keep the PDF efficient and "
            "suitable for the deployed Render server, "
            "the detailed table below contains only "
            "the latest 200 price records.",
            styles["BodyTextReport"],
        )
    )

    data = [
        [
            "S.No.",
            "Date",
            "Crop",
            "District",
            "Price",
            "Data Type",
        ]
    ]

    for index, record in enumerate(
        records,
        start=1,
    ):

        date_value = getattr(
            record,
            "date",
            None,
        )

        date_text = (
            date_value.strftime("%d-%m-%Y")
            if date_value
            else "-"
        )

        crop = getattr(
            record,
            "crop",
            None,
        )

        crop_name = (
            crop.name
            if crop
            else "-"
        )

        district = (
            getattr(
                record,
                "district",
                "-",
            )
            or "-"
        )

        price = getattr(
            record,
            "price",
            0,
        )

        is_synthetic = getattr(
            record,
            "is_synthetic",
            False,
        )

        data_type = (
            "Simulated / Demo"
            if is_synthetic
            else "Market Data"
        )

        data.append(
            [
                index,
                date_text,
                crop_name,
                district,
                f"Rs. {price}",
                data_type,
            ]
        )

    story.append(
        make_table(
            data,
            [
                13 * mm,
                27 * mm,
                35 * mm,
                38 * mm,
                30 * mm,
                37 * mm,
            ],
            styles,
            small=True,
        )
    )

    story.append(Spacer(1, 12))

    story.append(
        Paragraph(
            "Forecasting Summary",
            styles["SectionTitle"],
        )
    )

    story.append(
        Paragraph(
            f"The AgriNova Price Forecast module "
            f"currently contains {total_records} "
            f"price records covering {different_crops} "
            f"crops and {different_districts} districts. "
            f"{synthetic_records} records are simulated/"
            f"demo data and {market_records} records are "
            f"marked as market data. These records support "
            f"historical price analysis and future "
            f"agricultural price forecasting.",
            styles["BodyTextReport"],
        )
    )

    story.append(
        Paragraph(
            "Note: The detailed table is intentionally "
            "limited to the latest 200 records so that "
            "the report can be generated reliably on "
            "the deployed application.",
            styles["BodyTextReport"],
        )
    )

    return create_pdf(
        "AgriNova_Price_Forecast_Report.pdf",
        story,
    )


# ============================================================
# 6. COMBINED REPORT
# ============================================================

def combined_report(request):
    styles = get_styles()
    story = []

    User = get_user_model()

    total_users = User.objects.count()

    total_orders = Order.objects.count()

    total_sales = (
        Order.objects.aggregate(
            total=Sum("total_amount")
        )["total"]
        or 0
    )

    total_listings = Listing.objects.count()

    total_chatbot_queries = ChatLog.objects.count()

    total_price_records = PriceRecord.objects.count()

    active_users = User.objects.filter(
        is_active=True
    ).count()

    staff_users = User.objects.filter(
        is_staff=True
    ).count()

    pending_orders = Order.objects.filter(
        status="pending"
    ).count()

    completed_orders = Order.objects.filter(
        status="completed"
    ).count()

    active_listings = Listing.objects.filter(
        is_active=True
    ).count()

    inactive_listings = (
        total_listings - active_listings
    )

    unique_chat_users = (
        ChatLog.objects
        .values("user")
        .distinct()
        .count()
    )

    crop_count = (
        PriceRecord.objects
        .values("crop")
        .distinct()
        .count()
    )

    district_count = (
        PriceRecord.objects
        .values("district")
        .distinct()
        .count()
    )

    synthetic_records = (
        PriceRecord.objects
        .filter(is_synthetic=True)
        .count()
    )

    market_records = (
        PriceRecord.objects
        .filter(is_synthetic=False)
        .count()
    )

    report_title(
        story,
        "AgriNova Combined Report",
        "Comprehensive administrative overview of the AgriNova platform.",
        styles,
    )

    story.append(
        Paragraph(
            "Executive Summary",
            styles["SectionTitle"],
        )
    )

    story.append(
        Paragraph(
            "This combined report provides a "
            "consolidated overview of the major "
            "activities performed within the AgriNova "
            "smart agriculture marketplace. It includes "
            "user activity, purchasing activity, seller "
            "listings, AI chatbot usage and agricultural "
            "price data.",
            styles["BodyTextReport"],
        )
    )

    story.append(Spacer(1, 8))

    story.append(
        summary_boxes(
            [
                ("Users", total_users),
                ("Orders", total_orders),
                ("Listings", total_listings),
                (
                    "Chatbot Queries",
                    total_chatbot_queries,
                ),
            ],
            styles,
        )
    )

    story.append(Spacer(1, 10))

    story.append(
        summary_boxes(
            [
                (
                    "Purchase / Sales Value",
                    f"Rs. {total_sales}",
                ),
                (
                    "Price Records",
                    total_price_records,
                ),
                (
                    "Active Users",
                    active_users,
                ),
                (
                    "Active Listings",
                    active_listings,
                ),
            ],
            styles,
        )
    )

    story.append(PageBreak())

    # --------------------------------------------------------
    # USER MODULE
    # --------------------------------------------------------

    story.append(
        Paragraph(
            "1. User Activity Summary",
            styles["SectionTitle"],
        )
    )

    story.append(
        Paragraph(
            f"AgriNova has {total_users} registered "
            f"users. {active_users} accounts are currently "
            f"active and {staff_users} users have "
            f"administrative privileges.",
            styles["BodyTextReport"],
        )
    )

    user_data = [
        ["Metric", "Value"],
        ["Registered Users", total_users],
        ["Active Users", active_users],
        ["Staff Users", staff_users],
    ]

    story.append(
        make_table(
            user_data,
            [
                90 * mm,
                65 * mm,
            ],
            styles,
        )
    )

    story.append(Spacer(1, 15))

    # --------------------------------------------------------
    # BUY MODULE
    # --------------------------------------------------------

    story.append(
        Paragraph(
            "2. Buy / Purchase Summary",
            styles["SectionTitle"],
        )
    )

    story.append(
        Paragraph(
            f"The platform has recorded {total_orders} "
            f"orders with a total recorded value of "
            f"Rs. {total_sales}. There are "
            f"{pending_orders} pending orders and "
            f"{completed_orders} completed orders.",
            styles["BodyTextReport"],
        )
    )

    order_data = [
        ["Metric", "Value"],
        ["Total Orders", total_orders],
        [
            "Total Purchase / Sales Value",
            f"Rs. {total_sales}",
        ],
        ["Pending Orders", pending_orders],
        ["Completed Orders", completed_orders],
    ]

    story.append(
        make_table(
            order_data,
            [
                90 * mm,
                65 * mm,
            ],
            styles,
        )
    )

    story.append(Spacer(1, 15))

    # --------------------------------------------------------
    # SELL MODULE
    # --------------------------------------------------------

    story.append(
        Paragraph(
            "3. Sell / Listing Summary",
            styles["SectionTitle"],
        )
    )

    story.append(
        Paragraph(
            f"The marketplace contains {total_listings} "
            f"product listings. {active_listings} "
            f"listings are currently active and "
            f"{inactive_listings} are inactive.",
            styles["BodyTextReport"],
        )
    )

    listing_data = [
        ["Metric", "Value"],
        ["Total Listings", total_listings],
        ["Active Listings", active_listings],
        ["Inactive Listings", inactive_listings],
    ]

    story.append(
        make_table(
            listing_data,
            [
                90 * mm,
                65 * mm,
            ],
            styles,
        )
    )

    story.append(Spacer(1, 15))

    # --------------------------------------------------------
    # AI CHATBOT MODULE
    # --------------------------------------------------------

    story.append(
        Paragraph(
            "4. AI Chatbot Summary",
            styles["SectionTitle"],
        )
    )

    story.append(
        Paragraph(
            f"The AI Agriculture Assistant has "
            f"recorded {total_chatbot_queries} "
            f"queries from {unique_chat_users} users. "
            "These interactions support agricultural "
            "guidance and marketplace assistance.",
            styles["BodyTextReport"],
        )
    )

    chatbot_data = [
        ["Metric", "Value"],
        [
            "Total Chatbot Queries",
            total_chatbot_queries,
        ],
        [
            "Unique Users",
            unique_chat_users,
        ],
    ]

    story.append(
        make_table(
            chatbot_data,
            [
                90 * mm,
                65 * mm,
            ],
            styles,
        )
    )

    story.append(Spacer(1, 15))

    # --------------------------------------------------------
    # PRICE FORECAST MODULE
    # --------------------------------------------------------

    story.append(
        Paragraph(
            "5. Price Forecasting Summary",
            styles["SectionTitle"],
        )
    )

    story.append(
        Paragraph(
            f"The Price Forecasting module contains "
            f"{total_price_records} price records covering "
            f"{crop_count} crops and {district_count} "
            f"districts. {synthetic_records} records are "
            f"simulated/demo data and {market_records} "
            f"records are marked as market data.",
            styles["BodyTextReport"],
        )
    )

    forecast_data = [
        ["Metric", "Value"],
        [
            "Total Price Records",
            total_price_records,
        ],
        ["Different Crops", crop_count],
        [
            "Different Districts",
            district_count,
        ],
        [
            "Simulated / Demo Records",
            synthetic_records,
        ],
        [
            "Market Data Records",
            market_records,
        ],
    ]

    story.append(
        make_table(
            forecast_data,
            [
                90 * mm,
                65 * mm,
            ],
            styles,
        )
    )

    story.append(Spacer(1, 15))

    # --------------------------------------------------------
    # OVERALL PLATFORM STATISTICS
    # --------------------------------------------------------

    story.append(
        Paragraph(
            "Overall Platform Statistics",
            styles["SectionTitle"],
        )
    )

    overall_data = [
        [
            "Module",
            "Metric",
            "Value",
        ],
        [
            "Users",
            "Registered Users",
            total_users,
        ],
        [
            "Users",
            "Active Users",
            active_users,
        ],
        [
            "Orders",
            "Total Orders",
            total_orders,
        ],
        [
            "Orders",
            "Total Value",
            f"Rs. {total_sales}",
        ],
        [
            "Listings",
            "Total Listings",
            total_listings,
        ],
        [
            "Listings",
            "Active Listings",
            active_listings,
        ],
        [
            "AI Assistant",
            "Chatbot Queries",
            total_chatbot_queries,
        ],
        [
            "Forecasting",
            "Price Records",
            total_price_records,
        ],
    ]

    story.append(
        make_table(
            overall_data,
            [
                40 * mm,
                70 * mm,
                55 * mm,
            ],
            styles,
        )
    )

    story.append(Spacer(1, 15))

    # --------------------------------------------------------
    # CONCLUSION
    # --------------------------------------------------------

    story.append(
        Paragraph(
            "Conclusion",
            styles["SectionTitle"],
        )
    )

    story.append(
        Paragraph(
            "The combined report demonstrates the "
            "overall activity of the AgriNova platform "
            "across marketplace, ordering, seller, "
            "AI assistant and agricultural price modules. "
            "These statistics provide administrators "
            "with a high-level view of platform usage "
            "and operational activity.",
            styles["BodyTextReport"],
        )
    )

    story.append(
        Paragraph(
            f"Report generated on "
            f"{datetime.now().strftime('%d-%m-%Y %H:%M')}.",
            styles["BodyTextReport"],
        )
    )

    return create_pdf(
        "AgriNova_Combined_Report.pdf",
        story,
    )