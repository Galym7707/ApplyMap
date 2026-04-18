const path = require("path");
const pptxgen = require("pptxgenjs");
const {
  imageSizingContain,
  safeOuterShadow,
  warnIfSlideHasOverlaps,
  warnIfSlideElementsOutOfBounds,
} = require("./pptxgenjs_helpers");

const pptx = new pptxgen();
pptx.defineLayout({ name: "CUSTOM_WIDE", width: 13.333, height: 7.5 });
pptx.layout = "CUSTOM_WIDE";
pptx.author = "ApplyMap";
pptx.company = "ApplyMap";
pptx.subject = "Samsung Solve for Tomorrow Kazakhstan - презентация на 12 слайдов";
pptx.title = "ApplyMap для Samsung Solve for Tomorrow";
pptx.lang = "ru-RU";
pptx.theme = {
  headFontFace: "Arial",
  bodyFontFace: "Arial",
  lang: "ru-RU",
};

const W = 13.333;
const H = 7.5;
const logoPath = path.join(__dirname, "applymap-logo.png");
const outPath = path.join(__dirname, "ApplyMap_Samsung_Solve_For_Tomorrow_12_slides.pptx");

const C = {
  white: "FFFFFF",
  ink: "08090D",
  muted: "5F687A",
  faint: "EEF2F7",
  panel: "F8FAFC",
  line: "D9E0EC",
  navy: "11135F",
  blue: "3147FF",
  sky: "E7EEFF",
  green: "12845B",
  greenSoft: "EAF8F1",
  amber: "B45309",
  amberSoft: "FFF7E6",
  red: "D92D20",
};

function addFooter(slide, n, source) {
  slide.addText(String(n).padStart(2, "0"), {
    x: 0.42,
    y: 7.06,
    w: 0.38,
    h: 0.16,
    fontFace: "Arial",
    fontSize: 7.2,
    bold: true,
    color: "A5AEC0",
    margin: 0,
  });
  if (source) {
    slide.addText(source, {
      x: 0.86,
      y: 7.03,
      w: 11.95,
      h: 0.2,
      fontFace: "Arial",
      fontSize: 6.9,
      color: "98A2B3",
      margin: 0,
      breakLine: false,
    });
  }
}

function addLogo(slide, x = 0.58, y = 0.42, size = 0.4) {
  slide.addImage({ path: logoPath, ...imageSizingContain(logoPath, x, y, size, size) });
  slide.addText("ApplyMap", {
    x: x + size + 0.13,
    y: y + 0.1,
    w: 1.5,
    h: 0.2,
    fontFace: "Arial",
    fontSize: 10.5,
    bold: true,
    color: C.ink,
    margin: 0,
  });
}

function title(slide, text, x = 0.58, y = 0.75, w = 8.8, h = 0.82, size = 27) {
  slide.addText(text, {
    x,
    y,
    w,
    h,
    fontFace: "Arial",
    fontSize: size,
    bold: true,
    color: C.ink,
    margin: 0,
    valign: "top",
    breakLine: false,
  });
}

function kicker(slide, text, x = 0.58, y = 0.48, w = 5.5) {
  slide.addText(text.toUpperCase(), {
    x,
    y,
    w,
    h: 0.17,
    fontFace: "Arial",
    fontSize: 7.4,
    bold: true,
    color: "98A2B3",
    charSpace: 2.6,
    margin: 0,
  });
}

function p(slide, text, x, y, w, h, opts = {}) {
  slide.addText(text, {
    x,
    y,
    w,
    h,
    fontFace: "Arial",
    fontSize: opts.size || 14.6,
    bold: opts.bold || false,
    color: opts.color || C.ink,
    margin: opts.margin ?? 0,
    valign: "top",
    breakLine: false,
    breakLineOnHyphen: false,
  });
}

function label(slide, text, x, y, w = 2) {
  slide.addText(text.toUpperCase(), {
    x,
    y,
    w,
    h: 0.15,
    fontFace: "Arial",
    fontSize: 7.3,
    bold: true,
    color: "98A2B3",
    charSpace: 2.2,
    margin: 0,
  });
}

function card(slide, x, y, w, h, opts = {}) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x,
    y,
    w,
    h,
    rectRadius: 0.08,
    fill: { color: opts.fill || C.white },
    line: { color: opts.line || C.line, transparency: opts.lineTransparency ?? 0 },
    shadow: opts.shadow ? safeOuterShadow("000000", 0.1, 45, 2, 1) : undefined,
  });
}

