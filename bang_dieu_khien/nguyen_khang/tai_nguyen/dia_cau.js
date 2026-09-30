const nenBien = document.createElementNS("http://www.w3.org/2000/svg", "svg");
nenBien.setAttribute("aria-hidden", "true");
nenBien.style.cssText = "position:absolute;width:0;height:0;pointer-events:none";
nenBien.innerHTML = `<defs><radialGradient id="mau-bien" cx="32%" cy="25%" r="85%">
  <stop stop-color="#367E98"/><stop offset=".5" stop-color="#163E5C"/>
  <stop offset="1" stop-color="#081D35"/></radialGradient></defs>`;
document.body.append(nenBien);
let diemBatDau = null;
let daKeo = false;
document.addEventListener("pointerdown", e => {
  diemBatDau = e.target.closest("#overview-globe, #globe") ? [e.clientX, e.clientY] : null;
  daKeo = false;
}, true);
document.addEventListener("pointermove", e => {
  if (diemBatDau && Math.hypot(e.clientX - diemBatDau[0], e.clientY - diemBatDau[1]) > 6) daKeo = true;
}, true);
document.addEventListener("click", e => {
  if (daKeo && e.detail && e.target.closest("#overview-globe, #globe")) e.stopImmediatePropagation();
  diemBatDau = null;
  daKeo = false;
}, true);
