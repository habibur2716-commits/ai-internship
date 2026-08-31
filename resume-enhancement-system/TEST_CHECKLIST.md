# Manual Test Checklist

## 1. Happy Path
**Steps:** Enter a valid job URL, upload a valid resume PDF, click Generate.
**Expected:** All 6 agents run, result displays on screen with proper formatting,
PDF downloads with matching formatting (headings, bold, bullets).
**Status:** ✅ Passed

## 2. Invalid PDF Upload
**Steps:** Upload a non-PDF file renamed to .pdf, or a corrupted PDF.
**Expected:** Clear error message ("This file doesn't look like a valid PDF..."),
no crash.
**Status:** ✅ Passed

## 3. Invalid Job URL
**Steps:** Enter malformed text instead of a URL (e.g. "hello world" or a URL
missing http/https).
**Expected:** Clear error message ("That doesn't look like a valid URL..."),
no crash.
**Status:** ✅ Passed

## 4. Job Scraping Failure (Bonus — Phase 3 fallback)
**Steps:** Enter a URL from a site known to block scraping (e.g. Indeed).
**Expected:** Warning shown, manual paste text box appears, app continues
successfully once text is pasted.
**Status:** ✅ Passed

## 5. Missing API Key
**Steps:** Leave Gemini/Serper API key fields empty in both sidebar and .env.
**Expected:** Clear error message ("Missing API key(s)..."), no crash.
**Status:** ✅ Passed

## 6. Invalid API Key
**Steps:** Enter a fake/wrong Gemini API key in the sidebar.
**Expected:** Clear error message showing the underlying API error, app does not
crash, temp files still get cleaned up.
**Status:** ✅ Passed (tested in Phase 2)

## 7. Oversized Resume/Job Text
**Steps:** Use a very long resume or paste a very long job description
(12,000+ characters).
**Expected:** Warning shown that text was trimmed, pipeline still completes
successfully.
**Status:** ✅ Passed

## 8. Scanned/Image-Based PDF Resume
**Steps:** Upload a resume PDF that is a scanned image (no extractable text).
**Expected:** Clear error message, no crash, no empty/garbage output.
**Status:** ✅ Passed (tested in Phase 3)