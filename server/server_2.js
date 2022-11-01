//Create a server on port 8080 with the express app

const express = require('express');
const app = express();
const server = require('http').createServer(app);
const io = require('socket.io')(server);
const { SERVERS } = require('./config');
const port = SERVERS[1][1];
// Routing
app.use(express.static('public'))
//Use sockets to listen new connection

io.on('connection', (socket) => {
    console.log('a user connected');
    socket.on('disconnect', () => {
        console.log('user disconnected');
    });
});


//Get routes
app.get('/', function (req, res) {
    res.sendFile(__dirname + '/index.html');
});


server.listen(port, function () {
    console.log('Server listening at port %d', port);
    // server.maxConnections = 1;
});

server.on('connection', function (socket) {
    console.log('A new connection was made by a client.');
    socket.on('close', function () {
        console.log('A connection was closed by a client.');
    });
});





//Command for run server: node server.js