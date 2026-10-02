const { chromium } = require('/opt/node22/lib/node_modules/playwright');
(async () => {
  const [,, file, outBase] = process.argv;
  const p = process.env.HTTPS_PROXY;
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome', proxy: p?{server:p}:undefined, args:['--ignore-certificate-errors'] });
  const pg = await (await b.newContext({viewport:{width:1600,height:1100}, deviceScaleFactor:2})).newPage();
  await pg.goto('file://'+file,{waitUntil:'networkidle'});
  await pg.evaluate(()=>document.fonts.ready);
  const secs = await pg.$$('section');
  for (let i=0;i<secs.length;i++) await secs[i].screenshot({path:`${outBase}_${i+1}.png`});
  console.log(secs.length);
  await b.close();
})();
