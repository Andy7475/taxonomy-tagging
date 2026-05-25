"""Seed taxonomy paths and emoji documents into Elasticsearch."""

import asyncio
import sys
from datetime import datetime, timezone

from elasticsearch import AsyncElasticsearch

ES_URL = "http://localhost:9200"
DOCUMENTS_INDEX = "taxonomy_documents"
TAXONOMY_INDEX = "taxonomy_paths"

TAXONOMY_NODES = [
    # Faces - emotion
    {
        "path": "type/face/emotion/positive",
        "label": "Positive Emotion",
        "synonyms": ["happy", "glad", "joy", "smile", "cheerful", "grin", "laugh"],
    },
    {
        "path": "type/face/emotion/negative",
        "label": "Negative Emotion",
        "synonyms": ["sad", "angry", "upset", "unhappy", "cry", "mad", "rage", "grief"],
    },
    {
        "path": "type/face/emotion/neutral",
        "label": "Neutral Emotion",
        "synonyms": ["indifferent", "blank", "expressionless", "stoic"],
    },
    {
        "path": "type/face/emotion/sick",
        "label": "Sick / Unwell",
        "synonyms": ["ill", "nausea", "fever", "cold", "dizzy", "vomit", "sneeze"],
    },
    {
        "path": "type/face/special",
        "label": "Special / Fantasy Face",
        "synonyms": [
            "alien",
            "robot",
            "ghost",
            "skull",
            "clown",
            "monster",
            "devil",
            "zombie",
        ],
    },
    {
        "path": "type/face/gesture",
        "label": "Hand Gesture",
        "synonyms": ["wave", "point", "thumbs", "clap", "fist", "peace", "ok", "pray"],
    },
    # People
    {
        "path": "type/person",
        "label": "Person",
        "synonyms": ["human", "people", "man", "woman", "child", "baby", "person"],
    },
    {
        "path": "type/person/role",
        "label": "Person with Role",
        "synonyms": [
            "worker",
            "professional",
            "job",
            "occupation",
            "uniform",
            "career",
        ],
    },
    # Animals
    {
        "path": "type/animal/mammal",
        "label": "Mammal",
        "synonyms": [
            "dog",
            "cat",
            "bear",
            "lion",
            "tiger",
            "horse",
            "pig",
            "cow",
            "fur",
            "paw",
        ],
    },
    {
        "path": "type/animal/bird",
        "label": "Bird",
        "synonyms": [
            "chicken",
            "penguin",
            "eagle",
            "owl",
            "duck",
            "parrot",
            "feather",
            "wing",
            "beak",
            "fly",
        ],
    },
    {
        "path": "type/animal/marine",
        "label": "Marine Animal",
        "synonyms": [
            "fish",
            "whale",
            "dolphin",
            "shark",
            "octopus",
            "crab",
            "ocean",
            "sea",
            "underwater",
        ],
    },
    {
        "path": "type/animal/reptile",
        "label": "Reptile / Amphibian",
        "synonyms": [
            "snake",
            "lizard",
            "frog",
            "turtle",
            "dragon",
            "dinosaur",
            "scales",
            "cold blooded",
        ],
    },
    {
        "path": "type/animal/insect",
        "label": "Insect / Bug",
        "synonyms": [
            "bug",
            "spider",
            "butterfly",
            "bee",
            "ant",
            "worm",
            "crawl",
            "six legs",
        ],
    },
    # Food
    {
        "path": "type/food/fruit",
        "label": "Fruit",
        "synonyms": ["sweet", "juicy", "berry", "tropical", "orchard", "citrus"],
    },
    {
        "path": "type/food/vegetable",
        "label": "Vegetable",
        "synonyms": ["veggie", "greens", "salad", "healthy", "garden", "root"],
    },
    {
        "path": "type/food/meal",
        "label": "Prepared Meal",
        "synonyms": [
            "dish",
            "cooked",
            "recipe",
            "cuisine",
            "dinner",
            "lunch",
            "eat",
            "food",
        ],
    },
    {
        "path": "type/food/snack",
        "label": "Snack / Fast Food",
        "synonyms": [
            "junk food",
            "burger",
            "fries",
            "pizza",
            "chips",
            "sandwich",
            "fast",
            "quick",
        ],
    },
    {
        "path": "type/food/dessert",
        "label": "Dessert / Sweets",
        "synonyms": [
            "cake",
            "candy",
            "sugar",
            "sweet",
            "chocolate",
            "ice cream",
            "cookie",
            "pudding",
        ],
    },
    {
        "path": "type/food/bread",
        "label": "Bread / Bakery",
        "synonyms": ["bake", "loaf", "wheat", "flour", "dough", "pastry", "croissant"],
    },
    # Drinks
    {
        "path": "type/drink/hot",
        "label": "Hot Drink",
        "synonyms": [
            "coffee",
            "tea",
            "hot chocolate",
            "warm",
            "brew",
            "mug",
            "steam",
            "cafe",
        ],
    },
    {
        "path": "type/drink/cold",
        "label": "Cold Drink",
        "synonyms": [
            "juice",
            "soda",
            "water",
            "cool",
            "refresh",
            "chill",
            "ice",
            "smoothie",
        ],
    },
    {
        "path": "type/drink/alcohol",
        "label": "Alcoholic Drink",
        "synonyms": [
            "beer",
            "wine",
            "cocktail",
            "whiskey",
            "booze",
            "drink",
            "party",
            "cheers",
            "bar",
        ],
    },
    # Nature
    {
        "path": "type/nature/weather/sky",
        "label": "Sky / Atmospheric",
        "synonyms": [
            "air",
            "atmosphere",
            "celestial",
            "heavenly",
            "sun",
            "moon",
            "star",
            "cloud",
        ],
    },
    {
        "path": "type/nature/weather/storm",
        "label": "Storm / Rain",
        "synonyms": [
            "rain",
            "weather",
            "cloudy",
            "thunder",
            "lightning",
            "wet",
            "hurricane",
            "flood",
        ],
    },
    {
        "path": "type/nature/plants/flower",
        "label": "Flower",
        "synonyms": [
            "bloom",
            "blossom",
            "floral",
            "petal",
            "rose",
            "garden",
            "bouquet",
        ],
    },
    {
        "path": "type/nature/plants",
        "label": "Plants & Trees",
        "synonyms": [
            "tree",
            "leaf",
            "grass",
            "forest",
            "jungle",
            "wood",
            "organic",
            "green",
        ],
    },
    {
        "path": "type/nature/earth",
        "label": "Earth / Landscape",
        "synonyms": [
            "mountain",
            "volcano",
            "desert",
            "island",
            "beach",
            "rock",
            "cave",
            "land",
        ],
    },
    {
        "path": "type/nature/space",
        "label": "Space / Astronomy",
        "synonyms": [
            "planet",
            "star",
            "galaxy",
            "universe",
            "comet",
            "meteor",
            "orbit",
            "cosmos",
        ],
    },
    # Vehicles
    {
        "path": "type/vehicle/land/road",
        "label": "Road Vehicle",
        "synonyms": [
            "drive",
            "transport",
            "land",
            "car",
            "automobile",
            "wheels",
            "road",
        ],
    },
    {
        "path": "type/vehicle/land/rail",
        "label": "Rail Vehicle",
        "synonyms": ["train", "metro", "subway", "tram", "rail", "track"],
    },
    {
        "path": "type/vehicle/air/flight",
        "label": "Aircraft",
        "synonyms": ["travel", "sky", "wing", "fly", "aviation", "jet", "airport"],
    },
    {
        "path": "type/vehicle/water",
        "label": "Water Vehicle",
        "synonyms": [
            "boat",
            "ship",
            "sail",
            "ferry",
            "submarine",
            "anchor",
            "sea",
            "ocean",
        ],
    },
    {
        "path": "type/vehicle/space",
        "label": "Space Vehicle",
        "synonyms": [
            "rocket",
            "satellite",
            "spacecraft",
            "ufo",
            "launch",
            "nasa",
            "orbit",
        ],
    },
    # Activities
    {
        "path": "type/activity/sport/ball",
        "label": "Ball Sport",
        "synonyms": [
            "sport",
            "game",
            "athletic",
            "play",
            "ball",
            "kick",
            "throw",
            "team",
        ],
    },
    {
        "path": "type/activity/sport/water",
        "label": "Water Sport",
        "synonyms": ["swim", "surf", "dive", "kayak", "rowing", "pool", "sea"],
    },
    {
        "path": "type/activity/sport/winter",
        "label": "Winter Sport",
        "synonyms": ["ski", "snowboard", "ice", "skate", "sled", "cold", "snow"],
    },
    {
        "path": "type/activity/sport/athletics",
        "label": "Athletics / Running",
        "synonyms": [
            "run",
            "sprint",
            "race",
            "marathon",
            "track",
            "jump",
            "throw",
            "olympic",
        ],
    },
    {
        "path": "type/activity/sport/martial",
        "label": "Martial Arts / Combat",
        "synonyms": ["fight", "karate", "boxing", "wrestling", "judo", "kick", "punch"],
    },
    {
        "path": "type/activity/music/instrument",
        "label": "Musical Instrument",
        "synonyms": [
            "music",
            "play",
            "band",
            "orchestra",
            "melody",
            "tune",
            "sound",
            "note",
        ],
    },
    {
        "path": "type/activity/celebration",
        "label": "Celebration / Party",
        "synonyms": [
            "party",
            "celebrate",
            "festival",
            "birthday",
            "firework",
            "confetti",
            "fun",
        ],
    },
    {
        "path": "type/activity/art",
        "label": "Art / Creativity",
        "synonyms": [
            "paint",
            "draw",
            "design",
            "craft",
            "create",
            "art",
            "brush",
            "colour",
        ],
    },
    {
        "path": "type/activity/game",
        "label": "Game / Gaming",
        "synonyms": [
            "play",
            "game",
            "console",
            "video",
            "board",
            "dice",
            "chess",
            "cards",
        ],
    },
    # Objects
    {
        "path": "type/object/tech/device",
        "label": "Tech Device",
        "synonyms": [
            "gadget",
            "electronics",
            "tech",
            "computer",
            "digital",
            "hardware",
            "screen",
        ],
    },
    {
        "path": "type/object/tool/utility",
        "label": "Utility Tool",
        "synonyms": [
            "tool",
            "instrument",
            "equipment",
            "gear",
            "implement",
            "fix",
            "build",
        ],
    },
    {
        "path": "type/object/clothing",
        "label": "Clothing / Fashion",
        "synonyms": [
            "wear",
            "dress",
            "shirt",
            "pants",
            "shoes",
            "hat",
            "fashion",
            "style",
            "outfit",
        ],
    },
    {
        "path": "type/object/household",
        "label": "Household Item",
        "synonyms": [
            "home",
            "furniture",
            "appliance",
            "kitchen",
            "bedroom",
            "bath",
            "sofa",
            "lamp",
        ],
    },
    {
        "path": "type/object/office",
        "label": "Office / Stationery",
        "synonyms": [
            "pen",
            "paper",
            "book",
            "write",
            "work",
            "study",
            "desk",
            "notebook",
        ],
    },
    {
        "path": "type/object/medical",
        "label": "Medical / Health",
        "synonyms": [
            "health",
            "doctor",
            "medicine",
            "pill",
            "hospital",
            "care",
            "band",
            "syringe",
        ],
    },
    {
        "path": "type/object/money",
        "label": "Money / Finance",
        "synonyms": [
            "cash",
            "coin",
            "dollar",
            "bank",
            "rich",
            "wealth",
            "pay",
            "currency",
        ],
    },
    # Symbols
    {
        "path": "type/symbol/heart/love",
        "label": "Love / Heart Symbol",
        "synonyms": [
            "romance",
            "affection",
            "crush",
            "passion",
            "heart",
            "care",
            "valentine",
        ],
    },
    {
        "path": "type/symbol/time/clock",
        "label": "Clock / Time",
        "synonyms": ["time", "hour", "watch", "schedule", "alarm", "tick", "minute"],
    },
    {
        "path": "type/symbol/warning",
        "label": "Warning / Alert",
        "synonyms": [
            "danger",
            "caution",
            "alert",
            "attention",
            "hazard",
            "stop",
            "exclamation",
        ],
    },
    {
        "path": "type/symbol/religious",
        "label": "Religious / Spiritual",
        "synonyms": [
            "faith",
            "prayer",
            "divine",
            "holy",
            "spirit",
            "peace",
            "star",
            "cross",
        ],
    },
    # Visual
    {
        "path": "visual/color/red",
        "label": "Red",
        "synonyms": ["crimson", "hot", "warm", "fire", "ruby", "scarlet"],
    },
    {
        "path": "visual/color/blue",
        "label": "Blue",
        "synonyms": ["cold", "water", "ocean", "sky", "cool", "navy", "azure"],
    },
    {
        "path": "visual/color/yellow",
        "label": "Yellow",
        "synonyms": ["gold", "sunny", "bright", "lemon", "amber"],
    },
    {
        "path": "visual/color/green",
        "label": "Green",
        "synonyms": ["nature", "forest", "mint", "lime", "emerald", "jade"],
    },
    {
        "path": "visual/color/purple",
        "label": "Purple",
        "synonyms": ["violet", "lavender", "magenta", "indigo", "plum"],
    },
    {
        "path": "visual/color/orange",
        "label": "Orange",
        "synonyms": ["amber", "tangerine", "rust", "copper"],
    },
    {
        "path": "visual/color/white",
        "label": "White",
        "synonyms": ["bright", "clean", "snow", "pure", "pale", "ivory"],
    },
    {
        "path": "visual/color/black",
        "label": "Black",
        "synonyms": ["dark", "night", "shadow", "ebony", "charcoal"],
    },
    {
        "path": "visual/color/brown",
        "label": "Brown",
        "synonyms": ["wood", "earth", "tan", "sienna", "chocolate", "mocha"],
    },
    {
        "path": "visual/color/pink",
        "label": "Pink",
        "synonyms": ["blush", "rose", "salmon", "coral", "magenta"],
    },
    {
        "path": "visual/color/multicolor",
        "label": "Multicolor / Rainbow",
        "synonyms": ["rainbow", "colorful", "pride", "vibrant", "diverse"],
    },
    {
        "path": "visual/style/sparkly",
        "label": "Sparkly / Glittery",
        "synonyms": ["glitter", "shine", "sparkle", "shiny", "glimmer", "glam"],
    },
    {
        "path": "visual/style/metallic",
        "label": "Metallic",
        "synonyms": ["metal", "silver", "chrome", "steel", "iron", "alloy", "shiny"],
    },
    {
        "path": "visual/style/fluffy",
        "label": "Fluffy / Soft",
        "synonyms": ["soft", "fuzzy", "plush", "cozy", "cuddly", "wool", "fur"],
    },
]

