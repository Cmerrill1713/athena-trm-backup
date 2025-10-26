# 🔧 FIX YOUR BROWSER WINDOW RIGHT NOW

## **Open Browser Console and Run This:**

1. **Open DevTools:** Press `F12` or `Cmd + Option + I`
2. **Go to Console tab**
3. **Paste this code and press Enter:**

```javascript
// INSTANT FIX - Run this in your browser console
(async function () {
  console.clear();
  console.log("🔧 Fixing UI now...");

  // Fix the sendStream function
  window.sendStream = async function (prompt, model = "athena-rag", onChunk) {
    console.log("✅ Using FIXED sendStream");

    try {
      const r = await fetch("http://localhost:8089/v1/chat/completions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: [{ role: "user", content: prompt }],
          max_tokens: 500,
        }),
      });

      if (!r.ok) {
        throw new Error(`HTTP ${r.status}`);
      }

      const data = await r.json();
      const content = data.choices?.[0]?.message?.content || "No response";

      console.log("✅ Got response:", content.substring(0, 100));

      if (onChunk) {
        onChunk(content);
      }
      return content;
    } catch (err) {
      console.error("❌ Error:", err);
      if (onChunk) {
        onChunk(`Error: ${err.message}`);
      }
      throw err;
    }
  };

  console.log("✅ Function fixed!");
  console.log("✅ Now try typing a message and clicking Send");
})();
```

## **That's it!**

Now type a message in the UI and click Send - it should work!

---

## **Alternative: Quick Test**

After pasting the fix above, test it immediately:

```javascript
// Test the fix
await window.sendStream("Hello", "athena-rag", (response) => {
  console.log("✅ RESPONSE:", response);
  alert("SUCCESS! Got: " + response.substring(0, 100));
});
```

---

## **Or Just Reload**

If you want to start fresh:

1. Press `Cmd + Shift + R` (hard refresh)
2. The new code should load

---

## **Still Not Working?**

Open console and run:

```javascript
// Check backend
fetch("http://localhost:8089/health")
  .then((r) => r.json())
  .then((d) => console.log("✅ Backend:", d))
  .catch((e) => console.error("❌ Backend error:", e));

// Test API directly
fetch("http://localhost:8089/v1/chat/completions", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    messages: [{ role: "user", content: "Hello" }],
    max_tokens: 50,
  }),
})
  .then((r) => r.json())
  .then((d) => console.log("✅ API Response:", d))
  .catch((e) => console.error("❌ API Error:", e));
```

This will tell us exactly what's failing!

