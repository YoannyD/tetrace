# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging
import PIL
import reportlab
import reportlab.lib.pagesizes as pdf_sizes
try:
    from StringIO import StringIO ## for Python 2
except ImportError:
    from io import StringIO ## for Python 3

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class Attachment(models.Model):
    _inherit = "ir.attachment"

    def convert_tiff_to_pdf(self):
        for r in self:
            if r.mimetype != 'image/tiff' and r.type != 'binary' and not r.db_datas:
                continue

            # Open the Image in PIL
            tiff_img = PIL.Image.open(StringIO(r.db_datas.decode("utf-8")))

            # Get tiff dimensions from exiff data. The values are swapped for some reason.
            height, width = tiff_img.tag[0x101][0], tiff_img.tag[0x100][0]

            # Create our output PDF
            out_pdf_io = StringIO()
            c = reportlab.pdfgen.canvas.Canvas(out_pdf_io, pagesize=pdf_sizes.letter)

            # Create our output PDF
            out_pdf_io = StringIO()
            c = reportlab.pdfgen.canvas.Canvas(out_pdf_io, pagesize=pdf_sizes.letter)

            # The PDF Size
            pdf_width, pdf_height = pdf_sizes.letter

            # Iterate through the pages
            max_pages = 200
            page = 0
            while True:
                try:
                    tiff_img.seek(page)
                except EOFError:
                    break
                _logger.info("Converting tiff page: %s" % page)
                # Stretch the TIFF image to the full page of the PDF
                if pdf_width * height / width <= pdf_height:
                    # Stretch wide
                    c.drawInlineImage(tiff_img, 0, 0, pdf_width, pdf_width * height / width)
                else:
                    # Stretch long
                    c.drawInlineImage(tiff_img, 0, 0, pdf_height * width / height, pdf_height)
                c.showPage()
                if max_pages and page > max_pages:
                    logging.error("Too many pages, breaking early")
                    break
                page += 1

            _logger.info("Saving tiff image")
            c.save()
            db_datas = out_pdf_io.getvalue()
            r.write({'db_datas': db_datas})

