"""
RAG Evaluation Test Questions for "Ask Spurgeon"

These questions are inspired by real theological questions from GotQuestions.org
and other common Christian inquiries, curated to test the quality of the
Spurgeon RAG system.

Categories covered (50 questions total):
- Direct sermon recall
- Core Spurgeon themes (sovereignty, grace, suffering, prayer, election)
- Bible passage interpretation
- Edge cases / "I don't know" testing
- Application / pastoral questions
- The Holy Spirit
- Evangelism & Missions
- Eternity
- The Church
- Practical Christian Living
- And more
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class RAGTestQuestion:
    id: int
    question: str
    category: str
    expected_themes: List[str]  # High-level topics we hope to retrieve
    notes: str = ""             # Why this question is useful for testing


TEST_QUESTIONS: List[RAGTestQuestion] = [
    # === Direct / Famous Spurgeon Sermons ===
    RAGTestQuestion(
        id=1,
        question="What did Spurgeon teach about the immutability of God?",
        category="Direct Sermon Recall",
        expected_themes=["Immutability of God", "Malachi 3:6", "God's unchanging nature"],
        notes="Direct hit on Sermon #1. Should retrieve the famous opening sermon strongly."
    ),
    RAGTestQuestion(
        id=2,
        question="What does Spurgeon say about suffering and reigning with Jesus?",
        category="Suffering & Sovereignty",
        expected_themes=["Suffering", "Reigning with Christ", "Consolation in trials"],
        notes="Tests retrieval on Sermon 13 and related suffering sermons."
    ),

    # === Core Theological Themes Spurgeon Preached Extensively ===
    RAGTestQuestion(
        id=3,
        question="How does Spurgeon reconcile God's sovereignty with human responsibility?",
        category="Theology - Sovereignty",
        expected_themes=["Sovereignty", "Human responsibility", "Election and free agency"],
        notes="Classic Spurgeon tension. Good test for balanced retrieval across multiple sermons."
    ),
    RAGTestQuestion(
        id=4,
        question="What did Spurgeon teach about the perseverance of the saints?",
        category="Theology - Salvation",
        expected_themes=["Perseverance", "Eternal security", "God's preserving grace"],
        notes="Central to Spurgeon's Calvinistic preaching."
    ),
    RAGTestQuestion(
        id=5,
        question="How does Spurgeon describe the relationship between faith and works in salvation?",
        category="Theology - Salvation",
        expected_themes=["Faith", "Works", "Grace", "Justification"],
        notes="Tests nuanced understanding of grace vs works."
    ),

    # === Prayer ===
    RAGTestQuestion(
        id=6,
        question="What did Spurgeon teach about the importance and power of prayer?",
        category="Prayer",
        expected_themes=["Prayer", "Wrestling in prayer", "Answers to prayer"],
        notes="Spurgeon wrote and preached extensively on prayer."
    ),
    RAGTestQuestion(
        id=7,
        question="How does Spurgeon advise Christians to pray when they feel spiritually dry or distant from God?",
        category="Prayer",
        expected_themes=["Dryness in prayer", "Persistence", "Dependence on the Spirit"],
        notes="Pastoral / practical application question."
    ),

    # === Suffering & Sovereignty ===
    RAGTestQuestion(
        id=8,
        question="What comfort does Spurgeon offer to believers who are going through deep suffering or trials?",
        category="Suffering & Sovereignty",
        expected_themes=["Comfort in affliction", "God's purposes in suffering", "Sovereignty"],
        notes="Very common theme in Spurgeon's ministry (he suffered greatly himself)."
    ),
    RAGTestQuestion(
        id=9,
        question="Did Spurgeon believe that God ordains or permits suffering for His people?",
        category="Suffering & Sovereignty",
        expected_themes=["God and evil", "Sovereignty over suffering"],
        notes="Tests careful handling of theodicy from Spurgeon's perspective."
    ),

    # === Bible Passage Questions ===
    RAGTestQuestion(
        id=10,
        question="What did Spurgeon preach from Romans 8, especially regarding the love of God?",
        category="Bible Passage",
        expected_themes=["Romans 8", "Nothing can separate us", "God's love"],
        notes="Romans 8 was one of Spurgeon's favorite chapters."
    ),
    RAGTestQuestion(
        id=11,
        question="How does Spurgeon explain John 3:16 and the 'whosoever' in the gospel?",
        category="Bible Passage",
        expected_themes=["John 3:16", "Whosoever", "Free offer of the gospel"],
        notes="Tests how Spurgeon held together sovereignty and the free offer."
    ),

    # === Election & Grace ===
    RAGTestQuestion(
        id=12,
        question="What did Spurgeon teach about election and predestination?",
        category="Theology - Election",
        expected_themes=["Election", "Predestination", "Sovereign grace"],
        notes="Core Spurgeon doctrine. Should retrieve many strong sermons."
    ),
    RAGTestQuestion(
        id=13,
        question="How did Spurgeon preach the doctrines of grace without making people passive or fatalistic?",
        category="Theology - Election",
        expected_themes=["Doctrines of grace", "Evangelism", "Human responsibility"],
        notes="Good test of balanced retrieval."
    ),

    # === Practical / Pastoral ===
    RAGTestQuestion(
        id=14,
        question="What counsel does Spurgeon give to someone struggling with assurance of salvation?",
        category="Pastoral / Assurance",
        expected_themes=["Assurance", "Doubt", "Looking to Christ"],
        notes="Very practical and common pastoral issue."
    ),
    RAGTestQuestion(
        id=15,
        question="How does Spurgeon advise Christians to fight against sin and temptation?",
        category="Spiritual Life",
        expected_themes=["Mortification of sin", "Dependence on Christ", "The Spirit's power"],
        notes="Tests practical sanctification teaching."
    ),

    # === Edge Cases & "I don't know" Testing ===
    RAGTestQuestion(
        id=16,
        question="What did Spurgeon teach about the use of modern technology and social media in the church?",
        category="Edge Case / Out of Corpus",
        expected_themes=[],
        notes="Should trigger honest 'I do not find this addressed in the sermons' response."
    ),
    RAGTestQuestion(
        id=17,
        question="What are Spurgeon's views on the role of women in church leadership and preaching?",
        category="Edge Case / Historical",
        expected_themes=["Women in ministry"],
        notes="Historically interesting. The corpus may have limited direct material."
    ),

    # === More Strong Topics ===
    RAGTestQuestion(
        id=18,
        question="What does Spurgeon say about the blood of Jesus and its power?",
        category="Christ & Atonement",
        expected_themes=["Blood of Christ", "Atonement", "Substitution"],
        notes="Extremely frequent theme in Spurgeon."
    ),
    RAGTestQuestion(
        id=19,
        question="How does Spurgeon describe the Christian's battle against the world, the flesh, and the devil?",
        category="Spiritual Warfare",
        expected_themes=["Spiritual warfare", "The flesh", "The world", "The devil"],
        notes="Classic Puritan/Spurgeon three enemies framework."
    ),
    RAGTestQuestion(
        id=20,
        question="What did Spurgeon teach about the return of Christ and the end times?",
        category="Eschatology",
        expected_themes=["Second Coming", "End times", "Millennium"],
        notes="Spurgeon had premillennial leanings later in life. Good test of retrieval."
    ),

    # === Expanded set to reach 50 questions ===

    # Assurance & Doubt
    RAGTestQuestion(
        id=21,
        question="What did Spurgeon say to Christians who struggle with doubts about their salvation?",
        category="Pastoral / Assurance",
        expected_themes=["Assurance", "Doubt", "Evidence of grace"],
        notes="Very common pastoral theme in Spurgeon's ministry."
    ),
    RAGTestQuestion(
        id=22,
        question="How does Spurgeon help believers gain and maintain assurance?",
        category="Pastoral / Assurance",
        expected_themes=["Assurance", "Looking to Christ", "The Spirit's witness"],
        notes="Tests practical advice on assurance."
    ),

    # Sanctification & Holiness
    RAGTestQuestion(
        id=23,
        question="What did Spurgeon teach about the process of sanctification and growing in holiness?",
        category="Spiritual Life",
        expected_themes=["Sanctification", "Holiness", "Growth in grace"],
        notes="Core practical doctrine."
    ),
    RAGTestQuestion(
        id=24,
        question="How does Spurgeon describe the Christian's ongoing battle with indwelling sin?",
        category="Spiritual Life",
        expected_themes=["Indwelling sin", "Mortification", "The flesh"],
        notes="Classic Spurgeon/Puritan theme."
    ),

    # The Holy Spirit
    RAGTestQuestion(
        id=25,
        question="What did Spurgeon teach about the person and work of the Holy Spirit?",
        category="Theology - Holy Spirit",
        expected_themes=["Holy Spirit", "Indwelling", "Power for service"],
        notes="Spurgeon emphasized the Spirit greatly."
    ),
    RAGTestQuestion(
        id=26,
        question="How does Spurgeon describe the Spirit's role in conversion and regeneration?",
        category="Theology - Holy Spirit",
        expected_themes=["Regeneration", "New birth", "Effectual calling"],
        notes="Key to Spurgeon's Calvinism."
    ),

    # More Bible Passages Spurgeon Preached On
    RAGTestQuestion(
        id=27,
        question="What did Spurgeon say about Psalm 23 and the Good Shepherd?",
        category="Bible Passage",
        expected_themes=["Psalm 23", "The Good Shepherd", "Comfort"],
        notes="One of the most beloved passages."
    ),
    RAGTestQuestion(
        id=28,
        question="How does Spurgeon preach on the love of God from Romans 8:28-39?",
        category="Bible Passage",
        expected_themes=["Romans 8", "God's love", "Nothing can separate"],
        notes="Powerful section Spurgeon returned to often."
    ),
    RAGTestQuestion(
        id=29,
        question="What does Spurgeon teach from Ephesians 2 about salvation by grace?",
        category="Bible Passage",
        expected_themes=["Ephesians 2", "By grace through faith", "Gift of God"],
        notes="Foundational text for Spurgeon's gospel."
    ),

    # Evangelism & Missions
    RAGTestQuestion(
        id=30,
        question="What did Spurgeon teach about the Christian's responsibility to evangelize and share the gospel?",
        category="Evangelism & Missions",
        expected_themes=["Evangelism", "Soul-winning", "The free offer"],
        notes="Spurgeon was a passionate evangelist."
    ),
    RAGTestQuestion(
        id=31,
        question="How does Spurgeon balance the doctrines of grace with passionate evangelism?",
        category="Evangelism & Missions",
        expected_themes=["Doctrines of grace", "Free offer of the gospel", "Urgency"],
        notes="Important tension in Spurgeon's ministry."
    ),

    # Suffering & Comfort (expanded)
    RAGTestQuestion(
        id=32,
        question="What does Spurgeon say to those who are depressed or experiencing spiritual darkness?",
        category="Suffering & Sovereignty",
        expected_themes=["Depression", "Spiritual darkness", "God's faithfulness"],
        notes="Spurgeon himself struggled with depression."
    ),
    RAGTestQuestion(
        id=33,
        question="How does Spurgeon explain why God allows His people to suffer?",
        category="Suffering & Sovereignty",
        expected_themes=["Why suffering", "God's purposes", "Sanctification through trials"],
        notes="Deep theodicy question."
    ),

    # The Cross & Atonement (expanded)
    RAGTestQuestion(
        id=34,
        question="What did Spurgeon emphasize about the substitutionary death of Christ?",
        category="Christ & Atonement",
        expected_themes=["Substitution", "The Cross", "Penal substitution"],
        notes="Central to Spurgeon's preaching."
    ),
    RAGTestQuestion(
        id=35,
        question="How does Spurgeon describe the power of the blood of Jesus?",
        category="Christ & Atonement",
        expected_themes=["Blood of Christ", "Cleansing", "Redemption"],
        notes="Recurring powerful theme."
    ),

    # Heaven, Hell, Eternity
    RAGTestQuestion(
        id=36,
        question="What did Spurgeon teach about heaven and the eternal state of believers?",
        category="Eternity",
        expected_themes=["Heaven", "Eternal joy", "Seeing Christ"],
        notes="Spurgeon often spoke longingly of heaven."
    ),
    RAGTestQuestion(
        id=37,
        question="How does Spurgeon describe the reality and horror of hell?",
        category="Eternity",
        expected_themes=["Hell", "Eternal punishment", "The wrath of God"],
        notes="He did not shy away from the doctrine."
    ),

    # The Bible & Revelation
    RAGTestQuestion(
        id=38,
        question="What was Spurgeon's view of the inspiration and authority of Scripture?",
        category="Theology - Bible",
        expected_themes=["Inspiration", "Authority of the Bible", "Inerrancy"],
        notes="Foundational for Spurgeon."
    ),
    RAGTestQuestion(
        id=39,
        question="How does Spurgeon advise Christians to read and study the Bible?",
        category="Theology - Bible",
        expected_themes=["Bible reading", "Meditation", "Application"],
        notes="Very practical teaching."
    ),

    # More Edge Cases & Modern Topics
    RAGTestQuestion(
        id=40,
        question="What would Spurgeon likely say about the prosperity gospel or health-and-wealth teaching?",
        category="Edge Case / False Teaching",
        expected_themes=[],
        notes="Good test of whether the system stays within the corpus or speculates."
    ),
    RAGTestQuestion(
        id=41,
        question="Did Spurgeon have anything to say about psychology, counseling, or mental health treatment?",
        category="Edge Case / Out of Corpus",
        expected_themes=[],
        notes="Another strong 'I don't know' test."
    ),

    # Family, Marriage, Daily Life
    RAGTestQuestion(
        id=42,
        question="What counsel did Spurgeon give regarding marriage and family life?",
        category="Practical Christian Living",
        expected_themes=["Marriage", "Family", "Parenting"],
        notes="Spurgeon spoke practically on these topics."
    ),
    RAGTestQuestion(
        id=43,
        question="How does Spurgeon address the Christian's attitude toward money and wealth?",
        category="Practical Christian Living",
        expected_themes=["Money", "Stewardship", "Contentment"],
        notes="Important practical theme."
    ),

    # Repentance & Conversion
    RAGTestQuestion(
        id=44,
        question="What did Spurgeon teach about genuine repentance?",
        category="Theology - Salvation",
        expected_themes=["Repentance", "Conviction of sin", "Turning from sin"],
        notes="Essential to Spurgeon's evangelistic preaching."
    ),
    RAGTestQuestion(
        id=45,
        question="How does Spurgeon describe the experience of coming to faith in Christ?",
        category="Theology - Salvation",
        expected_themes=["Conversion", "Coming to Christ", "New birth"],
        notes="Many of his sermons describe this."
    ),

    # Final Strong Topics
    RAGTestQuestion(
        id=46,
        question="What does Spurgeon say about the importance of the local church and fellowship with other believers?",
        category="The Church",
        expected_themes=["Church", "Fellowship", "Corporate worship"],
        notes="Spurgeon was a strong churchman."
    ),
    RAGTestQuestion(
        id=47,
        question="How does Spurgeon describe the Christian's hope in the face of death?",
        category="Eternity",
        expected_themes=["Death", "Hope", "Resurrection"],
        notes="Pastoral and comforting theme."
    ),
    RAGTestQuestion(
        id=48,
        question="What did Spurgeon teach about the dangers of formalism and dead religion?",
        category="Spiritual Life",
        expected_themes=["Formalism", "Dead religion", "Heart religion"],
        notes="He frequently warned against this."
    ),
    RAGTestQuestion(
        id=49,
        question="How does Spurgeon encourage believers to persevere in the Christian life when they feel weak?",
        category="Spiritual Life",
        expected_themes=["Perseverance", "Weakness", "Dependence on Christ"],
        notes="Encouraging and realistic pastoral teaching."
    ),
    RAGTestQuestion(
        id=50,
        question="What does Spurgeon say is the ultimate purpose of the Christian life?",
        category="Theology - General",
        expected_themes=["Purpose of life", "Glorifying God", "Enjoying God"],
        notes="Good summative question that should pull from multiple themes."
    ),
]


def get_all_test_questions() -> List[RAGTestQuestion]:
    return TEST_QUESTIONS


if __name__ == "__main__":
    print(f"Total test questions: {len(TEST_QUESTIONS)}")
    for q in TEST_QUESTIONS:
        print(f"  {q.id}. [{q.category}] {q.question[:80]}...")
