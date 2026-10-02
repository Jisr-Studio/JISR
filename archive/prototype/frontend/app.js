const $ = (s) => document.querySelector(s);
const $$ = (s) => [...document.querySelectorAll(s)];
// Where the project data comes from.
// Now: the local mock file. Later (when the backend is ready): "/api/projects/demo"
const DATA_URL = "mock/project.json";
let project = null;
let segments = [];
let filter = "all",
  showArabic = true,
  selected = 0,
  customVideo = false,
  objectURL = null,
  toastTimer;
const video = $("#video");
const fmt = (n) =>
  `${String(Math.floor(n / 60)).padStart(2, "0")}:${String(Math.floor(n % 60)).padStart(2, "0")}`;
const escape = (s) =>
  String(s).replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
function toast(text) {
  $("#toast").textContent = text;
  $("#toast").classList.add("visible");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => $("#toast").classList.remove("visible"), 3500);
}
function render() {
  const list = segments
    .map((s, i) => ({ s, i }))
    .filter(({ s }) => filter === "all" || s.type === filter);
  $("#segments").innerHTML =
    list
      .map(
        ({ s, i }) =>
          `<div class="segment ${selected === i ? "current" : ""}" data-index="${i}"><button class="segment-time" data-seek="${i}" aria-label="الانتقال إلى ${fmt(s.start)}">${fmt(s.start)}<br><span>${fmt(s.end)}</span></button><div class="segment-body">${s.type === "quran" ? '<span class="tag quran">البقرة · ٢٢٢</span>' : s.type === "hadith" ? '<span class="tag hadith">حديث نبوي · صحيح مسلم</span>' : s.type === "review" ? '<span class="tag review">يحتاج مراجعة</span>' : ""}${showArabic ? `<p class="ar">${escape(s.ar)}</p>` : ""}<p class="en" dir="ltr">${escape(s.en)}</p>${s.type === "review" ? '<div class="review-message">△ كلمة غير واضحة — استمع للمقطع ثم صحح النص</div>' : ""}</div><button class="edit" data-edit="${i}" aria-label="تعديل المقطع ${i + 1}">✎</button></div>`,
      )
      .join("") ||
    '<p style="padding:20px;color:#75828d">لا توجد مقاطع تحتاج مراجعة.</p>';
  $$("[data-seek]").forEach((b) => (b.onclick = () => seekTo(+b.dataset.seek)));
  $$("[data-edit]").forEach((b) => (b.onclick = () => edit(+b.dataset.edit)));
}
function seekTo(i) {
  video.currentTime = segments[i].start;
  selected = i;
  render();
  updateSubtitle();
}
function updateSubtitle() {
  const s = segments[selected];
  const quote = ["quran", "hadith"].includes(s.type);
  $("#subtitleArabic").textContent =
    quote && $("#bilingual").checked ? s.ar : "";
  $("#subtitleArabic").style.display =
    quote && $("#bilingual").checked ? "" : "none";
  $("#subtitleEnglish").textContent = s.en;
  $("#subtitleRef").textContent = s.ref || "";
}
function updateTime() {
  const d = Number.isFinite(video.duration) ? video.duration : 48;
  $("#seek").max = d;
  $("#seek").value = video.currentTime;
  $("#time").textContent = `${fmt(video.currentTime)} / ${fmt(d)}`;
  const i = segments.findIndex(
    (s) => video.currentTime >= s.start && video.currentTime < s.end,
  );
  if (i >= 0 && i !== selected) {
    selected = i;
    render();
    updateSubtitle();
  }
}
video.addEventListener("timeupdate", updateTime);
video.addEventListener("loadedmetadata", updateTime);
video.addEventListener("play", () => {
  $("#play").textContent = "Ⅱ";
  $("#play").ariaLabel = "إيقاف مؤقت";
});
video.addEventListener("pause", () => {
  $("#play").textContent = "▶";
  $("#play").ariaLabel = "تشغيل الفيديو";
});
$("#play").onclick = () =>
  video.paused
    ? video
        .play()
        .catch(() => toast("تعذر تشغيل الفيديو. يمكنك اختيار مقطع محلي."))
    : video.pause();
