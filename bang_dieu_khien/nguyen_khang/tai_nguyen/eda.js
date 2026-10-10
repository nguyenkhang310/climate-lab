function closeEda(event) {
  if (event.key === "Escape" || event.target.id === "eda-modal") {
    document.querySelector("#eda-modal.open #close-eda-modal")?.click();
  }
}
document.addEventListener("keydown", closeEda);
document.addEventListener("click", closeEda);

function syncEdaModal() {
  const body = document.body;
  const open = !!document.querySelector("#eda-modal.open");
  if (open === (body.style.overflow === "hidden")) return;
  const width = body.clientWidth;
  const top = window.scrollY;
  body.style.overflow = open ? "hidden" : "";
  body.style.width = open ? `calc(100% - ${body.clientWidth - width}px)` : "";
  window.scrollTo(0, top);
}

function autoplayEdaMap() {
  document.querySelectorAll(".eda-gallery .js-plotly-plot").forEach(plot => {
    const play = plot.querySelector(".slider-container")
      && plot.querySelector(".updatemenu-button");
    if (!play || plot.dataset.edaAutoplay) return;
    plot.dataset.edaAutoplay = "true";
    setTimeout(() => play.dispatchEvent(new MouseEvent("click", {bubbles: true})), 500);
  });
}

new MutationObserver(() => {
  syncEdaModal();
  autoplayEdaMap();
}).observe(document.documentElement, {
  childList: true,
  subtree: true,
});
autoplayEdaMap();
