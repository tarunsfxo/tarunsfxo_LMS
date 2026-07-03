from extensions import db
from models import User, Category, Bite, QuizQuestion
from slugify_helper import slugify


CATEGORIES = [
    {"name": "Python", "icon": "python", "color": "#3776ab"},
    {"name": "JavaScript", "icon": "javascript", "color": "#f7df1e"},
    {"name": "Web Dev", "icon": "globe", "color": "#06b6d4"},
    {"name": "Databases", "icon": "database", "color": "#10b981"},
    {"name": "Git & Tools", "icon": "git", "color": "#f97316"},
    {"name": "Algorithms", "icon": "cpu", "color": "#8b5cf6"},
]

BITES = [
    {
        "category": "Python",
        "title": "Understanding List Comprehensions",
        "summary": "Write cleaner, faster loops using Python's list comprehension syntax.",
        "difficulty": "beginner",
        "duration": 4,
        "content": "List comprehensions let you build lists in a single readable line. Instead of writing a for-loop "
                    "that appends to a list, you can express the same intent as [expression for item in iterable if condition]. "
                    "This is not just shorter — it's typically faster too, because the looping happens in optimized C code "
                    "rather than the Python interpreter loop. Use them for simple transformations and filters; for complex "
                    "logic, a regular loop is often more readable.",
        "code": "squares = [x**2 for x in range(10) if x % 2 == 0]\nprint(squares)  # [0, 4, 16, 36, 64]",
        "questions": [
            {
                "q": "What does [x*2 for x in range(3)] produce?",
                "a": "[0, 2, 4]", "b": "[1, 2, 3]", "c": "[0, 1, 2]", "d": "[2, 4, 6]",
                "correct": "A", "exp": "range(3) gives 0,1,2; doubling each gives 0,2,4.",
            }
        ],
    },
    {
        "category": "Python",
        "title": "Decorators in 5 Minutes",
        "summary": "Learn how Python decorators wrap functions to extend behavior.",
        "difficulty": "intermediate",
        "duration": 6,
        "content": "A decorator is a function that takes another function and extends its behavior without "
                    "explicitly modifying it. They are widely used for logging, timing, caching, and access control. "
                    "The @decorator syntax is just sugar for func = decorator(func).",
        "code": "def logger(func):\n    def wrapper(*args, **kwargs):\n        print(f'Calling {func.__name__}')\n        return func(*args, **kwargs)\n    return wrapper\n\n@logger\ndef greet(name):\n    return f'Hello {name}'",
        "questions": [
            {
                "q": "What does @decorator above a function do?",
                "a": "Deletes the function", "b": "Wraps the function with new behavior",
                "c": "Converts it to a class", "d": "Runs it immediately",
                "correct": "B", "exp": "Decorators wrap the original function to add behavior.",
            }
        ],
    },
    {
        "category": "JavaScript",
        "title": "Closures Explained Simply",
        "summary": "Understand how JavaScript functions remember their lexical scope.",
        "difficulty": "intermediate",
        "duration": 5,
        "content": "A closure is formed when a function retains access to variables from its outer scope, even after "
                    "that outer function has finished executing. This is the foundation of patterns like private state, "
                    "memoization, and event handler factories in JavaScript.",
        "code": "function counter() {\n  let count = 0;\n  return function() {\n    count++;\n    return count;\n  };\n}\nconst increment = counter();\nconsole.log(increment()); // 1\nconsole.log(increment()); // 2",
        "questions": [
            {
                "q": "What will the second call to increment() return?",
                "a": "1", "b": "0", "c": "2", "d": "undefined",
                "correct": "C", "exp": "The closure retains 'count' between calls, incrementing it each time.",
            }
        ],
    },
    {
        "category": "JavaScript",
        "title": "Promises vs Async/Await",
        "summary": "Compare the two main ways JavaScript handles asynchronous code.",
        "difficulty": "beginner",
        "duration": 5,
        "content": "Promises represent a value that may be available now, later, or never. Async/await is syntactic "
                    "sugar built on top of promises that lets asynchronous code read like synchronous code, improving "
                    "readability especially when chaining multiple async operations.",
        "code": "async function getData() {\n  const res = await fetch('/api/data');\n  const json = await res.json();\n  return json;\n}",
        "questions": [
            {
                "q": "What keyword pauses execution until a Promise resolves?",
                "a": "yield", "b": "await", "c": "pause", "d": "defer",
                "correct": "B", "exp": "'await' pauses execution of an async function until the Promise settles.",
            }
        ],
    },
    {
        "category": "Web Dev",
        "title": "CSS Flexbox Fundamentals",
        "summary": "Master one-dimensional layouts with Flexbox properties.",
        "difficulty": "beginner",
        "duration": 5,
        "content": "Flexbox is a one-dimensional layout model designed for distributing space along a single axis — "
                    "either a row or a column. Setting display: flex on a container unlocks properties like "
                    "justify-content, align-items, and flex-grow on its children.",
        "code": ".container {\n  display: flex;\n  justify-content: space-between;\n  align-items: center;\n}",
        "questions": [
            {
                "q": "Which property aligns flex items along the main axis?",
                "a": "align-items", "b": "justify-content", "c": "flex-direction", "d": "flex-wrap",
                "correct": "B", "exp": "justify-content controls alignment along the main axis.",
            }
        ],
    },
    {
        "category": "Web Dev",
        "title": "Responsive Design with Media Queries",
        "summary": "Build layouts that adapt across screen sizes.",
        "difficulty": "beginner",
        "duration": 4,
        "content": "Media queries let CSS rules apply conditionally based on device characteristics like viewport "
                    "width. Mobile-first design starts with base styles for small screens, then adds min-width "
                    "queries to enhance the layout for larger screens.",
        "code": "@media (min-width: 768px) {\n  .grid { grid-template-columns: repeat(2, 1fr); }\n}",
        "questions": [
            {
                "q": "What does a mobile-first approach mean?",
                "a": "Design for desktop first", "b": "Design base styles for mobile, enhance for larger screens",
                "c": "Only support mobile devices", "d": "Use fixed pixel widths",
                "correct": "B", "exp": "Mobile-first means writing base CSS for small screens then layering enhancements.",
            }
        ],
    },
    {
        "category": "Databases",
        "title": "SQL Joins Demystified",
        "summary": "Understand INNER, LEFT, RIGHT, and FULL joins with simple examples.",
        "difficulty": "intermediate",
        "duration": 6,
        "content": "Joins combine rows from two or more tables based on a related column. INNER JOIN returns only "
                    "matching rows. LEFT JOIN returns all rows from the left table plus matches from the right, filling "
                    "unmatched columns with NULL. Understanding joins is essential for relational data modeling.",
        "code": "SELECT users.username, orders.total\nFROM users\nLEFT JOIN orders ON orders.user_id = users.id;",
        "questions": [
            {
                "q": "Which join returns all rows from the left table even without a match?",
                "a": "INNER JOIN", "b": "LEFT JOIN", "c": "CROSS JOIN", "d": "SELF JOIN",
                "correct": "B", "exp": "LEFT JOIN keeps all left-table rows, filling unmatched right columns with NULL.",
            }
        ],
    },
    {
        "category": "Databases",
        "title": "Indexing for Faster Queries",
        "summary": "Learn why and when to add indexes to database columns.",
        "difficulty": "advanced",
        "duration": 6,
        "content": "An index is a data structure (commonly a B-tree) that speeds up row lookups at the cost of extra "
                    "storage and slower writes. Index columns that are frequently used in WHERE clauses, JOIN conditions, "
                    "or ORDER BY, but avoid over-indexing tables with heavy write loads.",
        "code": "CREATE INDEX idx_users_email ON users(email);",
        "questions": [
            {
                "q": "What is a tradeoff of adding more indexes?",
                "a": "Faster writes", "b": "Slower writes and more storage",
                "c": "No effect on performance", "d": "Smaller database size",
                "correct": "B", "exp": "Indexes speed reads but slow down writes and use extra storage.",
            }
        ],
    },
    {
        "category": "Git & Tools",
        "title": "Git Branching Strategies",
        "summary": "Compare feature branching, Git Flow, and trunk-based development.",
        "difficulty": "intermediate",
        "duration": 5,
        "content": "Branching strategy defines how teams organize parallel work. Trunk-based development keeps a single "
                    "main branch with short-lived feature branches merged frequently. Git Flow uses longer-lived develop, "
                    "release, and feature branches, suited for scheduled releases.",
        "code": "git checkout -b feature/login-page\ngit push -u origin feature/login-page",
        "questions": [
            {
                "q": "Which strategy favors frequent merges into a single main branch?",
                "a": "Git Flow", "b": "Trunk-based development", "c": "Fork and pull", "d": "Release branching",
                "correct": "B", "exp": "Trunk-based development emphasizes short-lived branches merged often into main.",
            }
        ],
    },
    {
        "category": "Algorithms",
        "title": "Big O Notation Basics",
        "summary": "Learn to reason about algorithm efficiency using Big O notation.",
        "difficulty": "beginner",
        "duration": 5,
        "content": "Big O notation describes how an algorithm's runtime or memory usage grows relative to input size. "
                    "O(1) is constant time, O(n) is linear, O(n^2) is quadratic. It helps compare algorithms independent "
                    "of hardware or implementation details.",
        "code": "# O(n) - linear search\ndef find(arr, target):\n    for item in arr:\n        if item == target:\n            return True\n    return False",
        "questions": [
            {
                "q": "What does O(n) mean?",
                "a": "Constant time", "b": "Runtime grows linearly with input size",
                "c": "Runtime is always fast", "d": "Quadratic growth",
                "correct": "B", "exp": "O(n) means the runtime scales linearly with the size of the input.",
            }
        ],
    },
    {
        "category": "Algorithms",
        "title": "Binary Search Step by Step",
        "summary": "Efficiently search sorted arrays in logarithmic time.",
        "difficulty": "intermediate",
        "duration": 6,
        "content": "Binary search repeatedly divides a sorted array in half, comparing the target to the middle element "
                    "and discarding the half that cannot contain it. This achieves O(log n) time complexity, dramatically "
                    "faster than linear search for large datasets.",
        "code": "def binary_search(arr, target):\n    lo, hi = 0, len(arr) - 1\n    while lo <= hi:\n        mid = (lo + hi) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            lo = mid + 1\n        else:\n            hi = mid - 1\n    return -1",
        "questions": [
            {
                "q": "What is required for binary search to work correctly?",
                "a": "The array must be sorted", "b": "The array must be reversed",
                "c": "The array must contain duplicates", "d": "No requirement",
                "correct": "A", "exp": "Binary search relies on the array being sorted to discard halves safely.",
            }
        ],
    },
]