function kpi(slide, value, labelText, x, y, w, opts = {}) {
  card(slide, x, y, w, 1.28, { fill: opts.fill || C.panel, line: opts.line || C.line });
  slide.addText(value, {
    x: x + 0.22,
    y: y + 0.21,
    w: w - 0.44,
    h: 0.36,
    fontFace: "Arial",
    fontSize: opts.size || 22,
    bold: true,
    color: opts.color || C.navy,
    margin: 0,
  });
  p(slide, labelText, x + 0.22, y + 0.72, w - 0.44, 0.33, {
    size: 9.6,
    color: C.muted,
  });
}

function bulletList(slide, items, x, y, w, opts = {}) {
  const gap = opts.gap || 0.5;
  items.forEach((item, i) => {
    const yy = y + i * gap;
    slide.addText("-", {
      x,
      y: yy + 0.01,
      w: 0.18,
      h: 0.18,
      fontFace: "Arial",
      fontSize: opts.size || 14.4,
      bold: true,
      color: opts.bulletColor || C.ink,
      margin: 0,
    });
    p(slide, item, x + 0.28, yy, w - 0.28, opts.itemH || 0.34, {
      size: opts.size || 14.4,
      color: opts.color || C.ink,
    });
  });
}

function smallTag(slide, text, x, y, w, opts = {}) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x,
    y,
    w,
    h: 0.28,
    rectRadius: 0.08,
    fill: { color: opts.fill || C.sky },
    line: { color: opts.fill || C.sky },
  });
  slide.addText(text, {
    x: x + 0.07,
    y: y + 0.075,
    w: w - 0.14,
    h: 0.12,
    fontFace: "Arial",
    fontSize: 7.4,
    bold: true,
    color: opts.color || C.navy,
    align: "center",
    margin: 0,
  });
}

function divider(slide, y) {
  slide.addShape(pptx.ShapeType.line, {
    x: 0.58,
    y,
    w: 12.16,
    h: 0,
    line: { color: "E5EAF2", width: 1 },
  });
}

function line(slide, x, y, w, h, opts = {}) {
  slide.addShape(pptx.ShapeType.line, {
    x,
    y,
    w,
    h,
    line: { color: opts.color || C.line, width: opts.width || 1.2, beginArrowType: opts.begin, endArrowType: opts.end },
  });
}

function studentLaptopVisual(slide, x, y, w, h) {
  card(slide, x, y, w, h, { fill: "F7F9FC", line: "E5EAF2" });
  slide.addShape(pptx.ShapeType.arc, {
    x: x + 0.36,
    y: y + 0.42,
    w: w - 0.72,
    h: h - 0.72,
    line: { color: "E1E7F0", width: 1.4 },
    adjustPoint: 0.25,
  });
  slide.addShape(pptx.ShapeType.ellipse, {
    x: x + 1.05,
    y: y + 0.82,
    w: 0.78,
    h: 0.78,
    fill: { color: "DDE7FF" },
    line: { color: "DDE7FF" },
  });
  slide.addShape(pptx.ShapeType.arc, {
    x: x + 0.78,
    y: y + 1.5,
    w: 1.28,
    h: 1.18,
    line: { color: C.navy, width: 2 },
    adjustPoint: 0.35,
  });
  slide.addShape(pptx.ShapeType.roundRect, {
    x: x + 2.18,
    y: y + 1.06,
    w: 2.5,
    h: 1.52,
    rectRadius: 0.06,
    fill: { color: C.white },
    line: { color: C.navy, width: 1.5 },
  });
  slide.addShape(pptx.ShapeType.rect, {
    x: x + 2.37,
    y: y + 1.25,
    w: 2.12,
    h: 1.04,
    fill: { color: "EEF3FF" },
    line: { color: "EEF3FF" },
  });
  line(slide, x + 2.58, y + 1.5, 1.18, 0, { color: C.blue, width: 2 });
  line(slide, x + 2.58, y + 1.78, 1.58, 0, { color: C.green, width: 2 });
  slide.addShape(pptx.ShapeType.trapezoid, {
    x: x + 1.92,
    y: y + 2.62,
    w: 3.02,
    h: 0.35,
    fill: { color: C.navy },
    line: { color: C.navy },
    rotate: 180,
  });
  slide.addText("Навигация для школьников Казахстана", {
    x: x + 0.46,
    y: y + h - 0.58,
    w: w - 0.92,
    h: 0.18,
    fontFace: "Arial",
    fontSize: 8,
    color: C.muted,
    align: "center",
    margin: 0,
  });
}

