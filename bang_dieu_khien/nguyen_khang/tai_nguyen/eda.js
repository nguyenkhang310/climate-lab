function closeEda(event) {
  if (event.key === "Escape" || event.target.id === "eda-modal") {
    document.querySelector("#eda-modal.open #close-eda-modal")?.click();
  }
}
document.addEventListener("keydown", closeEda);
document.addEventListener("click", closeEda);

document.addEventListener("click", event => {
  const button = event.target.closest(".updatemenu-button");
  const action = button?.__data__;
  const plot = button?.closest(".js-plotly-plot");
  if (!plot || action?.method !== "animate" || action.execute !== false) return;
  Plotly.animate(plot, ...action.args).catch(error => {
    // Plotly hủy promise bằng undefined khi bấm Dừng hoặc đổi bộ lọc.
    if (error !== undefined) console.error(error);
  });
});

function autoplayEdaMap() {
  document.querySelectorAll(".js-plotly-plot").forEach(plot => {
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
