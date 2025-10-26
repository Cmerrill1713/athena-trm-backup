#!/usr/bin/env node
/**
 * Automated Open WebUI Setup - Version 2
 * More robust selector handling
 */

const { chromium } = require('playwright');

const BASE_URL = 'http://localhost:3000';
const OLLAMA_URL = 'http://host.docker.internal:11434';
const ADMIN_EMAIL = 'admin@athena.local';
const ADMIN_PASSWORD = 'athena-admin-2024';
const ADMIN_NAME = 'Athena Admin';

async function waitAndLog(page, message, ms = 2000) {
  console.log(message);
  await page.waitForTimeout(ms);
}

async function setupOpenWebUI() {
  console.log('==========================================');
  console.log('🚀 Automated Open WebUI Setup v2');
  console.log('==========================================\n');

  const browser = await chromium.launch({ 
    headless: false,
    slowMo: 300
  });
  
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    // Navigate to Open WebUI
    await waitAndLog(page, '📋 Step 1: Opening Open WebUI...', 1000);
    await page.goto(BASE_URL, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(3000);

    // Take screenshot for debugging
    await page.screenshot({ path: 'openwebui-initial.png' });
    console.log('   📸 Screenshot saved: openwebui-initial.png');

    // Check what page we're on
    const url = page.url();
    console.log(`   Current URL: ${url}`);

    // Handle signup if needed
    if (url.includes('/auth')) {
      await waitAndLog(page, '\n📋 Step 2: Creating account...', 1000);
      
      // Wait for form to be visible
      await page.waitForSelector('input', { timeout: 10000 });
      
      // Get all input fields
      const inputs = await page.$$('input');
      console.log(`   Found ${inputs.length} input fields`);
      
      // Fill inputs in order (usually: name, email, password, confirm password)
      if (inputs.length >= 2) {
        // Try different field orders
        try {
          await page.fill('input[type="text"]', ADMIN_NAME);
          console.log('   ✅ Filled name field');
        } catch (e) {}
        
        try {
          await page.fill('input[type="email"]', ADMIN_EMAIL);
          console.log('   ✅ Filled email field');
        } catch (e) {
          // Try by placeholder
          await page.fill('input[placeholder*="mail" i]', ADMIN_EMAIL);
          console.log('   ✅ Filled email field (by placeholder)');
        }
        
        // Fill all password fields
        const passwordFields = await page.$$('input[type="password"]');
        for (const field of passwordFields) {
          await field.fill(ADMIN_PASSWORD);
        }
        console.log(`   ✅ Filled ${passwordFields.length} password field(s)`);
        
        await page.screenshot({ path: 'openwebui-filled.png' });
        console.log('   📸 Screenshot saved: openwebui-filled.png');
        
        // Find and click submit button
        await page.waitForTimeout(1000);
        
        // Try multiple button selectors
        const buttonSelectors = [
          'button[type="submit"]',
          'button:has-text("Sign up")',
          'button:has-text("Create")',
          'button:has-text("Submit")',
          'button.primary',
          'button.btn-primary',
          'button'
        ];
        
        let clicked = false;
        for (const selector of buttonSelectors) {
          try {
            const button = page.locator(selector).first();
            if (await button.isVisible({ timeout: 1000 })) {
              await button.click();
              console.log(`   ✅ Clicked button: ${selector}`);
              clicked = true;
              break;
            }
          } catch (e) {}
        }
        
        if (!clicked) {
          console.log('   ⚠️  Could not find submit button, trying Enter key...');
          await page.keyboard.press('Enter');
        }
        
        await page.waitForTimeout(5000);
        await page.screenshot({ path: 'openwebui-after-submit.png' });
        console.log('   📸 Screenshot saved: openwebui-after-submit.png');
        
        console.log('   ✅ Account creation attempted');
        console.log(`   📧 Email: ${ADMIN_EMAIL}`);
        console.log(`   🔑 Password: ${ADMIN_PASSWORD}`);
      }
    }

    // Navigate to settings
    await waitAndLog(page, '\n📋 Step 3: Opening Settings...', 2000);
    
    // Try to go directly to settings
    await page.goto(`${BASE_URL}/settings`, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(3000);
    await page.screenshot({ path: 'openwebui-settings.png' });
    console.log('   📸 Screenshot saved: openwebui-settings.png');

    // Look for Ollama input field
    await waitAndLog(page, '\n📋 Step 4: Configuring Ollama...', 1000);
    
    // Try to find Ollama input by various methods
    const ollamaSelectors = [
      'input[placeholder*="ollama" i]',
      'input[id*="ollama" i]',
      'input[name*="ollama" i]',
      'input[value*="11434"]',
      'input[value*="localhost"]'
    ];
    
    let configured = false;
    for (const selector of ollamaSelectors) {
      try {
        const input = page.locator(selector).first();
        if (await input.isVisible({ timeout: 2000 })) {
          await input.clear();
          await input.fill(OLLAMA_URL);
          console.log(`   ✅ Set Ollama URL using selector: ${selector}`);
          console.log(`   🦙 URL: ${OLLAMA_URL}`);
          configured = true;
          
          // Try to trigger refresh
          await page.keyboard.press('Enter');
          await page.waitForTimeout(2000);
          break;
        }
      } catch (e) {}
    }
    
    if (!configured) {
      console.log('   ⚠️  Could not auto-configure Ollama');
      console.log('   📝 Manual step needed: Set Ollama URL in Settings → Connections');
    }
    
    await page.screenshot({ path: 'openwebui-configured.png' });
    console.log('   📸 Screenshot saved: openwebui-configured.png');

    // Go back to chat
    await waitAndLog(page, '\n📋 Step 5: Opening chat interface...', 1000);
    await page.goto(BASE_URL, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(3000);
    await page.screenshot({ path: 'openwebui-final.png' });
    console.log('   📸 Screenshot saved: openwebui-final.png');

    console.log('\n==========================================');
    console.log('✅ Setup Process Complete!');
    console.log('==========================================\n');
    console.log('📧 Login Credentials:');
    console.log(`   Email: ${ADMIN_EMAIL}`);
    console.log(`   Password: ${ADMIN_PASSWORD}\n`);
    console.log('🦙 Ollama Configuration:');
    console.log(`   URL: ${OLLAMA_URL}\n`);
    console.log('📸 Screenshots saved for verification:');
    console.log('   - openwebui-initial.png');
    console.log('   - openwebui-filled.png');
    console.log('   - openwebui-after-submit.png');
    console.log('   - openwebui-settings.png');
    console.log('   - openwebui-configured.png');
    console.log('   - openwebui-final.png\n');
    console.log('🔍 Test browser research:');
    console.log('   Ask: "search for machine learning"\n');
    console.log('Browser will close in 10 seconds...');
    
    await page.waitForTimeout(10000);
    
    return true;

  } catch (error) {
    console.error('\n❌ Error:', error.message);
    await page.screenshot({ path: 'openwebui-error.png' });
    console.log('   📸 Error screenshot saved: openwebui-error.png');
    return false;
  } finally {
    await browser.close();
  }
}

setupOpenWebUI().then(success => {
  console.log(success ? '\n✅ Done!' : '\n⚠️  Please check screenshots for manual steps');
  process.exit(success ? 0 : 1);
});