function kazakhstanNetworkVisual(slide, x, y, w, h) {
  card(slide, x, y, w, h, { fill: "F8FAFC" });
  p(slide, "Казахстан", x + 0.28, y + 0.22, 2.2, 0.22, { size: 14.2, bold: true });
  const dots = [
    [0.16, 0.58, C.blue], [0.32, 0.4, C.green], [0.52, 0.62, C.blue],
    [0.66, 0.45, C.green], [0.8, 0.7, C.blue], [0.92, 0.42, C.green],
    [0.3, 0.82, C.green], [0.5, 0.88, C.blue], [0.7, 0.84, C.green],
    [0.9, 0.9, C.blue],
  ];
  dots.forEach((d, idx) => {
    const [rx, ry, color] = d;
    const dx = rx * w;
    const dy = ry * h;
    slide.addShape(pptx.ShapeType.ellipse, {
      x: x + dx,
      y: y + dy,
      w: idx % 3 === 0 ? 0.18 : 0.13,
      h: idx % 3 === 0 ? 0.18 : 0.13,
      fill: { color },
      line: { color },
    });
    if (idx > 0) {
      const prev = dots[idx - 1];
      const px = prev[0] * w;
      const py = prev[1] * h;
      line(slide, x + px + 0.07, y + py + 0.07, dx - px, dy - py, { color: "CCD6E6", width: 0.75 });
    }
  });
  smallTag(slide, "город", x + w - 1.42, y + h - 0.38, 0.62, { fill: "E7EEFF", color: C.blue });
  smallTag(slide, "село", x + w - 0.72, y + h - 0.38, 0.58, { fill: "EAF8F1", color: C.green });
}

function simpleIcon(slide, type, x, y, s = 0.52, color = C.navy) {
  if (type === "school") {
    slide.addShape(pptx.ShapeType.homePlate, { x, y: y + 0.02, w: s, h: s * 0.72, fill: { color: "FFFFFF", transparency: 100 }, line: { color, width: 1.4 } });
    line(slide, x + s * 0.1, y + s * 0.4, s * 0.8, 0, { color, width: 1.2 });
    line(slide, x + s * 0.25, y + s * 0.72, 0, -s * 0.28, { color, width: 1.2 });
    line(slide, x + s * 0.5, y + s * 0.72, 0, -s * 0.28, { color, width: 1.2 });
    line(slide, x + s * 0.75, y + s * 0.72, 0, -s * 0.28, { color, width: 1.2 });
  } else if (type === "person") {
    slide.addShape(pptx.ShapeType.ellipse, { x: x + s * 0.32, y, w: s * 0.36, h: s * 0.36, fill: { color }, line: { color } });
    slide.addShape(pptx.ShapeType.arc, { x: x + s * 0.12, y: y + s * 0.34, w: s * 0.76, h: s * 0.52, line: { color, width: 1.7 }, adjustPoint: 0.25 });
  } else if (type === "question") {
    slide.addShape(pptx.ShapeType.ellipse, { x, y, w: s, h: s, fill: { color: "FFFFFF" }, line: { color, width: 1.3 } });
    slide.addText("?", { x, y: y + s * 0.16, w: s, h: s * 0.4, fontSize: 18, bold: true, color, align: "center", margin: 0 });
  } else if (type === "route") {
    slide.addShape(pptx.ShapeType.ellipse, { x, y: y + s * 0.1, w: s * 0.16, h: s * 0.16, fill: { color }, line: { color } });
    line(slide, x + s * 0.12, y + s * 0.18, s * 0.7, s * 0.44, { color, width: 1.2 });
    slide.addShape(pptx.ShapeType.ellipse, { x: x + s * 0.77, y: y + s * 0.58, w: s * 0.2, h: s * 0.2, fill: { color }, line: { color } });
  }
}

function validate(slide, opts = {}) {
  warnIfSlideElementsOutOfBounds(slide, pptx);
  if (!opts.allowIntentionalOverlap) {
    warnIfSlideHasOverlaps(slide, pptx, {
      ignoreLines: true,
      ignoreDecorativeShapes: true,
      muteContainment: true,
    });
  }
}

let slideNo = 1;
function newSlide(source) {
  const slide = pptx.addSlide();
  slide.background = { color: C.white };
  addFooter(slide, slideNo, source);
  slideNo += 1;
  return slide;
}

// 1. Cover
{
  const slide = newSlide("Визуал: нейтральная иллюстрация продукта, не документальное фото.");
  addLogo(slide, 0.64, 0.5, 0.52);
  title(slide, "ApplyMap", 0.72, 1.46, 5.2, 0.62, 34);
  p(
    slide,
    "Цифровой проводник для школьников Казахстана, которым не хватает качественной навигации по поступлению",
    0.76,
    2.28,
    6.15,
    0.86,
    { size: 19.5, color: C.ink },
  );
  p(slide, "STEM-решение для снижения образовательного неравенства", 0.78, 4.02, 5.2, 0.28, { size: 13.2, bold: true, color: C.navy });
  studentLaptopVisual(slide, 7.02, 0.72, 5.46, 5.72);
  // The cover visual intentionally layers editable shapes to create a laptop/student illustration.
  validate(slide, { allowIntentionalOverlap: true });
}

