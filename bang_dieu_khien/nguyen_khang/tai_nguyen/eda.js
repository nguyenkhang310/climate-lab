function closeEda(event) {
  if (event.key === "Escape" || event.target.id === "eda-modal") {
    document.querySelector("#eda-modal.open #close-eda-modal")?.click();
  }
}
document.addEventListener("keydown", closeEda);
document.addEventListener("click", closeEda);

const edaAnimations = new Map();
function cleanupEdaAnimations() {
  edaAnimations.forEach((animation, plot) => {
    if (!plot.isConnected || animation !== plot._transitionData) {
      const remaining = animation._frameQueue?.map(frame => frame.name);
      cancelAnimationFrame(animation._animationRaf);
      edaAnimations.delete(plot);
      if (plot.isConnected && remaining?.length) requestAnimationFrame(() => {
        if (!plot.isConnected || edaAnimations.has(plot)) return;
        const frames = remaining.filter(name => plot._transitionData?._frameHash[name]);
        if (frames.length) animateEda(plot, [frames, plot.layout.updatemenus[0].buttons[0].args[1]]);
      });
    }
  });
}

function animateEda(plot, args) {
  cleanupEdaAnimations();
  edaAnimations.set(plot, plot._transitionData);
  return window.Plotly.animate(plot, ...args)
    .catch(error => { if (error !== undefined) throw error; });
}

function pauseEda(plot) {
  if (plot._transitionData?._animationRaf) {
    animateEda(plot, [[null], {
      mode: "immediate", frame: {duration: 0, redraw: false}, transition: {duration: 0}
    }]);
  }
}

function stopEdaAnimation(event) {
  if (event.key !== "Escape" && !event.target.closest(
    'a[href^="#"], #filter-bar, .eda-expand-button, #close-eda-modal'
  ) && event.target.id !== "eda-modal") return;
  document.querySelectorAll(".js-plotly-plot").forEach(pauseEda);
}
document.addEventListener("click", stopEdaAnimation, true);
document.addEventListener("keydown", stopEdaAnimation, true);

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
  document.querySelectorAll(".eda-gallery .js-plotly-plot, .eda-modal-chart .js-plotly-plot").forEach(plot => {
    const play = plot.querySelector(".slider-container")
      && plot.querySelector(".updatemenu-button");
    if (!play || !plot._ev || plot._ev.listeners("plotly_buttonclicked")
        .some(handler => handler.name === "handleEdaButton")) return;
    plot.on("plotly_click", () => pauseEda(plot));
    const timer = setTimeout(() => {
      if (!plot.closest(".eda-gallery") || !plot.isConnected || !plot._fullLayout
          || plot._transitionData?._animationRaf) return;
      animateEda(plot, plot.layout.updatemenus[0].buttons[0].args);
    }, 500);
    plot.on("plotly_buttonclicked", function handleEdaButton(event) {
      clearTimeout(timer);
      animateEda(plot, event.button.args);
    });
    plot.on("plotly_sliderchange", event => {
      if (event.interaction) {
        clearTimeout(timer);
        animateEda(plot, event.step.args);
      }
    });
    plot.once("plotly_sliderstart", () => clearTimeout(timer));
  });
}

new MutationObserver(() => {
  cleanupEdaAnimations();
  syncEdaModal();
  autoplayEdaMap();
}).observe(document.documentElement, {
  childList: true,
  subtree: true,
});
autoplayEdaMap();
