# 🔧 UI Troubleshooting Guide

## Current Status

- ✅ Backend services working perfectly
- ✅ API responding correctly (200 OK)
- ✅ Smart routing functioning
- ❓ UI issue needs debugging

## Quick Tests

### 1. Simple Test UI

Open: http://localhost:8080/test-ui.html

- This is a minimal test interface
- Will show connection status
- Allows direct API testing

### 2. Browser Developer Tools

1. Right-click on page → Inspect
2. Go to Console tab
3. Look for JavaScript errors
4. Go to Network tab to see requests

### 3. Hard Refresh

- **Mac:** Cmd + Shift + R
- **Windows:** Ctrl + Shift + R
- This clears cached files

### 4. Different Browser

Try the UI in:

- Chrome
- Firefox
- Safari
- Edge

## Common Issues & Solutions

### Issue: "Thinking..." Never Resolves

**Cause:** JavaScript error or network issue
**Solution:**

1. Check browser console for errors
2. Try the simple test UI
3. Hard refresh the page

### Issue: Connection Refused

**Cause:** Services not running
**Solution:**

```bash
# Check services
curl http://localhost:8089/health
curl http://localhost:8080/test-ui.html
```

### Issue: CORS Errors

**Cause:** Cross-origin request blocked
**Solution:** The services have CORS enabled, but try:

1. Different browser
2. Disable browser security temporarily

### Issue: Slow Responses

**Cause:** Large model loading
**Solution:** This is normal for complex queries using 14B+ models

## Debug Commands

```bash
# Test API directly
curl http://localhost:8089/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"messages":[{"role":"user","content":"Hello"}],"max_tokens":50}'

# Check service health
curl http://localhost:8089/health

# Check UI server
curl http://localhost:8080/test-ui.html
```

## Next Steps

1. **Try the simple test UI first:** http://localhost:8080/test-ui.html
2. **Check browser console** for JavaScript errors
3. **Try different browser** if issues persist
4. **Hard refresh** the original UI page

The backend is working perfectly - this is just a frontend debugging issue!
