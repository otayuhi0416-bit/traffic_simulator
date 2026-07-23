const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

const targetDir = 'C:/Users/Genno_Shirou/.gemini/antigravity/brain/7e385f5d-3be8-4c84-b159-4d0366740fbd';
if (!fs.existsSync(targetDir)) {
    fs.mkdirSync(targetDir, { recursive: true });
}

(async () => {
  console.log("Launching browser...");
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const page = await browser.newPage();
  
  // Set viewport to a good size
  await page.setViewport({ width: 1400, height: 900 });
  
  console.log("Navigating to http://127.0.0.1:5000...");
  try {
    await page.goto('http://127.0.0.1:5000', { waitUntil: 'networkidle2', timeout: 30000 });
  } catch (err) {
    console.error("Navigation failed:", err);
    await browser.close();
    process.exit(1);
  }
  
  console.log("Waiting for network elements to load...");
  await new Promise(r => setTimeout(r, 4000));
  
  console.log("Taking main editor screenshot...");
  await page.screenshot({ path: path.join(targetDir, 'editor_main.png') });
  
  // Click on a specific junction to open the edit panel
  // Let's click the junction item in the list if available, or target a specific junction ID
  console.log("Selecting a junction (1386150782)...");
  
  // We can try to search for the junction in the list
  const searchInputSelector = '#search-input';
  const hasSearchInput = await page.$(searchInputSelector);
  if (hasSearchInput) {
    await page.type(searchInputSelector, '1386150782');
    await new Promise(r => setTimeout(r, 2000)); // Wait for search list to filter
    
    const firstItemSelector = '#junctions-list .junction-item';
    const firstItem = await page.$(firstItemSelector);
    if (firstItem) {
        console.log("Junction found in list, clicking...");
        await firstItem.click();
        await new Promise(r => setTimeout(r, 4000)); // wait for details and SVG map to load
        
        console.log("Taking editing screenshot...");
        await page.screenshot({ path: path.join(targetDir, 'editor_editing.png') });
    } else {
        console.log("Junction list item not found.");
    }
  } else {
    console.log("Search input not found, trying general click...");
    const items = await page.$$('#junctions-list .junction-item');
    if (items.length > 0) {
        await items[0].click();
        await new Promise(r => setTimeout(r, 4000));
        await page.screenshot({ path: path.join(targetDir, 'editor_editing.png') });
    }
  }

  await browser.close();
  console.log("Screenshots captured successfully!");
})();
