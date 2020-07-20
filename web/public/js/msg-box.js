let current_frame = 0;
let history = []
let historyIndex = 0;

function scrolledUp(e){
  return e.scrollTop < (e.scrollHeight - 200)
}

function updateMessages(){
  document.getElementById('msg-wrapper').className = 'msg-wrapper timer-mode';
  let e = document.getElementById('msg-box');
  let btn = document.getElementById('auto-scroll');
  while(0 < msg_queue.length){
    let data = msg_queue.shift();
    let msg = createMsgNode(data[0], data[1], data[2]);
    // scrolls down if user isnt looking at old messages
    if(scrolledUp(e)){ // if scrolled up
      if(btn.style.display !== 'block'){ // check if already displayed
        btn.style.display = 'block';
        e.style.height = '175px';
      }
      e.appendChild(msg)
    }else if(!scrolledUp(e)){ // if not scrolling
      e.appendChild(msg)
      e.scrollTo(0, e.scrollHeight);
    }
  }
  if(activeLoop === false && document.getElementById('msg-wrapper').className === 'msg-wrapper timer-mode'){
    setTimeout(() => {
      document.getElementById('msg-wrapper').className = 'msg-wrapper';
    },2000);
  }
}

function scrollBottom(){
  let e = document.getElementById('msg-box');
  let btn = document.getElementById('auto-scroll');
  if(scrolledUp(e))
    e.scrollTo(0, e.scrollHeight);
  btn.style.display = 'none';
  e.style.height = '200px';
}

function createMsgNode(sender, msg, flag=0){
  let node = document.createElement('div'); // wrapper
  let p = document.createElement('p'); // holds text
  let span = document.createElement('span'); // sender space
  let text = document.createTextNode(msg);
  sender = document.createTextNode(sender);
  if(flag === 1){
    span.style.color = '#ffff00';
  }else if(flag === 2){
    span.style.color = '#ffd500';
    p.style.color = '#ffd500';
  }else if(flag === 3){
    span.style.color = '#61afef';
  }else if(flag === 4){
    span.style.color = '#90ee90';
  }else if(flag === 5){
    span.style.color = '#ff4d4d';
  }
  span.appendChild(sender);
  p.appendChild(span);
  p.appendChild(text);
  node.appendChild(p);
  node.className = 'msg-node';
  return node;
}

function dragElement(elmnt) {
  var pos1 = 0, pos2 = 0, pos3 = 0, pos4 = 0;
  if (document.getElementById('drag-space')) {
    /* if present, the header is where you move the DIV from:*/
    document.getElementById('drag-space').onmousedown = dragMouseDown;
  } else {
    /* otherwise, move the DIV from anywhere inside the DIV:*/
    elmnt.onmousedown = dragMouseDown;
  }
  function dragMouseDown(e) {
    document.getElementById('drag-space').style.background = 'red';
    e = e || window.event;
    e.preventDefault();
    // get the mouse cursor position at startup:
    pos3 = e.clientX;
    pos4 = e.clientY;
    document.onmouseup = closeDragElement;
    // call a function whenever the cursor moves:
    document.onmousemove = elementDrag;
  }
  function elementDrag(e) {
    e = e || window.event;
    e.preventDefault();
    // calculate the new cursor position:
    pos1 = pos3 - e.clientX;
    pos2 = pos4 - e.clientY;
    pos3 = e.clientX;
    pos4 = e.clientY;
    // set the element's new position:
    elmnt.style.top = (elmnt.offsetTop - pos2) + "px";
    elmnt.style.left = (elmnt.offsetLeft - pos1) + "px";
  }
  function closeDragElement() {
    document.getElementById('drag-space').style.background = 'rgba(50,50,50,0.6)';
    /* stop moving when mouse button is released:*/
    document.onmouseup = null;
    document.onmousemove = null;
  }
}

function adjust(){
  let e = document.getElementById('msg-box');
  let msg = document.getElementById('auto-scroll');
  if(!scrolledUp(e) && msg.style.display !== 'none')
    scrollBottom()
}

function insertHistory(val){
  if(historyIndex > 0){
     history.splice(0, historyIndex);
     historyIndex = 0;
     history.unshift('');
  }else if(val !== history[1]){
    history.unshift('');
  }
}

function sendMsg(to, msg){
  socket.emit('send-msg', to, msg);
}

function userInput(){
  let key = event.keyCode;
  // enter
  let e = document.getElementById('user-input');
  let val = e.value.trim();
  if(key === 13 && val.length > 0){
    insertHistory(val);
    let lowerdVal = val.toLowerCase()
    if(lowerdVal.indexOf('/team ') === 0){
      sendMsg(val.substr(0, 5), val.substr(5).trim());
    }else if(lowerdVal.indexOf('/all ') === 0){
      sendMsg(val.substr(0, 4), val.substr(4).trim());
    }else if(lowerdVal.indexOf('/private ') === 0){
      sendMsg(val.substr(0, 8), val.substr(8).trim());
    }else if(lowerdVal.indexOf('/kick ') === 0){
      socket.emit('kick-user', val.substr(5).trim());
    }else if(lowerdVal.indexOf('/list') === 0){
      socket.emit('list-users', val.substr(5).trim());
    }else if(lowerdVal.indexOf('/admin ') === 0){
      sendMsg(val.substr(0, 6), val.substr(6).trim());
    }else if(lowerdVal === '/ready'){
      ready();
    }else if(lowerdVal === '/clear'){
      document.getElementById('msg-box').innerHTML = '';
    }else if(prevTime > 0){
      submitFrame(val);
    }else{
      msg_queue.push(['Server', 'The game has not started yet. Did you mean to send a message?']);
      updateMessages();
    }
    e.value = '';
  // down arrow
  }else if(key === 40 && historyIndex > 0){
    historyIndex -= 1;
    e.value = history[historyIndex];
  // up arrow
  }else if(key === 38 && history.length > 0 && historyIndex < history.length - 1){
    historyIndex += 1;
    e.value = history[historyIndex];
  // save text modifications
  }else if(val.length > 0){
    history[historyIndex] = val;
  }
}

setTimeout(() => {
  dragElement(document.getElementById("msg-wrapper"));
  document.getElementById('user-input').addEventListener("focus", () => {
    document.getElementById('msg-wrapper').className = 'msg-wrapper timer-mode';
  });
  document.getElementById('user-input').addEventListener("blur", () => {
    if(activeLoop === false && document.getElementById('msg-wrapper').className === 'msg-wrapper timer-mode')
      document.getElementById('msg-wrapper').className = 'msg-wrapper';
  });
  document.getElementById('user-input').addEventListener("input", () => {
    if(document.getElementById('msg-wrapper').className === 'msg-wrapper')
      document.getElementById('msg-wrapper').className = 'msg-wrapper timer-mode';
  });
}, 500);

function toggleMsgHelp(){
  let e = document.getElementById("msg-box-help");
  if(e.style.display === "none"){
    e.style.display = "block";
  }else{
    e.style.display = "none";
  }
}