// 2. Scale of problem
{
  const slide = newSlide("Источники: БНС, Образование в РК 2019-2023; Минпросвещения, итоги 2023/24.");
  kicker(slide, "масштаб проблемы");
  title(slide, "Проблема касается сотен тысяч школьников", 0.58, 0.78, 9.2, 0.62, 27);
  p(
    slide,
    "В 2023/24 учебном году в школах Казахстана обучались 3 819 071 ученик. Из них 1 555 132 - в сельской местности. Только в 10-11 классах было около 402 906 учеников, а выпускников 11 класса - около 186 тысяч. Это значит, что ежегодно огромная группа школьников одновременно принимает решения о будущем обучении, но не у всех есть доступ к качественной навигационной поддержке.",
    0.62,
    1.58,
    7.0,
    1.2,
    { size: 14.3, color: C.muted },
  );
  kpi(slide, "3.8 млн", "школьников в системе", 0.66, 3.2, 3.25);
  kpi(slide, "1.56 млн", "сельских школьников", 4.22, 3.2, 3.25, { color: C.green, fill: C.greenSoft, line: "CAEEDB" });
  kpi(slide, "~403 тыс.", "учеников 10-11 классов", 7.78, 3.2, 3.25, { color: C.blue, fill: C.sky, line: "D6E0FF" });
  kazakhstanNetworkVisual(slide, 8.18, 1.66, 3.88, 1.28);
  p(slide, "Расчет: 10 класс 217 268 + 11 класс 185 638 = 402 906.", 0.7, 5.28, 6.7, 0.22, { size: 8.8, color: "98A2B3" });
  // The Kazakhstan network visual uses connected dots, so small line/dot overlaps are intentional.
  validate(slide, { allowIntentionalOverlap: true });
}

// 3. Guidance gap
{
  const slide = newSlide("Источники: OECD Skills Strategy Kazakhstan, p.134; таблицы БНС по школьной сети, 2023/24.");
  kicker(slide, "разрыв в поддержке");
  title(slide, "Не всем школьникам доступна одинаковая помощь", 0.58, 0.78, 9.0, 0.62, 27);
  card(slide, 0.72, 1.78, 4.42, 3.98, { fill: C.panel });
  slide.addText("67%", {
    x: 1.05,
    y: 2.26,
    w: 3.2,
    h: 0.72,
    fontFace: "Arial",
    fontSize: 45,
    bold: true,
    color: C.navy,
    margin: 0,
  });
  p(slide, "школьной сети страны составляют сельские школы", 1.07, 3.16, 3.34, 0.48, { size: 15.8 });
  simpleIcon(slide, "school", 1.0, 4.36, 0.64, C.green);
  simpleIcon(slide, "route", 2.46, 4.4, 0.64, C.blue);
  simpleIcon(slide, "question", 3.92, 4.34, 0.64, C.amber);
  card(slide, 5.72, 1.78, 6.6, 3.98, { fill: "FFFFFF" });
  label(slide, "цитата OECD", 6.12, 2.2, 1.55);
  p(slide, "\"Школы обычно не предоставляют карьерное консультирование.\"", 6.12, 2.64, 4.95, 0.62, { size: 19, bold: true, color: C.ink });
  p(
    slide,
    "OECD также отмечает, что карьерное консультирование в Казахстане в основном дают центры занятости и частные агентства. Это создает практический разрыв для учеников, которым нужна регулярная, понятная и качественная помощь.",
    6.12,
    3.54,
    5.42,
    0.92,
    { size: 13.6, color: C.muted },
  );
  p(slide, "ApplyMap закрывает этот разрыв как цифровой слой навигации по поступлению.", 6.12, 5.06, 5.2, 0.28, { size: 13.8, bold: true, color: C.navy });
  // Icons are built from layered editable primitives.
  validate(slide, { allowIntentionalOverlap: true });
}

