# Phase 1: Spurgeon Continued Pretraining — Step 1: Data Collection Report

This file documents the results, findings, and dataset characteristics gathered during **Step 1: Data Collection** of the continued pretraining pipeline.

---

## 1. Corpus Inventory Metrics

We ran the inventory script against the raw Markdown files located in `.\data\chspurgeon-sermons\`. Below is the complete volume-level character size audit:

| Volume               |  Files |   Avg Size (chars) |
|:---------------------|:-------|:-------------------|
| volume-1             |     50 |        35,173 chars |
| volume-2             |     50 |        34,346 chars |
| volume-3             |     56 |        33,745 chars |
| volume-4             |     60 |        34,962 chars |
| volume-5             |     59 |        36,170 chars |
| volume-6             |     59 |        37,549 chars |
| volume-7             |     66 |        38,250 chars |
| volume-8             |     57 |        37,918 chars |
| volume-9             |     59 |        37,695 chars |
| volume-10            |     60 |        38,039 chars |
| volume-11            |     60 |        37,896 chars |
| volume-12            |     60 |        37,610 chars |
| volume-13            |     60 |        37,565 chars |
| volume-14            |     60 |        37,028 chars |
| volume-15            |     60 |        36,264 chars |
| volume-16            |     60 |        37,633 chars |
| volume-17            |     60 |        38,440 chars |
| volume-18            |     61 |        37,931 chars |
| volume-19            |     61 |        36,856 chars |
| volume-20            |     60 |        37,498 chars |
| volume-21            |     61 |        36,915 chars |
| volume-22            |     61 |        38,022 chars |
| volume-23            |     60 |        38,094 chars |
| volume-24            |     60 |        38,449 chars |
| volume-25            |     69 |        33,150 chars |
| volume-26            |     63 |        36,050 chars |
| volume-27            |     63 |        36,779 chars |
| volume-28            |     61 |        37,405 chars |
| volume-29            |     59 |        38,526 chars |
| volume-30            |     59 |        37,681 chars |
| volume-31            |     60 |        36,099 chars |
| volume-32            |     61 |        36,603 chars |
| volume-33            |     63 |        36,225 chars |
| volume-34            |     59 |        36,645 chars |
| volume-35            |     59 |        36,444 chars |
| volume-36            |     59 |        35,920 chars |
| volume-37            |     56 |        36,911 chars |
| volume-38            |     52 |        36,367 chars |
| volume-39            |     53 |        37,156 chars |
| volume-40            |     52 |        37,397 chars |
| volume-41            |     52 |        36,927 chars |
| volume-42            |     52 |        37,449 chars |
| volume-43            |     52 |        37,805 chars |
| volume-44            |     53 |        36,228 chars |
| volume-45            |     53 |        37,541 chars |
| volume-46            |     52 |        36,676 chars |
| volume-47            |     52 |        36,740 chars |
| volume-48            |     52 |        36,833 chars |
| volume-49            |     52 |        36,860 chars |
| volume-50            |     51 |        37,753 chars |
| volume-51            |     52 |        36,831 chars |
| volume-52            |     52 |        36,455 chars |
| volume-53            |     52 |        36,773 chars |
| volume-54            |     52 |        36,576 chars |
| volume-55            |     53 |        36,491 chars |
| volume-56            |     53 |        35,565 chars |
| volume-57            |     52 |        34,643 chars |
| volume-58            |     52 |        34,995 chars |
| volume-59            |     52 |        35,162 chars |
| volume-60            |     53 |        35,686 chars |
| volume-61            |     53 |        35,140 chars |
| volume-62            |     52 |        31,194 chars |
| volume-63            |     19 |        33,785 chars |
|:---------------------|:-------|:-------------------|
| **TOTAL**            | **3536**|    **36,650 chars** |

* **Estimated Raw Data Size:** 129.60 MB (129,595,999 characters)
* **Average Sermon Length:** 36,650 characters

---

## 2. Formatting & Structure Observations

We sampled and examined several sermon files from various volumes:
1. **Frontmatter:** None present in the raw `.md` files. Standard files start directly with the sermon title header.
2. **Typography & Styling:**
   - Emphasis is represented by markdown markers (`**bold**`, `*italic*`).
   - Line endings are mixed (CRLF on Windows environment).
   - Double-hyphens (`--`) are used frequently instead of em-dashes.
3. **Outlining:** Subheading outline markers like `I.`, `II.`, `III.` are used by Spurgeon to organize sermon flows and should be kept as text.
4. **OCR Noise:** Some words contain mid-word hyphenation (e.g., `atmos-pheres`) due to line-break captures in text scanning.
5. **Footers:** Volumes 11–62 contain publisher ad/credit metadata blocks at the end of files (e.g., references to Passmore & Alabaster, collection version credits, scripture portions read, or hymns lists).

---

## 3. Anomalous Files Flagged

We ran size-limit boundary checks to identify potentially corrupt files, stubs, or multi-sermon files:

### 3.1 — Stubs & Index Files (< 3,000 characters)
* Found exactly **1** file:
  * `README.md` (2,115 characters) located at the root of `data/chspurgeon-sermons/`.
  * *Action:* Safely skip this file when cleaning and building the training corpus.

### 3.2 — Multi-Sermon Concatenations (> 80,000 characters)
* Found exactly **2** files:
  * `volume-7\sermon_385-388.md` (147,005 characters)
  * `volume-5\sermon-268-270.md` (121,110 characters)
  * *Action:* Keep these in the training dataset as they contain valid theological content, though they represent combined sermon series documents.

---

## 4. Held-out Evaluation Set (Holdout Split)

Exactly **50 random sermons** were set aside in `data/chspurgeon-holdout/` to serve as a clean validation split. To keep the original source folder unmutated, files were copied, and their subfolder structure was preserved.

The selected holdout sermons are:
1. `volume-50\sermon_2886.md`
2. `volume-16\sermon_953.md`
3. `volume-10\sermon_598.md`
4. `volume-58\sermon_3305.md`
5. `volume-26\sermon_1564.md`
6. `volume-24\sermon_1449.md`
7. `volume-23\sermon_1360.md`
8. `volume-18\sermon_1068.md`
9. `volume-58\sermon_3284.md`
10. `volume-16\sermon_916.md`
11. `volume-53\sermon_3039.md`
12. `volume-58\sermon_3301.md`
13. `volume-44\sermon_2558.md`
14. `volume-15\sermon_853.md`
15. `volume-47\sermon_2743.md`
16. `volume-35\sermon_2112.md`
17. `volume-11\sermon_626.md`
18. `volume-11\sermon_618.md`
19. `volume-15\sermon_880.md`
20. `volume-23\sermon_1341.md`
21. `volume-24\sermon_1398.md`
22. `volume-41\sermon_2394.md`
23. `volume-48\sermon_2790.md`
24. `volume-10\sermon_604.md`
25. `volume-45\sermon_2623.md`
26. `volume-21\sermon_1261.md`
27. `volume-56\sermon_3200.md`
28. `volume-51\sermon_2928.md`
29. `volume-55\sermon_3140.md`
30. `volume-44\sermon_2557.md`
31. `volume-35\sermon_2102.md`
32. `volume-23\sermon_1348.md`
33. `volume-37\sermon_2225.md`
34. `volume-47\sermon_2738.md`
35. `volume-27\sermon_1577.md`
36. `volume-62\sermon_3524.md`
37. `volume-1\sermon-32.md`
38. `volume-59\sermon_3376.md`
39. `volume-62\sermon_3509.md`
40. `volume-2\sermon-100.md`
41. `volume-55\sermon_3127.md`
42. `volume-35\sermon_2115.md`
43. `volume-30\sermon_1774.md`
44. `volume-27\sermon_1576.md`
45. `volume-19\sermon_1133.md`
46. `volume-22\sermon_1328.md`
47. `volume-6\sermon-294.md`
48. `volume-30\sermon_1759.md`
49. `volume-16\sermon_915.md`
50. `volume-15\sermon_876.md`

*Note: The cleaning and corpus-building script in Step 2 is configured to dynamically skip these files during training set compilation so they remain completely unseen by the language model.*
