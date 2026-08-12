# Prompt Engineering Notes

## System/User/Assistant Roles
- System: AI ka overall behavior set karta hai
- User: Insaan ka message
- Assistant: AI ka response

## Weak vs Strong Prompt Example
Weak: "Mujhe kuch likh do"
Strong: "Ek 100 word ka paragraph likho AI ke fayde ke baare mein, students ke liye, simple language mein"

## Few-Shot Example
Example: Translation
English: "Good night" → Urdu: "شب بخیر"
English: "Please" → Urdu: "براہِ کرم"
English: "Welcome" → Urdu: "خوش آمدید"

## Chain-of-Thought Example
Example: Logic & Math Problem

Question: Ek class mein 24 students hain. Un mein se 1/3 students football khelte hain aur baqi students cricket khelte hain. Cricket khelne wale students mein se 4 students ghar chale gaye. Ab class mein kitne cricket players reh gaye?

Reasoning:

Total students = 24
Football players = 24 ÷ 3 = 8
Cricket players = 24 − 8 = 16
4 cricket players ghar chale gaye → 16 − 4 = 12

Final Answer: 12 cricket players.