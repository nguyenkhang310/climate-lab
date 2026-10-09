function closeEda(event) {
  if (event.key === "Escape" || event.target.id === "eda-modal") {
    document.querySelector("#eda-modal.open #close-eda-modal")?.click();
  }
}
document.addEventListener("keydown", closeEda);
document.addEventListener("click", closeEda);

function autoplayEdaMap() {
  document.querySelectorAll(".eda-gallery .js-plotly-plot").forEach(plot => {
    const play = plot.querySelector(".slider-container")
      && plot.querySelector(".updatemenu-button");
    if (!play || plot.dataset.edaAutoplay) return;
    plot.dataset.edaAutoplay = "true";
    setTimeout(() => play.dispatchEvent(new MouseEvent("click", {bubbles: true})), 500);
  });
}

new MutationObserver(autoplayEdaMap).observe(document.documentElement, {
  childList: true,
  subtree: true,
});
autoplayEdaMap();
