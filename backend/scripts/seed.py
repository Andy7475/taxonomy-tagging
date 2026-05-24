"""Seed taxonomy paths and emoji documents into Elasticsearch."""
import asyncio
import sys
from datetime import datetime, timezone

from elasticsearch import AsyncElasticsearch

ES_URL = "http://localhost:9200"
DOCUMENTS_INDEX = "taxonomy_documents"
TAXONOMY_INDEX = "taxonomy_paths"

TAXONOMY_NODES = [
    {"path": "type/face/emotion/positive", "label": "Positive Emotion",
     "synonyms": ["happy", "glad", "joy", "smile", "cheerful", "grin", "laugh"]},
    {"path": "type/face/emotion/negative", "label": "Negative Emotion",
     "synonyms": ["sad", "angry", "upset", "unhappy", "cry", "mad", "rage", "grief"]},
    {"path": "type/face/emotion/neutral", "label": "Neutral Emotion",
     "synonyms": ["indifferent", "blank", "expressionless", "stoic"]},
    {"path": "type/nature/weather/sky", "label": "Sky / Atmospheric",
     "synonyms": ["air", "atmosphere", "celestial", "heavenly"]},
    {"path": "type/nature/weather/storm", "label": "Storm / Rain",
     "synonyms": ["rain", "weather", "cloudy", "thunder", "lightning", "wet"]},
    {"path": "type/nature/plants/flower", "label": "Flower",
     "synonyms": ["bloom", "blossom", "floral", "petal"]},
    {"path": "type/nature/plants", "label": "Plants & Food",
     "synonyms": ["tree", "fruit", "food", "vegetable", "organic", "garden"]},
    {"path": "type/object/tech/device", "label": "Tech Device",
     "synonyms": ["gadget", "electronics", "tech", "computer", "digital", "hardware"]},
    {"path": "type/object/tool/utility", "label": "Utility Tool",
     "synonyms": ["tool", "instrument", "equipment", "gear", "implement"]},
    {"path": "type/activity/sport/ball", "label": "Ball Sport",
     "synonyms": ["sport", "game", "athletic", "play", "ball", "kick", "throw"]},
    {"path": "type/activity/music/instrument", "label": "Musical Instrument",
     "synonyms": ["music", "play", "band", "orchestra", "melody", "tune", "sound"]},
    {"path": "type/vehicle/land/road", "label": "Road Vehicle",
     "synonyms": ["drive", "transport", "land", "car", "automobile", "wheels"]},
    {"path": "type/vehicle/air/flight", "label": "Aircraft",
     "synonyms": ["travel", "sky", "wing", "fly", "aviation", "jet"]},
    {"path": "type/symbol/heart/love", "label": "Love / Heart Symbol",
     "synonyms": ["romance", "affection", "crush", "passion", "heart", "care"]},
    {"path": "type/symbol/time/clock", "label": "Clock / Time",
     "synonyms": ["time", "hour", "watch", "schedule", "alarm", "tick"]},
    # Visual
    {"path": "visual/color/red", "label": "Red",
     "synonyms": ["crimson", "hot", "warm", "fire", "ruby", "scarlet"]},
    {"path": "visual/color/blue", "label": "Blue",
     "synonyms": ["cold", "water", "ocean", "sky", "cool", "navy", "azure"]},
    {"path": "visual/color/yellow", "label": "Yellow",
     "synonyms": ["gold", "sunny", "bright", "lemon", "amber"]},
    {"path": "visual/color/green", "label": "Green",
     "synonyms": ["nature", "forest", "mint", "lime", "emerald", "jade"]},
    {"path": "visual/color/purple", "label": "Purple",
     "synonyms": ["violet", "lavender", "magenta", "indigo", "plum"]},
    {"path": "visual/color/orange", "label": "Orange",
     "synonyms": ["amber", "tangerine", "rust", "copper"]},
    {"path": "visual/color/white", "label": "White",
     "synonyms": ["bright", "clean", "snow", "pure", "pale", "ivory"]},
    {"path": "visual/color/black", "label": "Black",
     "synonyms": ["dark", "night", "shadow", "ebony", "charcoal"]},
    {"path": "visual/color/brown", "label": "Brown",
     "synonyms": ["wood", "earth", "tan", "sienna", "chocolate", "mocha"]},
    {"path": "visual/color/pink", "label": "Pink",
     "synonyms": ["blush", "rose", "salmon", "coral", "magenta"]},
    {"path": "visual/style/sparkly", "label": "Sparkly / Glittery",
     "synonyms": ["glitter", "shine", "sparkle", "shiny", "glimmer", "glam"]},
    {"path": "visual/style/metallic", "label": "Metallic",
     "synonyms": ["metal", "silver", "chrome", "steel", "iron", "alloy"]},
]

