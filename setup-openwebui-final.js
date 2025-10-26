#!/usr/bin/env node
/**
 * Simple Open WebUI Auto-Setup
 * Opens browser and guides you through with automation where possible
 */

const { chromium } = require('playwright');

const OLLAMA_URL = 'http://host.docker.internal:11434';
const CREDENTIALS = {
  email: 'admin@athena.local',
  password: 'athena-local-2024',
  name: 'Athena Admin'
};

(async () => {
  console.log('==========================================');
  console.log('🚀 Open WebUI Guided Setup');
  console.log('==========================================\n');
  
  const browser = await chromium.launch({ headless: false, slowMo: 500 });
  const page = await browser.newPage();
  
  try {
    // Step 1: Open and wait
    console.log('📋 Step 1: Opening Open WebUI...');
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    const currentUrl = page.url();
    console.log(`   Current page: ${currentUrl}\n`);
    
    // Step 2: Sign up if needed
    if (currentUrl.includes('/auth')) {
      console.log('📋 Step 2: Account Creation');
      console.log('   The browser is now open. Please:');
      console.log('   1. Fill in the signup form');
      console.log(`   2. Suggested credentials:`);
      console.log(`      Email: ${CREDENTIALS.email}`);
      console.log(`      Password: ${CREDENTIALS.password}`);
      console.log('   3. Click "Sign Up"\n');
      console.log('   ⏳ Waiting for you to complete signup...\n');
      
      // Wait for navigation away from auth page
      await page.waitForURL(url => !url.toString().includes('/auth'), { timeout: 120000 });
      console.log('   ✅ Account created!\n');
    } else {
      console.log('📋 Step 2: Already logged in\n');
    }
    
    // Step 3: Navigate to settings
    console.log('📋 Step 3: Navigating to Settings...');
    await page.goto('http://localhost:3000/settings');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    console.log('   ✅ Settings page opened\n');
    
    // Step 4: Configure Ollama
    console.log('📋 Step 4: Configuring Ollama Connection');
    console.log('   Looking for Ollama settings...\n');
    
    // Try to find and fill Ollama URL input
    try {
      // Wait for any input that might be the Ollama URL
      await page.waitForSelector('input', { timeout: 5000 });
      
      // Get all visible inputs
      const inputs = await page.$$('input[type="text"], input[type="url"]');
      console.log(`   Found ${inputs.length} text input(s)\n`);
      
      // Try to fill the one that looks like a URL field
      let filled = false;
      for (const input of inputs) {
        const value = await input.inputValue().catch(() => '');
        if (value.includes('localhost') || value.includes('11434') || value.includes('ollama')) {
          await input.clear();
          await input.fill(OLLAMA_URL);
          console.log(`   ✅ Found and filled Ollama URL field`);
          console.log(`   🦙 Set to: ${OLLAMA_URL}\n`);
          filled = true;
          
          // Press Tab to trigger any change handlers
          await input.press('Tab');
          await page.waitForTimeout(1000);
          break;
        }
      }
      
      if (!filled) {
        console.log('   ℹ️  Could not auto-fill Ollama URL');
        console.log('   📝 Manual action needed:');
        console.log('      1. Find "Ollama Base URL" or "Connections" section');
        console.log(`      2. Enter: ${OLLAMA_URL}`);
        console.log('      3. Click Save or Refresh\n');
        console.log('   ⏳ Please complete this step...');
        await page.waitForTimeout(30000); // Give time to configure
      }
      
      // Try to click any refresh/save button
      const buttons = await page.$$('button');
      for (const button of buttons) {
        const text = await button.textContent().catch(() => '');
        if (text.toLowerCase().includes('refresh') || text.toLowerCase().includes('save')) {
          await button.click();
          console.log(`   ✅ Clicked "${text}" button\n`);
          break;
        }
      }
      
    } catch (e) {
      console.log('   ⚠️  Settings page structure not recognized');
      console.log(`   📝 Please manually set Ollama URL to: ${OLLAMA_URL}\n`);
      await page.waitForTimeout(30000);
    }
    
    // Step 5: Go to chat
    console.log('📋 Step 5: Opening Chat Interface...');
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    console.log('   ✅ Chat interface ready!\n');
    
    // Final instructions
    console.log('==========================================');
    console.log('✅ Setup Complete!');
    console.log('==========================================\n');
    console.log('🎯 Next Steps:');
    console.log('   1. Select a model from the dropdown');
    console.log('   2. Test with: "search for machine learning"');
    console.log('   3. Athena will return real search results!\n');
    console.log('💾 Your credentials:');
    console.log(`   Email: ${CREDENTIALS.email}`);
    console.log(`   Password: ${CREDENTIALS.password}\n`);
    console.log('🦙 Ollama URL: ' + OLLAMA_URL + '\n');
    console.log('The browser will stay open. Close it when done.\n');
    console.log('Press Ctrl+C to close this script.');
    
    // Keep browser open
    await page.waitForTimeout(300000); // 5 minutes
    
  } catch (error) {
    console.error('\n❌ Error:', error.message);
  }
  
  // Don't auto-close so user can continue using it
  console.log('\nClosing...');
  await browser.close();
})();

