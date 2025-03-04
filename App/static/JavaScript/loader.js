var l = document.getElementById("loader");

window.addEventListener("load", function(){
  // Wait 2 seconds after the page loads
  setTimeout(function(){
    l.style.opacity = "0"; // Start fade out (1s transition defined in CSS)
    // After fade-out transition is done, hide the loader completely
    setTimeout(function(){
      l.style.display = "none";
    }, 1000);
  }, 500);
});