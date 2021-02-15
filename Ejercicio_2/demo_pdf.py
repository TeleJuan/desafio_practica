from fpdf import FPDF

def set_header(pdf,title):
    # Logo
    pdf.image('.\images\logo.png', 10, 8, 33)
    # Arial bold 15
    pdf.set_font('Arial', 'B', 15)
    # Move to the right
    pdf.cell(80)
    # Title
    pdf.cell(30, 10, title, 'B', 0, 'C')
    # Line break
    pdf.ln(20)

class PDF(FPDF):

    # Page footer
    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        # Arial italic 8
        self.set_font('Arial', 'I', 8)
        # Page number
        self.cell(0, 10, 'Page ' + str(self.page_no()) + '/{nb}', 0, 0, 'C')

# Instantiation of inherited class
pdf = PDF()
pdf.set_left_margin(10)
pdf.set_font('Times', '', 10)
pdf.alias_nb_pages()

epw = pdf.w - 2*pdf.l_margin
col_width = epw/5
pdf.add_page()

set_header(pdf,"prueba")
for i in range(1, 50):

    for datum in range(4):
        pdf.cell(col_width, 10, str(datum+1), border=1)
 
    pdf.ln(10)
pdf.add_page()

pdf.output('tuto2.pdf', 'F')