import os
from sqlalchemy.orm import Session
from typing import Callable, Dict, Any, List, Optional, TypeVar, Type
from decimal import Decimal
import uuid
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch

from core.services.service_base import ServiceBase
from infrastructure.persistence.utils import session_scope
from core.models.sale import Sale, SaleItem
from core.interfaces.repository_interfaces import ISaleRepository, IProductRepository, ICustomerRepository

class SaleService(ServiceBase):
    def __init__(self, 
                 sale_repo_factory: Callable[[Session], ISaleRepository], 
                 product_repo_factory: Callable[[Session], IProductRepository], 
                 customer_repo_factory: Callable[[Session], ICustomerRepository], 
                 inventory_service, 
                 customer_service):
        """
        Initialize with repository factories and related services.
        
        Args:
            sale_repo_factory: Factory function to create sale repository
            product_repo_factory: Factory function to create product repository
            customer_repo_factory: Factory function to create customer repository
            inventory_service: Service for inventory operations
            customer_service: Service for customer operations
        """
        super().__init__()  # Initialize base class with default logger
        self.sale_repo_factory = sale_repo_factory
        self.product_repo_factory = product_repo_factory
        self.customer_repo_factory = customer_repo_factory
        self.inventory_service = inventory_service
        self.customer_service = customer_service

    def create_sale(self, items_data: List[Dict[str, Any]], user_id: int, 
                   payment_type: Optional[str] = None, customer_id: Optional[int] = None, 
                   is_credit_sale: bool = False, session: Optional[Session] = None) -> Sale:
        """Create a new sale with the given items and parameters."""
        def _create_sale(session, items_data, user_id, payment_type, customer_id, is_credit_sale):
            # Get repositories from factories
            product_repo = self._get_repository(self.product_repo_factory, session)
            sale_repo = self._get_repository(self.sale_repo_factory, session)
            
            # Convert item dictionaries to SaleItem objects
            sale_items = []
            for item_data in items_data:
                # Get product details if not provided
                product_id = item_data["product_id"]
                quantity = item_data["quantity"]
                
                # Handle case where only product_id and quantity are provided
                if "product_code" not in item_data or "product_description" not in item_data or "unit_price" not in item_data:
                    # Fetch product from repository to get missing details
                    product = product_repo.get_by_id(product_id)
                    if product:
                        product_code = product.code
                        product_description = product.description
                        unit_price = product.sell_price
                    else:
                        # Fallback values if product not found
                        product_code = f"PROD-{product_id}"
                        product_description = f"Product {product_id}"
                        unit_price = 0.0
                else:
                    # Use provided values
                    product_code = item_data["product_code"]
                    product_description = item_data["product_description"]
                    unit_price = item_data["unit_price"]
                
                sale_item = SaleItem(
                    product_id=product_id,
                    product_code=product_code,
                    product_description=product_description,
                    quantity=quantity,
                    unit_price=unit_price
                )
                sale_items.append(sale_item)
            
            # Create the sale object with the SaleItem objects
            sale = Sale(
                items=sale_items,
                user_id=user_id,
                payment_type=payment_type,
                customer_id=customer_id,
                is_credit_sale=is_credit_sale
            )
            
            return sale_repo.add_sale(sale)
            
        # If session is provided, use it directly; otherwise use _with_session
        if session:
            return _create_sale(session, items_data, user_id, payment_type, customer_id, is_credit_sale)
        else:
            return self._with_session(_create_sale, items_data, user_id, payment_type, customer_id, is_credit_sale)

    def get_sale_by_id(self, sale_id: int) -> Optional[Sale]:
        """Get a sale by its ID. Returns None if not found."""
        def _get_sale(session, sale_id):
            sale_repo = self._get_repository(self.sale_repo_factory, session)
            return sale_repo.get_by_id(sale_id)
        return self._with_session(_get_sale, sale_id)

    def assign_customer_to_sale(self, sale_id: int, customer_id: int) -> bool:
        """Assign a customer to an existing sale. Returns True if successful."""
        def _assign_customer(session, sale_id, customer_id):
            sale_repo = self._get_repository(self.sale_repo_factory, session)
            sale = sale_repo.get_by_id(sale_id)
            if sale:
                # Assume update method exists in repository
                update_data = {"customer_id": customer_id}
                sale_repo.update(sale_id, update_data)
                return True
            return False
        return self._with_session(_assign_customer, sale_id, customer_id)

    def update_sale(self, sale_id: int, update_data: dict) -> Sale:
        """Update a sale."""
        def _update_sale(session, sale_id, update_data):
            sale_repo = self._get_repository(self.sale_repo_factory, session)
            sale = sale_repo.get_by_id(sale_id)
            if sale:
                # Assume update method exists in repository
                return sale_repo.update(sale_id, update_data)
            return None
            
        return self._with_session(_update_sale, sale_id, update_data)

    def delete_sale(self, sale_id: int) -> bool:
        """Delete a sale by ID."""
        def _delete_sale(session, sale_id):
            sale_repo = self._get_repository(self.sale_repo_factory, session)
            sale = sale_repo.get_by_id(sale_id)
            if sale:
                return sale_repo.delete(sale_id)
            return False
            
        return self._with_session(_delete_sale, sale_id)

    def generate_receipt_pdf(self, sale_id: int, output_dir: str) -> str:
        """Generate a PDF receipt for a sale and return the file path."""
        def _generate_receipt_pdf(session, sale_id, output_dir):
            sale_repo = self._get_repository(self.sale_repo_factory, session)
            sale = sale_repo.get_by_id(sale_id)
            if not sale:
                raise ValueError(f"Sale with ID {sale_id} not found")
                
            filename = f"receipt_{sale_id}.pdf"
            file_path = os.path.join(output_dir, filename)
                
            create_receipt_pdf(sale, file_path)
            return file_path
            
        return self._with_session(_generate_receipt_pdf, sale_id, output_dir)

    def generate_presupuesto_pdf(self, items_data: List[Any], total_amount: Decimal, 
                                 output_dir: str, customer_name: Optional[str] = None, 
                                 user_name: Optional[str] = None) -> str:
        """Generate a PDF for a 'Presupuesto' (Quote) and return the file path."""
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
                self.logger.info(f"Created output directory: {output_dir}")
            except OSError as e:
                self.logger.error(f"Error creating output directory {output_dir}: {e}")
                raise  # Re-raise the exception if directory creation fails

        presupuesto_uuid = str(uuid.uuid4())[:8] # Short UUID for ID
        filename = f"presupuesto_{presupuesto_uuid}.pdf"
        file_path = os.path.join(output_dir, filename)
        
        try:
            create_presupuesto_pdf_content(
                filename=file_path, 
                items=items_data, 
                total_amount=total_amount,
                customer_name=customer_name,
                user_name=user_name,
                presupuesto_id=presupuesto_uuid
            )
            self.logger.info(f"Presupuesto PDF generated: {file_path}")
            return file_path
        except Exception as e:
            self.logger.error(f"Failed to generate presupuesto PDF {file_path}: {e}")
            # Depending on desired behavior, could re-raise or return None/error indicator
            raise # Re-raise to let the caller (UI) handle the error message


