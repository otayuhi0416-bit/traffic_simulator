import asyncio
import os
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        # ヘッドレスブラウザを起動
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # ページ読み込み時のコンソールログ収集
        console_logs = []
        page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))
        
        print("Navigating to http://localhost:5000...")
        await page.goto("http://localhost:5000")
        
        # リストのロード待ち
        await page.wait_for_selector(".junction-item")
        print("Junction list loaded.")
        
        # 10610370478 の交差点項目をクリック
        target_selector = ".junction-item[data-id='10610370478']"
        print("Clicking on junction 10610370478...")
        await page.click(target_selector)
        
        # SVGのレンダリング待ち
        await page.wait_for_timeout(2000)
        
        # スクリーンショットを保存
        output_dir = r"C:\Users\genno\.gemini\antigravity\brain\18c6286c-3bf0-4a65-8eb4-6fe2e721b8d8\scratch"
        os.makedirs(output_dir, exist_ok=True)
        screenshot_path = os.path.join(output_dir, "junction_10610370478.png")
        
        await page.screenshot(path=screenshot_path)
        print(f"Screenshot saved to: {screenshot_path}")
        
        # コンソールログの出力
        print("\nBrowser Console Logs:")
        print("="*60)
        for log in console_logs:
            print(log)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
