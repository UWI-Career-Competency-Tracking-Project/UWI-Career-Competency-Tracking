function toggleBookmark(element) {
    let card = element.closest(".job-card");
    let container = document.getElementById("jobContainer");

    
    card.classList.toggle("bookmarked");
    element.classList.toggle("active");

    
    if (card.classList.contains("bookmarked")) {
        container.prepend(card);
    } else {
        container.appendChild(card);
    }
}


document.getElementById("searchBar").addEventListener("keyup", function() {
    let filter = this.value.toLowerCase();
    let jobCards = document.querySelectorAll(".job-card");

    jobCards.forEach(card => {
        let title = card.querySelector(".job-title").textContent.toLowerCase();
        card.style.display = title.includes(filter) ? "block" : "none";
    });
});
