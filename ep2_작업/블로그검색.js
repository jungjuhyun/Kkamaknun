// 네이버 블로그 검색 결과(제목·요약·주소)를 브라우저로 모아 nv.json에 저장한다.
// 쓰는 법: node 블로그검색.js "검색어1" "검색어2" ...  (Playwright 필요)
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
(async () => {
  const qs = process.argv.slice(2);
  const p = process.env.HTTPS_PROXY;
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome', proxy: p?{server:p}:undefined, args:['--ignore-certificate-errors'] });
  const ctx = await b.newContext({ userAgent:'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36', locale:'ko-KR' });
  const pg = await ctx.newPage();
  const out = {};
  for (const q of qs) {
    const url = 'https://search.naver.com/search.naver?ssc=tab.blog.all&sm=tab_jum&query=' + encodeURIComponent(q);
    const r = await pg.goto(url, { waitUntil: 'domcontentloaded', timeout: 45000 });
    await pg.waitForTimeout(2500);
    for (let i=0;i<3;i++){ await pg.mouse.wheel(0, 4000); await pg.waitForTimeout(1200); }
    const items = await pg.evaluate(() => {
      const res = [];
      document.querySelectorAll('a[href*="blog.naver.com"]').forEach(a => {
        const t = a.innerText.trim();
        if (t.length > 8) res.push({ href: a.href, text: t.slice(0, 300) });
      });
      return res;
    });
    out[q] = { status: r.status(), n: items.length, items };
  }
  require('fs').writeFileSync('nv.json', JSON.stringify(out, null, 1));
  for (const q of qs) console.log(q, out[q].status, out[q].n);
  await b.close();
})();
