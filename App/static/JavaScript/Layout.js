document.addEventListener("DOMContentLoaded", () => {

    // Profile dropdown functionality with smooth slide
    const dropdown = document.querySelector(".dropdown");
    const dropdownContent = document.querySelector(".dropdown-content");
    dropdownContent.style.transition = "opacity 0.4s ease, transform 0.4s ease";
    dropdownContent.style.opacity = "0";
    dropdownContent.style.transform = "translateY(-20px)";
    dropdownContent.style.display = "none";

    dropdown.addEventListener("click", (e) => {
        e.stopPropagation();
        if (dropdownContent.style.display === "block") {
            dropdownContent.style.opacity = "0";
            dropdownContent.style.transform = "translateY(-20px)";
            setTimeout(() => {
                dropdownContent.style.display = "none";
            }, 400);
        } else {
            dropdownContent.style.display = "block";
            setTimeout(() => {
                dropdownContent.style.opacity = "1";
                dropdownContent.style.transform = "translateY(0)";
            }, 10);
        }
    });

    document.addEventListener("click", (e) => {
        if (!dropdown.contains(e.target) && dropdownContent.style.display === "block") {
            dropdownContent.style.opacity = "0";
            dropdownContent.style.transform = "translateY(-20px)";
            setTimeout(() => {
                dropdownContent.style.display = "none";
            }, 400);
        }
    });
});