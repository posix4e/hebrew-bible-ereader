// Main JavaScript for Torah EPUB site
// Extracted from index.html

// Set current date in footer
document.addEventListener("DOMContentLoaded", function () {
  const updateDateElement = document.getElementById("update-date");
  if (updateDateElement) {
    updateDateElement.textContent = new Date().toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  }
});