DOCUMENTS = [
    {
        "name": "Grinning Face",
        "icon": "😀",
        "tags": [
            "type/face/emotion/positive",
            "visual/color/brown",
            "visual/color/yellow",
        ],
    },
    {
        "name": "Beaming Face with Smiling Eyes",
        "icon": "😁",
        "tags": [
            "type/face/emotion/positive",
            "visual/color/brown",
            "visual/color/yellow",
        ],
    },
    {
        "name": "Face with Tears of Joy",
        "icon": "😂",
        "tags": [
            "type/face/emotion/positive",
            "visual/color/blue",
            "visual/color/brown",
            "visual/color/yellow",
        ],
    },
    {
        "name": "Rolling on the Floor Laughing",
        "icon": "🤣",
        "tags": [
            "type/face/emotion/positive",
            "visual/color/blue",
            "visual/color/brown",
            "visual/color/yellow",
        ],
    },
    {
        "name": "Slightly Smiling Face",
        "icon": "🙂",
        "tags": [
            "type/face/emotion/positive",
            "visual/color/brown",
            "visual/color/yellow",
        ],
    },
    {
        "name": "Winking Face",
        "icon": "😉",
        "tags": [
            "type/face/emotion/positive",
            "visual/color/brown",
            "visual/color/yellow",
        ],
    },
    {
        "name": "Smiling Face with Smiling Eyes",
        "icon": "😊",
        "tags": [
            "type/face/emotion/positive",
            "visual/color/brown",
            "visual/color/yellow",
            "visual/color/red",
        ],
    },
    {
        "name": "Smiling Face with Halo",
        "icon": "😇",
        "tags": [
            "type/face/emotion/positive",
            "type/symbol/religious",
            "visual/color/yellow",
            "visual/color/blue",
            "visual/color/brown",
        ],
    },
    {
        "name": "Smiling Face with Hearts",
        "icon": "🥰",
        "tags": [
            "type/face/emotion/positive",
            "type/symbol/heart/love",
            "visual/color/yellow",
            "visual/color/brown",
            "visual/color/red",
        ],
    },
    {
        "name": "Smiling Face with Heart-Eyes",
        "icon": "😍",
        "tags": [
            "type/face/emotion/positive",
            "type/symbol/heart/love",
            "visual/color/brown",
            "visual/color/yellow",
            "visual/color/red",
        ],
    },
    {
        "name": "Star-Struck",
        "icon": "🤩",
        "tags": [
            "type/face/emotion/positive",
            "visual/style/sparkly",
            "visual/color/orange",
            "visual/color/brown",
            "visual/color/yellow",
        ],
    },
    {
        "name": "Face Blowing a Kiss",
        "icon": "😘",
        "tags": [
            "type/face/emotion/positive",
            "type/symbol/heart/love",
            "visual/color/yellow",
            "visual/color/brown",
            "visual/color/red",
        ],
    },
    {
        "name": "Face Savoring Food",
        "icon": "😋",
        "tags": [
            "type/face/emotion/positive",
            "type/food/meal",
            "visual/color/brown",
            "visual/color/yellow",
            "visual/color/red",
        ],
    },
    {
        "name": "Partying Face",
        "icon": "🥳",
        "tags": [
            "type/face/emotion/positive",
            "type/activity/celebration",
            "visual/style/sparkly",
            "visual/color/multicolor",
        ],
    },
    {
        "name": "Hugging Face",
        "icon": "🤗",
        "tags": [
            "type/face/emotion/positive",
            "type/face/gesture",
            "visual/color/brown",
            "visual/color/yellow",
        ],
    },
    {
        "name": "Sweat Smile",
        "icon": "😅",
        "tags": [
            "type/face/emotion/positive",
            "visual/color/blue",
            "visual/color/brown",
            "visual/color/yellow",
        ],
    },
    {
        "name": "Crying Face",
        "icon": "😢",
        "tags": [
            "type/face/emotion/negative",
            "visual/color/blue",
            "visual/color/brown",
            "visual/color/yellow",
        ],
    },
    {
        "name": "Loudly Crying Face",
        "icon": "😭",
        "tags": [
            "type/face/emotion/negative",
            "visual/color/blue",
            "visual/color/brown",
            "visual/color/yellow",
            "visual/color/red",
        ],
    },
    {
        "name": "Angry Face",
        "icon": "😡",
        "tags": [
            "type/face/emotion/negative",
            "visual/color/black",
            "visual/color/red",
        ],
    },
    {
        "name": "Face with Steam from Nose",
        "icon": "😤",
        "tags": [
            "type/face/emotion/negative",
            "visual/color/brown",
            "visual/color/yellow",
            "visual/color/white",
        ],
    },
    {
        "name": "Enraged Face",
        "icon": "🤬",
        "tags": [
            "type/face/emotion/negative",
            "visual/color/black",
            "visual/color/red",
        ],
    },
    {
        "name": "Fearful Face",
        "icon": "😨",
        "tags": [
            "type/face/emotion/negative",
            "visual/color/brown",
            "visual/color/yellow",
            "visual/color/blue",
        ],
    },
    {
        "name": "Anxious Face with Sweat",
        "icon": "😰",
        "tags": [
            "type/face/emotion/negative",
            "visual/color/blue",
            "visual/color/brown",
            "visual/color/yellow",
        ],
    },
    {
        "name": "Disappointed Face",
        "icon": "😞",
        "tags": [
            "type/face/emotion/negative",
            "visual/color/brown",
            "visual/color/yellow",
        ],
    },
    {
        "name": "Weary Face",
        "icon": "😩",
        "tags": [
            "type/face/emotion/negative",
            "visual/color/brown",
            "visual/color/yellow",
        ],
    },
    {
        "name": "Tired Face",
        "icon": "😫",
        "tags": [
            "type/face/emotion/negative",
            "visual/color/brown",
            "visual/color/yellow",
            "visual/color/blue",
        ],
    },
    {
        "name": "Broken Heart",
        "icon": "💔",
        "tags": [
            "type/face/emotion/negative",
            "type/symbol/heart/love",
            "visual/color/red",
        ],
    },
    {
        "name": "Neutral Face",
        "icon": "😐",
        "tags": [
            "type/face/emotion/neutral",
            "visual/color/brown",
            "visual/color/yellow",
        ],
    },
    {
        "name": "Expressionless Face",
        "icon": "😑",
        "tags": [
            "type/face/emotion/neutral",
            "visual/color/brown",
            "visual/color/yellow",
        ],
    },
    {
        "name": "Face Without Mouth",
        "icon": "😶",
        "tags": [
            "type/face/emotion/neutral",
            "visual/color/brown",
            "visual/color/yellow",
        ],
    },
    {
        "name": "Thinking Face",
        "icon": "🤔",
        "tags": [
            "type/face/emotion/neutral",
            "visual/color/yellow",
            "visual/color/brown",
        ],
    },
    {
        "name": "Shushing Face",
        "icon": "🤫",
        "tags": [
            "type/face/emotion/neutral",
            "type/face/gesture",
            "visual/color/yellow",
            "visual/color/brown",
        ],
    },
    {
        "name": "Zipper-Mouth Face",
        "icon": "🤐",
        "tags": [
            "type/face/emotion/neutral",
            "visual/color/blue",
            "visual/color/brown",
            "visual/color/yellow",
        ],
    },
    {
        "name": "Sleeping Face",
        "icon": "😴",
        "tags": [
            "type/face/emotion/neutral",
            "visual/color/yellow",
            "visual/color/brown",
            "visual/color/blue",
        ],
    },
    {
        "name": "Drooling Face",
        "icon": "🤤",
        "tags": [
            "type/face/emotion/neutral",
            "visual/color/brown",
            "visual/color/yellow",
            "visual/color/blue",
        ],
    },
    {
        "name": "Unamused Face",
        "icon": "😒",
        "tags": [
            "type/face/emotion/neutral",
            "visual/color/brown",
            "visual/color/yellow",
        ],
    },
    {
        "name": "Face with Rolling Eyes",
        "icon": "🙄",
        "tags": [
            "type/face/emotion/neutral",
            "visual/color/yellow",
            "visual/color/white",
            "visual/color/brown",
        ],
    },
    {
        "name": "Smirking Face",
        "icon": "😏",
        "tags": [
            "type/face/emotion/neutral",
            "visual/color/brown",
            "visual/color/yellow",
        ],
    },
    {
        "name": "Face with Medical Mask",
        "icon": "😷",
        "tags": [
            "type/face/emotion/sick",
            "type/object/medical",
            "visual/color/brown",
            "visual/color/yellow",
            "visual/color/white",
        ],
    },
    {
        "name": "Face with Thermometer",
        "icon": "🤒",
        "tags": [
            "type/face/emotion/sick",
            "type/object/medical",
            "visual/color/brown",
            "visual/color/yellow",
            "visual/color/red",
            "visual/color/blue",
        ],
    },
    {
        "name": "Nauseated Face",
        "icon": "🤢",
        "tags": ["type/face/emotion/sick", "visual/color/green", "visual/color/black"],
    },
    {
        "name": "Sneezing Face",
        "icon": "🤧",
        "tags": [
            "type/face/emotion/sick",
            "visual/color/brown",
            "visual/color/yellow",
            "visual/color/white",
            "visual/color/blue",
        ],
    },
    {
        "name": "Hot Face",
        "icon": "🥵",
        "tags": [
            "type/face/emotion/sick",
            "visual/color/blue",
            "visual/color/red",
            "visual/color/black",
        ],
    },
    {
        "name": "Cold Face",
        "icon": "🥶",
        "tags": ["type/face/emotion/sick", "visual/color/blue"],
    },
    {
        "name": "Dizzy Face",
        "icon": "😵",
        "tags": ["type/face/emotion/sick", "visual/color/brown", "visual/color/yellow"],
    },
    {
        "name": "Alien",
        "icon": "👽",
        "tags": [
            "type/face/special",
            "type/vehicle/space",
            "visual/color/black",
            "visual/color/blue",
        ],
    },
    {
        "name": "Robot",
        "icon": "🤖",
        "tags": [
            "type/face/special",
            "type/object/tech/device",
            "visual/style/metallic",
            "visual/color/yellow",
            "visual/color/red",
            "visual/color/white",
            "visual/color/blue",
        ],
    },
    {
        "name": "Ghost",
        "icon": "👻",
        "tags": [
            "type/face/special",
            "visual/color/blue",
            "visual/color/black",
            "visual/color/white",
        ],
    },
    {
        "name": "Skull",
        "icon": "💀",
        "tags": ["type/face/special", "visual/color/black", "visual/color/blue"],
    },
    {
        "name": "Skull and Crossbones",
        "icon": "☠️",
        "tags": [
            "type/face/special",
            "type/symbol/warning",
            "visual/color/blue",
            "visual/color/black",
        ],
    },
    {
        "name": "Clown Face",
        "icon": "🤡",
        "tags": [
            "type/face/special",
            "type/activity/celebration",
            "visual/color/blue",
            "visual/color/red",
            "visual/color/yellow",
            "visual/color/brown",
        ],
    },
    {
        "name": "Devil",
        "icon": "😈",
        "tags": ["type/face/special", "visual/color/purple"],
    },
    {
        "name": "Ogre",
        "icon": "👹",
        "tags": [
            "type/face/special",
            "visual/color/yellow",
            "visual/color/red",
            "visual/color/black",
            "visual/color/blue",
        ],
    },
    {
        "name": "Goblin",
        "icon": "👺",
        "tags": [
            "type/face/special",
            "visual/color/yellow",
            "visual/color/red",
            "visual/color/black",
            "visual/color/white",
        ],
    },
    {
        "name": "Pile of Poo",
        "icon": "💩",
        "tags": [
            "type/face/special",
            "visual/color/red",
            "visual/color/orange",
            "visual/color/black",
            "visual/color/white",
        ],
    },
    {
        "name": "Zombie",
        "icon": "🧟",
        "tags": ["type/face/special", "visual/color/multicolor"],
    },
    {
        "name": "Waving Hand",
        "icon": "👋",
        "tags": ["type/face/gesture", "visual/color/blue", "visual/color/yellow"],
    },
    {
        "name": "Thumbs Up",
        "icon": "👍",
        "tags": [
            "type/face/gesture",
            "type/face/emotion/positive",
            "visual/color/yellow",
        ],
    },
    {
        "name": "Thumbs Down",
        "icon": "👎",
        "tags": [
            "type/face/gesture",
            "type/face/emotion/negative",
            "visual/color/yellow",
        ],
    },
    {
        "name": "Clapping Hands",
        "icon": "👏",
        "tags": [
            "type/face/gesture",
            "type/face/emotion/positive",
            "visual/color/orange",
            "visual/color/yellow",
        ],
    },
    {
        "name": "Folded Hands",
        "icon": "🙏",
        "tags": [
            "type/face/gesture",
            "type/symbol/religious",
            "visual/color/yellow",
            "visual/color/blue",
        ],
    },
    {
        "name": "Peace Hand",
        "icon": "✌️",
        "tags": ["type/face/gesture", "visual/color/yellow"],
    },
    {
        "name": "OK Hand",
        "icon": "👌",
        "tags": [
            "type/face/gesture",
            "type/face/emotion/positive",
            "visual/color/yellow",
        ],
    },
    {
        "name": "Raised Fist",
        "icon": "✊",
        "tags": ["type/face/gesture", "visual/color/yellow"],
    },
    {
        "name": "Backhand Index Pointing Up",
        "icon": "☝️",
        "tags": ["type/face/gesture", "visual/color/yellow"],
    },
    {
        "name": "Raised Hand",
        "icon": "✋",
        "tags": ["type/face/gesture", "visual/color/yellow"],
    },
    {
        "name": "Flexed Biceps",
        "icon": "💪",
        "tags": [
            "type/face/gesture",
            "type/activity/sport/athletics",
            "visual/color/yellow",
        ],
    },
    {
        "name": "Eyes",
        "icon": "👀",
        "tags": [
            "type/face/gesture",
            "visual/color/blue",
            "visual/color/black",
            "visual/color/white",
        ],
    },
    {
        "name": "Baby",
        "icon": "👶",
        "tags": ["type/person", "visual/color/red", "visual/color/yellow"],
    },
    {
        "name": "Child",
        "icon": "🧒",
        "tags": [
            "type/person",
            "visual/color/yellow",
            "visual/color/red",
            "visual/color/orange",
        ],
    },
    {
        "name": "Person",
        "icon": "🧑",
        "tags": [
            "type/person",
            "visual/color/yellow",
            "visual/color/red",
            "visual/color/orange",
        ],
    },
    {
        "name": "Older Person",
        "icon": "🧓",
        "tags": [
            "type/person",
            "visual/color/red",
            "visual/color/yellow",
            "visual/color/white",
            "visual/color/orange",
        ],
    },
    {
        "name": "Police Officer",
        "icon": "👮",
        "tags": [
            "type/person/role",
            "visual/color/yellow",
            "visual/color/blue",
            "visual/color/red",
            "visual/color/orange",
        ],
    },
    {
        "name": "Construction Worker",
        "icon": "👷",
        "tags": ["type/person/role", "visual/color/multicolor"],
    },
    {
        "name": "Doctor",
        "icon": "🧑\u200d⚕️",
        "tags": ["type/person/role", "type/object/medical", "visual/color/multicolor"],
    },
    {
        "name": "Cook",
        "icon": "🧑\u200d🍳",
        "tags": ["type/person/role", "type/food/meal", "visual/color/multicolor"],
    },
    {
        "name": "Scientist",
        "icon": "🧑\u200d🔬",
        "tags": [
            "type/person/role",
            "type/object/tech/device",
            "visual/color/multicolor",
        ],
    },
    {
        "name": "Astronaut",
        "icon": "🧑\u200d🚀",
        "tags": ["type/person/role", "type/vehicle/space", "visual/color/multicolor"],
    },
    {
        "name": "Farmer",
        "icon": "🧑\u200d🌾",
        "tags": ["type/person/role", "type/nature/plants", "visual/color/multicolor"],
    },
    {
        "name": "Artist",
        "icon": "🧑\u200d🎨",
        "tags": ["type/person/role", "type/activity/art", "visual/color/multicolor"],
    },
    {
        "name": "Singer",
        "icon": "🧑\u200d🎤",
        "tags": [
            "type/person/role",
            "type/activity/music/instrument",
            "visual/color/multicolor",
        ],
    },
    {
        "name": "Pilot",
        "icon": "🧑\u200d✈️",
        "tags": [
            "type/person/role",
            "type/vehicle/air/flight",
            "visual/color/multicolor",
        ],
    },
    {
        "name": "Firefighter",
        "icon": "🧑\u200d🚒",
        "tags": ["type/person/role", "type/symbol/warning", "visual/color/multicolor"],
    },
    {
        "name": "Dog",
        "icon": "🐶",
        "tags": [
            "type/animal/mammal",
            "visual/color/red",
            "visual/color/orange",
            "visual/color/black",
        ],
    },
    {
        "name": "Cat",
        "icon": "🐱",
        "tags": [
            "type/animal/mammal",
            "visual/color/yellow",
            "visual/color/black",
            "visual/color/red",
            "visual/color/brown",
        ],
    },
    {
        "name": "Mouse",
        "icon": "🐭",
        "tags": [
            "type/animal/mammal",
            "visual/style/fluffy",
            "visual/color/blue",
            "visual/color/brown",
            "visual/color/red",
            "visual/color/black",
        ],
    },
    {
        "name": "Hamster",
        "icon": "🐹",
        "tags": [
            "type/animal/mammal",
            "visual/style/fluffy",
            "visual/color/yellow",
            "visual/color/black",
            "visual/color/red",
            "visual/color/orange",
        ],
    },
    {
        "name": "Rabbit",
        "icon": "🐰",
        "tags": [
            "type/animal/mammal",
            "visual/style/fluffy",
            "visual/color/red",
            "visual/color/blue",
            "visual/color/black",
        ],
    },
    {
        "name": "Fox",
        "icon": "🦊",
        "tags": [
            "type/animal/mammal",
            "visual/color/yellow",
            "visual/color/black",
            "visual/color/red",
        ],
    },
    {
        "name": "Bear",
        "icon": "🐻",
        "tags": [
            "type/animal/mammal",
            "visual/style/fluffy",
            "visual/color/black",
            "visual/color/red",
            "visual/color/orange",
        ],
    },
    {
        "name": "Panda",
        "icon": "🐼",
        "tags": [
            "type/animal/mammal",
            "visual/style/fluffy",
            "visual/color/multicolor",
        ],
    },
    {
        "name": "Koala",
        "icon": "🐨",
        "tags": [
            "type/animal/mammal",
            "visual/style/fluffy",
            "visual/color/blue",
            "visual/color/brown",
            "visual/color/black",
        ],
    },
    {
        "name": "Tiger",
        "icon": "🐯",
        "tags": [
            "type/animal/mammal",
            "visual/color/yellow",
            "visual/color/black",
            "visual/color/red",
        ],
    },
    {
        "name": "Lion",
        "icon": "🦁",
        "tags": [
            "type/animal/mammal",
            "visual/color/yellow",
            "visual/color/black",
            "visual/color/red",
            "visual/color/orange",
        ],
    },
    {
        "name": "Cow",
        "icon": "🐮",
        "tags": ["type/animal/mammal", "visual/color/multicolor"],
    },
    {
        "name": "Pig",
        "icon": "🐷",
        "tags": ["type/animal/mammal", "visual/color/red", "visual/color/black"],
    },
    {
        "name": "Monkey",
        "icon": "🐵",
        "tags": [
            "type/animal/mammal",
            "visual/color/orange",
            "visual/color/red",
            "visual/color/black",
        ],
    },
    {
        "name": "Gorilla",
        "icon": "🦍",
        "tags": [
            "type/animal/mammal",
            "visual/color/blue",
            "visual/color/brown",
            "visual/color/black",
        ],
    },
    {
        "name": "Horse",
        "icon": "🐴",
        "tags": [
            "type/animal/mammal",
            "visual/color/red",
            "visual/color/black",
            "visual/color/orange",
        ],
    },
    {
        "name": "Unicorn",
        "icon": "🦄",
        "tags": [
            "type/animal/mammal",
            "visual/style/sparkly",
            "visual/color/multicolor",
        ],
    },
    {
        "name": "Zebra",
        "icon": "🦓",
        "tags": [
            "type/animal/mammal",
            "visual/color/brown",
            "visual/color/black",
            "visual/color/white",
        ],
    },
    {
        "name": "Deer",
        "icon": "🦌",
        "tags": [
            "type/animal/mammal",
            "visual/color/red",
            "visual/color/black",
            "visual/color/orange",
        ],
    },
    {
        "name": "Bison",
        "icon": "🦬",
        "tags": [
            "type/animal/mammal",
            "visual/color/blue",
            "visual/color/orange",
            "visual/color/black",
            "visual/color/red",
        ],
    },
    {
        "name": "Elephant",
        "icon": "🐘",
        "tags": [
            "type/animal/mammal",
            "visual/color/blue",
            "visual/color/brown",
            "visual/color/black",
        ],
    },
    {
        "name": "Hippopotamus",
        "icon": "🦛",
        "tags": [
            "type/animal/mammal",
            "visual/color/brown",
            "visual/color/blue",
            "visual/color/black",
            "visual/color/white",
        ],
    },
    {
        "name": "Rhinoceros",
        "icon": "🦏",
        "tags": [
            "type/animal/mammal",
            "visual/color/brown",
            "visual/color/blue",
            "visual/color/red",
            "visual/color/black",
        ],
    },
    {
        "name": "Giraffe",
        "icon": "🦒",
        "tags": [
            "type/animal/mammal",
            "visual/color/yellow",
            "visual/color/brown",
            "visual/color/black",
        ],
    },
    {
        "name": "Camel",
        "icon": "🐪",
        "tags": ["type/animal/mammal", "visual/color/black", "visual/color/orange"],
    },
    {
        "name": "Wolf",
        "icon": "🐺",
        "tags": [
            "type/animal/mammal",
            "visual/color/brown",
            "visual/color/black",
            "visual/color/blue",
        ],
    },
    {
        "name": "Boar",
        "icon": "🐗",
        "tags": [
            "type/animal/mammal",
            "visual/color/red",
            "visual/color/white",
            "visual/color/black",
            "visual/color/orange",
        ],
    },
    {
        "name": "Otter",
        "icon": "🦦",
        "tags": [
            "type/animal/mammal",
            "visual/color/black",
            "visual/color/orange",
            "visual/color/yellow",
            "visual/color/brown",
        ],
    },
    {
        "name": "Skunk",
        "icon": "🦨",
        "tags": ["type/animal/mammal", "visual/color/black", "visual/color/white"],
    },
    {
        "name": "Kangaroo",
        "icon": "🦘",
        "tags": ["type/animal/mammal", "visual/color/orange", "visual/color/black"],
    },
    {
        "name": "Badger",
        "icon": "🦡",
        "tags": [
            "type/animal/mammal",
            "visual/color/blue",
            "visual/color/black",
            "visual/color/white",
        ],
    },
    {
        "name": "Bat",
        "icon": "🦇",
        "tags": [
            "type/animal/mammal",
            "visual/color/brown",
            "visual/color/black",
            "visual/color/blue",
        ],
    },
    {
        "name": "Raccoon",
        "icon": "🦝",
        "tags": [
            "type/animal/mammal",
            "visual/color/blue",
            "visual/color/brown",
            "visual/color/black",
            "visual/color/white",
        ],
    },
    {
        "name": "Chicken",
        "icon": "🐔",
        "tags": [
            "type/animal/bird",
            "visual/color/yellow",
            "visual/color/red",
            "visual/color/black",
            "visual/color/white",
        ],
    },
    {
        "name": "Penguin",
        "icon": "🐧",
        "tags": [
            "type/animal/bird",
            "visual/color/yellow",
            "visual/color/black",
            "visual/color/white",
        ],
    },
    {
        "name": "Bird",
        "icon": "🐦",
        "tags": [
            "type/animal/bird",
            "visual/color/yellow",
            "visual/color/red",
            "visual/color/black",
        ],
    },
    {
        "name": "Baby Chick",
        "icon": "🐤",
        "tags": ["type/animal/bird", "visual/color/yellow", "visual/color/red"],
    },
    {
        "name": "Duck",
        "icon": "🦆",
        "tags": ["type/animal/bird", "visual/color/multicolor"],
    },
    {
        "name": "Eagle",
        "icon": "🦅",
        "tags": [
            "type/animal/bird",
            "visual/color/yellow",
            "visual/color/black",
            "visual/color/white",
        ],
    },
    {
        "name": "Owl",
        "icon": "🦉",
        "tags": [
            "type/animal/bird",
            "visual/color/yellow",
            "visual/color/black",
            "visual/color/red",
            "visual/color/orange",
        ],
    },
    {
        "name": "Flamingo",
        "icon": "🦩",
        "tags": [
            "type/animal/bird",
            "visual/color/red",
            "visual/color/white",
            "visual/color/black",
        ],
    },
    {
        "name": "Peacock",
        "icon": "🦚",
        "tags": [
            "type/animal/bird",
            "visual/color/green",
            "visual/color/black",
            "visual/color/blue",
        ],
    },
    {
        "name": "Parrot",
        "icon": "🦜",
        "tags": ["type/animal/bird", "visual/color/multicolor"],
    },
    {
        "name": "Swan",
        "icon": "🦢",
        "tags": [
            "type/animal/bird",
            "visual/color/yellow",
            "visual/color/black",
            "visual/color/white",
            "visual/color/blue",
        ],
    },
    {
        "name": "Turkey",
        "icon": "🦃",
        "tags": ["type/animal/bird", "visual/color/multicolor"],
    },
    {
        "name": "Rooster",
        "icon": "🐓",
        "tags": [
            "type/animal/bird",
            "visual/color/yellow",
            "visual/color/white",
            "visual/color/black",
            "visual/color/red",
        ],
    },
    {
        "name": "Hatching Chick",
        "icon": "🐣",
        "tags": [
            "type/animal/bird",
            "visual/color/yellow",
            "visual/color/blue",
            "visual/color/white",
            "visual/color/red",
        ],
    },
    {
        "name": "Whale",
        "icon": "🐳",
        "tags": ["type/animal/marine", "visual/color/blue", "visual/color/black"],
    },
    {
        "name": "Dolphin",
        "icon": "🐬",
        "tags": ["type/animal/marine", "visual/color/blue", "visual/color/black"],
    },
    {
        "name": "Seal",
        "icon": "🦭",
        "tags": [
            "type/animal/marine",
            "visual/color/blue",
            "visual/color/brown",
            "visual/color/black",
        ],
    },
    {"name": "Fish", "icon": "🐟", "tags": ["type/animal/marine", "visual/color/blue"]},
    {
        "name": "Tropical Fish",
        "icon": "🐠",
        "tags": ["type/animal/marine", "visual/color/yellow", "visual/color/black"],
    },
    {
        "name": "Blowfish",
        "icon": "🐡",
        "tags": [
            "type/animal/marine",
            "visual/color/red",
            "visual/color/orange",
            "visual/color/black",
        ],
    },
    {
        "name": "Shark",
        "icon": "🦈",
        "tags": ["type/animal/marine", "visual/color/brown", "visual/color/black"],
    },
    {
        "name": "Octopus",
        "icon": "🐙",
        "tags": ["type/animal/marine", "visual/color/purple", "visual/color/black"],
    },
    {
        "name": "Crab",
        "icon": "🦀",
        "tags": ["type/animal/marine", "visual/color/red", "visual/color/black"],
    },
    {
        "name": "Lobster",
        "icon": "🦞",
        "tags": ["type/animal/marine", "visual/color/red", "visual/color/black"],
    },
    {
        "name": "Shrimp",
        "icon": "🦐",
        "tags": ["type/animal/marine", "visual/color/red", "visual/color/black"],
    },
    {
        "name": "Squid",
        "icon": "🦑",
        "tags": ["type/animal/marine", "visual/color/red", "visual/color/black"],
    },
    {
        "name": "Clam",
        "icon": "🐚",
        "tags": ["type/animal/marine", "visual/color/blue", "visual/color/brown"],
    },
    {
        "name": "Coral",
        "icon": "🪸",
        "tags": ["type/animal/marine", "visual/color/blue", "visual/color/orange"],
    },
    {
        "name": "Turtle",
        "icon": "🐢",
        "tags": ["type/animal/reptile", "visual/color/green", "visual/color/black"],
    },
    {
        "name": "Lizard",
        "icon": "🦎",
        "tags": ["type/animal/reptile", "visual/color/green", "visual/color/black"],
    },
    {
        "name": "Snake",
        "icon": "🐍",
        "tags": [
            "type/animal/reptile",
            "visual/color/green",
            "visual/color/black",
            "visual/color/red",
        ],
    },
    {
        "name": "Dragon",
        "icon": "🐲",
        "tags": ["type/animal/reptile", "visual/color/green", "visual/color/black"],
    },
    {
        "name": "T-Rex",
        "icon": "🦖",
        "tags": [
            "type/animal/reptile",
            "visual/color/green",
            "visual/color/yellow",
            "visual/color/black",
        ],
    },
    {
        "name": "Frog",
        "icon": "🐸",
        "tags": ["type/animal/reptile", "visual/color/green", "visual/color/black"],
    },
    {
        "name": "Crocodile",
        "icon": "🐊",
        "tags": ["type/animal/reptile", "visual/color/green", "visual/color/black"],
    },
    {
        "name": "Butterfly",
        "icon": "🦋",
        "tags": [
            "type/animal/insect",
            "visual/style/sparkly",
            "visual/color/blue",
            "visual/color/black",
        ],
    },
    {
        "name": "Bug",
        "icon": "🐛",
        "tags": ["type/animal/insect", "visual/color/purple"],
    },
    {"name": "Ant", "icon": "🐜", "tags": ["type/animal/insect", "visual/color/black"]},
    {
        "name": "Honeybee",
        "icon": "🐝",
        "tags": [
            "type/animal/insect",
            "visual/color/blue",
            "visual/color/yellow",
            "visual/color/black",
        ],
    },
    {
        "name": "Ladybug",
        "icon": "🐞",
        "tags": ["type/animal/insect", "visual/color/black", "visual/color/red"],
    },
    {
        "name": "Cricket",
        "icon": "🦗",
        "tags": [
            "type/animal/insect",
            "visual/color/orange",
            "visual/color/yellow",
            "visual/color/black",
        ],
    },
    {
        "name": "Spider",
        "icon": "🕷️",
        "tags": ["type/animal/insect", "visual/color/black"],
    },
    {
        "name": "Snail",
        "icon": "🐌",
        "tags": ["type/animal/insect", "visual/color/yellow", "visual/color/purple"],
    },
    {
        "name": "Mosquito",
        "icon": "🦟",
        "tags": [
            "type/animal/insect",
            "visual/color/brown",
            "visual/color/black",
            "visual/color/white",
            "visual/color/blue",
        ],
    },
    {
        "name": "Fly",
        "icon": "🪰",
        "tags": [
            "type/animal/insect",
            "visual/color/black",
            "visual/color/red",
            "visual/color/white",
        ],
    },
    {
        "name": "Worm",
        "icon": "🪱",
        "tags": [
            "type/animal/insect",
            "visual/color/red",
            "visual/color/pink",
            "visual/color/purple",
        ],
    },
    {
        "name": "Grapes",
        "icon": "🍇",
        "tags": ["type/food/fruit", "visual/color/purple", "visual/color/green"],
    },
    {
        "name": "Watermelon",
        "icon": "🍉",
        "tags": [
            "type/food/fruit",
            "visual/color/yellow",
            "visual/color/red",
            "visual/color/green",
        ],
    },
    {
        "name": "Tangerine",
        "icon": "🍊",
        "tags": [
            "type/food/fruit",
            "visual/color/red",
            "visual/color/yellow",
            "visual/color/green",
        ],
    },
    {
        "name": "Lemon",
        "icon": "🍋",
        "tags": ["type/food/fruit", "visual/color/yellow", "visual/color/green"],
    },
    {
        "name": "Banana",
        "icon": "🍌",
        "tags": [
            "type/food/fruit",
            "visual/color/yellow",
            "visual/color/green",
            "visual/color/orange",
        ],
    },
    {
        "name": "Pineapple",
        "icon": "🍍",
        "tags": ["type/food/fruit", "visual/color/yellow", "visual/color/green"],
    },
    {
        "name": "Mango",
        "icon": "🥭",
        "tags": ["type/food/fruit", "visual/color/red", "visual/color/green"],
    },
    {
        "name": "Red Apple",
        "icon": "🍎",
        "tags": ["type/food/fruit", "visual/color/red", "visual/color/green"],
    },
    {
        "name": "Green Apple",
        "icon": "🍏",
        "tags": ["type/food/fruit", "visual/color/red", "visual/color/green"],
    },
    {
        "name": "Pear",
        "icon": "🍐",
        "tags": ["type/food/fruit", "visual/color/red", "visual/color/green"],
    },
    {
        "name": "Peach",
        "icon": "🍑",
        "tags": ["type/food/fruit", "visual/color/red", "visual/color/green"],
    },
    {
        "name": "Cherries",
        "icon": "🍒",
        "tags": ["type/food/fruit", "visual/color/red", "visual/color/green"],
    },
    {
        "name": "Strawberry",
        "icon": "🍓",
        "tags": ["type/food/fruit", "visual/color/red", "visual/color/green"],
    },
    {
        "name": "Blueberries",
        "icon": "🫐",
        "tags": [
            "type/food/fruit",
            "visual/color/green",
            "visual/color/blue",
            "visual/color/purple",
        ],
    },
    {
        "name": "Kiwi Fruit",
        "icon": "🥝",
        "tags": [
            "type/food/fruit",
            "visual/color/green",
            "visual/color/black",
            "visual/color/orange",
        ],
    },
    {
        "name": "Tomato",
        "icon": "🍅",
        "tags": ["type/food/fruit", "visual/color/green", "visual/color/red"],
    },
    {
        "name": "Olive",
        "icon": "🫒",
        "tags": [
            "type/food/fruit",
            "visual/color/orange",
            "visual/color/green",
            "visual/color/yellow",
        ],
    },
    {
        "name": "Coconut",
        "icon": "🥥",
        "tags": [
            "type/food/fruit",
            "visual/color/blue",
            "visual/color/yellow",
            "visual/color/brown",
            "visual/color/white",
        ],
    },
    {"name": "Melon", "icon": "🍈", "tags": ["type/food/fruit", "visual/color/green"]},
    {
        "name": "Aubergine",
        "icon": "🍆",
        "tags": ["type/food/vegetable", "visual/color/purple", "visual/color/green"],
    },
    {
        "name": "Avocado",
        "icon": "🥑",
        "tags": ["type/food/vegetable", "visual/color/green", "visual/color/red"],
    },
    {
        "name": "Broccoli",
        "icon": "🥦",
        "tags": ["type/food/vegetable", "visual/color/green"],
    },
    {
        "name": "Leafy Greens",
        "icon": "🥬",
        "tags": ["type/food/vegetable", "visual/color/green"],
    },
    {
        "name": "Cucumber",
        "icon": "🥒",
        "tags": ["type/food/vegetable", "visual/color/green"],
    },
    {
        "name": "Hot Pepper",
        "icon": "🌶️",
        "tags": ["type/food/vegetable", "visual/color/green", "visual/color/red"],
    },
    {
        "name": "Bell Pepper",
        "icon": "🫑",
        "tags": ["type/food/vegetable", "visual/color/green"],
    },
    {
        "name": "Garlic",
        "icon": "🧄",
        "tags": ["type/food/vegetable", "visual/color/blue", "visual/color/white"],
    },
    {
        "name": "Onion",
        "icon": "🧅",
        "tags": ["type/food/vegetable", "visual/color/yellow"],
    },
    {
        "name": "Potato",
        "icon": "🥔",
        "tags": ["type/food/vegetable", "visual/color/orange"],
    },
    {
        "name": "Corn",
        "icon": "🌽",
        "tags": ["type/food/vegetable", "visual/color/green", "visual/color/yellow"],
    },
    {
        "name": "Mushroom",
        "icon": "🍄",
        "tags": ["type/food/vegetable", "visual/color/blue", "visual/color/red"],
    },
    {
        "name": "Peanuts",
        "icon": "🥜",
        "tags": ["type/food/vegetable", "visual/color/orange"],
    },
    {
        "name": "Bread",
        "icon": "🍞",
        "tags": ["type/food/bread", "visual/color/yellow", "visual/color/orange"],
    },
    {
        "name": "Croissant",
        "icon": "🥐",
        "tags": ["type/food/bread", "visual/color/yellow", "visual/color/brown"],
    },
    {
        "name": "Baguette",
        "icon": "🥖",
        "tags": ["type/food/bread", "visual/color/yellow"],
    },
    {
        "name": "Flatbread",
        "icon": "🫓",
        "tags": [
            "type/food/bread",
            "visual/color/red",
            "visual/color/yellow",
            "visual/color/orange",
        ],
    },
    {
        "name": "Pretzel",
        "icon": "🥨",
        "tags": ["type/food/bread", "visual/color/yellow", "visual/color/brown"],
    },
    {
        "name": "Pancakes",
        "icon": "🥞",
        "tags": [
            "type/food/bread",
            "visual/color/yellow",
            "visual/color/brown",
            "visual/color/blue",
        ],
    },
    {
        "name": "Waffle",
        "icon": "🧇",
        "tags": [
            "type/food/bread",
            "visual/color/yellow",
            "visual/color/brown",
            "visual/color/blue",
        ],
    },
    {
        "name": "Cheese Wedge",
        "icon": "🧀",
        "tags": ["type/food/meal", "visual/color/yellow"],
    },
    {
        "name": "Fried Egg",
        "icon": "🍳",
        "tags": [
            "type/food/meal",
            "visual/color/yellow",
            "visual/color/brown",
            "visual/color/black",
            "visual/color/white",
        ],
    },
    {
        "name": "Bacon",
        "icon": "🥓",
        "tags": ["type/food/meal", "visual/color/yellow", "visual/color/red"],
    },
    {
        "name": "Steak",
        "icon": "🥩",
        "tags": [
            "type/food/meal",
            "visual/color/white",
            "visual/color/yellow",
            "visual/color/brown",
            "visual/color/red",
        ],
    },
    {
        "name": "Poultry Leg",
        "icon": "🍗",
        "tags": ["type/food/meal", "visual/color/yellow", "visual/color/orange"],
    },
    {
        "name": "Sushi",
        "icon": "🍣",
        "tags": ["type/food/meal", "visual/color/multicolor"],
    },
    {
        "name": "Bento Box",
        "icon": "🍱",
        "tags": ["type/food/meal", "visual/color/multicolor"],
    },
    {
        "name": "Rice",
        "icon": "🍚",
        "tags": [
            "type/food/meal",
            "visual/color/red",
            "visual/color/white",
            "visual/color/blue",
        ],
    },
    {
        "name": "Curry",
        "icon": "🍛",
        "tags": [
            "type/food/meal",
            "visual/color/white",
            "visual/color/yellow",
            "visual/color/blue",
            "visual/color/brown",
        ],
    },
    {
        "name": "Ramen",
        "icon": "🍜",
        "tags": [
            "type/food/meal",
            "visual/color/blue",
            "visual/color/yellow",
            "visual/color/red",
        ],
    },
    {
        "name": "Spaghetti",
        "icon": "🍝",
        "tags": ["type/food/meal", "visual/color/multicolor"],
    },
    {
        "name": "Taco",
        "icon": "🌮",
        "tags": [
            "type/food/meal",
            "visual/color/yellow",
            "visual/color/green",
            "visual/color/red",
            "visual/color/orange",
        ],
    },
    {
        "name": "Burrito",
        "icon": "🌯",
        "tags": ["type/food/meal", "visual/color/multicolor"],
    },
    {
        "name": "Salad",
        "icon": "🥗",
        "tags": ["type/food/meal", "type/food/vegetable", "visual/color/multicolor"],
    },
    {
        "name": "Paella",
        "icon": "🥘",
        "tags": [
            "type/food/meal",
            "visual/color/green",
            "visual/color/yellow",
            "visual/color/black",
            "visual/color/orange",
        ],
    },
    {
        "name": "Pot of Food",
        "icon": "🍲",
        "tags": ["type/food/meal", "visual/color/multicolor"],
    },
    {
        "name": "Hamburger",
        "icon": "🍔",
        "tags": [
            "type/food/snack",
            "visual/color/yellow",
            "visual/color/green",
            "visual/color/red",
            "visual/color/orange",
        ],
    },
    {
        "name": "French Fries",
        "icon": "🍟",
        "tags": ["type/food/snack", "visual/color/yellow", "visual/color/red"],
    },
    {
        "name": "Pizza",
        "icon": "🍕",
        "tags": ["type/food/snack", "visual/color/yellow", "visual/color/red"],
    },
    {
        "name": "Hot Dog",
        "icon": "🌭",
        "tags": [
            "type/food/snack",
            "visual/color/orange",
            "visual/color/yellow",
            "visual/color/red",
        ],
    },
    {
        "name": "Sandwich",
        "icon": "🥪",
        "tags": [
            "type/food/snack",
            "visual/color/yellow",
            "visual/color/green",
            "visual/color/red",
        ],
    },
    {
        "name": "Kebab",
        "icon": "🥙",
        "tags": [
            "type/food/snack",
            "visual/color/green",
            "visual/color/red",
            "visual/color/yellow",
            "visual/color/orange",
        ],
    },
    {
        "name": "Popcorn",
        "icon": "🍿",
        "tags": [
            "type/food/snack",
            "visual/color/red",
            "visual/color/blue",
            "visual/color/yellow",
            "visual/color/white",
        ],
    },
    {
        "name": "Ice Cream",
        "icon": "🍦",
        "tags": ["type/food/dessert", "visual/color/yellow"],
    },
    {
        "name": "Shaved Ice",
        "icon": "🍧",
        "tags": [
            "type/food/dessert",
            "visual/color/red",
            "visual/color/pink",
            "visual/color/blue",
        ],
    },
    {
        "name": "Ice Cream Scoop",
        "icon": "🍨",
        "tags": [
            "type/food/dessert",
            "visual/color/red",
            "visual/color/brown",
            "visual/color/blue",
            "visual/color/yellow",
        ],
    },
    {
        "name": "Doughnut",
        "icon": "🍩",
        "tags": [
            "type/food/dessert",
            "visual/color/red",
            "visual/color/yellow",
            "visual/color/blue",
            "visual/color/brown",
        ],
    },
    {
        "name": "Cookie",
        "icon": "🍪",
        "tags": ["type/food/dessert", "visual/color/orange", "visual/color/brown"],
    },
    {
        "name": "Birthday Cake",
        "icon": "🎂",
        "tags": [
            "type/food/dessert",
            "type/activity/celebration",
            "visual/color/red",
            "visual/color/yellow",
            "visual/color/white",
            "visual/color/blue",
        ],
    },
    {
        "name": "Shortcake",
        "icon": "🍰",
        "tags": [
            "type/food/dessert",
            "visual/color/white",
            "visual/color/red",
            "visual/color/yellow",
            "visual/color/brown",
        ],
    },
    {
        "name": "Cupcake",
        "icon": "🧁",
        "tags": ["type/food/dessert", "visual/color/multicolor"],
    },
    {
        "name": "Pie",
        "icon": "🥧",
        "tags": ["type/food/dessert", "visual/color/yellow", "visual/color/red"],
    },
    {
        "name": "Chocolate Bar",
        "icon": "🍫",
        "tags": [
            "type/food/dessert",
            "visual/color/red",
            "visual/color/brown",
            "visual/color/blue",
            "visual/color/orange",
        ],
    },
    {
        "name": "Candy",
        "icon": "🍬",
        "tags": ["type/food/dessert", "visual/color/red", "visual/color/white"],
    },
    {
        "name": "Lollipop",
        "icon": "🍭",
        "tags": ["type/food/dessert", "visual/color/yellow", "visual/color/red"],
    },
    {
        "name": "Honey Pot",
        "icon": "🍯",
        "tags": ["type/food/dessert", "visual/color/yellow", "visual/color/red"],
    },
    {
        "name": "Hot Beverage",
        "icon": "☕",
        "tags": [
            "type/drink/hot",
            "visual/color/blue",
            "visual/color/orange",
            "visual/color/white",
            "visual/color/brown",
        ],
    },
    {"name": "Teapot", "icon": "🫖", "tags": ["type/drink/hot", "visual/color/blue"]},
    {
        "name": "Tea",
        "icon": "🍵",
        "tags": [
            "type/drink/hot",
            "visual/color/brown",
            "visual/color/green",
            "visual/color/black",
            "visual/color/white",
        ],
    },
    {
        "name": "Juice Box",
        "icon": "🧃",
        "tags": [
            "type/drink/cold",
            "visual/color/yellow",
            "visual/color/blue",
            "visual/color/red",
        ],
    },
    {
        "name": "Cup with Straw",
        "icon": "🥤",
        "tags": [
            "type/drink/cold",
            "visual/color/blue",
            "visual/color/red",
            "visual/color/purple",
            "visual/color/white",
        ],
    },
    {
        "name": "Bubble Tea",
        "icon": "🧋",
        "tags": ["type/drink/cold", "visual/color/multicolor"],
    },
    {"name": "Sake", "icon": "🍶", "tags": ["type/drink/cold", "visual/color/blue"]},
    {
        "name": "Beer Mug",
        "icon": "🍺",
        "tags": ["type/drink/alcohol", "visual/color/yellow", "visual/color/white"],
    },
    {
        "name": "Clinking Beer Mugs",
        "icon": "🍻",
        "tags": [
            "type/drink/alcohol",
            "type/activity/celebration",
            "visual/color/yellow",
            "visual/color/white",
            "visual/color/orange",
        ],
    },
    {
        "name": "Clinking Glasses",
        "icon": "🥂",
        "tags": [
            "type/drink/alcohol",
            "type/activity/celebration",
            "visual/style/sparkly",
            "visual/color/orange",
            "visual/color/yellow",
            "visual/color/white",
        ],
    },
    {
        "name": "Wine Glass",
        "icon": "🍷",
        "tags": ["type/drink/alcohol", "visual/color/red", "visual/color/blue"],
    },
    {
        "name": "Cocktail Glass",
        "icon": "🍸",
        "tags": [
            "type/drink/alcohol",
            "visual/color/green",
            "visual/color/blue",
            "visual/color/red",
        ],
    },
    {
        "name": "Tropical Drink",
        "icon": "🍹",
        "tags": ["type/drink/alcohol", "visual/color/multicolor"],
    },
    {
        "name": "Bottle with Popping Cork",
        "icon": "🍾",
        "tags": [
            "type/drink/alcohol",
            "type/activity/celebration",
            "visual/color/multicolor",
        ],
    },
    {
        "name": "Whiskey Glass",
        "icon": "🥃",
        "tags": [
            "type/drink/alcohol",
            "visual/color/yellow",
            "visual/color/white",
            "visual/color/brown",
            "visual/color/blue",
        ],
    },
    {
        "name": "Rose",
        "icon": "🌹",
        "tags": ["type/nature/plants/flower", "visual/color/green", "visual/color/red"],
    },
    {
        "name": "Tulip",
        "icon": "🌷",
        "tags": ["type/nature/plants/flower", "visual/color/red", "visual/color/green"],
    },
    {
        "name": "Sunflower",
        "icon": "🌻",
        "tags": [
            "type/nature/plants/flower",
            "visual/color/yellow",
            "visual/color/green",
            "visual/color/orange",
        ],
    },
    {
        "name": "Bouquet",
        "icon": "💐",
        "tags": [
            "type/nature/plants/flower",
            "visual/color/yellow",
            "visual/color/green",
            "visual/color/red",
        ],
    },
    {
        "name": "Cherry Blossom",
        "icon": "🌸",
        "tags": [
            "type/nature/plants/flower",
            "visual/color/yellow",
            "visual/color/red",
        ],
    },
    {
        "name": "White Flower",
        "icon": "💮",
        "tags": ["type/nature/plants/flower", "visual/color/red"],
    },
    {
        "name": "Blossom",
        "icon": "🌼",
        "tags": [
            "type/nature/plants/flower",
            "visual/color/green",
            "visual/color/yellow",
            "visual/color/white",
            "visual/color/blue",
        ],
    },
    {
        "name": "Hibiscus",
        "icon": "🌺",
        "tags": [
            "type/nature/plants/flower",
            "visual/color/yellow",
            "visual/color/red",
            "visual/color/green",
        ],
    },
    {
        "name": "Evergreen Tree",
        "icon": "🌲",
        "tags": ["type/nature/plants", "visual/color/green", "visual/color/red"],
    },
    {
        "name": "Deciduous Tree",
        "icon": "🌳",
        "tags": ["type/nature/plants", "visual/color/green", "visual/color/red"],
    },
    {
        "name": "Palm Tree",
        "icon": "🌴",
        "tags": ["type/nature/plants", "visual/color/green", "visual/color/orange"],
    },
    {
        "name": "Cactus",
        "icon": "🌵",
        "tags": ["type/nature/plants", "visual/color/green"],
    },
    {
        "name": "Sheaf of Rice",
        "icon": "🌾",
        "tags": ["type/nature/plants", "visual/color/yellow", "visual/color/green"],
    },
    {
        "name": "Herb",
        "icon": "🌿",
        "tags": ["type/nature/plants", "visual/color/green", "visual/color/red"],
    },
    {
        "name": "Shamrock",
        "icon": "☘️",
        "tags": ["type/nature/plants", "visual/color/green"],
    },
    {
        "name": "Four Leaf Clover",
        "icon": "🍀",
        "tags": ["type/nature/plants", "visual/color/green"],
    },
    {
        "name": "Maple Leaf",
        "icon": "🍁",
        "tags": ["type/nature/plants", "visual/color/red"],
    },
    {
        "name": "Fallen Leaf",
        "icon": "🍂",
        "tags": ["type/nature/plants", "visual/color/orange"],
    },
    {
        "name": "Leaf Fluttering in Wind",
        "icon": "🍃",
        "tags": ["type/nature/plants", "visual/color/blue", "visual/color/green"],
    },
    {
        "name": "Seedling",
        "icon": "🌱",
        "tags": ["type/nature/plants", "visual/color/green"],
    },
    {
        "name": "Sun",
        "icon": "☀️",
        "tags": ["type/nature/weather/sky", "visual/color/yellow"],
    },
    {
        "name": "Full Moon",
        "icon": "🌕",
        "tags": ["type/nature/weather/sky", "visual/color/yellow"],
    },
    {
        "name": "Crescent Moon",
        "icon": "🌙",
        "tags": ["type/nature/weather/sky", "visual/color/yellow"],
    },
    {
        "name": "Star",
        "icon": "⭐",
        "tags": ["type/nature/weather/sky", "visual/color/yellow"],
    },
    {
        "name": "Glowing Star",
        "icon": "🌟",
        "tags": [
            "type/nature/weather/sky",
            "visual/style/sparkly",
            "visual/color/yellow",
        ],
    },
    {
        "name": "Shooting Star",
        "icon": "🌠",
        "tags": [
            "type/nature/weather/sky",
            "visual/style/sparkly",
            "visual/color/yellow",
            "visual/color/blue",
        ],
    },
    {
        "name": "Rainbow",
        "icon": "🌈",
        "tags": ["type/nature/weather/sky", "visual/color/multicolor"],
    },
    {
        "name": "Cloud",
        "icon": "☁️",
        "tags": ["type/nature/weather/sky", "visual/color/white", "visual/color/blue"],
    },
    {
        "name": "Sun Behind Cloud",
        "icon": "⛅",
        "tags": [
            "type/nature/weather/sky",
            "visual/color/yellow",
            "visual/color/white",
        ],
    },
    {
        "name": "Cloud with Rain",
        "icon": "🌧️",
        "tags": [
            "type/nature/weather/storm",
            "visual/color/blue",
            "visual/color/white",
        ],
    },
    {
        "name": "Lightning",
        "icon": "⚡",
        "tags": ["type/nature/weather/storm", "visual/color/yellow"],
    },
    {
        "name": "Snowflake",
        "icon": "❄️",
        "tags": ["type/nature/weather/storm", "visual/color/blue"],
    },
    {
        "name": "Snowman",
        "icon": "⛄",
        "tags": ["type/nature/weather/storm", "visual/color/multicolor"],
    },
    {
        "name": "Tornado",
        "icon": "🌪️",
        "tags": [
            "type/nature/weather/storm",
            "visual/color/brown",
            "visual/color/blue",
        ],
    },
    {
        "name": "Fog",
        "icon": "🌫️",
        "tags": [
            "type/nature/weather/storm",
            "visual/color/blue",
            "visual/color/white",
        ],
    },
    {
        "name": "Water Wave",
        "icon": "🌊",
        "tags": ["type/nature/weather/sky", "visual/color/blue"],
    },
    {
        "name": "Fire",
        "icon": "🔥",
        "tags": ["type/nature/weather/storm", "visual/color/yellow"],
    },
    {
        "name": "Droplet",
        "icon": "💧",
        "tags": ["type/nature/weather/sky", "visual/color/blue"],
    },
    {
        "name": "Umbrella",
        "icon": "☂️",
        "tags": [
            "type/nature/weather/storm",
            "visual/color/purple",
            "visual/color/brown",
        ],
    },
    {
        "name": "Globe Showing Americas",
        "icon": "🌎",
        "tags": ["type/nature/earth", "visual/color/blue", "visual/color/green"],
    },
    {
        "name": "Globe Showing Europe-Africa",
        "icon": "🌍",
        "tags": ["type/nature/earth", "visual/color/blue", "visual/color/green"],
    },
    {
        "name": "Globe Showing Asia-Australia",
        "icon": "🌏",
        "tags": ["type/nature/earth", "visual/color/blue", "visual/color/green"],
    },
    {
        "name": "Mount Fuji",
        "icon": "🗻",
        "tags": [
            "type/nature/earth",
            "visual/color/brown",
            "visual/color/blue",
            "visual/color/black",
            "visual/color/white",
        ],
    },
    {
        "name": "Volcano",
        "icon": "🌋",
        "tags": ["type/nature/earth", "visual/color/multicolor"],
    },
    {
        "name": "Desert",
        "icon": "🏜️",
        "tags": ["type/nature/earth", "visual/color/yellow", "visual/color/green"],
    },
    {
        "name": "Beach",
        "icon": "🏖️",
        "tags": [
            "type/nature/earth",
            "visual/color/brown",
            "visual/color/blue",
            "visual/color/yellow",
            "visual/color/red",
        ],
    },
    {
        "name": "Island",
        "icon": "🏝️",
        "tags": [
            "type/nature/earth",
            "visual/color/yellow",
            "visual/color/blue",
            "visual/color/green",
            "visual/color/orange",
        ],
    },
    {
        "name": "Mountain",
        "icon": "⛰️",
        "tags": [
            "type/nature/earth",
            "visual/color/brown",
            "visual/color/black",
            "visual/color/green",
        ],
    },
    {
        "name": "Camping",
        "icon": "🏕️",
        "tags": ["type/nature/earth", "visual/color/multicolor"],
    },
    {
        "name": "National Park",
        "icon": "🏞️",
        "tags": ["type/nature/earth", "visual/color/multicolor"],
    },
    {
        "name": "Ringed Planet",
        "icon": "🪐",
        "tags": ["type/nature/space", "visual/color/brown", "visual/color/yellow"],
    },
    {
        "name": "Comet",
        "icon": "☄️",
        "tags": [
            "type/nature/space",
            "visual/style/sparkly",
            "visual/color/blue",
            "visual/color/white",
        ],
    },
    {
        "name": "Milky Way",
        "icon": "🌌",
        "tags": [
            "type/nature/space",
            "visual/style/sparkly",
            "visual/color/purple",
            "visual/color/black",
            "visual/color/white",
        ],
    },
    {
        "name": "Black Hole",
        "icon": "🕳️",
        "tags": [
            "type/nature/space",
            "visual/color/black",
            "visual/color/brown",
            "visual/color/blue",
        ],
    },
    {
        "name": "Red Car",
        "icon": "🚗",
        "tags": [
            "type/vehicle/land/road",
            "visual/color/blue",
            "visual/color/black",
            "visual/color/red",
        ],
    },
    {
        "name": "Blue Car",
        "icon": "🚙",
        "tags": ["type/vehicle/land/road", "visual/color/blue", "visual/color/black"],
    },
    {
        "name": "Police Car",
        "icon": "🚓",
        "tags": ["type/vehicle/land/road", "visual/color/multicolor"],
    },
    {
        "name": "Ambulance",
        "icon": "🚑",
        "tags": [
            "type/vehicle/land/road",
            "type/object/medical",
            "visual/color/red",
            "visual/color/blue",
            "visual/color/black",
            "visual/color/white",
        ],
    },
    {
        "name": "Fire Engine",
        "icon": "🚒",
        "tags": ["type/vehicle/land/road", "visual/color/multicolor"],
    },
    {
        "name": "Bus",
        "icon": "🚌",
        "tags": [
            "type/vehicle/land/road",
            "visual/color/brown",
            "visual/color/yellow",
            "visual/color/blue",
            "visual/color/black",
        ],
    },
    {
        "name": "Trolleybus",
        "icon": "🚎",
        "tags": ["type/vehicle/land/road", "visual/color/multicolor"],
    },
    {
        "name": "Taxi",
        "icon": "🚕",
        "tags": [
            "type/vehicle/land/road",
            "visual/color/yellow",
            "visual/color/black",
            "visual/color/blue",
        ],
    },
    {
        "name": "Delivery Truck",
        "icon": "🚚",
        "tags": [
            "type/vehicle/land/road",
            "visual/color/yellow",
            "visual/color/red",
            "visual/color/black",
            "visual/color/blue",
        ],
    },
    {
        "name": "Tractor",
        "icon": "🚜",
        "tags": ["type/vehicle/land/road", "visual/color/multicolor"],
    },
    {
        "name": "Bicycle",
        "icon": "🚲",
        "tags": [
            "type/vehicle/land/road",
            "visual/color/red",
            "visual/color/brown",
            "visual/color/black",
        ],
    },
    {
        "name": "Motor Scooter",
        "icon": "🛵",
        "tags": [
            "type/vehicle/land/road",
            "visual/color/yellow",
            "visual/color/red",
            "visual/color/blue",
            "visual/color/black",
        ],
    },
    {
        "name": "Motorcycle",
        "icon": "🏍️",
        "tags": [
            "type/vehicle/land/road",
            "visual/color/brown",
            "visual/color/green",
            "visual/color/blue",
            "visual/color/black",
        ],
    },
    {
        "name": "Train",
        "icon": "🚂",
        "tags": ["type/vehicle/land/rail", "visual/color/multicolor"],
    },
    {
        "name": "Bullet Train",
        "icon": "🚄",
        "tags": ["type/vehicle/land/rail", "visual/color/multicolor"],
    },
    {
        "name": "Metro",
        "icon": "🚇",
        "tags": ["type/vehicle/land/rail", "visual/color/multicolor"],
    },
    {
        "name": "Tram",
        "icon": "🚊",
        "tags": ["type/vehicle/land/rail", "visual/color/multicolor"],
    },
    {
        "name": "Monorail",
        "icon": "🚝",
        "tags": [
            "type/vehicle/land/rail",
            "visual/color/brown",
            "visual/color/green",
            "visual/color/white",
            "visual/color/blue",
        ],
    },
    {
        "name": "Airplane",
        "icon": "✈️",
        "tags": ["type/vehicle/air/flight", "visual/color/brown", "visual/color/blue"],
    },
    {
        "name": "Small Airplane",
        "icon": "🛩️",
        "tags": [
            "type/vehicle/air/flight",
            "visual/color/brown",
            "visual/color/black",
            "visual/color/red",
            "visual/color/blue",
        ],
    },
    {
        "name": "Helicopter",
        "icon": "🚁",
        "tags": [
            "type/vehicle/air/flight",
            "visual/color/blue",
            "visual/color/yellow",
            "visual/color/brown",
        ],
    },
    {
        "name": "Parachute",
        "icon": "🪂",
        "tags": ["type/vehicle/air/flight", "visual/color/multicolor"],
    },
    {
        "name": "Hot Air Balloon",
        "icon": "🎈",
        "tags": [
            "type/vehicle/air/flight",
            "type/activity/celebration",
            "visual/color/red",
            "visual/color/yellow",
        ],
    },
    {
        "name": "Sailboat",
        "icon": "⛵",
        "tags": [
            "type/vehicle/water",
            "visual/color/yellow",
            "visual/color/white",
            "visual/color/brown",
            "visual/color/blue",
        ],
    },
    {
        "name": "Canoe",
        "icon": "🛶",
        "tags": [
            "type/vehicle/water",
            "visual/color/blue",
            "visual/color/yellow",
            "visual/color/red",
        ],
    },
    {
        "name": "Speedboat",
        "icon": "🚤",
        "tags": ["type/vehicle/water", "visual/color/multicolor"],
    },
    {
        "name": "Ferry",
        "icon": "⛴️",
        "tags": ["type/vehicle/water", "visual/color/multicolor"],
    },
    {
        "name": "Ship",
        "icon": "🚢",
        "tags": ["type/vehicle/water", "visual/color/multicolor"],
    },
    {
        "name": "Anchor",
        "icon": "⚓",
        "tags": ["type/vehicle/water", "visual/style/metallic", "visual/color/blue"],
    },
    {
        "name": "Rocket",
        "icon": "🚀",
        "tags": [
            "type/vehicle/space",
            "visual/color/yellow",
            "visual/color/red",
            "visual/color/blue",
        ],
    },
    {
        "name": "Flying Saucer",
        "icon": "🛸",
        "tags": [
            "type/vehicle/space",
            "visual/style/metallic",
            "visual/color/blue",
            "visual/color/yellow",
            "visual/color/white",
            "visual/color/brown",
        ],
    },
    {
        "name": "Satellite",
        "icon": "🛰️",
        "tags": ["type/vehicle/space", "visual/color/blue", "visual/color/yellow"],
    },
    {
        "name": "Soccer Ball",
        "icon": "⚽",
        "tags": [
            "type/activity/sport/ball",
            "visual/color/black",
            "visual/color/blue",
            "visual/color/white",
        ],
    },
    {
        "name": "Basketball",
        "icon": "🏀",
        "tags": [
            "type/activity/sport/ball",
            "visual/color/black",
            "visual/color/yellow",
        ],
    },
    {
        "name": "American Football",
        "icon": "🏈",
        "tags": ["type/activity/sport/ball", "visual/color/red", "visual/color/white"],
    },
    {
        "name": "Baseball",
        "icon": "⚾",
        "tags": [
            "type/activity/sport/ball",
            "visual/color/red",
            "visual/color/blue",
            "visual/color/white",
        ],
    },
    {
        "name": "Softball",
        "icon": "🥎",
        "tags": ["type/activity/sport/ball", "visual/color/yellow", "visual/color/red"],
    },
    {
        "name": "Volleyball",
        "icon": "🏐",
        "tags": ["type/activity/sport/ball", "visual/color/blue", "visual/color/white"],
    },
    {
        "name": "Rugby Football",
        "icon": "🏉",
        "tags": ["type/activity/sport/ball", "visual/color/blue", "visual/color/white"],
    },
    {
        "name": "Tennis",
        "icon": "🎾",
        "tags": ["type/activity/sport/ball", "visual/color/green"],
    },
    {
        "name": "Bowling",
        "icon": "🎳",
        "tags": [
            "type/activity/sport/ball",
            "visual/color/red",
            "visual/color/black",
            "visual/color/blue",
        ],
    },
    {
        "name": "Billiards",
        "icon": "🎱",
        "tags": [
            "type/activity/sport/ball",
            "visual/color/black",
            "visual/color/white",
        ],
    },
    {
        "name": "Ping Pong",
        "icon": "🏓",
        "tags": [
            "type/activity/sport/ball",
            "visual/color/yellow",
            "visual/color/orange",
            "visual/color/red",
            "visual/color/blue",
        ],
    },
    {
        "name": "Badminton",
        "icon": "🏸",
        "tags": [
            "type/activity/sport/ball",
            "visual/color/blue",
            "visual/color/black",
            "visual/color/white",
            "visual/color/red",
        ],
    },
    {
        "name": "Flying Disc",
        "icon": "🥏",
        "tags": [
            "type/activity/sport/ball",
            "visual/color/yellow",
            "visual/color/white",
        ],
    },
    {
        "name": "Golf",
        "icon": "⛳",
        "tags": [
            "type/activity/sport/ball",
            "visual/color/green",
            "visual/color/red",
            "visual/color/black",
            "visual/color/yellow",
        ],
    },
    {
        "name": "Swimming",
        "icon": "🏊",
        "tags": [
            "type/activity/sport/water",
            "visual/color/yellow",
            "visual/color/orange",
            "visual/color/blue",
        ],
    },
    {
        "name": "Surfing",
        "icon": "🏄",
        "tags": ["type/activity/sport/water", "visual/color/multicolor"],
    },
    {
        "name": "Diving",
        "icon": "🤽",
        "tags": [
            "type/activity/sport/water",
            "visual/color/yellow",
            "visual/color/orange",
            "visual/color/blue",
        ],
    },
    {
        "name": "Rowing",
        "icon": "🚣",
        "tags": [
            "type/activity/sport/water",
            "visual/color/yellow",
            "visual/color/blue",
            "visual/color/orange",
        ],
    },
    {
        "name": "Skier",
        "icon": "⛷️",
        "tags": ["type/activity/sport/winter", "visual/color/multicolor"],
    },
    {
        "name": "Snowboarder",
        "icon": "🏂",
        "tags": ["type/activity/sport/winter", "visual/color/multicolor"],
    },
    {
        "name": "Ice Skate",
        "icon": "⛸️",
        "tags": [
            "type/activity/sport/winter",
            "visual/style/metallic",
            "visual/color/blue",
            "visual/color/white",
            "visual/color/red",
        ],
    },
    {
        "name": "Runner",
        "icon": "🏃",
        "tags": [
            "type/activity/sport/athletics",
            "visual/color/yellow",
            "visual/color/orange",
            "visual/color/blue",
        ],
    },
    {
        "name": "Cyclist",
        "icon": "🚴",
        "tags": [
            "type/activity/sport/athletics",
            "type/vehicle/land/road",
            "visual/color/yellow",
            "visual/color/orange",
            "visual/color/blue",
            "visual/color/black",
        ],
    },
    {
        "name": "Person Climbing",
        "icon": "🧗",
        "tags": [
            "type/activity/sport/athletics",
            "type/nature/earth",
            "visual/color/multicolor",
        ],
    },
    {
        "name": "Weightlifter",
        "icon": "🏋️",
        "tags": ["type/activity/sport/athletics", "visual/color/multicolor"],
    },
    {
        "name": "Trophy",
        "icon": "🏆",
        "tags": [
            "type/activity/sport/athletics",
            "visual/style/metallic",
            "visual/color/yellow",
            "visual/color/orange",
        ],
    },
    {
        "name": "Medal",
        "icon": "🥇",
        "tags": [
            "type/activity/sport/athletics",
            "visual/style/metallic",
            "visual/color/yellow",
            "visual/color/blue",
            "visual/color/brown",
        ],
    },
    {
        "name": "Boxing Glove",
        "icon": "🥊",
        "tags": [
            "type/activity/sport/martial",
            "visual/color/blue",
            "visual/color/red",
            "visual/color/white",
        ],
    },
    {
        "name": "Martial Arts Uniform",
        "icon": "🥋",
        "tags": [
            "type/activity/sport/martial",
            "visual/color/brown",
            "visual/color/blue",
            "visual/color/black",
            "visual/color/white",
        ],
    },
    {
        "name": "Guitar",
        "icon": "🎸",
        "tags": ["type/activity/music/instrument", "visual/color/multicolor"],
    },
    {
        "name": "Piano",
        "icon": "🎹",
        "tags": [
            "type/activity/music/instrument",
            "visual/color/black",
            "visual/color/white",
        ],
    },
    {
        "name": "Trumpet",
        "icon": "🎺",
        "tags": [
            "type/activity/music/instrument",
            "visual/style/metallic",
            "visual/color/blue",
            "visual/color/yellow",
        ],
    },
    {
        "name": "Violin",
        "icon": "🎻",
        "tags": [
            "type/activity/music/instrument",
            "visual/color/blue",
            "visual/color/red",
            "visual/color/yellow",
            "visual/color/black",
        ],
    },
    {
        "name": "Saxophone",
        "icon": "🎷",
        "tags": [
            "type/activity/music/instrument",
            "visual/style/metallic",
            "visual/color/blue",
            "visual/color/yellow",
        ],
    },
    {
        "name": "Drum",
        "icon": "🥁",
        "tags": [
            "type/activity/music/instrument",
            "visual/color/yellow",
            "visual/color/red",
            "visual/color/white",
        ],
    },
    {
        "name": "Banjo",
        "icon": "🪕",
        "tags": ["type/activity/music/instrument", "visual/color/multicolor"],
    },
    {
        "name": "Accordion",
        "icon": "🪗",
        "tags": ["type/activity/music/instrument", "visual/color/multicolor"],
    },
    {
        "name": "Microphone",
        "icon": "🎤",
        "tags": [
            "type/activity/music/instrument",
            "visual/style/metallic",
            "visual/color/blue",
            "visual/color/black",
        ],
    },
    {
        "name": "Headphones",
        "icon": "🎧",
        "tags": [
            "type/activity/music/instrument",
            "visual/color/blue",
            "visual/color/brown",
            "visual/color/black",
        ],
    },
    {
        "name": "Musical Notes",
        "icon": "🎵",
        "tags": ["type/activity/music/instrument", "visual/color/blue"],
    },
    {
        "name": "Party Popper",
        "icon": "🎉",
        "tags": [
            "type/activity/celebration",
            "visual/style/sparkly",
            "visual/color/yellow",
            "visual/color/green",
            "visual/color/red",
            "visual/color/purple",
        ],
    },
    {
        "name": "Confetti Ball",
        "icon": "🎊",
        "tags": [
            "type/activity/celebration",
            "visual/style/sparkly",
            "visual/color/multicolor",
        ],
    },
    {
        "name": "Fireworks",
        "icon": "🎆",
        "tags": [
            "type/activity/celebration",
            "visual/style/sparkly",
            "visual/color/yellow",
            "visual/color/white",
            "visual/color/blue",
        ],
    },
    {
        "name": "Sparkler",
        "icon": "🎇",
        "tags": [
            "type/activity/celebration",
            "visual/style/sparkly",
            "visual/color/blue",
            "visual/color/yellow",
            "visual/color/white",
        ],
    },
    {
        "name": "Gift",
        "icon": "🎁",
        "tags": [
            "type/activity/celebration",
            "visual/color/red",
            "visual/color/yellow",
        ],
    },
    {
        "name": "Christmas Tree",
        "icon": "🎄",
        "tags": [
            "type/activity/celebration",
            "type/nature/plants",
            "visual/color/yellow",
            "visual/color/red",
            "visual/color/green",
        ],
    },
    {
        "name": "Jack-O-Lantern",
        "icon": "🎃",
        "tags": [
            "type/activity/celebration",
            "visual/color/red",
            "visual/color/yellow",
            "visual/color/green",
        ],
    },
    {
        "name": "Firework",
        "icon": "🧨",
        "tags": [
            "type/activity/celebration",
            "visual/style/sparkly",
            "visual/color/yellow",
            "visual/color/red",
            "visual/color/orange",
        ],
    },
    {
        "name": "Ticket",
        "icon": "🎫",
        "tags": ["type/activity/celebration", "visual/color/blue"],
    },
    {
        "name": "Artist Palette",
        "icon": "🎨",
        "tags": ["type/activity/art", "visual/color/multicolor"],
    },
    {
        "name": "Paintbrush",
        "icon": "🖌️",
        "tags": [
            "type/activity/art",
            "visual/color/red",
            "visual/color/blue",
            "visual/color/orange",
        ],
    },
    {
        "name": "Pencil",
        "icon": "✏️",
        "tags": ["type/activity/art", "type/object/office", "visual/color/multicolor"],
    },
    {
        "name": "Scissors",
        "icon": "✂️",
        "tags": [
            "type/activity/art",
            "type/object/tool/utility",
            "visual/style/metallic",
            "visual/color/blue",
            "visual/color/red",
        ],
    },
    {
        "name": "Thread",
        "icon": "🧵",
        "tags": ["type/activity/art", "visual/color/purple", "visual/color/orange"],
    },
    {
        "name": "Yarn",
        "icon": "🧶",
        "tags": [
            "type/activity/art",
            "visual/style/fluffy",
            "visual/color/blue",
            "visual/color/red",
        ],
    },
    {
        "name": "Video Game",
        "icon": "🎮",
        "tags": ["type/activity/game", "visual/color/multicolor"],
    },
    {
        "name": "Chess Pawn",
        "icon": "♟️",
        "tags": ["type/activity/game", "visual/color/brown", "visual/color/black"],
    },
    {
        "name": "Game Die",
        "icon": "🎲",
        "tags": ["type/activity/game", "visual/color/red", "visual/color/white"],
    },
    {
        "name": "Joker Card",
        "icon": "🃏",
        "tags": ["type/activity/game", "visual/color/multicolor"],
    },
    {
        "name": "Mahjong Red Dragon",
        "icon": "🀄",
        "tags": ["type/activity/game", "visual/color/white", "visual/color/red"],
    },
    {
        "name": "Puzzle Piece",
        "icon": "🧩",
        "tags": ["type/activity/game", "visual/color/green"],
    },
    {
        "name": "Teddy Bear",
        "icon": "🧸",
        "tags": [
            "type/activity/game",
            "visual/style/fluffy",
            "visual/color/orange",
            "visual/color/black",
            "visual/color/red",
        ],
    },
    {
        "name": "Yo-Yo",
        "icon": "🪀",
        "tags": ["type/activity/game", "visual/color/red", "visual/color/blue"],
    },
    {
        "name": "Kite",
        "icon": "🪁",
        "tags": ["type/activity/game", "visual/color/purple", "visual/color/blue"],
    },
    {
        "name": "Laptop",
        "icon": "💻",
        "tags": [
            "type/object/tech/device",
            "visual/style/metallic",
            "visual/color/blue",
        ],
    },
    {
        "name": "Mobile Phone",
        "icon": "📱",
        "tags": ["type/object/tech/device", "visual/color/black", "visual/color/blue"],
    },
    {
        "name": "Desktop Computer",
        "icon": "🖥️",
        "tags": ["type/object/tech/device", "visual/color/blue", "visual/color/white"],
    },
    {
        "name": "Keyboard",
        "icon": "⌨️",
        "tags": ["type/object/tech/device", "visual/color/blue", "visual/color/black"],
    },
    {
        "name": "Computer Mouse",
        "icon": "🖱️",
        "tags": ["type/object/tech/device", "visual/color/blue", "visual/color/black"],
    },
    {
        "name": "Camera",
        "icon": "📷",
        "tags": [
            "type/object/tech/device",
            "visual/color/brown",
            "visual/color/black",
            "visual/color/white",
            "visual/color/blue",
        ],
    },
    {
        "name": "Video Camera",
        "icon": "📹",
        "tags": ["type/object/tech/device", "visual/color/brown", "visual/color/black"],
    },
    {
        "name": "TV",
        "icon": "📺",
        "tags": [
            "type/object/tech/device",
            "visual/color/brown",
            "visual/color/black",
            "visual/color/blue",
        ],
    },
    {
        "name": "Radio",
        "icon": "📻",
        "tags": [
            "type/object/tech/device",
            "visual/color/blue",
            "visual/color/brown",
            "visual/color/black",
        ],
    },
    {
        "name": "Telephone",
        "icon": "☎️",
        "tags": ["type/object/tech/device", "visual/color/red"],
    },
    {
        "name": "Printer",
        "icon": "🖨️",
        "tags": [
            "type/object/tech/device",
            "visual/color/blue",
            "visual/color/black",
            "visual/color/white",
            "visual/color/brown",
        ],
    },
    {
        "name": "Battery",
        "icon": "🔋",
        "tags": ["type/object/tech/device", "visual/color/green", "visual/color/blue"],
    },
    {
        "name": "Floppy Disk",
        "icon": "💾",
        "tags": [
            "type/object/tech/device",
            "visual/color/black",
            "visual/color/white",
            "visual/color/blue",
        ],
    },
    {
        "name": "DVD",
        "icon": "📀",
        "tags": [
            "type/object/tech/device",
            "visual/style/metallic",
            "visual/color/yellow",
        ],
    },
    {
        "name": "Hammer",
        "icon": "🔨",
        "tags": [
            "type/object/tool/utility",
            "visual/style/metallic",
            "visual/color/brown",
            "visual/color/yellow",
        ],
    },
    {
        "name": "Wrench",
        "icon": "🔧",
        "tags": [
            "type/object/tool/utility",
            "visual/style/metallic",
            "visual/color/blue",
        ],
    },
    {
        "name": "Screwdriver",
        "icon": "🪛",
        "tags": [
            "type/object/tool/utility",
            "visual/style/metallic",
            "visual/color/brown",
            "visual/color/red",
            "visual/color/blue",
            "visual/color/white",
        ],
    },
    {
        "name": "Nut and Bolt",
        "icon": "🔩",
        "tags": [
            "type/object/tool/utility",
            "visual/style/metallic",
            "visual/color/brown",
            "visual/color/blue",
            "visual/color/white",
        ],
    },
    {
        "name": "Chains",
        "icon": "⛓️",
        "tags": [
            "type/object/tool/utility",
            "visual/style/metallic",
            "visual/color/blue",
            "visual/color/white",
        ],
    },
    {
        "name": "Axe",
        "icon": "🪓",
        "tags": [
            "type/object/tool/utility",
            "visual/style/metallic",
            "visual/color/brown",
            "visual/color/yellow",
            "visual/color/blue",
        ],
    },
    {
        "name": "Knife",
        "icon": "🔪",
        "tags": [
            "type/object/tool/utility",
            "visual/style/metallic",
            "visual/color/blue",
            "visual/color/black",
            "visual/color/white",
        ],
    },
    {
        "name": "Dagger",
        "icon": "🗡️",
        "tags": [
            "type/object/tool/utility",
            "visual/style/metallic",
            "visual/color/yellow",
            "visual/color/orange",
            "visual/color/blue",
            "visual/color/brown",
        ],
    },
    {
        "name": "Sword",
        "icon": "⚔️",
        "tags": [
            "type/object/tool/utility",
            "visual/style/metallic",
            "visual/color/yellow",
            "visual/color/orange",
            "visual/color/blue",
            "visual/color/brown",
        ],
    },
    {
        "name": "Shield",
        "icon": "🛡️",
        "tags": [
            "type/object/tool/utility",
            "visual/style/metallic",
            "visual/color/blue",
        ],
    },
    {
        "name": "Light Bulb",
        "icon": "💡",
        "tags": [
            "type/object/tool/utility",
            "visual/color/blue",
            "visual/color/yellow",
        ],
    },
    {
        "name": "Flashlight",
        "icon": "🔦",
        "tags": [
            "type/object/tool/utility",
            "visual/color/yellow",
            "visual/color/brown",
            "visual/color/blue",
        ],
    },
    {
        "name": "Candle",
        "icon": "🕯️",
        "tags": [
            "type/object/tool/utility",
            "visual/color/yellow",
            "visual/color/white",
            "visual/color/blue",
            "visual/color/brown",
        ],
    },
    {
        "name": "Telescope",
        "icon": "🔭",
        "tags": [
            "type/object/tool/utility",
            "type/nature/space",
            "visual/style/metallic",
            "visual/color/red",
            "visual/color/black",
            "visual/color/blue",
        ],
    },
    {
        "name": "Microscope",
        "icon": "🔬",
        "tags": [
            "type/object/tool/utility",
            "visual/style/metallic",
            "visual/color/brown",
            "visual/color/blue",
            "visual/color/white",
        ],
    },
    {
        "name": "Magnet",
        "icon": "🧲",
        "tags": [
            "type/object/tool/utility",
            "visual/color/yellow",
            "visual/color/red",
            "visual/color/blue",
        ],
    },
    {
        "name": "Lock",
        "icon": "🔒",
        "tags": [
            "type/object/tool/utility",
            "visual/color/blue",
            "visual/color/yellow",
        ],
    },
    {
        "name": "Key",
        "icon": "🔑",
        "tags": ["type/object/tool/utility", "visual/color/orange"],
    },
    {
        "name": "T-Shirt",
        "icon": "👕",
        "tags": ["type/object/clothing", "visual/color/green"],
    },
    {
        "name": "Jeans",
        "icon": "👖",
        "tags": ["type/object/clothing", "visual/color/blue"],
    },
    {
        "name": "Dress",
        "icon": "👗",
        "tags": ["type/object/clothing", "visual/color/blue"],
    },
    {
        "name": "Bikini",
        "icon": "👙",
        "tags": ["type/object/clothing", "visual/color/purple"],
    },
    {
        "name": "Top Hat",
        "icon": "🎩",
        "tags": [
            "type/object/clothing",
            "visual/color/purple",
            "visual/color/brown",
            "visual/color/black",
        ],
    },
    {
        "name": "Graduation Cap",
        "icon": "🎓",
        "tags": [
            "type/object/clothing",
            "visual/color/yellow",
            "visual/color/black",
            "visual/color/brown",
        ],
    },
    {
        "name": "Cowboy Hat",
        "icon": "🤠",
        "tags": ["type/object/clothing", "visual/color/brown", "visual/color/yellow"],
    },
    {
        "name": "Crown",
        "icon": "👑",
        "tags": [
            "type/object/clothing",
            "visual/style/sparkly",
            "visual/color/yellow",
            "visual/color/red",
            "visual/color/green",
            "visual/color/purple",
        ],
    },
    {
        "name": "Sunglasses",
        "icon": "🕶️",
        "tags": ["type/object/clothing", "visual/color/black"],
    },
    {
        "name": "Glasses",
        "icon": "👓",
        "tags": ["type/object/clothing", "visual/color/black", "visual/color/blue"],
    },
    {
        "name": "Purse",
        "icon": "👛",
        "tags": [
            "type/object/clothing",
            "visual/color/white",
            "visual/color/brown",
            "visual/color/red",
        ],
    },
    {
        "name": "Handbag",
        "icon": "👜",
        "tags": ["type/object/clothing", "visual/color/yellow", "visual/color/purple"],
    },
    {
        "name": "Backpack",
        "icon": "🎒",
        "tags": ["type/object/clothing", "visual/color/red", "visual/color/orange"],
    },
    {
        "name": "Shoe",
        "icon": "👟",
        "tags": ["type/object/clothing", "visual/color/red", "visual/color/blue"],
    },
    {
        "name": "High-Heeled Shoe",
        "icon": "👠",
        "tags": ["type/object/clothing", "visual/color/black", "visual/color/red"],
    },
    {
        "name": "Boot",
        "icon": "👢",
        "tags": ["type/object/clothing", "visual/color/red", "visual/color/orange"],
    },
    {
        "name": "Ring",
        "icon": "💍",
        "tags": [
            "type/object/clothing",
            "visual/style/sparkly",
            "visual/style/metallic",
            "visual/color/blue",
        ],
    },
    {
        "name": "House",
        "icon": "🏠",
        "tags": [
            "type/place/building",
            "type/object/household",
            "visual/color/multicolor",
        ],
    },
    {
        "name": "Couch",
        "icon": "🛋️",
        "tags": [
            "type/object/household",
            "visual/color/green",
            "visual/color/yellow",
            "visual/color/blue",
        ],
    },
    {
        "name": "Bed",
        "icon": "🛏️",
        "tags": [
            "type/object/household",
            "visual/color/blue",
            "visual/color/orange",
            "visual/color/green",
        ],
    },
    {
        "name": "Bath",
        "icon": "🛁",
        "tags": ["type/object/household", "visual/color/blue"],
    },
    {
        "name": "Toilet",
        "icon": "🚽",
        "tags": ["type/object/household", "visual/color/blue", "visual/color/white"],
    },
    {
        "name": "Shower",
        "icon": "🚿",
        "tags": ["type/object/household", "visual/color/blue", "visual/color/brown"],
    },
    {
        "name": "Mirror",
        "icon": "🪞",
        "tags": [
            "type/object/household",
            "visual/style/metallic",
            "visual/color/multicolor",
        ],
    },
    {
        "name": "Door",
        "icon": "🚪",
        "tags": [
            "type/object/household",
            "visual/color/yellow",
            "visual/color/orange",
            "visual/color/brown",
        ],
    },
    {
        "name": "Window",
        "icon": "🪟",
        "tags": ["type/object/household", "visual/color/orange", "visual/color/blue"],
    },
    {
        "name": "Chair",
        "icon": "🪑",
        "tags": ["type/object/household", "visual/color/orange"],
    },
    {
        "name": "Cooking Pot",
        "icon": "🫕",
        "tags": ["type/object/household", "type/food/meal", "visual/color/multicolor"],
    },
    {
        "name": "Broom",
        "icon": "🧹",
        "tags": [
            "type/object/household",
            "visual/color/yellow",
            "visual/color/brown",
            "visual/color/blue",
            "visual/color/orange",
        ],
    },
    {
        "name": "Bucket",
        "icon": "🪣",
        "tags": ["type/object/household", "visual/color/blue", "visual/color/black"],
    },
    {
        "name": "Soap",
        "icon": "🧼",
        "tags": [
            "type/object/household",
            "visual/color/red",
            "visual/color/white",
            "visual/color/blue",
        ],
    },
    {
        "name": "Toothbrush",
        "icon": "🪥",
        "tags": ["type/object/household", "visual/color/blue"],
    },
    {
        "name": "Book",
        "icon": "📚",
        "tags": [
            "type/object/office",
            "visual/color/purple",
            "visual/color/yellow",
            "visual/color/blue",
        ],
    },
    {
        "name": "Notebook",
        "icon": "📓",
        "tags": [
            "type/object/office",
            "visual/color/brown",
            "visual/color/black",
            "visual/color/white",
            "visual/color/blue",
        ],
    },
    {
        "name": "Memo",
        "icon": "📝",
        "tags": ["type/object/office", "visual/color/multicolor"],
    },
    {
        "name": "Calendar",
        "icon": "📅",
        "tags": [
            "type/object/office",
            "type/symbol/time/clock",
            "visual/color/red",
            "visual/color/brown",
            "visual/color/white",
        ],
    },
    {
        "name": "Clipboard",
        "icon": "📋",
        "tags": [
            "type/object/office",
            "visual/color/blue",
            "visual/color/black",
            "visual/color/orange",
        ],
    },
    {
        "name": "Chart Increasing",
        "icon": "📈",
        "tags": [
            "type/object/office",
            "visual/color/red",
            "visual/color/white",
            "visual/color/blue",
        ],
    },
    {
        "name": "Chart Decreasing",
        "icon": "📉",
        "tags": ["type/object/office", "visual/color/blue", "visual/color/white"],
    },
    {
        "name": "Bar Chart",
        "icon": "📊",
        "tags": [
            "type/object/office",
            "visual/color/red",
            "visual/color/blue",
            "visual/color/green",
            "visual/color/white",
        ],
    },
    {
        "name": "Envelope",
        "icon": "✉️",
        "tags": ["type/object/office", "visual/color/blue", "visual/color/white"],
    },
    {
        "name": "Inbox Tray",
        "icon": "📥",
        "tags": [
            "type/object/office",
            "visual/color/red",
            "visual/color/orange",
            "visual/color/green",
        ],
    },
    {
        "name": "Paperclip",
        "icon": "📎",
        "tags": ["type/object/office", "visual/style/metallic", "visual/color/blue"],
    },
    {
        "name": "Pushpin",
        "icon": "📌",
        "tags": ["type/object/office", "visual/color/blue", "visual/color/red"],
    },
    {
        "name": "Magnifying Glass",
        "icon": "🔍",
        "tags": [
            "type/object/office",
            "visual/style/metallic",
            "visual/color/blue",
            "visual/color/brown",
        ],
    },
    {
        "name": "Syringe",
        "icon": "💉",
        "tags": [
            "type/object/medical",
            "visual/color/brown",
            "visual/color/blue",
            "visual/color/black",
        ],
    },
    {
        "name": "Pill",
        "icon": "💊",
        "tags": ["type/object/medical", "visual/color/red", "visual/color/yellow"],
    },
    {
        "name": "Adhesive Bandage",
        "icon": "🩹",
        "tags": ["type/object/medical", "visual/color/orange", "visual/color/white"],
    },
    {
        "name": "Stethoscope",
        "icon": "🩺",
        "tags": [
            "type/object/medical",
            "visual/style/metallic",
            "visual/color/blue",
            "visual/color/black",
        ],
    },
    {
        "name": "X-Ray",
        "icon": "🩻",
        "tags": ["type/object/medical", "visual/color/blue"],
    },
    {
        "name": "Gold Coin",
        "icon": "🪙",
        "tags": ["type/object/money", "visual/style/metallic", "visual/color/yellow"],
    },
    {
        "name": "Banknote",
        "icon": "💵",
        "tags": ["type/object/money", "visual/color/green", "visual/color/yellow"],
    },
    {
        "name": "Money Bag",
        "icon": "💰",
        "tags": [
            "type/object/money",
            "visual/color/orange",
            "visual/color/yellow",
            "visual/color/brown",
        ],
    },
    {
        "name": "Credit Card",
        "icon": "💳",
        "tags": [
            "type/object/money",
            "visual/color/yellow",
            "visual/color/blue",
            "visual/color/white",
            "visual/color/black",
        ],
    },
    {
        "name": "Chart with Upward Trend",
        "icon": "💹",
        "tags": ["type/object/money", "type/object/office", "visual/color/green"],
    },
    {
        "name": "ATM Sign",
        "icon": "🏧",
        "tags": ["type/object/money", "type/place/building", "visual/color/blue"],
    },
    {
        "name": "Red Heart",
        "icon": "❤️",
        "tags": ["type/symbol/heart/love", "visual/color/red"],
    },
    {
        "name": "Orange Heart",
        "icon": "🧡",
        "tags": ["type/symbol/heart/love", "visual/color/yellow"],
    },
    {
        "name": "Yellow Heart",
        "icon": "💛",
        "tags": ["type/symbol/heart/love", "visual/color/yellow"],
    },
    {
        "name": "Green Heart",
        "icon": "💚",
        "tags": ["type/symbol/heart/love", "visual/color/green"],
    },
    {
        "name": "Blue Heart",
        "icon": "💙",
        "tags": ["type/symbol/heart/love", "visual/color/blue"],
    },
    {
        "name": "Purple Heart",
        "icon": "💜",
        "tags": ["type/symbol/heart/love", "visual/color/purple"],
    },
    {
        "name": "Brown Heart",
        "icon": "🤎",
        "tags": ["type/symbol/heart/love", "visual/color/orange"],
    },
    {
        "name": "Black Heart",
        "icon": "🖤",
        "tags": ["type/symbol/heart/love", "visual/color/black"],
    },
    {
        "name": "White Heart",
        "icon": "🤍",
        "tags": ["type/symbol/heart/love", "visual/color/white"],
    },
    {
        "name": "Sparkling Heart",
        "icon": "💖",
        "tags": [
            "type/symbol/heart/love",
            "visual/style/sparkly",
            "visual/color/yellow",
            "visual/color/red",
        ],
    },
    {
        "name": "Heart with Arrow",
        "icon": "💘",
        "tags": ["type/symbol/heart/love", "visual/color/yellow", "visual/color/red"],
    },
    {
        "name": "Revolving Hearts",
        "icon": "💞",
        "tags": ["type/symbol/heart/love", "visual/color/red"],
    },
    {
        "name": "Clock",
        "icon": "🕒",
        "tags": [
            "type/symbol/time/clock",
            "visual/style/metallic",
            "visual/color/blue",
            "visual/color/brown",
            "visual/color/white",
        ],
    },
    {
        "name": "Hourglass",
        "icon": "⏳",
        "tags": ["type/symbol/time/clock", "visual/color/yellow", "visual/color/blue"],
    },
    {
        "name": "Stopwatch",
        "icon": "⏱️",
        "tags": [
            "type/symbol/time/clock",
            "visual/style/metallic",
            "visual/color/multicolor",
        ],
    },
    {
        "name": "Alarm Clock",
        "icon": "⏰",
        "tags": [
            "type/symbol/time/clock",
            "visual/color/yellow",
            "visual/color/brown",
            "visual/color/red",
            "visual/color/white",
        ],
    },
    {
        "name": "Warning",
        "icon": "⚠️",
        "tags": ["type/symbol/warning", "visual/color/yellow", "visual/color/black"],
    },
    {
        "name": "Prohibited",
        "icon": "🚫",
        "tags": ["type/symbol/warning", "visual/color/red"],
    },
    {
        "name": "Radioactive",
        "icon": "☢️",
        "tags": ["type/symbol/warning", "visual/color/yellow"],
    },
    {
        "name": "Biohazard",
        "icon": "☣️",
        "tags": ["type/symbol/warning", "visual/color/yellow"],
    },
    {
        "name": "SOS Button",
        "icon": "🆘",
        "tags": ["type/symbol/warning", "visual/color/red"],
    },
    {
        "name": "Star of David",
        "icon": "✡️",
        "tags": ["type/symbol/religious", "visual/color/purple"],
    },
    {
        "name": "Latin Cross",
        "icon": "✝️",
        "tags": ["type/symbol/religious", "visual/color/purple"],
    },
    {
        "name": "Peace Symbol",
        "icon": "☮️",
        "tags": ["type/symbol/religious", "visual/color/purple"],
    },
    {
        "name": "Yin Yang",
        "icon": "☯️",
        "tags": ["type/symbol/religious", "visual/color/purple"],
    },
    {
        "name": "Om",
        "icon": "🕉️",
        "tags": ["type/symbol/religious", "visual/color/purple"],
    },
    {
        "name": "Hospital",
        "icon": "🏥",
        "tags": [
            "type/place/building",
            "type/object/medical",
            "visual/color/red",
            "visual/color/blue",
            "visual/color/white",
        ],
    },
    {
        "name": "School",
        "icon": "🏫",
        "tags": [
            "type/place/building",
            "type/object/office",
            "visual/color/multicolor",
        ],
    },
    {
        "name": "Office Building",
        "icon": "🏢",
        "tags": [
            "type/place/building",
            "visual/color/brown",
            "visual/color/yellow",
            "visual/color/blue",
        ],
    },
    {
        "name": "Bank",
        "icon": "🏦",
        "tags": [
            "type/place/building",
            "type/object/money",
            "visual/color/brown",
            "visual/color/blue",
            "visual/color/black",
            "visual/color/white",
        ],
    },
    {
        "name": "Hotel",
        "icon": "🏨",
        "tags": [
            "type/place/building",
            "visual/color/yellow",
            "visual/color/blue",
            "visual/color/orange",
        ],
    },
    {
        "name": "Convenience Store",
        "icon": "🏪",
        "tags": [
            "type/place/building",
            "visual/color/brown",
            "visual/color/red",
            "visual/color/blue",
            "visual/color/black",
        ],
    },
    {
        "name": "Castle",
        "icon": "🏯",
        "tags": [
            "type/place/building",
            "visual/color/brown",
            "visual/color/blue",
            "visual/color/orange",
            "visual/color/white",
        ],
    },
    {
        "name": "Stadium",
        "icon": "🏟️",
        "tags": [
            "type/place/building",
            "type/activity/sport/ball",
            "visual/color/multicolor",
        ],
    },
    {
        "name": "Church",
        "icon": "⛪",
        "tags": [
            "type/place/building",
            "type/symbol/religious",
            "visual/color/red",
            "visual/color/brown",
            "visual/color/yellow",
        ],
    },
    {
        "name": "Mosque",
        "icon": "🕌",
        "tags": [
            "type/place/building",
            "type/symbol/religious",
            "visual/color/yellow",
            "visual/color/red",
        ],
    },
    {
        "name": "Diamond",
        "icon": "💎",
        "tags": ["visual/style/sparkly", "type/object/money", "visual/color/blue"],
    },
    {
        "name": "Crystal Ball",
        "icon": "🔮",
        "tags": [
            "visual/style/sparkly",
            "visual/color/purple",
            "visual/color/brown",
            "visual/color/orange",
        ],
    },
    {
        "name": "Explosion",
        "icon": "💥",
        "tags": [
            "visual/style/sparkly",
            "visual/color/red",
            "visual/color/white",
            "visual/color/yellow",
        ],
    },
    {
        "name": "Dizzy Symbol",
        "icon": "💫",
        "tags": ["visual/style/sparkly", "visual/color/yellow"],
    },
    {
        "name": "Sparkles",
        "icon": "✨",
        "tags": ["visual/style/sparkly", "visual/color/yellow"],
    },
    {
        "name": "Rainbow Flag",
        "icon": "🏳️\u200d🌈",
        "tags": ["type/symbol/religious", "visual/color/multicolor"],
    },
    {
        "name": "Map",
        "icon": "🗺️",
        "tags": [
            "type/nature/earth",
            "type/object/office",
            "visual/color/blue",
            "visual/color/green",
            "visual/color/white",
        ],
    },
    {
        "name": "Compass",
        "icon": "🧭",
        "tags": [
            "type/nature/earth",
            "type/object/tool/utility",
            "visual/color/multicolor",
        ],
    },
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
    print(
        f"\nDone! {len(TAXONOMY_NODES)} taxonomy nodes and {len(DOCUMENTS)} documents seeded."
    )
    await es.close()


if __name__ == "__main__":
    asyncio.run(main())
