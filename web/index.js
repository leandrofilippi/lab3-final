var express = require('express');
var bodyParser = require('body-parser');
var request = require('request');
var session = require('express-session');
var handlers = require('express-handlebars').create({ defaultLayout: 'main' }); // busca siempre en views/layout el archivo main.handlebars
var app = express();

app.engine('handlebars', handlers.engine);
app.set('view engine', 'handlebars')
//extended: false significa que parsea solo string (no archivos de imagenes por ejemplo)
app.use(bodyParser.urlencoded({ extended: false }));
app.use(session({
    secret: 'mys3cr3t',
    resave: false,
    saveUninitialized: true,
    cookie: {secure: false}
}));

app.get('/', (req, res) => {
    var sess = req.session
    if(sess.token){
      res.redirect('/dashboard');
    }else{
        res.redirect('/login')
    }
  //  res.render('home'); // se pasa el nombre home, y lo busca (rendrisa) en views/home.handlebars
});

app.get('/dashboard', function (req, res) {
  var sess = req.session
  if(sess.token){
        // hago request para obtener todas mis encuestas
        var options = {
                headers: {
                  'Authorization':'Bearer ' + sess.token,
                  'content-type': 'application/json',
                  'Accept': 'application/json'
                },
                json : {},
                uri: "http://tw-svc:8088/tw-svc/all",
                method: "GET"
            }
            request(options, function (error, response, body) {
               if(!error && response.statusCode == 200){
                 console.log(body);
                 console.log(body.status);
                 state = body.status;
                 if(body.status == "OK"){
                   console.log(body.status);
                   all = body.table;
                   console.log(body.table);
                   res.render('dashboard', {tabla: all});
                 }
                 else {
                    res.send("FAIL TW-SVC/ALL");
                 }
               }
            });
  }
  else{  res.render('home');  }
});

app.get('/newsurvey', function (req, res) {
        res.render('tw');
});

app.get('/login', function (req, res) {
        res.render('home');
});

// ruta test para verificar si llega token
app.get('/test', function (req, res) {

    var sess = req.session
    if(!sess.token){
        res.redirect("/login")
    }else{

        var options = {
            method: 'GET',
            //uri: 'http://localhost:8081/test', // autenticacion (api ptyhon)
            uri: 'http://auth-svc:8081/test',
            headers: {
              'Authorization':'Bearer ' +sess.token,
              'content-type': 'application/json'
          },
          json:{}
          };

          request(options, function (error, response, body) {
             if(!error && response.statusCode == 200){
               console.log(body.status);
               if(body.status == "OK"){
                 // aca tenemos que crear el token // funciona
                 console.log("token recibido:\n");
                 console.log(sess.token);
                 res.redirect("/dashboard"); // si esta todo bienlo
               } else {
                  res.render('login', {status:body.msg});
               }
             }
          });
        }
});


app.get('/registrar', (req, res) => {
    res.render('registrar');
});

app.post('/control', (req, res) => {

    var num1 = req.body.nombre;
    var num2 = req.body.pass;
    var status;
    var sess = req.session
    var options = {
            uri: "http://auth-svc:8081/auth-svc/login",
            method: "POST",
            headers: "Content-Type: application/json",
            json: { "user": num1, "pass": num2 }
        }

        request(options, function (error, response, body) {
            if (!error && response.statusCode == 200) {
                 console.log(body.status);
                if (body.status == "OK") {
                  sess.token = body.token; // guardamos lo que el servicio de auth nos da como token
                  console.log("token recibido de /control:\n");
                  res.redirect("/dashboard");
                }
                else{
                    res.render('home', { status: body.msg });
                }
            }

        });
});

app.post('/controlTW', (req, res) => {
    var num1 = req.body.hash;
    var num2 = req.body.time;
    var num3 = req.body.surveyname;
    var status;
    var sess = req.session
    var options = {
            uri: "http://tw-svc:8088/tw-svc/encuesta",
            method: "POST",
            headers: {
              'Authorization':'Bearer ' + sess.token,
              'content-type': 'application/json'
            },
            json: { "hash": num1, "time": num2, "surveyname": num3}
        }

        request(options, function (error, response, body) {
            if (!error && response.statusCode == 200) {
                 console.log(body.status);
                if (body.status == "OK") {
                  res.redirect("/dashboard");
                }
                else{
                    res.render('tw', { status: body.msg });
                }
            }

        });
});

app.post('/procesar', (req, res) => {
    var name = req.body.username;
    var pass = req.body.pass;
    var repass = req.body.repass;
    var sess = req.session
    if (pass != repass) {
        res.render('registrar', { err: 'Password incorrect' });
    }

    else {
        var options = {
            uri: "http://auth-svc:8081/auth-svc/register",
            method: "POST",
            headers: "Content-Type: application/json",
            json: { "username": name, "pass": pass }
        }

        request(options, function (error, response, body) {
            if (!error && response.statusCode == 200) {
                console.log(body.status);
                if (body.status == "OK") {
                  sess.token = body.token; // guardamos lo que el servicio de auth nos da como token
                  console.log("token recibido:\n");
                  console.log(sess.token);
                  res.redirect("/dashboard");
                }
                else{
                    res.render('registrar', { status: body.msg });
                }
            }

        });
    }
})

app.listen(3000);
