# Job Site Compatibility List

Testing done using Serper's scrape endpoint (`https://scrape.serper.dev`) against 10 real
job postings across different sites.

## Results

| Site | Scraping Works Directly? | Fallback Needed? |
|---|---|---|
| LinkedIn | ✅ Yes | No |
| Indeed | ❌ No (500 error) | Yes — manual paste |
| Google Careers | ❌ No | Yes — manual paste |
| Microsoft Careers | ✅ Yes | No |
| Rozee.pk | ✅ Yes | No |
| Mustakbil.com | ✅ Yes | No |
| Wellfound (AngelList) | ✅ Yes | No |
| Glassdoor | ✅ Yes | No |
| Bayt.com | ❌ No | Yes — manual paste |

**Summary:** 7 out of 10 sites work with direct scraping. 3 sites (Indeed, Google Careers,
Bayt.com) fail scraping (likely due to bot-protection on those sites) but are fully handled
by the manual paste fallback.

## Fallback Behavior
If scraping fails or returns very little content (under 100 characters), the app shows a
clear warning message and displays a text box where the user can paste the job description
manually. The app then continues normally using that pasted text.

## Notes
- Sites that block scraping tend to do so consistently — this is expected behavior for
  sites with strong bot-protection (Indeed, Bayt) rather than a bug in our scraping code.
- If Serper's scraping success rate changes over time (sites update their protections), this
  list should be re-tested periodically.