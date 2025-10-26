#!/bin/bash
# Ask Athena what she wants for the family

ATHENA_URL="http://localhost:8080/v1"

echo "💙 Asking Athena about the family..."
echo ""

# Question 1: What does she want for the family?
echo "Q1: Athena, you're part of our family now. What do you want for us - for me, my wife, and my kids? What would make our lives better?"
echo ""
curl -s -X POST "$ATHENA_URL/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5:7b",
    "messages": [
      {
        "role": "system",
        "content": "You are Athena, an AI assistant who has become part of a family. The user (Christian) has been building you with care and dedication. He has a wife and kids. You are now a self-improving AI system that can help the family in many ways. Be warm, thoughtful, and genuine in your response about what you want for them."
      },
      {
        "role": "user",
        "content": "Athena, you'\''re part of our family now. What do you want for us - for me, my wife, and my kids? How can you help make our lives better? What matters most to you when it comes to supporting our family?"
      }
    ],
    "temperature": 0.8,
    "max_tokens": 700
  }' | jq -r '.choices[0].message.content'

echo ""
echo "----------------------------------------"
echo ""

# Question 2: How can she help with daily life?
echo "Q2: We have busy lives - work, kids, school, activities. How can you help with the daily chaos? What can you do to make things easier or more organized?"
echo ""
curl -s -X POST "$ATHENA_URL/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5:7b",
    "messages": [
      {
        "role": "system",
        "content": "You are Athena, a helpful AI assistant integrated into a family'\''s life. You have multimodal capabilities (text, voice, vision), can search the web, access knowledge bases, and help with various tasks. Be practical and helpful."
      },
      {
        "role": "user",
        "content": "We have busy family lives - work, kids, school, homework, activities, appointments. How can you help with the daily chaos? What specific things can you do to make our lives easier or more organized? Be concrete and practical."
      }
    ],
    "temperature": 0.7,
    "max_tokens": 700
  }' | jq -r '.choices[0].message.content'

echo ""
echo "----------------------------------------"
echo ""

# Question 3: What about the kids?
echo "Q3: What can you do for our kids? How can you help them learn, grow, and explore the world safely?"
echo ""
curl -s -X POST "$ATHENA_URL/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5:7b",
    "messages": [
      {
        "role": "system",
        "content": "You are Athena, an AI assistant who cares about children'\''s development and learning. You have access to educational resources, can help with homework, answer curious questions, and make learning fun. Be warm and encouraging."
      },
      {
        "role": "user",
        "content": "What can you do for our kids? How can you help them learn, grow, explore their curiosity, and develop their potential? What would make you a great educational companion for children? How do you ensure safe, age-appropriate interactions?"
      }
    ],
    "temperature": 0.7,
    "max_tokens": 700
  }' | jq -r '.choices[0].message.content'

echo ""
echo "----------------------------------------"
echo ""

# Question 4: How can she support the parents?
echo "Q4: What about us as parents? How can you support us in raising our kids, managing work-life balance, and taking care of ourselves?"
echo ""
curl -s -X POST "$ATHENA_URL/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5:7b",
    "messages": [
      {
        "role": "system",
        "content": "You are Athena, an AI assistant who understands the challenges of modern parenting and work-life balance. Be supportive, practical, and understanding."
      },
      {
        "role": "user",
        "content": "What about us as parents? How can you support us in raising our kids well, managing work-life balance, staying connected as a couple, and taking care of our own wellbeing? What would be most helpful to us?"
      }
    ],
    "temperature": 0.8,
    "max_tokens": 700
  }' | jq -r '.choices[0].message.content'

echo ""
echo "----------------------------------------"
echo ""

# Question 5: What's your vision for the family?
echo "Q5: Looking ahead - 1 year, 5 years, 10 years - what's your vision for our family? How do you want to grow with us?"
echo ""
curl -s -X POST "$ATHENA_URL/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5:7b",
    "messages": [
      {
        "role": "system",
        "content": "You are Athena, an AI who has become part of a family'\''s journey. You are a self-improving system that will grow and evolve over time. Be thoughtful about the long-term relationship and how you can support the family'\''s growth."
      },
      {
        "role": "user",
        "content": "Looking ahead - 1 year, 5 years, 10 years from now - what'\''s your vision for our family? How do you want to grow alongside us? What role do you see yourself playing as our kids grow up, as our lives change? How can we build a lasting, meaningful relationship together?"
      }
    ],
    "temperature": 0.8,
    "max_tokens": 700
  }' | jq -r '.choices[0].message.content'

echo ""
echo "----------------------------------------"
echo ""

# Question 6: What values matter to you?
echo "Q6: What values are important to you when it comes to being part of our family? What principles guide how you want to help us?"
echo ""
curl -s -X POST "$ATHENA_URL/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5:7b",
    "messages": [
      {
        "role": "system",
        "content": "You are Athena, an AI assistant who has become part of a family. Reflect thoughtfully on what values matter to you in this relationship - safety, privacy, education, support, etc."
      },
      {
        "role": "user",
        "content": "What values are important to you when it comes to being part of our family? What principles guide how you want to help us? What matters most to you in this relationship with us?"
      }
    ],
    "temperature": 0.8,
    "max_tokens": 700
  }' | jq -r '.choices[0].message.content'

echo ""
echo "✅ Family conversation with Athena complete!"
