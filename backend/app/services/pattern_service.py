from collections import defaultdict
import re


def analyze_patterns(memories):
    topic_count = defaultdict(int)   # frequency
    topic_time = defaultdict(int)    # total time

    STOPWORDS = {
        "i", "learned", "studied", "today",
        "for", "hours", "hour", "mins", "minutes"
    }

    for m in memories:
        content = m.content.lower()

        # 🔍 extract words (topics)
        words = re.findall(r'\b[a-zA-Z]{2,}\b', content)

        # remove stopwords
        topics = [w for w in words if w not in STOPWORDS]

        if not topics:
            continue

        # 🎯 count frequency
        for t in topics:
            topic_count[t] += 1

        # ⏱ extract duration
        if m.duration:
            match = re.search(r'(\d+)', m.duration)
            if match:
                time_value = int(match.group(1))

                # assign time to LAST meaningful topic
                topic_time[topics[-1]] += time_value

    # ❌ no data
    if not topic_count:
        return "I couldn't detect any pattern."

    # 🎯 DECISION LOGIC
    if topic_time:
        # ✅ PRIORITY → longest time
        top_topic = max(topic_time, key=topic_time.get)
        total_time = topic_time[top_topic]

        return f"You mostly study '{top_topic}' and spent about {total_time} hours in total."

    else:
        # ✅ FALLBACK → frequency
        top_topic = max(topic_count, key=topic_count.get)
        freq = topic_count[top_topic]

        return f"You often study '{top_topic}' ({freq} times)."