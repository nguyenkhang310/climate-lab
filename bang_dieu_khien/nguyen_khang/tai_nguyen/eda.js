
function closeEda(event) {
  if (event.key === "Escape" || event.target.id === "eda-modal") {
    document.querySelector("#eda-modal.open #close-eda-modal")?.click();
  }
}
document.addEventListener("keydown", closeEda);
document.addEventListener("click", closeEda);