// 4. International path
{
  const slide = newSlide("Источники: World Bank на основе UNESCO UIS; отчет Open Doors Kazakhstan 2024.");
  kicker(slide, "международная траектория");
  title(slide, "Международная образовательная траектория уже массовая", 0.58, 0.78, 9.8, 0.68, 26);
  p(
    slide,
    "Казахстан уже давно не ограничивается только внутренними траекториями. По данным World Bank на основе UNESCO UIS, у Казахстана было 90 333 студента высшего образования за рубежом, при этом 78% из них учились в России. По данным Open Doors, число студентов из Казахстана в США выросло с 2 440 в 2022/23 до 2 712 в 2023/24.",
    0.62,
    1.6,
    7.2,
    0.95,
    { size: 14.2, color: C.muted },
  );
  card(slide, 0.74, 3.08, 5.78, 1.56, { fill: C.panel });
  p(slide, "90 333 студента за рубежом", 1.0, 3.38, 3.55, 0.28, { size: 17.4, bold: true, color: C.navy });
  slide.addShape(pptx.ShapeType.rect, { x: 1.02, y: 3.96, w: 4.7, h: 0.18, fill: { color: "E2E8F0" }, line: { color: "E2E8F0" } });
  slide.addShape(pptx.ShapeType.rect, { x: 1.02, y: 3.96, w: 3.66, h: 0.18, fill: { color: C.green }, line: { color: C.green } });
  p(slide, "78% Россия", 4.82, 4.2, 1.2, 0.2, { size: 10.3, bold: true, color: C.green });
  card(slide, 7.12, 3.08, 4.95, 1.56, { fill: "FFFFFF" });
  p(slide, "Студенты из Казахстана в США", 7.38, 3.38, 3.2, 0.22, { size: 13.2, bold: true });
  p(slide, "2,440", 7.4, 4.28, 0.86, 0.18, { size: 10.8, bold: true, color: C.muted });
  p(slide, "2,712", 10.62, 3.34, 0.86, 0.18, { size: 10.8, bold: true, color: C.navy });
  line(slide, 8.02, 4.14, 2.8, -0.44, { color: C.blue, width: 2.2 });
  slide.addShape(pptx.ShapeType.ellipse, { x: 7.94, y: 4.06, w: 0.16, h: 0.16, fill: { color: C.blue }, line: { color: C.blue } });
  slide.addShape(pptx.ShapeType.ellipse, { x: 10.74, y: 3.62, w: 0.16, h: 0.16, fill: { color: C.blue }, line: { color: C.blue } });
  p(slide, "2022/23", 7.7, 4.36, 0.82, 0.16, { size: 8.8, color: C.muted });
  p(slide, "2023/24", 10.44, 4.36, 0.82, 0.16, { size: 8.8, color: C.muted });
  p(slide, "Казахстан", 8.0, 5.46, 1.1, 0.18, { size: 10.2, bold: true });
  line(slide, 9.03, 5.54, 0.88, 0, { color: C.line, width: 1.2, end: "triangle" });
  p(slide, "Россия / США / другие направления", 10.04, 5.46, 2.55, 0.18, { size: 10.2, bold: true });
  // The mini-chart intentionally overlays dots on the trend line.
  validate(slide, { allowIntentionalOverlap: true });
}

// 5. User pain
{
  const slide = newSlide("Источник: синтез проблемы из предоставленного PDF и стратегии ApplyMap.");
  kicker(slide, "путь ученика");
  title(slide, "Сильные ученики теряются не из-за отсутствия потенциала, а из-за хаоса", 0.58, 0.78, 11.0, 0.76, 25);
  p(
    slide,
    "У многих школьников уже есть реальные достижения: олимпиады, проекты, волонтерство, семейные обязанности, школьные инициативы. Но эти факты разбросаны по PDF, грамотам, чатам и заметкам.",
    0.62,
    1.72,
    11.0,
    0.52,
    { size: 14.2, color: C.muted },
  );
  const items = [
    ["ГРАМОТЫ", "олимпиады / конкурсы"],
    ["ЧАТЫ", "проекты / договоренности"],
    ["ЗАМЕТКИ", "черновики опыта"],
    ["ДЕДЛАЙНЫ", "даты и требования"],
  ];
  items.forEach((item, i) => {
    const x = 0.82 + i * 1.58;
    card(slide, x, 3.0, 1.18, 0.95, { fill: C.panel });
    label(slide, item[0], x + 0.18, 3.22, 0.78);
    p(slide, item[1], x + 0.18, 3.5, 0.88, 0.28, { size: 8.4, color: C.muted });
  });
  line(slide, 7.08, 3.48, 0.62, 0, { color: C.line, width: 1.8, end: "triangle" });
  card(slide, 7.88, 2.72, 1.55, 1.52, { fill: C.amberSoft, line: "F4D19E" });
  p(slide, "хаос", 8.13, 3.22, 1.02, 0.26, { size: 18.5, bold: true, color: C.amber });
  line(slide, 9.64, 3.48, 0.62, 0, { color: C.line, width: 1.8, end: "triangle" });
  card(slide, 10.48, 2.72, 1.85, 1.52, { fill: "FFF1F0", line: "FBC9C4" });
  p(slide, "слабая заявка", 10.74, 3.08, 1.28, 0.36, { size: 14.2, bold: true, color: C.red });
  p(slide, "ошибки в выборе и подаче", 10.75, 3.62, 1.25, 0.24, { size: 8.4, color: C.muted });
  p(slide, "Ученик не понимает, что считать сильным сигналом, как описать опыт на английском, какие университеты подходят и на что не стоит тратить время.", 0.82, 5.22, 10.9, 0.44, { size: 15.3, bold: true });
  validate(slide);
}

