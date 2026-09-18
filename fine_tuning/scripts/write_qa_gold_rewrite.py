#!/usr/bin/env python3
"""Apply session gold assistant rewrites onto sampled qa_mix_v2 rows.

Reads fine_tuning/data/qa_rewrite_pilot/sample.json (system+user unchanged).
Writes qa_gold_rewrite_pilot.jsonl and pilot_manifest.json.

Does not modify qa_mix_train/val/test or the Kaggle zip.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from sample_qa_rewrite_pilot import SEED  # noqa: E402

# Assistant-only rewrites. Quotes are contiguous substrings of that row's CONTEXT.
GOLD: dict[str, str] = {
    "pilot-01": (
        "Spurgeon teaches that God sometimes pleads the cause of His people by silencing their enemies. "
        'Hear it: "What a remarkable instance you have of this in the case of Jacob!" '
        "[Sermon 579] Though his sons had done a foul deed, the Canaanites did not gather "
        "to destroy him, for the Lord had cast a solemn awe upon their hearts."
    ),
    "pilot-02": (
        "If your God cannot succour you in trouble, He is no God worth trusting. "
        'The word is plain: "Your God is not worth having if He cannot help you when you want help." '
        "[Sermon 579] Yet the living God does plead your cause in Providence, and you may "
        "rest upon His wisdom even when help is delayed."
    ),
    "pilot-03": (
        "If a penitent asks what he must do to be saved, Spurgeon would not send him home to works, "
        "but to Christ alone. He would say, "
        '"Christ must save you-believe on the name of the Lord Jesus Christ." '
        "[Sermon 34] Prayer and searching the Scriptures have their place after faith, but the "
        "first direction is naked faith on God's gospel."
    ),
    "pilot-04": (
        "It was necessary that Jesus should go, for the purposes of God required it. "
        '"It behoved him to suffer, that he might be made a propitiation for our sins." '
        "[Sermon 5] He must also slumber in the dust awhile, that He might perfume the "
        "chamber of the grave for His people."
    ),
    "pilot-05": (
        "However we may differ on other points, we agree in the end—we must die. And "
        '"we all want to die the death of the righteous and to have our last end like his." '
        "[Sermon 635] The question is personal: how will you do in that hour?"
    ),
    "pilot-06": (
        "The believer's trust is not a guess at a name, but a resting upon the incarnate Son. "
        '"I trust Him for what He is, what He has done, what He has promised yet to do"—'
        "he relies on Him, the incarnate Son of God. [Sermon 646] Next he trusts the Holy Spirit, "
        "who has begun to save him from inbred sin."
    ),
    "pilot-07": (
        "When the load would break the back, the everyday precept is still, Call unto Me. "
        'And more: "Cast your burden upon the Lord and He shall sustain you!" '
        "[Sermon 619] He shall never suffer the righteous to be moved, whether you are in "
        "the valley or on the mountain."
    ),
    "pilot-08": (
        "Men may argue from history, but Spurgeon sends the hearer to the Book. "
        '"the Bible, after all, is the best proof of any doctrine we can advance" '
        "[Sermon 33] — therefore look to the texts themselves rather than to our speculations."
    ),
    "pilot-09": (
        "Nathanael's case differs from the rest. "
        '"Was he converted by ministry? It does not appear so." '
        "[Sermon 570] Philip found him, yet he would not at first believe; Christ told him "
        "the secrets of his heart, and he was already a devout Israelite under the fig tree."
    ),
    "pilot-10": (
        "Necessity is laid upon the preacher while souls perish by thousands. After that "
        'doleful music, you will hear the voice: "woe is unto thee if thou preaches not the gospel." '
        "[Sermon 34] Until the earth itself is dissolved, the preacher must still thunder forth the Word."
    ),
    "pilot-11": (
        "Had the Lord not called you, you would have gone on as you were—deaf to many earlier "
        "calls, preferring the things of this world. "
        '"Some of you were drunkards, were profane, were injurious." '
        "[Sermon 616] Yet when this particular call came, Divine influence made you throw down "
        "your sword. I will not invent a scene the excerpt does not describe."
    ),
    "pilot-12": (
        "To the seeking soul already praying, God is on the way to meet you. You shall hear Him say, "
        '"Your sins, which are many, are all forgiven." '
        "[Sermon 619] Expect not a handful of barley only: He may astound you with mercy."
    ),
    "pilot-13": (
        "Prosperity often breeds presumption even in real Christians. David himself said, "
        '"I shall never be moved." '
        "[Sermon 22] We are not much better than David, nor half as good, if God always "
        "rocked us in the cradle of success."
    ),
    "pilot-14": (
        "Do not say, Lie by till morning—now is the accepted time. Trust Him and listen to "
        'His commandment, then "your peace shall be as a river and your righteousness as the waves of the sea." '
        "[Sermon 610]"
    ),
    "pilot-15": (
        "Those who already know how to pray are bidden to use that gift upon this word. "
        '"Pray, ye who know how to pray, that this message may be made effective in the hand of God." '
        "[Sermon 561] And you who have never prayed, God help you to pray now."
    ),
    "pilot-16": (
        "Looking at Christ is life, but strength to serve comes at His table. Let the minister say, "
        '"Come and dine!" '
        "[Sermon 633] Put before the flock the finest of the wheat, that they may have fellowship "
        "with the Master and with one another."
    ),
    "pilot-17": (
        "I cannot answer from these excerpts: they do not speak of Sunday School classrooms "
        "in the twenty-first century, and I will not guess beyond the sermons provided."
    ),
    "pilot-18": (
        "I do not find in these excerpts any instruction upon a wedding feast without guests; "
        "therefore I must say the provided sermons do not address it, and I will not speculate."
    ),
    "pilot-19": (
        "These excerpts do not treat of how godly sons should deal with ungodly "
        "brothers, and I will not invent an answer where the text is silent. The context is insufficient."
    ),
    "pilot-20": (
        "These excerpts do not treat of this matter, and I will not invent an "
        "answer where the text is silent. The context is insufficient."
    ),
}


def main() -> int:
    root = Path(__file__).resolve().parent.parent / "data" / "qa_rewrite_pilot"
    sample_path = root / "sample.json"
    rows = json.loads(sample_path.read_text(encoding="utf-8"))
    if len(rows) != 20:
        raise SystemExit(f"expected 20 sample rows, got {len(rows)}")
    missing = [r["id"] for r in rows if r["id"] not in GOLD]
    extra = sorted(set(GOLD) - {r["id"] for r in rows})
    if missing or extra:
        raise SystemExit(f"GOLD mismatch missing={missing} extra={extra}")

    out_rows = []
    for r in rows:
        out_rows.append(
            {
                "id": r["id"],
                "source_line": r["source_line"],
                "slice": r["slice"],
                "messages": [
                    {"role": "system", "content": r["system"]},
                    {"role": "user", "content": r["user"]},
                    {"role": "assistant", "content": GOLD[r["id"]]},
                ],
            }
        )

    jsonl_path = root / "qa_gold_rewrite_pilot.jsonl"
    with jsonl_path.open("w", encoding="utf-8") as f:
        for row in out_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "version": "qa_gold_rewrite_pilot",
        "teacher": "cursor-session",
        "seed": SEED,
        "source_mix": "fine_tuning/data/qa_mix_train.jsonl",
        "source_sample": "fine_tuning/data/qa_rewrite_pilot/sample.json",
        "counts": {
            "rows": len(out_rows),
            "answerable": sum(1 for r in rows if r["slice"] == "answerable"),
            "refusal": sum(1 for r in rows if r["slice"] == "refusal"),
        },
        "notes": [
            "Assistant-only rewrite; system and user copied byte-identical from sample.json.",
            "Does not replace qa_mix_train/val/test or spurgeon-qa-mix-v1.zip.",
            "Frozen test set was not sampled.",
        ],
    }
    man_path = root / "pilot_manifest.json"
    man_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {jsonl_path} ({len(out_rows)} rows)")
    print(f"Wrote {man_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
