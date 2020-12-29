const express = require('express');
const { spawn } = require('child_process');

const app = express();

app.use(express.urlencoded());
app.use(express.static(__dirname));

app.set('view engine', 'ejs');

app.post('/survey.ejs', (req, res) => {
    if (req.body['haveAddress'] == 'true'){
        var greeting = 'We got your Address. Lets see your Investment Preference';
    }
    else {
        var greeting = 'No Address is fine. Lets see your Investment Preference';
    }
    res.render('survey', {message: greeting});
});

app.post('/result.ejs', (req, res) => {
    let py = spawn('python', ['py/recommend.py']);
    let userProfile = {
        Address: req.body['address'],
        Period: req.body['period']
    }
    py.stdin.write(JSON.stringify(userProfile) + '\n');
    py.stdout.on('data', (recommendation) => {
        res.render('result', {result: recommendation});
    });
});

app.listen(80);