$("#seek").oninput = (e) => {
  video.currentTime = +e.target.value;
  updateTime();
};
$("#mute").onclick = () => {
  video.muted = !video.muted;
  $("#mute").textContent = video.muted ? "♩" : "♪";
  toast(
    customVideo
      ? video.muted
        ? "تم كتم الصوت"
        : "تم تشغيل الصوت"
      : "الفيديو التجريبي صامت",
  );
};
$("#fullscreen").onclick = () =>
  $("#videoStage")
    .requestFullscreen?.()
    .catch(() => toast("ملء الشاشة غير متاح في هذا المتصفح"));
$$("[data-filter]").forEach(
  (b) =>
    (b.onclick = () => {
      filter = b.dataset.filter;
      $$("[data-filter]").forEach((x) => x.classList.toggle("active", x === b));
      render();
    }),
);
$("#toggleAll").onclick = () => {
  showArabic = !showArabic;
  $("#toggleAll").textContent = showArabic
    ? "إخفاء النص العربي"
    : "عرض النص العربي";
  render();
};
$("#toggleAll").textContent = "إخفاء النص العربي";
function applyStyle() {
  const el = $("#subtitle");
  el.style.fontSize = $("#fontSize").value + "px";
  el.style.setProperty("--chosen-size", $("#fontSize").value + "px");
  $("#fontValue").value = $("#fontSize").value + " px";
  el.style.fontFamily =
    $("#font").value === "amiri"
      ? "Amiri,serif"
      : $("#font").value === "system"
        ? "Arial,sans-serif"
        : "'IBM Plex Sans Arabic',sans-serif";
  $$(".subtitle>div").forEach(
    (x) =>
      (x.style.background = $("#backdrop").checked
        ? "#05141dbb"
        : "transparent"),
  );
  updateSubtitle();
}
["font", "fontSize", "backdrop", "bilingual"].forEach((id) =>
  $("#" + id).addEventListener("input", applyStyle),
);
$$("[data-color]").forEach(
  (b) =>
    (b.onclick = () => {
      $("#subtitle").style.setProperty("--subcolor", b.dataset.color);
      $$("[data-color]").forEach((x) =>
        x.classList.toggle("selected", x === b),
      );
    }),
);
$$("[data-pos]").forEach(
  (b) =>
    (b.onclick = () => {
      const s = $("#subtitle");
      s.style.bottom = b.dataset.pos === "bottom" ? "7%" : "auto";
      s.style.top =
        b.dataset.pos === "top"
          ? "13%"
          : b.dataset.pos === "middle"
            ? "45%"
            : "auto";
      $$("[data-pos]").forEach((x) => x.classList.toggle("active", x === b));
    }),
);
$("#resetStyle").onclick = () => {
  $("#font").value = "plex";
  $("#fontSize").value = 22;
  $("#backdrop").checked = true;
  $("#bilingual").checked = true;
  $$("[data-color]")[0].click();
  $$("[data-pos]")[0].click();
  applyStyle();
  toast("أُعيد مظهر الترجمة الافتراضي");
};
function modal(title, html) {
  video.pause();
  $("#modalTitle").textContent = title;
  $("#modalBody").innerHTML = html;
  $("#modal").showModal();
}
$("#closeModal").onclick = () => $("#modal").close();
$("#modal").addEventListener("click", (e) => {
  if (e.target === $("#modal")) {
    const r = e.target.getBoundingClientRect();
    if (
      e.clientX < r.left ||
      e.clientX > r.right ||
      e.clientY < r.top ||
      e.clientY > r.bottom
    )
      e.target.close();
  }
});
function edit(i) {
  const s = segments[i];
  modal(
    "تعديل المقطع · " + fmt(s.start),
    `<label for="editAr">النص العربي</label><textarea id="editAr">${escape(s.ar)}</textarea><label for="editEn">الترجمة الإنجليزية</label><textarea id="editEn" dir="ltr">${escape(s.en)}</textarea>${s.type === "review" ? '<label><input type="checkbox" id="reviewed"> راجعت الكلمة غير الواضحة وصححتها</label>' : ""}<div class="modal-actions"><button class="button primary" id="saveEdit">حفظ التعديلات</button><button class="button secondary" id="cancelEdit">إلغاء</button></div>`,
  );
  $("#cancelEdit").onclick = () => $("#modal").close();
  $("#saveEdit").onclick = () => {
    if (!$("#editAr").value.trim() || !$("#editEn").value.trim())
      return toast("أدخل النص والترجمة قبل الحفظ");
    s.ar = $("#editAr").value.trim();
    s.en = $("#editEn").value.trim();
    if ($("#reviewed")?.checked) s.type = "speech";
    selected = i;
    render();
    updateSubtitle();
    $("#modal").close();
    const count = segments.filter((x) => x.type === "review").length;
    $("#reviewCount").textContent = count;
    $("#reviewSummary").textContent = count
      ? "مقطع واحد يحتاج انتباهك"
      : "اكتملت مراجعة المقاطع";
    $("#saveState").textContent = "تم حفظ التعديل في هذه الجلسة";
    toast("تم حفظ التعديل وتحديث المعاينة");
  };
}
function reference(type) {
  const q = type === "quran";
  modal(
    q ? "سورة البقرة · الآية ٢٢٢" : "حديث الطهور شطر الإيمان",
    `<span class="tag ${type}">${q ? "قرآن كريم · اقتباس جزئي" : "حديث نبوي · اقتباس جزئي"}</span><p class="modal-verse">${q ? segments[1].ar : segments[3].ar}</p><p dir="ltr">${q ? segments[1].en : segments[3].en}</p><dl class="source-list">${q ? "<dt>الموضع</dt><dd>سورة البقرة، نهاية الآية ٢٢٢</dd><dt>الإنجليزية</dt><dd>مثال عرض من ترجمة Saheeh International</dd>" : "<dt>الراوي</dt><dd>أبو مالك الأشعري</dd><dt>المصدر</dt><dd>صحيح مسلم، حديث ٢٢٣</dd><dt>الحكم</dt><dd>صحيح — أخرجه مسلم في صحيحه</dd><dt>الإنجليزية</dt><dd>ترجمة توضيحية للواجهة</dd>"}</dl><h3>للتعمق في المعنى</h3><p>${q ? "افتح المرجع لقراءة الآية كاملة والتفاسير المرتبطة بها." : "افتح المرجع لقراءة الحديث كاملاً وشرحه، وتمييز الجزء المقتبس من بقية الحديث."}</p><a href="${q ? "https://quran.com/2/222" : "https://sunnah.com/muslim:223"}" target="_blank" rel="noopener">${q ? "قراءة الآية والتفسير" : "قراءة الحديث وشرحه"}</a><p class="modal-note">هذا نموذج واجهة. لا يتم الاتصال بمصادر التوثيق أو توليد شرح آلي في هذه النسخة.</p><button class="button secondary" id="jumpRef">الانتقال إلى موضع الاقتباس</button>`,
  );
  $("#jumpRef").onclick = () => {
    $("#modal").close();
    seekTo(q ? 1 : 3);
  };
}
$$("[data-reference]").forEach(
  (b) => (b.onclick = () => reference(b.dataset.reference)),
);
$("#sourcesNav").onclick = () => {
  $("#referencePanel").scrollIntoView({ behavior: "smooth", block: "center" });
  $("#referencePanel").animate(
    [{ boxShadow: "0 0 0 3px #087e8b55" }, { boxShadow: "none" }],
    { duration: 1800 },
  );
};
$("#editorNav").onclick = () => {
  document.body.classList.remove("viewer-mode");
  window.scrollTo({ top: 0, behavior: "smooth" });
};
$("#help").onclick = () =>
  modal(
    "عن نموذج جسر",
    '<p>جرّب تشغيل الفيديو، والتنقل بين المقاطع، وتعديل النصوص، وتغيير الخط، وفتح مراجع الآيات والأحاديث.</p><p class="modal-note">الفيديو صامت والبيانات تجريبية. لا يوجد تسجيل دخول، أو نسخ احتياطي، أو تفريغ وترجمة آليان. التعديلات مؤقتة وتنتهي بتحديث الصفحة.</p>',
  );
