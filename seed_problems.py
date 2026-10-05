import os
from app import create_app
from extensions import db
from models import CodingProblem, CodingTestCase, CodingTag

app = create_app()

def seed_problems():
    with app.app_context():
        # Check if they exist to avoid duplicates
        if CodingProblem.query.first():
            print("Problems already exist. Skipping seed.")
            return
            
        print("Creating sample problems...")

        # Tags
        tag_arrays = CodingTag(name="Arrays")
        tag_math = CodingTag(name="Math")
        db.session.add_all([tag_arrays, tag_math])
        db.session.commit()

        # Problem 1: Two Sum
        p1 = CodingProblem(
            title="Two Sum",
            slug="two-sum",
            difficulty="Easy",
            is_published=True,
            description="""
Given an array of integers `nums` and an integer `target`, return indices of the two numbers such that they add up to `target`.

You may assume that each input would have exactly one solution, and you may not use the same element twice.

**Example 1:**
```
Input: nums = [2,7,11,15], target = 9
Output: [0,1]
Explanation: Because nums[0] + nums[1] == 9, we return [0, 1].
```
            """
        )
        p1.tags.append(tag_arrays)
        db.session.add(p1)
        db.session.commit()

        tc1 = CodingTestCase(problem_id=p1.id, input_data="[2,7,11,15]\n9", expected_output="[0,1]", is_hidden=False)
        tc2 = CodingTestCase(problem_id=p1.id, input_data="[3,2,4]\n6", expected_output="[1,2]", is_hidden=False)
        db.session.add_all([tc1, tc2])
        
        # Problem 2: Palindrome Number
        p2 = CodingProblem(
            title="Palindrome Number",
            slug="palindrome-number",
            difficulty="Easy",
            is_published=True,
            description="""
Given an integer `x`, return `true` if `x` is a palindrome, and `false` otherwise.

**Example 1:**
```
Input: x = 121
Output: true
Explanation: 121 reads as 121 from left to right and from right to left.
```

**Example 2:**
```
Input: x = -121
Output: false
Explanation: From left to right, it reads -121. From right to left, it becomes 121-. Therefore it is not a palindrome.
```
            """
        )
        p2.tags.append(tag_math)
        db.session.add(p2)
        db.session.commit()

        tc3 = CodingTestCase(problem_id=p2.id, input_data="121", expected_output="true", is_hidden=False)
        tc4 = CodingTestCase(problem_id=p2.id, input_data="-121", expected_output="false", is_hidden=False)
        db.session.add_all([tc3, tc4])

        db.session.commit()
        print("Successfully created sample problems!")

if __name__ == "__main__":
    seed_problems()