// 6. Solution
{
  const slide = newSlide("Источник: локальный README и текущий scope продукта.");
  kicker(slide, "решение");
  title(slide, "ApplyMap превращает хаос достижений в понятную карту поступления", 0.58, 0.78, 10.4, 0.72, 26);
  p(
    slide,
    "ApplyMap помогает школьнику собрать достижения в одном месте, выделить сильнейшие активности и награды, оформить их в понятный для заявки формат и получить реалистичный список университетов. Платформа не обещает поступление и не выдумывает достижения.",
    0.62,
    1.64,
    7.05,
    0.74,
    { size: 14.2, color: C.muted },
  );
  const steps = [
    ["1", "Собрать профиль"],
    ["2", "Проверить факты"],
    ["3", "Оформить достижения"],
    ["4", "Подобрать университеты"],
  ];
  steps.forEach((s, i) => {
    const x = 0.74 + i * 3.05;
    card(slide, x, 3.1, 2.48, 1.55, { fill: i === 0 ? C.sky : C.white, shadow: i === 0 });
    slide.addShape(pptx.ShapeType.ellipse, { x: x + 0.22, y: 3.38, w: 0.42, h: 0.42, fill: { color: C.navy }, line: { color: C.navy } });
    slide.addText(s[0], { x: x + 0.22, y: 3.5, w: 0.42, h: 0.12, fontSize: 8, bold: true, color: C.white, align: "center", margin: 0 });
    p(slide, s[1], x + 0.78, 3.44, 1.35, 0.34, { size: 14.8, bold: true });
    if (i < steps.length - 1) line(slide, x + 2.56, 3.88, 0.48, 0, { color: C.line, width: 1.2, end: "triangle" });
  });
  card(slide, 8.02, 1.72, 4.32, 1.0, { fill: C.panel });
  p(slide, "Главный принцип", 8.28, 2.02, 1.7, 0.18, { size: 10.4, bold: true, color: C.navy });
  p(slide, "реальные факты, ясная структура, следующий шаг с источниками", 8.28, 2.36, 3.6, 0.18, { size: 10.8, color: C.muted });
  validate(slide);
}

// 7. STEM
{
  const slide = newSlide("Источники: локальный README и API-сервисы правил, Gemini и поиска.");
  kicker(slide, "технология внутри");
  title(slide, "Как в решении используется STEM", 0.58, 0.78, 7.2, 0.62, 27);
  p(
    slide,
    "Проект основан на программировании, анализе данных и элементах искусственного интеллекта. STEM в ApplyMap - это не просто чат-бот, а сочетание инженерии продукта, анализа данных и ИИ для решения социальной проблемы.",
    0.62,
    1.58,
    6.7,
    0.74,
    { size: 14.4, color: C.muted },
  );
  const nodes = [
    ["Профиль ученика", 0.9, 3.02],
    ["Хранилище достижений", 3.22, 3.02],
    ["ИИ + правила", 5.82, 3.02],
    ["Подбор вузов", 8.04, 3.02],
    ["Отчет", 10.82, 3.02],
  ];
  nodes.forEach((n, i) => {
    const [txt, x, y] = n;
    card(slide, x, y, i === 3 ? 2.15 : 1.78, 0.78, { fill: i === 2 ? C.navy : C.white });
    p(slide, txt, x + 0.12, y + 0.27, (i === 3 ? 1.9 : 1.54), 0.14, { size: 8.8, bold: true, color: i === 2 ? C.white : C.ink });
    if (i < nodes.length - 1) {
      const nextX = nodes[i + 1][1];
      line(slide, x + (i === 3 ? 2.15 : 1.78), y + 0.39, nextX - x - (i === 3 ? 2.15 : 1.78), 0, { color: C.line, width: 1.2, end: "triangle" });
    }
  });
  bulletList(
    slide,
    [
      "классифицирует достижения",
      "выявляет повторы и пробелы",
      "задает уточняющие вопросы",
      "связывает профиль с требованиями университетов",
      "показывает проверяемый результат",
    ],
    1.0,
    4.66,
    10.3,
    { gap: 0.34, size: 12.6, color: C.muted, itemH: 0.22, bulletColor: C.blue },
  );
  validate(slide);
}

