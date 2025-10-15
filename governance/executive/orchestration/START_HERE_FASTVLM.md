# 🚀 START HERE - FastVLM Quick Guide

**Get vision AI running in 5 minutes**

---

## Step 1: Go Live

```bash
cd /Users/christianmerrill/Documents/GitHub
make fastvlm-go-live
```

**The script will guide you through everything.**

---

## Step 2: Verify

```bash
make daily-ops
```

**All green? You're ready!**

---

## Step 3: Use It

```bash
# Analyze a chart
make vision-chart IMG=~/Desktop/chart.png

# Extract text from document
make vision-ocr IMG=~/Desktop/document.png

# Analyze UI screenshot
make vision-ui IMG=~/Desktop/screenshot.png
```

---

## Step 4: Check Model History

```bash
make lineage-tree
```

**See the family tree of your models!**

---

## Daily Operations

Run this every morning (90 seconds):

```bash
make daily-ops
```

---

## 📚 More Info

- **README_FASTVLM.md** - Feature overview
- **GO_LIVE_CHECKLIST.md** - Detailed deployment
- **FASTVLM_FINAL_SUMMARY.md** - Complete reference

---

## 🆘 Need Help?

```bash
make help                        # All commands
make fastvlm-health             # Check status
make fastvlm-logs               # View logs
```

---

**That's it! Run `make fastvlm-go-live` and you're off!** 🚀
