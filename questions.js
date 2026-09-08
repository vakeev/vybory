function flashDone(btn, doneLabel) {
  const span = btn.querySelector('span');
  const restore = span ? span.textContent : btn.dataset.label;
  btn.classList.add('done');
  if (span) span.textContent = doneLabel;
  else btn.textContent = doneLabel;
  setTimeout(() => {
    btn.classList.remove('done');
    if (span) span.textContent = restore;
    else btn.textContent = restore;
  }, 1600);
}

function fallbackCopy(text, done) {
  const ta = document.createElement('textarea');
  ta.value = text;
  ta.style.position = 'fixed';
  ta.style.opacity = '0';
  document.body.appendChild(ta);
  ta.select();
  try {
    document.execCommand('copy');
    done();
  } finally {
    ta.remove();
  }
}

function copyText(btn, text, doneLabel) {
  const done = () => flashDone(btn, doneLabel);
  if (navigator.clipboard) {
    navigator.clipboard.writeText(text).then(done).catch(() => fallbackCopy(text, done));
  } else {
    fallbackCopy(text, done);
  }
}

document.querySelectorAll('.copy').forEach((btn) => {
  btn.dataset.label = btn.textContent.trim();
  const q = btn.closest('.question').querySelector('.qtext');
  btn.addEventListener('click', () => copyText(btn, q.textContent.trim(), 'Скопировано!'));
});

document.querySelectorAll('.ask').forEach((btn) => {
  btn.dataset.label = btn.textContent.trim();
  btn.addEventListener('click', () => {
    const bank = window.VOPROSY;
    if (!bank || !bank.length) return;
    const text = btn.dataset.greet + bank[Math.floor(Math.random() * bank.length)];
    copyText(btn, text, 'Скопировано!');
  });
});
