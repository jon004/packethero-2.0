let socket = io.connect('http://localhost:3000') //'https://' + document.domain + ':' + location.port);
let song_to_play = new Audio(document.getElementById('song_name').value);
let msg_queue = [];
let admin_flag = document.getElementById('af').value;
let user_data;


let already_sent = false; // use this variable to prevent duplicate messages
let loop = 0;
let prevTime = -1

function ready(){
  already_sent = false;
  socket.emit('ready');
}

function initLoop(){
  prevTime = -1
  loop = setInterval(() => { // checks for game updates every second
    socket.emit('game-loop');
  }, 1000);
}

// if time is up display message and end game loop
function timedOut(){
  clearInterval(loop);
  loop = 0;
  if(!already_sent){
    msg_queue.push(['Time', 0, 2]);
    msg_queue.push(['Server [Team]', 'Game Over', 0]);
    msg_queue.push(['Server [Team]', 'Your team ran out of time.', 0]);
    already_sent = true;
  }
  updateMessages();
}

// displays time if at least 1 second has passed since our previous time display
function displayTime(time){
  if(prevTime != Math.floor(time) && time > 0){
    msg_queue.push(['Time', time, 2]);
    updateMessages();
  }
  prevTime = Math.floor(time);
}

// on connect get and update game data variables
socket.on('connect', () => {
  socket.emit('get-users');
  socket.emit('setSID');
});

function kickUser(){
  let id = document.getElementById('booted-user').value;
  if(id !== 'select a user'){
    socket.emit('remove-user', id);
  }
}

// returns HTML/CSS formatted option element
function createOption(text, value){
  let option_node = document.createElement('option');
  let text_node = document.createTextNode(text);
  option_node.value = value;
  option_node.appendChild(text_node);
  return option_node;
}

function removeOption(user){
  let options = document.getElementsByTagName("option");
  for(let i in options){
    if(options[i] && options[i].value == user.id)
      options[i].parentElement.removeChild(options[i]);
  }
}

function isOption(user){
  let options = document.getElementsByTagName("option");
  for(let i in options){
    if(options[i].value == user.id)
      return true;
  }
  return false;
}

///////////////////////////////////////////////////////////////////////////////
// Socket Events

socket.on('addUser', (user) => {
  if(!isOption(user) && user.admin !== 1)
    document.getElementById('booted-user').appendChild(createOption(user.name, user.id));
  msg_queue.push(['Server [All]', `${user.name} has entered the room.`, 0]);
  updateMessages();
});

socket.on('removeUser', (user) => {
  removeOption(user);
  msg_queue.push(['Server [All]', `${user.name} has left the room.`, 0]);
  updateMessages();
});

socket.on('set-users', (users) => {
  let html = ['<option selected="true" disabled="disabled">select a user</option>'];
  for(let i in users){
    html.push(`<option value='${users[i].id}'>${users[i].name}</option>`);
  }
  document.getElementById('booted-user').innerHTML = html.join('');
});

socket.on('send-msg', (msg) => {
  msg_queue.push(msg);
  updateMessages();
});


socket.on('win', () =>{
  // play song and end our game loop
  song_to_play.play();
  clearInterval(loop);
  loop = 0;
  // sends congrats message (if statement prevents duplicate messages)
  if(!already_sent){
    msg_queue.push(['Server [Team]', 'Congratulations! Your team loaded the song!', 0]);
    msg_queue.push(['Server [Team]', 'Game Over', 0]);
    already_sent = true;
    updateMessages();
  }
});

socket.on('game-loop', (time) => {
  // displays time if at least 1 second has passed since our previous time display
  displayTime(time);
  // starts game loop
  if(loop === 0){
    initLoop()
  // ends loop if out of time and displayes messages
  }else if(prevTime === 0){
    timedOut();
  }
});