$("#upload").onclick = () =>
  modal(
    "إضافة مقطع تجريبي",
    '<p>اختر فيديو من جهازك لمعاينته داخل المحرر. يبقى على جهازك ولا يُرفع إلى أي خادم.</p><p class="modal-note">ستبقى النصوص التجريبية كما هي؛ هذه الواجهة لا تفرّغ أو تترجم الفيديو الجديد.</p><button class="button primary" id="chooseFile">اختيار فيديو من الجهاز</button>',
  );
$("#modalBody").addEventListener("click", (e) => {
  if (e.target.id === "chooseFile") $("#fileInput").click();
});
$("#fileInput").onchange = (e) => {
  const f = e.target.files[0];
  if (!f) return;
  if (!f.type.startsWith("video/")) return toast("اختر ملف فيديو صالحاً");
  if (objectURL) URL.revokeObjectURL(objectURL);
  objectURL = URL.createObjectURL(f);
  video.src = objectURL;
  customVideo = true;
  $("#projectTitle").textContent = f.name;
  $(".video-title").style.display = "none";
  $(".video-top").style.display = "none";
  $("#durationLabel").textContent = "معاينة محلية";
  $("#modal").close();
  toast("تم فتح الفيديو محلياً — النصوص ما زالت تجريبية");
};
function download(text, name, type) {
  const a = document.createElement("a");
  const url = URL.createObjectURL(new Blob([text], { type }));
  a.href = url;
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
$("#export").onclick = () => {
  modal(
    "تصدير المشروع",
    '<p class="modal-note">يمكن تنزيل الترجمة والمصادر فعلياً. دمج الترجمة بالفيديو وإنشاء رابط مشاهدة خاص بالمشروع معروضان كتجربة واجهة فقط.</p><div class="export-grid"><button class="export-option" id="srtExport"><b>ملف الترجمة · SRT</b><span>الترجمة الإنجليزية مع التعديلات والتوقيت</span></button><button class="export-option" id="sourcesExport"><b>قائمة الاقتباسات · TXT</b><span>الآيات والأحاديث وأوقات ظهورها ومراجعها</span></button><button class="export-option" id="videoExport"><b>الفيديو المترجم · MP4</b><span>معاينة إجراء التصدير</span></button><button class="export-option" id="shareExport"><b>رابط المشاهدة</b><span>معاينة صفحة المشاهد داخل النموذج</span></button></div>',
  );
  $("#srtExport").onclick = () => {
    download(
      segments
        .map(
          (s, i) =>
            `${i + 1}\n00:${fmt(s.start)},000 --> 00:${fmt(s.end)},000\n${s.en}\n`,
        )
        .join("\n"),
      "jisr-demo.srt",
      "text/plain;charset=utf-8",
    );
    toast("تم تنزيل ملف الترجمة");
  };
  $("#sourcesExport").onclick = () => {
    download(
      "جسر — قائمة مصادر تجريبية\n00:08 — سورة البقرة، الآية 222 (اقتباس جزئي)\nhttps://quran.com/2/222\n00:24 — الطهور شطر الإيمان (اقتباس جزئي)\nالراوي: أبو مالك الأشعري\nصحيح مسلم، 223\nhttps://sunnah.com/muslim:223\nهذه أمثلة عرض وليست نتائج تحقق آلي.",
      "jisr-sources.txt",
      "text/plain;charset=utf-8",
    );
    toast("تم تنزيل قائمة المصادر");
  };
  $("#videoExport").onclick = () =>
    modal(
      "معاينة تصدير الفيديو",
      '<p>سيُجهّز الفيديو هنا بالخط والترجمة المختارين في النسخة المتصلة بخدمة المعالجة.</p><p class="modal-note">لا يتم دمج الترجمة أو إنشاء فيديو مترجم في نموذج الواجهة.</p><a class="button secondary" href="assets/demo.mp4" download="jisr-silent-demo.mp4">تحميل الفيديو التجريبي الصامت</a>',
    );
  $("#shareExport").onclick = () => {
    $("#modal").close();
    document.body.classList.add("viewer-mode");
    window.scrollTo({ top: 0, behavior: "smooth" });
    toast(
      "معاينة المشاهد — اضغط «استوديو الترجمة» للعودة. لم يُنشأ رابط مشاركة.",
    );
  };
};
async function load() {
  try {
    const res = await fetch(DATA_URL);
    if (!res.ok) throw new Error(res.status);
    project = await res.json();
    segments = project.segments;
    render();
    updateSubtitle();
  } catch (err) {
    console.error("[jisr] failed to load project data", err);
    $("#segments").innerHTML =
      '<p style="padding:20px;color:#b54708">تعذر تحميل بيانات المشروع. شغّل المشروع عبر خادم محلي (Live Server أو uvicorn) وليس بفتح الملف مباشرة.</p>';
  }
}
load();
