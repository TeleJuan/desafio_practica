import psycopg2
import json

from fpdf import FPDF
from itertools import cycle
from datetime import datetime

data = ""
dict_name = "5c7dd876-39e4-425b-86bd-6a43adcf95d5"
# Se cargan parametros de configuracion
with open('conf.json') as json_file:
    data = json.load(json_file)

# funcion que valida los ruts
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

# Funcion que utiliza los parametros del archivo de configuracion para conectarse a la base de datos. Retorna un cursor
def connect():
    conn = psycopg2.connect(
        host=data["ENDPOINT"],
        database=data["DBNAME"],
        user=data["USR"],
        password=data["PSSWD"]
    )
    cur = conn.cursor() # cursor que permite realizar las querys
    return cur

# Funcion para obtener un diccionario para traducir los ids de las compañias a nombres
def get_companies(cur):
    cur.execute('SELECT id, name from companies;') #query para obtener ids y nombres de las compañias
    companies = cur.fetchall()
    company_dict = dict()
    for company in companies: #se recorren las filas de la query
        company_dict[company[0]] = company[1] # se añade entradas al diccionario del tipo {id:nombre}
    
    return company_dict

# Esta funcion obtiene todos los empleados y los clasifica de acorde a la compañia,
# retorna un diccionario del tipo {compañia:[empleados]}
def get_users(cur):

    companies = get_companies(cur)
    cur.execute('SELECT name, last_name, company_id, properties, audit  from users;')
    users = cur.fetchall()
    users_dict = dict()
    
    for user in users: # se recorren las filas de la query una a una
        company_name = user[2]

        # si la id de la compañia tiene un nombre asociado, se hace el cambio, 
        # de no poseer un nombre se deja tal cual. Esto puede modificarse para que ignore las compañias sin nombre (y a sus empleados)

        if user[2] not in companies.keys():
            company_name = user[2]
            #continue  #con este cambio se ingnoran las compañias sin nombre
        else:
            company_name = companies[user[2]]

        if company_name not in users_dict.keys(): # diccionario que separara a los empleados por compañia
            users_dict[company_name]=list()
        
        for k in user[3].keys(): # dado que algunos empleados tienen más de un objeto en el campo "properties", se elige el ultimo (Por lo revisado, todos son iguales).
            dict_name = k
            
        rut = user[3][dict_name]['rut']  # se obtiene el rut del objeto properties
        rut = rut[:-1] + '-' + rut[-1:] #se agrega el guion
        
        if not validarRut(rut): # si el rut es invalido, se deja en blanco
            rut = ' '

        last_login = user[4][dict_name]['last_login'] # Se obtiene el ultimo login

        date = ""
        time = ""
        if last_login != "": # si no esta en blanco, se debe modificar la hora de acuerdo a la zona horaria
            utc_time = datetime.strptime(last_login, "%Y-%m-%dT%H:%M:%SZ")
            epoch_time = (utc_time - datetime(1970, 1, 1)).total_seconds()
            last_login = datetime.fromtimestamp(epoch_time).strftime('%Y-%m-%dT%H:%M:%S')
            date = last_login.split('T')[0]
            time = last_login.split('T')[1]

        username = user[0] #primer nombre del empleado
        if " " in username:# si existen empleados con ambos nombres, se toma solo el primero.
            username = username.split(' ')[0]

        tupla =  (username,user[1],rut,date + ' ' + time) #se genera una tupla con toda la informacion requerida

        users_dict[company_name].append(tupla) # se añade la tupla al arreglo de tuplas asociadas a la compañia

    return users_dict

def set_header(pdf,title): # funcion utilizada para crear el encabezado de la pagina
    # Logo
    pdf.image('.\images\logo.png', 10, 8, 33) # se añade el logo de la empresa
    pdf.set_font('Arial', 'BU', 15)
    pdf.cell(80)
    pdf.cell(30, 10, title, '', 0, 'C') #title corresponde al nombre de la compañia
    pdf.ln(20)

class PDF(FPDF):
    def footer(self):  # funcion de la clase original FPDF que puede ser implementada para tener pie de pagina
        self.set_y(-15) #se fija la ubicacion del pie de pagina
        self.set_font('Arial', 'I', 8) # se elige la fuente y su tamaño
        self.cell(0, 10, 'Page ' + str(self.page_no()) + '/{nb}', 0, 0, 'C') # se agrega la numeracion a la hoja


def main():

    cur = connect() #conexion con la base de datos
    users = get_users(cur) #se obtiene el diccionario que separa a los empleados por compañias
    cur.close() # se cierra la conexion con la base de datos

    pdf = PDF() # se crea el documento pdf
    
    pdf.set_left_margin(10) #se establece el margen izquierdo
    pdf.set_font('Times', '', 11) #se configura la fuente
    pdf.alias_nb_pages() # se escoge el alias por defecto (nb) para el numero de pagina

    epw = pdf.w - 2*pdf.l_margin # se calcula el espacio efectivo del contenido
    col_width = epw/5 # se establece el ancho de cada columna de las tablas
 
    for i,j in users.items(): # se recorren las compañias
        
        pdf.add_page() # por cada compañia se agrega una pagina nueva
        set_header(pdf,i) # se agrega el encabezado
        pdf.set_font('Times', '', 11) # se define la fuente del cuerpo
        # se añade la fila con los valores requeridos al pdf
        pdf.cell(col_width, 10, str('Nombre'), border=1)
        pdf.cell(col_width, 10, str('Apellido'), border=1)
        pdf.cell(col_width, 10, str('Rut'), border=1)
        pdf.cell(1.5*col_width, 10, str('Ultima conexion'), border=1)
        pdf.ln(10) #salto de linea
        # se añaden las filas con los datos de los empleados una a una
        for k in j:
            cont = 0
            for datum in k:
                if cont != 3:
                    pdf.cell(col_width, 10, str(datum), border=1)
                else:pdf.cell(1.5*col_width, 10, str(datum), border=1)
                cont+=1
            pdf.ln(10)

    pdf.output('users.pdf', 'F') #se guarda el pdf

main()