def create_receipt_pdf(sale: Sale, filename: str) -> None:
    """Generate a PDF receipt for the given sale and save it to the specified filename."""
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Title
    story.append(Paragraph("Receipt", styles['h1']))
    story.append(Spacer(1, 0.2 * inch))

    # Sale Info
    story.append(Paragraph(f"Sale ID: {sale.id if sale.id is not None else 'N/A'}", styles['Normal']))
    story.append(Paragraph(f"Date: {sale.timestamp.strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    if sale.payment_type:
        story.append(Paragraph(f"Payment Type: {sale.payment_type}", styles['Normal']))
    # Placeholder for Customer and User Info - can be expanded later
    if sale.customer_id:
        story.append(Paragraph(f"Customer ID: {sale.customer_id}", styles['Normal']))
    if sale.user_id:
        story.append(Paragraph(f"User ID: {sale.user_id}", styles['Normal']))
    story.append(Spacer(1, 0.2 * inch))

    # Items Table
    # Headers: "Code", "Description", "Qty", "Price", "Subtotal"
    data = [["Code", "Description", "Qty", "Unit Price", "Subtotal"]]
    for item in sale.items:
        data.append([
            item.product_code if item.product_code else "N/A",
            item.product_description if item.product_description else "N/A",
            f"{item.quantity:.2f}",
            f"${item.unit_price:.2f}",
            f"${item.subtotal:.2f}"
        ])
    
    # Add total row to data
    data.append(["", "", "", Paragraph("<b>TOTAL:</b>", styles['Normal']), Paragraph(f"<b>${sale.total:.2f}</b>", styles['Normal'])])

    table = Table(data, colWidths=[0.7*inch, 2.5*inch, 0.5*inch, 1*inch, 1*inch]) # Adjusted column widths
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4F81BD')), # Header background
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -2), colors.HexColor('#DCE6F1')), # Item rows background
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        # Total row specific styles
        ('SPAN', (0, -1), (2, -1)), # Span first three cells of total row
        ('ALIGN', (3, -1), (4, -1), 'RIGHT'), # Align TOTAL: and amount to the right
        ('FONTNAME', (3, -1), (4, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (3, -1), (4, -1), 10),
        ('VALIGN', (3, -1), (4, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, -1), (-1, -1), 8),
        ('TOPPADDING', (0, -1), (-1, -1), 8),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#C5D9F1')), # Total row background
    ]))
    story.append(table)
    story.append(Spacer(1, 0.3 * inch))

    # Footer Message
    story.append(Paragraph("Thank you for your purchase!", styles['Normal']))

    try:
        doc.build(story)
        print(f"Receipt {filename} generated successfully for sale ID {sale.id}")
    except Exception as e:
        print(f"Error generating receipt PDF for sale ID {sale.id}: {e}")
        # Depending on the application's error handling, you might want to log this
        # or raise a custom exception.
        raise


