function closeEda(event) {
  if (event.key === "Escape" || event.target.id === "eda-modal") {
    document.querySelector("#eda-modal.open #close-eda-modal")?.click();
  }
}
document.addEventListener("keydown", closeEda);
document.addEventListener("click", closeEda);
document.addEventListener("pointerdown", event => {
  const plot = event.target.closest(".slider-container")?.closest(".js-plotly-plot");
  if (plot?.layout.meta?.autoplay) Plotly.relayout(plot, {"meta.autoplay": false});
});

setInterval(() => {
  if (document.hidden || !window.Plotly) return;
  const scope = document.querySelector("#eda-modal.open") || document;
  for (const plot of scope.querySelectorAll(".js-plotly-plot")) {
    const frames = plot._transitionData?._frames;
    if (!plot.layout?.meta?.autoplay || !frames?.length || plot.edaAnimating) continue;
    const next = (plot.layout.sliders[0].active + 1) % frames.length;
    plot.edaAnimating = true;
    Plotly.animate(plot, [frames[next].name], {
      mode: "immediate", frame: {duration: 0, redraw: true}, transition: {duration: 0}
    }).catch(error => {
      if (error !== undefined) console.error(error);
    }).finally(() => { plot.edaAnimating = false; });
  }
}, 1500);
