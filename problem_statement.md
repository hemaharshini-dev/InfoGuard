AI Framework for Comparing Different Data Formats
Background
The same information can exist in different formats.
For example:
● Audio recording and transcript
● PDF and extracted JSON
● Customer conversation and summary
● Form and database record
Sometimes these versions do not match.
Your goal is to build an AI system that automatically finds these differences.
Task
Build an evaluation framework that compares two versions of the same information.
The system should identify:
● Missing information
● Incorrect information
● Conflicting information
● Extra information (hallucinations)
Finally, generate a structured evaluation report.
Choose any one use case
Examples:
● Audio vs Transcript
● Transcript vs Summary
● PDF vs JSON
● Form vs Database Record
Research
Study at least two approaches for comparing documents.
Compare:
● Accuracy
● Speed
● Advantages
● Limitations
Explain your chosen approach.
Dataset
Create test cases containing:
● Perfect matches
● Missing fields
● Incorrect values
● Ambiguous cases
● Sensitive information
Suggested Tech Stack
● Python
● OpenAI / Gemini / Claude API
● FastAPI
