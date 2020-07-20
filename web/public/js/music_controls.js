let songs = {}
function play_frame(url){
  resetAudio();
  if(!songs[url]) // if song not loaded
    songs[url] = new Audio(url);
  songs[url].play();
}
function toggle_frame(url){
  if(!songs[url]) // if song not loaded
    songs[url] = new Audio(url);
  let wasPaused = songs[url].paused;
  resetAudio();
  if(wasPaused)
    songs[url].play();
}
function resetAudio(){
  for(key in songs){
    songs[key].currentTime = 0;
    songs[key].pause();
  }
}
