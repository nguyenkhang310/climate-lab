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
  if (diemBatDau) lenLichTheQuocGia();
}, true);
document.addEventListener("click", e => {
  if (daKeo && e.detail && e.target.closest("#overview-globe, #globe")) e.stopImmediatePropagation();
  diemBatDau = null;
  daKeo = false;
}, true);

let lichCanBieuDo, rongNoiDung = 0;
function theoDoiBoCuc() {
  const noiDung = document.querySelector(".main");
  if (!noiDung) return requestAnimationFrame(theoDoiBoCuc);
  new ResizeObserver(([khung]) => {
    if (Math.abs(khung.contentRect.width - rongNoiDung) < 1) return;
    rongNoiDung = khung.contentRect.width;
    cancelAnimationFrame(lichCanBieuDo);
    lichCanBieuDo = requestAnimationFrame(() =>
      document.querySelectorAll(".js-plotly-plot").forEach(bieuDo => {
        if (bieuDo.offsetParent) window.Plotly?.Plots.resize(bieuDo);
      })
    );
  }).observe(noiDung);
}
theoDoiBoCuc();

let lichTheQuocGia;
const banDoDaTheoDoi = new WeakSet();
function lenLichTheQuocGia() {
  cancelAnimationFrame(lichTheQuocGia);
  lichTheQuocGia = requestAnimationFrame(capNhatTheQuocGia);
}

function capNhatTheQuocGia() {
  const khung = document.querySelector(".earth-stage");
  const banDo = khung?.querySelector(".js-plotly-plot");
  const the = document.querySelector("#earth-popover");
  if (!the || !banDo?._fullLayout?.geo || !banDo._ev) return;
  if (!banDoDaTheoDoi.has(banDo._ev)) {
    banDoDaTheoDoi.add(banDo._ev);
    banDo.on("plotly_afterplot", lenLichTheQuocGia);
    banDo.on("plotly_relayout", lenLichTheQuocGia);
  }
  const {selected, coordinates, metric, year} = banDo.layout.meta;
  const chuThich = document.querySelector("#earth-map-caption");
  const nhan = `${metric === "co2" ? "Lượng CO₂" : "Chênh nhiệt độ"} · ${year}`;
  if (chuThich.textContent !== nhan) chuThich.textContent = nhan;
  const moc = document.querySelector("#earth-marker");
  const geo = banDo._fullLayout.geo;
  const [lon, lat] = coordinates || [0, 0];
  const goc = Math.PI / 180, xoay = geo.projection.rotation;
  const phiaTruoc = geo.projection.type !== "orthographic" || !coordinates ||
    Math.sin(lat * goc) * Math.sin(xoay.lat * goc) +
    Math.cos(lat * goc) * Math.cos(xoay.lat * goc) * Math.cos((lon - xoay.lon) * goc) > .03;
  the.hidden = selected === "all" || !phiaTruoc;
  moc.hidden = the.hidden || !coordinates;
  if (the.hidden) return;
  const [x, y] = coordinates ? geo._subplot.projection(coordinates) : [khung.clientWidth, 16];
  const benPhai = x >= khung.clientWidth / 2;
  const trai = benPhai ? Math.max(x + 28, khung.clientWidth / 2 + 28)
                      : Math.min(x - the.offsetWidth - 28, khung.clientWidth / 2 - the.offsetWidth - 28);
  the.style.left = `${Math.max(12, Math.min(trai, khung.clientWidth - the.offsetWidth - 12))}px`;
  the.style.top = `${Math.max(12, Math.min(y - the.offsetHeight / 2, banDo.clientHeight - banDo._fullLayout.margin.b - the.offsetHeight - 12))}px`;
  moc.style.left = `${x}px`;
  moc.style.top = `${y}px`;
}
new MutationObserver(lenLichTheQuocGia).observe(document.documentElement, {childList: true, subtree: true});
lenLichTheQuocGia();
document.addEventListener("keydown", e => {
  if (e.key === "Escape" && !e.target.closest(".filter-bar")) document.querySelector("#close-country-panel")?.click();
});