DOCUMENTS = [
    {"name": "Grinning Face", "icon": "😀", "tags": ["type/face/emotion/positive", "visual/color/yellow"]},
    {"name": "Crying Face", "icon": "😢", "tags": ["type/face/emotion/negative", "visual/color/yellow", "visual/color/blue"]},
    {"name": "Angry Face", "icon": "😡", "tags": ["type/face/emotion/negative", "visual/color/red"]},
    {"name": "Partying Face", "icon": "🥳", "tags": ["type/face/emotion/positive", "visual/color/yellow", "visual/style/sparkly"]},
    {"name": "Neutral Face", "icon": "😐", "tags": ["type/face/emotion/neutral", "visual/color/yellow"]},
    {"name": "Sweat Smile", "icon": "😅", "tags": ["type/face/emotion/positive", "visual/color/yellow", "visual/color/blue"]},
    {"name": "Sun", "icon": "☀️", "tags": ["type/nature/weather/sky", "visual/color/yellow"]},
    {"name": "Cloud with Rain", "icon": "🌧️", "tags": ["type/nature/weather/storm", "visual/color/blue"]},
    {"name": "Lightning", "icon": "⚡", "tags": ["type/nature/weather/storm", "visual/color/yellow"]},
    {"name": "Rose", "icon": "🌹", "tags": ["type/nature/plants/flower", "visual/color/red"]},
    {"name": "Sunflower", "icon": "🌻", "tags": ["type/nature/plants/flower", "visual/color/yellow", "visual/color/green"]},
    {"name": "Evergreen Tree", "icon": "🌲", "tags": ["type/nature/plants", "visual/color/green"]},
    {"name": "Laptop", "icon": "💻", "tags": ["type/object/tech/device", "visual/style/metallic"]},
    {"name": "Mobile Phone", "icon": "📱", "tags": ["type/object/tech/device", "visual/color/black"]},
    {"name": "Hammer", "icon": "🔨", "tags": ["type/object/tool/utility", "visual/style/metallic"]},
    {"name": "Light Bulb", "icon": "💡", "tags": ["type/object/tool/utility", "visual/color/yellow"]},
    {"name": "Red Heart", "icon": "❤️", "tags": ["type/symbol/heart/love", "visual/color/red"]},
    {"name": "Blue Heart", "icon": "💙", "tags": ["type/symbol/heart/love", "visual/color/blue"]},
    {"name": "Purple Heart", "icon": "💜", "tags": ["type/symbol/heart/love", "visual/color/purple"]},
    {"name": "Sparkling Heart", "icon": "💖", "tags": ["type/symbol/heart/love", "visual/style/sparkly", "visual/color/red"]},
    {"name": "Clock", "icon": "🕒", "tags": ["type/symbol/time/clock", "visual/style/metallic"]},
    {"name": "Basketball", "icon": "🏀", "tags": ["type/activity/sport/ball", "visual/color/orange"]},
    {"name": "Soccer Ball", "icon": "⚽", "tags": ["type/activity/sport/ball", "visual/color/white", "visual/color/black"]},
    {"name": "Tennis Ball", "icon": "🎾", "tags": ["type/activity/sport/ball", "visual/color/green"]},
    {"name": "Guitar", "icon": "🎸", "tags": ["type/activity/music/instrument", "visual/color/red"]},
    {"name": "Saxophone", "icon": "🎷", "tags": ["type/activity/music/instrument", "visual/color/yellow"]},
    {"name": "Red Car", "icon": "🚗", "tags": ["type/vehicle/land/road", "visual/color/red"]},
    {"name": "Police Car", "icon": "🚓", "tags": ["type/vehicle/land/road", "visual/color/blue", "visual/color/white"]},
    {"name": "Bus", "icon": "🚌", "tags": ["type/vehicle/land/road", "visual/color/yellow"]},
    {"name": "Airplane", "icon": "✈️", "tags": ["type/vehicle/air/flight", "visual/color/white", "visual/color/blue"]},
    {"name": "Bicycle", "icon": "🚲", "tags": ["type/vehicle/land/road"]},
    {"name": "Fire", "icon": "🔥", "tags": ["type/nature/weather/storm", "visual/color/orange", "visual/color/red"]},
    {"name": "Water Wave", "icon": "🌊", "tags": ["type/nature/weather/sky", "visual/color/blue"]},
    {"name": "Moon", "icon": "🌙", "tags": ["type/nature/weather/sky", "visual/color/yellow"]},
    {"name": "Apple", "icon": "🍎", "tags": ["type/nature/plants", "visual/color/red"]},
    {"name": "Orange Fruit", "icon": "🍊", "tags": ["type/nature/plants", "visual/color/orange"]},
    {"name": "Grapes", "icon": "🍇", "tags": ["type/nature/plants", "visual/color/purple"]},
    {"name": "Taco", "icon": "🌮", "tags": ["type/nature/plants", "visual/color/yellow"]},
    {"name": "Alien", "icon": "👽", "tags": ["type/face/emotion/neutral", "visual/color/green"]},
    {"name": "Ghost", "icon": "👻", "tags": ["type/face/emotion/neutral", "visual/color/white"]},
    {"name": "Explosion", "icon": "💥", "tags": ["visual/color/orange", "visual/color/red", "visual/style/sparkly"]},
    {"name": "Diamond", "icon": "💎", "tags": ["visual/color/blue", "visual/style/sparkly"]},
    {"name": "Gold Coin", "icon": "🪙", "tags": ["visual/color/yellow", "visual/style/metallic"]},
    {"name": "Tractor", "icon": "🚜", "tags": ["type/vehicle/land/road", "visual/color/green"]},
    {"name": "Rocket", "icon": "🚀", "tags": ["type/vehicle/air/flight", "visual/color/white", "visual/color/red"]},
    {"name": "Violin", "icon": "🎻", "tags": ["type/activity/music/instrument", "visual/color/brown"]},
    {"name": "Umbrella", "icon": "☂️", "tags": ["type/nature/weather/storm", "visual/color/purple"]},
    {"name": "Microphone", "icon": "🎤", "tags": ["type/activity/music/instrument", "visual/style/metallic"]},
    {"name": "Crystal Ball", "icon": "🔮", "tags": ["visual/color/purple", "visual/style/sparkly"]},
    {"name": "Beer Mug", "icon": "🍺", "tags": ["visual/color/yellow", "visual/color/white"]},
]


