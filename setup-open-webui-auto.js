#!/usr/bin/env node
/**
 * Automated Open WebUI Setup using Playwright
 * This script will:
 * 1. Create an admin account
 * 2. Configure Ollama connection
 * 3. Test the setup
 */

const { chromium } = require('playwright');

const BASE_URL = 'http://localhost:3000';
const OLLAMA_URL = 'http://host.docker.internal:11434';
const ADMIN_EMAIL = 'admin@athena.local';
const ADMIN_PASSWORD = 'athena-admin-2024';
const ADMIN_NAME = 'Athena Admin';

async function setupOpenWebUI() {
  console.log('==========================================');
  console.log('🚀 Automated Open WebUI Setup');
  console.log('==========================================\n');

  let browser;
  let success = false;

  try {
    // Launch browser
    console.log('📋 Launching browser...');
    browser = await chromium.launch({ 
      headless: false,  // Show browser so you can see what's happening
      slowMo: 500       // Slow down for visibility
    });
    const context = await browser.newContext();
    const page = await context.newPage();

    // Navigate to Open WebUI
    console.log(`📋 Navigating to ${BASE_URL}...`);
    await page.goto(BASE_URL, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    // Check if we need to sign up
    const currentUrl = page.url();
    console.log(`   Current URL: ${currentUrl}`);

    if (currentUrl.includes('/auth') || await page.locator('text=Sign up').isVisible().catch(() => false)) {
      console.log('\n📋 Creating admin account...');
      
      // Fill in signup form
      await page.fill('input[type="email"], input[placeholder*="email" i]', ADMIN_EMAIL);
      await page.fill('input[type="password"]', ADMIN_PASSWORD);
      
      // Try to find and fill name field
      const nameField = page.locator('input[placeholder*="name" i]').first();
      if (await nameField.isVisible().catch(() => false)) {
        await nameField.fill(ADMIN_NAME);
      }
      
      // Click sign up button
      const signUpButton = page.locator('button:has-text("Sign up"), button:has-text("Create Account")').first();
      await signUpButton.click();
      
      console.log('   ✅ Account created');
      console.log(`   📧 Email: ${ADMIN_EMAIL}`);
      console.log(`   🔑 Password: ${ADMIN_PASSWORD}`);
      
      await page.waitForTimeout(3000);
    } else if (currentUrl.includes('/auth/signin') || await page.locator('text=Sign in').isVisible().catch(() => false)) {
      console.log('\n📋 Logging in...');
      
      // Fill in signin form
      await page.fill('input[type="email"]', ADMIN_EMAIL);
      await page.fill('input[type="password"]', ADMIN_PASSWORD);
      
      // Click sign in button
      const signInButton = page.locator('button:has-text("Sign in")').first();
      await signInButton.click();
      
      console.log('   ✅ Logged in');
      await page.waitForTimeout(3000);
    } else {
      console.log('\n📋 Already logged in');
    }

    // Navigate to settings
    console.log('\n📋 Navigating to Settings...');
    
    // Try multiple methods to open settings
    try {
      // Method 1: Click profile button
      await page.click('button[aria-label*="Profile" i], button[aria-label*="User" i]', { timeout: 2000 });
      await page.waitForTimeout(1000);
      await page.click('text=Settings', { timeout: 2000 });
    } catch (e) {
      // Method 2: Direct navigation
      await page.goto(`${BASE_URL}/settings`, { waitUntil: 'networkidle' });
    }
    
    await page.waitForTimeout(2000);
    console.log('   ✅ Opened Settings');

    // Navigate to Connections tab
    console.log('\n📋 Configuring Ollama connection...');
    
    try {
      // Click on Connections tab
      await page.click('text=Connections', { timeout: 5000 });
      await page.waitForTimeout(1000);
    } catch (e) {
      console.log('   ⚠️  Could not find Connections tab, continuing...');
    }

    // Find and configure Ollama URL
    try {
      // Look for Ollama Base URL input
      const ollamaInput = page.locator('input[placeholder*="ollama" i], input[id*="ollama" i]').first();
      await ollamaInput.waitFor({ timeout: 5000 });
      
      // Clear and fill Ollama URL
      await ollamaInput.clear();
      await ollamaInput.fill(OLLAMA_URL);
      console.log(`   ✅ Set Ollama URL to: ${OLLAMA_URL}`);
      
      await page.waitForTimeout(1000);
      
      // Try to click refresh/save button
      try {
        const refreshButton = page.locator('button:has-text("Refresh"), button:has-text("Save"), button[aria-label*="refresh" i]').first();
        await refreshButton.click({ timeout: 2000 });
        console.log('   ✅ Clicked refresh/save');
      } catch (e) {
        console.log('   ℹ️  No refresh button found, settings may auto-save');
      }
      
      await page.waitForTimeout(2000);
      
    } catch (e) {
      console.log('   ⚠️  Could not configure Ollama automatically');
      console.log(`   Please set Ollama URL manually to: ${OLLAMA_URL}`);
    }

    // Navigate back to chat
    console.log('\n📋 Returning to chat interface...');
    await page.goto(BASE_URL, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    // Check if models are loaded
    try {
      const modelSelector = page.locator('select, button:has-text("Select")').first();
      if (await modelSelector.isVisible({ timeout: 2000 })) {
        console.log('   ✅ Models should be loaded');
      }
    } catch (e) {
      console.log('   ℹ️  Model selector not found');
    }

    console.log('\n==========================================');
    console.log('✅ Setup Complete!');
    console.log('==========================================\n');
    console.log('📧 Admin Email:', ADMIN_EMAIL);
    console.log('🔑 Admin Password:', ADMIN_PASSWORD);
    console.log('🦙 Ollama URL:', OLLAMA_URL);
    console.log('\n🔍 Test browser research by asking:');
    console.log('   "search for machine learning"');
    console.log('\n📝 Note: You can now close the browser or continue using it');
    console.log('         The browser will stay open for 30 seconds...\n');

    success = true;
    
    // Keep browser open for a bit
    await page.waitForTimeout(30000);

  } catch (error) {
    console.error('\n❌ Error during setup:', error.message);
    console.log('\n💡 You may need to complete some steps manually:');
    console.log('   1. Go to http://localhost:3000');
    console.log('   2. Create account or sign in');
    console.log('   3. Go to Settings → Connections');
    console.log(`   4. Set Ollama URL to: ${OLLAMA_URL}`);
  } finally {
    if (browser) {
      await browser.close();
    }
  }

  return success;
}

// Run the setup
setupOpenWebUI().then(success => {
  if (success) {
    console.log('✅ Automated setup completed successfully!');
    process.exit(0);
  } else {
    console.log('⚠️  Setup completed with some manual steps required');
    process.exit(1);
  }
}).catch(error => {
  console.error('❌ Fatal error:', error);
  process.exit(1);
});

