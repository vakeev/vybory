document.querySelectorAll('.copy').forEach((btn) => {
  btn.addEventListener('click', () => {
    const q = btn.closest('.question').querySelector('.qtext');
    const text = q.textContent.trim();
    const done = () => {
      btn.classList.add('done');
      const span = btn.querySelector('span');
      span.textContent = 'Скопировано';
      setTimeout(() => {
        btn.classList.remove('done');
        span.textContent = 'Копировать';
      }, 1600);
    };
    if (navigator.clipboard) {
      navigator.clipboard.writeText(text).then(done).catch(() => fallbackCopy(text, done));
    } else {
      fallbackCopy(text, done);
    }
  });
});

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