def seed_sample_data():
    cat_map = {}
    for c in CATEGORIES:
        cat = Category(name=c["name"], slug=slugify(c["name"]), icon=c["icon"], color=c["color"])
        db.session.add(cat)
        db.session.flush()
        cat_map[c["name"]] = cat

    for idx, b in enumerate(BITES):
        bite = Bite(
            title=b["title"],
            slug=slugify(b["title"]),
            summary=b["summary"],
            content=b["content"],
            code_snippet=b.get("code", ""),
            difficulty=b["difficulty"],
            duration_minutes=b["duration"],
            category_id=cat_map[b["category"]].id,
            is_premium=(idx % 5 == 4),
            order_index=idx,
        )
        db.session.add(bite)
        db.session.flush()

        for q in b["questions"]:
            question = QuizQuestion(
                bite_id=bite.id,
                question=q["q"],
                option_a=q["a"],
                option_b=q["b"],
                option_c=q["c"],
                option_d=q["d"],
                correct_option=q["correct"],
                explanation=q["exp"],
            )
            db.session.add(question)

    admin = User(username="admin", email="admin@tarunsfxo.com", is_admin=True, plan="team")
    admin.set_password("Admin@123")
    db.session.add(admin)

    demo = User(username="demo", email="demo@tarunsfxo.com", plan="free")
    demo.set_password("Demo@123")
    db.session.add(demo)

    db.session.commit()


def run_seed():
    db.drop_all()
    db.create_all()
    seed_sample_data()


if __name__ == "__main__":
    from app import create_app

    app = create_app()
    with app.app_context():
        run_seed()
        print("Seed complete. Admin login: admin@tarunsfxo.com / Admin@123")
