let socket = io.connect('https://' + document.domain + ':' + location.port');
let msg_queue = [];
let user_data;

activeLoop = false;
let loop = 0;
let prevTime = -1

function ready(){
  socket.emit('ready');
}

function initLoop(){
  loop = setInterval(() => { // checks for changes every second second
    socket.emit('game-loop');
  }, 200);
  activeLoop = true;
  document.getElementById('msg-wrapper').className = 'msg-wrapper timer-mode';
}

function submitFrame(frame){
  socket.emit('input-frame', frame);
}

// displays time if at least 1 second has passed since our previous time display
function displayTime(time){
  if(prevTime != time && time > 0){
    msg_queue.push(['Time', time, 2]);
    updateMessages();
  }
  prevTime = Math.floor(time);
}

//socket.on('ping-user', () => {
//  socket.emit('pong-server');
//});

//socket.on('ping-game', () => {
//  socket.emit('pong-server');
//});

socket.on('redirect', (url) => {
  window.location = url;
});

socket.on('send-msg', (msg) => {
  msg_queue.push(msg);
  updateMessages();
});

socket.on('game-loop', (time) => {
  // displays time if at least 1 second has passed since our previous time display
  displayTime(time);
  // starts game loop
  if(loop === 0)
    initLoop(true);
});

socket.on('close-loop', (win) => {
  clearInterval(loop);
  socket.emit('disconnect-room');
  activeLoop = false;
  loop = 0;
  prevTime = -1;
  setTimeout(() => {
    document.getElementById('msg-wrapper').className = 'msg-wrapper';
  }, 2000);
  if(win === true)
    console.log('play song');
});

socket.emit('request-song');