// 8. MVP
{
  const slide = newSlide("Источник: локальный README и текущая web/API-реализация.");
  kicker(slide, "рабочий MVP");
  title(slide, "У нас уже есть рабочий MVP", 0.58, 0.78, 7.1, 0.62, 27);
  p(
    slide,
    "В MVP реализованы ключевые части продукта: хранилище достижений, прозрачный ход работы ИИ, студия формулировок и советник по вузам. Это уже работающий прототип, который можно улучшать и тестировать на реальных школьниках.",
    0.62,
    1.58,
    7.0,
    0.62,
    { size: 14.4, color: C.muted },
  );
  const modules = [
    ["Хранилище достижений", "активности и награды в одном месте"],
    ["Прозрачный ход ИИ", "что ИИ прочитал, извлек и проверил"],
    ["Студия формулировок", "краткий английский текст под лимиты"],
    ["Советник по вузам", "план по выбранному вузу с источниками"],
  ];
  modules.forEach((m, i) => {
    const x = i % 2 === 0 ? 0.78 : 6.92;
    const y = i < 2 ? 2.88 : 4.74;
    card(slide, x, y, 5.46, 1.32, { fill: i === 0 ? C.sky : C.panel, shadow: i === 0 });
    label(slide, `0${i + 1}`, x + 0.26, y + 0.28, 0.42);
    p(slide, m[0], x + 0.82, y + 0.24, 2.3, 0.2, { size: 14.8, bold: true });
    p(slide, m[1], x + 0.82, y + 0.66, 3.05, 0.2, { size: 10.3, color: C.muted });
    slide.addShape(pptx.ShapeType.rect, { x: x + 4.72, y: y + 0.32, w: 0.42, h: 0.12, fill: { color: C.blue }, line: { color: C.blue } });
    slide.addShape(pptx.ShapeType.rect, { x: x + 4.72, y: y + 0.58, w: 0.58, h: 0.12, fill: { color: C.green }, line: { color: C.green } });
    slide.addShape(pptx.ShapeType.rect, { x: x + 4.72, y: y + 0.84, w: 0.32, h: 0.12, fill: { color: "CBD5E1" }, line: { color: "CBD5E1" } });
  });
  validate(slide);
}

// 9. Example output
{
  const slide = newSlide("Источник: пример результата на основе целей продукта ApplyMap.");
  kicker(slide, "пример результата");
  title(slide, "Что получает школьник на выходе", 0.58, 0.78, 7.4, 0.62, 27);
  p(
    slide,
    "Система помогает превратить сырую запись в структурированный и честный результат для заявки: роль, масштаб, контекст и формулировка на английском.",
    0.62,
    1.58,
    7.0,
    0.52,
    { size: 14.4, color: C.muted },
  );
  card(slide, 0.78, 2.72, 5.36, 2.64, { fill: C.panel });
  label(slide, "до", 1.08, 3.08, 0.8);
  p(
    slide,
    "был личным ментором для пятерых 8-классников будучи сам 11 классником в 2024-2025 года...",
    1.08,
    3.52,
    4.44,
    0.76,
    { size: 15.2, color: C.muted },
  );
  p(slide, "Проблема: роль неясна, язык смешан, impact не сформулирован.", 1.08, 4.58, 4.2, 0.2, { size: 9.2, color: C.amber });
  line(slide, 6.42, 4.0, 0.64, 0, { color: C.line, width: 1.8, end: "triangle" });
  card(slide, 7.34, 2.72, 5.2, 2.64, { fill: "FFFFFF", shadow: true });
  label(slide, "после", 7.66, 3.08, 0.7);
  p(slide, "Peer Mentor, NIS FMN Almaty", 7.66, 3.48, 3.65, 0.22, { size: 15.8, bold: true, color: C.navy });
  p(
    slide,
    "Mentored five Grade 8 students; co-led two school events with cards and peer support, 2024-25.",
    7.66,
    3.94,
    4.12,
    0.6,
    { size: 14.8, color: C.ink },
  );
  smallTag(slide, "роль", 7.68, 4.88, 0.56, { fill: C.sky, color: C.blue });
  smallTag(slide, "масштаб", 8.34, 4.88, 0.86, { fill: C.greenSoft, color: C.green });
  smallTag(slide, "год", 9.34, 4.88, 0.52, { fill: C.amberSoft, color: C.amber });
  validate(slide);
}