async def _ensure_parents(path: str, es: AsyncElasticsearch):
    segments = path.split("/")
    for i in range(1, len(segments)):
        parent = "/".join(segments[:i])
        if not await es.exists(index=TAXONOMY_INDEX, id=parent):
            await es.index(
                index=TAXONOMY_INDEX,
                id=parent,
                document={
                    "path": parent,
                    "label": segments[i - 1].replace("_", " ").title(),
                    "parent_path": "/".join(segments[: i - 1]) if i > 1 else None,
                    "depth": i - 1,
                    "synonyms": [],
                    "description": None,
                },
            )


async def main():
    es_url = sys.argv[1] if len(sys.argv) > 1 else ES_URL
    es = AsyncElasticsearch([es_url])

    print(f"Connecting to Elasticsearch at {es_url}...")
    info = await es.info()
    print(f"Connected: ES {info['version']['number']}")

    # Seed taxonomy
    print(f"\nSeeding {len(TAXONOMY_NODES)} taxonomy nodes...")
    for node in TAXONOMY_NODES:
        segments = node["path"].split("/")
        parent_path = "/".join(segments[:-1]) if len(segments) > 1 else None
        depth = len(segments) - 1

        await es.index(
            index=TAXONOMY_INDEX,
            id=node["path"],
            document={
                "path": node["path"],
                "label": node["label"],
                "parent_path": parent_path,
                "depth": depth,
                "synonyms": [s.lower() for s in node["synonyms"]],
                "description": None,
            },
        )
        await _ensure_parents(node["path"], es)
        print(f"  ✓ {node['path']}")

    await es.indices.refresh(index=TAXONOMY_INDEX)

    # Seed documents
    print(f"\nSeeding {len(DOCUMENTS)} documents...")
    import uuid as _uuid

    for doc in DOCUMENTS:
        now = datetime.now(timezone.utc).isoformat()
        await es.index(
            index=DOCUMENTS_INDEX,
            id=str(_uuid.uuid4()),
            document={**doc, "description": None, "metadata": None, "created_at": now},
        )
        print(f"  ✓ {doc['icon']}  {doc['name']}")

    await es.indices.refresh(index=DOCUMENTS_INDEX)

    print("\nDone! Taxonomy and emoji documents seeded successfully.")
    await es.close()


if __name__ == "__main__":
    asyncio.run(main())
