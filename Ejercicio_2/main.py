import psycopg2
import json

from fpdf import FPDF
from itertools import cycle


data = ""
dict_name = "5c7dd876-39e4-425b-86bd-6a43adcf95d5"
with open('conf.json') as json_file:
    data = json.load(json_file)

def validarRut(rut):
    rut_char = "0123456789K"
    rut = rut.upper()
    rut = rut.replace("-","")
    rut = rut.replace(".","")
    aux = rut[:-1]
    dv = rut[-1:]

    for i in rut:
        if i not in rut_char:
            return False
 
    revertido = map(int, reversed(str(aux)))
    factors = cycle(range(2,8))
    s = sum(d * f for d, f in zip(revertido,factors))
    res = (-s)%11
 
    if str(res) == dv:
        return True
    elif dv=="K" and res==10:
        return True
    else:
        return False

def connect():
    conn = psycopg2.connect(
        host=data["ENDPOINT"],
        database=data["DBNAME"],
        user=data["USR"],
        password=data["PSSWD"]
    )


    cur = conn.cursor()
    return cur


def get_companies(cur):
    cur.execute('SELECT id, name from companies;')
    companies = cur.fetchall()
    company_dict = dict()
    for company in companies:
        company_dict[company[0]] = company[1]
    
    return company_dict

def get_users(cur):
    companies = get_companies(cur)
    cur.execute('SELECT name, last_name, company_id, properties, audit  from users;')
    users = cur.fetchall()
    users_dict = dict()
    oini = set()
    for user in users:
        company_name = user[2]

        if user[2] not in companies.keys():
            company_name = user[2]
        else:
            company_name = companies[user[2]]

        if company_name not in users_dict.keys():
            users_dict[company_name]=list()
        

        #TODO: añadir soporte para diccionarios de nombres diferentes
        #if dict_name not in user[3].keys():    
        #    continue

        cont = 0
        for k in user[3].keys():    
            dict_name = k
            cont+=1 

        #if cont>1:
        #    print("usuario con dos diccionarios!!")
        #    print( user[3] )
        #    print("\n")

        rut = user[3][dict_name]['rut'] # TODO: darle formato al rut , verificar si el rut es valido ... 
        rut = rut[:-1] + '-' + rut[-1:]
        
        if not validarRut(rut):
            rut = ' '
        last_login = user[4][dict_name]['last_login']
        # TODO: Arreglar last_login a horario chileno
        date = ""
        time = ""
        if last_login != "":
            date = last_login.split('T')[0]
            time = last_login.split('T')[1]
        
        username = user[0]
        if " " in username:
            username = username.split(' ')[0]

        users_dict[company_name].append((username,user[1],rut,date + ' ' + time))

    return users_dict

def set_header(pdf,title):
    # Logo
    pdf.image('.\images\logo.png', 10, 8, 33)
    # Arial bold 15
    pdf.set_font('Arial', 'BU', 15)
    # Move to the right
    pdf.cell(80)
    # Title
    pdf.cell(30, 10, title, '', 0, 'C')
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


def main():

    cur = connect()
    users = get_users(cur)
    cur.close()

    pdf = PDF()
    pdf.set_left_margin(10)
    pdf.set_font('Times', '', 11)
    pdf.alias_nb_pages()

    epw = pdf.w - 2*pdf.l_margin
    col_width = epw/5

    for i,j in users.items():
        
        pdf.add_page()
        set_header(pdf,i)
        pdf.set_font('Times', '', 11)
        pdf.cell(col_width, 10, str('Nombre'), border=1)
        pdf.cell(col_width, 10, str('Apellido'), border=1)
        pdf.cell(col_width, 10, str('Rut'), border=1)
        pdf.cell(1.5*col_width, 10, str('Ultima conexion'), border=1)
        pdf.ln(10)
        for k in j:
            cont = 0
            for datum in k:
                if cont != 3:
                    pdf.cell(col_width, 10, str(datum), border=1)
                else:pdf.cell(1.5*col_width, 10, str(datum), border=1)
                cont+=1
            pdf.ln(10)

    pdf.output('users.pdf', 'F')

main()