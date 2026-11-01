<h1>Tipsport.cz</h1>
<p>
<h3>Kodi doplněk pro Tipsport.cz</h3>
<p>
Doplněk je funkční v Kodi běžícím ve Windows a Linuxu s Intel/AMD procesorem a vyžaduje mít nainstalovaný Google Chrome. Na ostatních zařízení s jiným OS nebo ARMovým procesorem je možné použít docker kontejner se Selenium Grid (funguje v CoreELEC/LibreELEC) nebo samostatně běžící Selenium Grid. Bohužel pro Android neexistují ani potřebný driver ani nativní možnost spuštění dockeru. Je možné využít vzdáleně běžící docker, ale toto řešení doporučuju jen v případě, že víte co děláte.<br>

<h3>Postup instalace</h3><br>
Stáhněte a nainstalujte <a href="https://codeload.github.com/waladir/script.module.selenium/zip/refs/heads/master">doplněk selenium</a> a samotný <a href="https://codeload.github.com/waladir/plugin.video.tipsport/zip/refs/heads/master">Tipsport.cz</a>

<h4>CoreELEC/LibreELEC</h4>
Pokud chcete provozovat doplněk v CoreELEC/LibreELEC, kde Google Chrome nejde standardně nainstalovat, nainstalujte si z nejprve z repozitáře CoreELEC/LibreELEC docker. Připojte se přes ssh (<a href="https://wiki.coreelec.org/coreelec:ssh">postup CoreELEC</a>) a vytvořte a nastartujte container (cca. 1.3 GB!):

<pre>
docker create \
   --name=selenium-chrome \
   -e TZ=Europe/Prague \
   -p 4444:4444 \
   -p 7900:7900 \
   --shm-size="1g" \
   --restart unless-stopped \
   --privileged \
   seleniarm/standalone-chromium:latest

docker start selenium-chrome
</pre><br>

V nastavení doplňku vyplňte jako Prohlížeč docker.<br><br>

<h4>Java</h4>
Selenium Grid lze pustit i na jiném počítači a doplněk k němu může přistupovat vzdáleně. Je potřeba mít nainstalované Java JRE a vyšší a Google Chrome.<br>

- stáhněte si aktuální verzi Selenium Serveru (selenium-server-<verze>.jar) z https://github.com/SeleniumHQ/selenium/releases/latest<br>
- spusťte Selenium Grid:<br>
 
<pre>java -jar selenium-server-<verze>.jar standalone --selenium-manager true</pre>
- v nastavení doplňku vyberte v Prohlížeč Selenium Grid a v Selenium Grid URL http://<adresa nebo jméno počítače s běžícím Selenium Grid>:4444/wd/hub<br><br>

<h4>Zadáním JSESSIONID přes webový formulář</h4>
Tento způsob nahrazuje přihlášení a při jeho použití není třeba volání žádného prohlížeče z doplňku.<br>

- v nastavení dopňku vyberte v Prohlížeč zadání přes web<br>
- v prohlížeči otevřete stránku z formulářem pro zadání JSESSIONID - http://127.0.0.1:8089/<br>
- na stránce zadejte podle postupu hodnotu JSESSIONID<br>
- formulář otevřete přímo na počítači s Kodi; naslouchá pouze na místním rozhraní a není dostupný ostatním zařízením v síti<br>
- JSESSIONID umožňuje přístup k přihlášené relaci; nesdílejte ho a při skončení platnosti předejte nové<br><br>

<hr>
v1.1.8 (1.3.2025)<br>
- aktualizace volání šablony<br><br>

v1.1.7 (22.12.2024)<br>
- automatický update chromedriveru<br><br>

v1.1.6 (21.9.2024)<br>
- vylepšené ošetření neplatné sessiony<br><br>

v1.1.5 (19.9.2024)<br>
- volání API přímo doplňkem<br>
- znovuzprovoznění zadání JSESSIONID přes webový formulář<br><br>

v1.1.4 (27.2.2024)<br>
- změna volání API přes Selenium<br><br>
</p>