// 10. Why now
{
  const slide = newSlide("Источники: БНС SDG 4.a.1; gov.kz по EduNavigator; gov.kz по Mansap Kompasy.");
  kicker(slide, "почему сейчас");
  title(slide, "Почему ApplyMap нужен именно сейчас", 0.58, 0.78, 8.4, 0.62, 27);
  p(
    slide,
    "Цифровая инфраструктура уже позволяет запускать такие решения в школах. Уже существуют цифровые профориентационные инструменты, но они в основном отвечают на вопрос \"кем быть\", а не на вопрос \"как реально подать сильную и честную заявку\".",
    0.62,
    1.58,
    8.0,
    0.72,
    { size: 14.2, color: C.muted },
  );
  kpi(slide, "96.0%", "школ с интернетом 4+ Мбит/с", 0.72, 3.0, 3.55, { color: C.blue, fill: C.sky, line: "D6E0FF" });
  kpi(slide, "100 тыс.+", "учеников прошли EduNavigator", 4.92, 3.0, 3.55, { color: C.green, fill: C.greenSoft, line: "CAEEDB", size: 20 });
  kpi(slide, "116.5 тыс.", "Mansap Kompasy, 7-11 классы", 9.12, 3.0, 3.55, { color: C.amber, fill: C.amberSoft, line: "F4D19E", size: 20 });
  p(slide, "ApplyMap встраивается после профориентации: от выбора направления к конкретной, честной и проверяемой стратегии поступления.", 0.76, 5.34, 10.9, 0.38, { size: 15.2, bold: true });
  validate(slide);
}

// 11. Pilot and metrics
{
  const slide = newSlide("Пилотный план: предложенная проверка, еще не завершенный результат.");
  kicker(slide, "пилот");
  title(slide, "Как мы проверим эффект", 0.58, 0.78, 6.8, 0.62, 27);
  p(
    slide,
    "Мы планируем пилот на 10-20 учениках из 2-3 школ разного типа: НИШ, обычная школа и частная школа. Успех проекта будем измерять не обещаниями \"поступления\", а качеством навигации, прозрачностью источников и полезностью результата.",
    0.62,
    1.58,
    7.5,
    0.72,
    { size: 14.2, color: C.muted },
  );
  const metrics = [
    ["Завершение", "дошел от профиля до готового отчета"],
    ["Понятность", "понял следующий конкретный шаг"],
    ["Качество", "меньше ручной переписи"],
    ["Источники", "есть проверяемые источники"],
    ["Доверие", "рекомендации честные и понятные"],
  ];
  metrics.forEach((m, i) => {
    const y = 2.78 + i * 0.58;
    card(slide, 0.78, y, 11.55, 0.42, { fill: i % 2 === 0 ? C.panel : C.white, line: "EDF1F7" });
    p(slide, m[0], 1.02, y + 0.12, 1.6, 0.12, { size: 9.2, bold: true, color: C.navy });
    p(slide, m[1], 2.9, y + 0.11, 7.7, 0.14, { size: 9.2, color: C.muted });
  });
  card(slide, 8.5, 1.2, 3.72, 1.0, { fill: C.sky, line: "D6E0FF" });
  p(slide, "Пилотная выборка", 8.76, 1.5, 1.6, 0.16, { size: 9.4, bold: true, color: C.blue });
  p(slide, "10-20 учеников, 2-3 типа школ", 8.76, 1.84, 2.75, 0.16, { size: 9.8, color: C.muted });
  validate(slide);
}

// 12. Closing
{
  const slide = newSlide("Источники по всей деке: БНС, Минпросвещения, OECD, World Bank/UNESCO UIS, Open Doors, gov.kz.");
  addLogo(slide, 0.66, 0.56, 0.5);
  title(slide, "ApplyMap помогает школьнику увидеть ценность своего труда", 0.72, 1.48, 10.65, 0.72, 29);
  p(
    slide,
    "ApplyMap делает навигационную поддержку доступнее для школьников Казахстана, которым не хватает системной помощи по поступлению. Мы не заменяем учителя и не обещаем поступление. Мы создаем честный цифровой инструмент, который помогает ученику понять свой профиль, оформить достижения и двигаться к следующему шагу осознанно.",
    0.76,
    2.52,
    9.9,
    0.86,
    { size: 15.6, color: C.muted },
  );
  card(slide, 0.76, 4.34, 11.66, 1.18, { fill: C.panel });
  p(slide, "Что нужно от Samsung Solve for Tomorrow", 1.04, 4.7, 4.8, 0.2, { size: 13.4, bold: true, color: C.navy });
  p(slide, "менторство, обратная связь по MVP и возможность протестировать пилот в школьной среде Казахстана", 1.04, 5.08, 10.2, 0.22, { size: 12.8, color: C.ink });
  p(slide, "Источники данных: БНС, Образование в РК 2019-2023; Минпросвещения; OECD Skills Strategy Kazakhstan; World Bank/UNESCO UIS; Open Doors; gov.kz EduNavigator/Mansap Kompasy.", 0.78, 6.34, 11.4, 0.28, { size: 8.2, color: "98A2B3" });
  validate(slide);
}

async function main() {
  await pptx.writeFile({ fileName: outPath });
  console.log(outPath);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