def create_presupuesto_pdf_content(filename: str, items: List[Any], total_amount: Decimal, 
                                   customer_name: Optional[str] = None, 
                                   user_name: Optional[str] = None, 
                                   presupuesto_id: Optional[str] = None) -> None:
    """Generate a PDF for a 'Presupuesto' (Quote) and save it to the specified filename."""
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = styles['h1']
    title_style.alignment = 1 # Center alignment
    story.append(Paragraph("PRESUPUESTO", title_style))
    story.append(Spacer(1, 0.3 * inch))

    # Presupuesto Info
    info_style = styles['Normal']
    info_style.leading = 14 # একটু বেশি লাইন স্পেসিং

    if presupuesto_id:
        story.append(Paragraph(f"<b>Presupuesto ID:</b> {presupuesto_id}", info_style))
    story.append(Paragraph(f"<b>Fecha:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", info_style))
    if customer_name:
        story.append(Paragraph(f"<b>Cliente:</b> {customer_name}", info_style))
    if user_name:
        story.append(Paragraph(f"<b>Atendido por:</b> {user_name}", info_style))
    story.append(Spacer(1, 0.2 * inch))

    # Items Table
    data = [[
        Paragraph("<b>Código</b>", styles['Normal']),
        Paragraph("<b>Descripción</b>", styles['Normal']),
        Paragraph("<b>Cant.</b>", styles['Normal']),
        Paragraph("<b>P. Unit.</b>", styles['Normal']),
        Paragraph("<b>Subtotal</b>", styles['Normal'])
    ]]

    for item in items:
        # Ensure all monetary values are Decimals and formatted
        # Assuming item is a dict-like or object with attributes: product_code, product_description, quantity, unit_price, subtotal
        try:
            quantity_val = Decimal(item.get('quantity') if isinstance(item, dict) else getattr(item, 'quantity', 0))
            unit_price_val = Decimal(item.get('unit_price') if isinstance(item, dict) else getattr(item, 'unit_price', 0))
            subtotal_val = Decimal(item.get('subtotal') if isinstance(item, dict) else getattr(item, 'subtotal', 0))

            data.append([
                item.get('product_code') if isinstance(item, dict) else getattr(item, 'product_code', "N/A"),
                item.get('product_description') if isinstance(item, dict) else getattr(item, 'product_description', "N/A"),
                f"{quantity_val:.2f}",
                f"${unit_price_val:.2f}",
                f"${subtotal_val:.2f}"
            ])
        except Exception as e:
            # Log error or handle gracefully if item structure is unexpected
            print(f"Error processing item for PDF: {item}. Error: {e}")
            data.append(["Error", "Error processing item", "", "", ""])

    # Total row
    total_decimal = Decimal(total_amount)
    data.append([
        "", "", "", 
        Paragraph("<b>TOTAL:</b>", styles['Normal']), 
        Paragraph(f"<b>${total_decimal:.2f}</b>", styles['Normal'])
    ])

    table = Table(data, colWidths=[0.8*inch, 3*inch, 0.6*inch, 1*inch, 1.1*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#CCCCCC')), # Header background
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (2, 1), (2, -1), 'RIGHT'), # Quantity right aligned
        ('ALIGN', (3, 1), (3, -1), 'RIGHT'), # Unit Price right aligned
        ('ALIGN', (4, 1), (4, -1), 'RIGHT'), # Subtotal right aligned
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), # Header font
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'), # Total row font bold
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -2), colors.beige), # Item rows background
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(table)
    story.append(Spacer(1, 0.3 * inch))

    # Footer Notes
    footer_style = styles['Normal']
    footer_style.fontSize = 9
    story.append(Paragraph("Este presupuesto es válido por 15 días a partir de la fecha de emisión.", footer_style))
    story.append(Paragraph("Los precios están sujetos a cambios sin previo aviso después de la fecha de validez.", footer_style))
    story.append(Paragraph("Este documento no es un comprobante fiscal.", footer_style))

    try:
        doc.build(story)
    except Exception as e:
        # Log the error more visibly if possible, or raise a specific exception
        print(f"Error building PDF '{filename}': {str(e)}")
        # Potentially re-raise or handle to inform the caller
        raise
