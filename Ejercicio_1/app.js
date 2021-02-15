
const express = require('express')
const app = express()
const port = 3000
const  { Pool }  = require("pg")

const fs = require("fs");
const { count } = require('console');
const data = JSON.parse(fs.readFileSync("conf.json"));

const pool = new Pool({
    user: data.USR,
    host: data.ENDPOINT,
    database: data.DBNAME,
    password: data.PSSWD,
    port: data.PORT,
  });

pool.connect()

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

const asyncMiddleware = fn => (req, res, next) => {
    Promise.resolve(fn(req, res, next))
        .catch(next);
};

function checkDate(init,end,users){
    var count = 0
    var from  = new Date(init)
    from = from.getTime();
    var to  = new Date(end);
    to = to.getTime() + (23*60*60+59*60+59)*1000 - 4*60*60*1000;
    users.forEach(user => {
        let date = user.audit['5c7dd876-39e4-425b-86bd-6a43adcf95d5']['last_login'];
        if(date != ''){
            var check = new Date(0)
            check = Date.parse(date) - 4*60*60; 
            if(check >= from && check <= to){
                count++;  
            };
        }
    });
    return count;
}

const getUsers = async (req, res, next) => {
    var query = ""
    var result = {}
    var count = 0
    if(req.query.name != null && req.query.dates==null){
        query =  "select count(*)  from users where name ilike " + req.query.name + "%"
        console.log('Dates null')
        users = await pool.query(query)
        result = {
            'count':users
        }
        
    }

    else if(req.query.name == null && req.query.dates!=null){
        console.log("name null")
        query = "select audit from users where audit->>'5c7dd876-39e4-425b-86bd-6a43adcf95d5' is not null";
        users_data = await pool.query(query);
        count = checkDate(req.query.init,req.query.end,users_data.rows);
        result = {
            'count':count
        }
    
    }

    else if(req.query.name != null && req.query.dates!=null){
        query = "select audit from users where name ilike '" + req.query.name + "%' and"+ " audit->>'5c7dd876-39e4-425b-86bd-6a43adcf95d5' is not null"
        users_data = await pool.query(query)
        count = checkDate(req.query.init,req.query.end,users_data.rows);
        result = {
            'count':count
        }
        
    }
    res.send(JSON.stringify(result))
}

app.get('/getusers', asyncMiddleware(getUsers));

app.get('/indexjs', (req,res) => {
    res.sendFile(__dirname +"/static/JS/index.js");
});
app.get('/indexcss', (req,res) => {
    res.sendFile(__dirname +"/static/CSS/index.css");
});


app.listen(port, () => {
  console.log(`Example app listening at http://localhost:${port}`)
})
