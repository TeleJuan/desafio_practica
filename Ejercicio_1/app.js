const express = require('express') 
const app = express()
const port = 3000 //se define el puerto donde el servidor recibe las peticiones
const  { Pool }  = require("pg") //modulo para conectarse a la base de datos

const fs = require("fs"); //modulo para leer archivos
const data = JSON.parse(fs.readFileSync("conf.json")); // se leen los parametrs de configuracion desde el archivo

const pool = new Pool({ //se configura el objeto de conexion con la base de datos
    user: data.USR,
    host: data.ENDPOINT,
    database: data.DBNAME,
    password: data.PSSWD,
    port: data.PORT,
  });
 
pool.connect() // se conecta a la base de datos

// ruta que carga el archivo index.html
app.get('/', (req, res) => { 
    res.writeHead(200, {
        'Content-Type': 'text/html'
    });
    fs.readFile('./index.html', null, function (error, data) {
        if (error) {
            res.writeHead(404);
            respone.write('Whoops! File not found!');
        } else {
            res.write(data);
        }
        res.end();
    });
})

// middleware que hace de intermediario en las funciones asincronas
const asyncMiddleware = fn => (req, res, next) => {
    Promise.resolve(fn(req, res, next))
        .catch(next);
};

//funcion que verifica si la ultima conexion está en el rango seleccionado, users es un arreglo usuarios
function checkDate(init,end,users){
    var count = 0
    // ambas fechas del rango se convierten en datetime epoch para compararlas
    var from  = new Date(init)
    from = from.getTime();
    var to  = new Date(end);
    to = to.getTime() + (23*60*60+59*60+59)*1000 - 4*60*60*1000;

    // se recorre el arreglo de usuarios
    users.forEach(user => {
        let date = user.audit['5c7dd876-39e4-425b-86bd-6a43adcf95d5']['last_login']; //se extrae la fecha del objeto contenido en el campo audit
        if(date != ''){
            var check = new Date(0) 
            check = Date.parse(date) - 4*60*60;  // se convierte a epoch la fecha del campo "last_login" si esque existe
            if(check >= from && check <= to){ //si la fecha está en el rango, se suma uno al contador
                count++;  
            };
        }
    });
    return count;
}

//funcion que recibe los parametros en la query de la url y hace la consulta a la base de datos
const getUsers = async (req, res, next) => {
    var query = ""
    var result = {}
    var count = 0
    //si solo viene el nombre el la url, se hace la consulta correspondiente
    if(req.query.name != null && req.query.dates==null){
        query =  "select count(*)  from users where name ilike " + req.query.name + "%"
        console.log('Dates null')
        users = await pool.query(query) //la query se hace a traves del objeto pool que esta conectado a la base de datos
        result = {
            'count':users //users contiene el numero de empleados que contengan el nombre buscado
        }
        
    }
    // si solo hay fechas , se consulta por el parametro audit de todos los usuarios
    else if(req.query.name == null && req.query.dates!=null){
        console.log("name null")
        query = "select audit from users where audit->>'5c7dd876-39e4-425b-86bd-6a43adcf95d5' is not null";
        users_data = await pool.query(query); //el conjunto de audits es el que se filtra en "checkDate" para contabilizar a los usuarios cuyo ultimo inicio de sesion esta en el rango
        count = checkDate(req.query.init,req.query.end,users_data.rows);
        result = {
            'count':count //count contiene la cuenta de empleados        
        }
    
    }

    // incluir el nombre en la url solo afecta la consulta que se hace en la base de datos
    else if(req.query.name != null && req.query.dates!=null){
        query = "select audit from users where name ilike '" + req.query.name + "%' and"+ " audit->>'5c7dd876-39e4-425b-86bd-6a43adcf95d5' is not null"
        users_data = await pool.query(query)
        count = checkDate(req.query.init,req.query.end,users_data.rows);
        result = {
            'count':count
        }
        
    }
    res.send(JSON.stringify(result)) //se convierte en texto el resultado del conteo 
}

app.get('/getusers', asyncMiddleware(getUsers)); // se define la ruta y se asocia la funcion getUsers al middleware

// en esta ruta se carga el archivo css
app.get('/indexcss', (req,res) => {
    res.sendFile(__dirname +"/static/CSS/index.css");
});

//se inicia el listener en el puerto configurado
app.listen(port, () => {
  console.log(`App listening at http://localhost:${port}`)
})
