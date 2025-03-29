var l = document.getElementById("loader");

window.addEventListener("load", function(){
  hideLoader();
  setTimeout(hideLoader, 5000); 
});

function hideLoader() {
  if (l) {
    l.style.opacity = "0";
    setTimeout(function(){
      l.style.display = "none";
    }, 1000);
  }
}