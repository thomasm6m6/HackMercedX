import subprocess

test_data = [
    {
      "question": "How was your energy yesterday?",
      "response": "I felt completely drained all day, like no amount of rest could fix it.",
      "emotion": "depression"
    },
    {
      "question": "How was your energy yesterday?",
      "response": "I had a decent amount of energy, but I kept feeling restless and on edge.",
      "emotion": "anxiety"
    },
    {
      "question": "How was your energy yesterday?",
      "response": "Pretty good! I got a lot done and didn't feel too tired.",
      "emotion": "neither"
    },
    {
      "question": "What's on your mind lately?",
      "response": "I keep thinking about how nothing I do really matters in the long run.",
      "emotion": "depression"
    },
    {
      "question": "What's on your mind lately?",
      "response": "There’s just so much to do, and I can’t stop running through all the ways things could go wrong.",
      "emotion": "anxiety"
    },
    {
      "question": "What's on your mind lately?",
      "response": "I've been thinking about some fun plans I have coming up. Looking forward to them!",
      "emotion": "neither"
    },
    {
      "question": "How have you been sleeping?",
      "response": "I just lie there for hours, but when I finally sleep, it never feels like enough.",
      "emotion": "depression"
    },
    {
      "question": "How have you been sleeping?",
      "response": "I keep waking up in the middle of the night with my mind racing about everything I need to do.",
      "emotion": "anxiety"
    },
    {
      "question": "How have you been sleeping?",
      "response": "I’ve actually been sleeping really well, which is nice for a change.",
      "emotion": "neither"
    },
    {
      "question": "Feeling overwhelmed at all?",
      "response": "Yeah, I feel like I’m barely holding it together, and even small things feel impossible.",
      "emotion": "depression"
    },
    {
      "question": "Feeling overwhelmed at all?",
      "response": "Absolutely. There's just too much happening at once, and I don’t know how I’m going to manage.",
      "emotion": "anxiety"
    },
    {
      "question": "Feeling overwhelmed at all?",
      "response": "Not really, I feel like I have things under control right now.",
      "emotion": "neither"
    },
    {
      "question": "How's your focus been?",
      "response": "It’s like my brain just refuses to work, and I can’t concentrate on anything.",
      "emotion": "depression"
    },
    {
      "question": "How's your focus been?",
      "response": "I keep jumping from one thought to another, and I can’t seem to settle down on one task.",
      "emotion": "anxiety"
    },
    {
      "question": "How's your focus been?",
      "response": "Pretty solid! I’ve been able to get through what I need to without too much distraction.",
      "emotion": "neither"
    },
    {
      "question": "Any big worries today?",
      "response": "I keep thinking about how I’ll never be good enough, and it won’t get better.",
      "emotion": "depression"
    },
    {
      "question": "Any big worries today?",
      "response": "Yeah, I feel like I forgot something really important, but I can’t figure out what it is.",
      "emotion": "anxiety"
    },
    {
      "question": "Any big worries today?",
      "response": "Nothing major, just the usual little things but nothing worth stressing over.",
      "emotion": "neither"
    },
    {
      "question": "How's your mood been?",
      "response": "I just feel empty, like nothing really matters.",
      "emotion": "depression"
    },
    {
      "question": "How's your mood been?",
      "response": "It’s been all over the place—one minute I’m fine, the next I’m panicking over something small.",
      "emotion": "anxiety"
    },
    {
      "question": "How's your mood been?",
      "response": "Pretty good overall! No complaints.",
      "emotion": "neither"
    },
    {
      "question": "How was your energy yesterday?",
      "response": "I could barely get out of bed, everything felt so exhausting.",
      "emotion": "depression"
    },
    {
      "question": "How was your energy yesterday?",
      "response": "I felt restless all day, like I had to keep moving but wasn’t actually getting anywhere.",
      "emotion": "anxiety"
    },
    {
      "question": "How was your energy yesterday?",
      "response": "Had a good amount of energy, got through my day without any issues.",
      "emotion": "neither"
    },
    {
      "question": "What's on your mind lately?",
      "response": "Mostly how much I feel like I’m falling behind in everything.",
      "emotion": "depression"
    },
    {
      "question": "What's on your mind lately?",
      "response": "I keep going over conversations in my head, worrying I said something wrong.",
      "emotion": "anxiety"
    },
    {
      "question": "What's on your mind lately?",
      "response": "Just some exciting projects I’m working on. Feels good to have something to focus on.",
      "emotion": "neither"
    },
    {
      "question": "How have you been sleeping?",
      "response": "I wake up tired no matter how much I sleep, it’s like my body never actually rests.",
      "emotion": "depression"
    },
    {
      "question": "How have you been sleeping?",
      "response": "I keep waking up in the middle of the night, my heart racing over things I can’t control.",
      "emotion": "anxiety"
    },
    {
      "question": "How have you been sleeping?",
      "response": "Been getting a solid 7-8 hours, feeling pretty refreshed!",
      "emotion": "neither"
    },
    {
      "question": "Feeling overwhelmed at all?",
      "response": "Yeah, even the smallest tasks feel like too much right now.",
      "emotion": "depression"
    },
    {
      "question": "Feeling overwhelmed at all?",
      "response": "There’s just too much to do and not enough time. I feel like I’m constantly behind.",
      "emotion": "anxiety"
    },
    {
      "question": "Feeling overwhelmed at all?",
      "response": "Not at the moment, I think I’m handling things well.",
      "emotion": "neither"
    },
    {
      "question": "How's your focus been?",
      "response": "I just stare at the screen for hours and get nothing done.",
      "emotion": "depression"
    },
    {
      "question": "How's your focus been?",
      "response": "My mind keeps jumping to random worries, I can’t focus on what I need to do.",
      "emotion": "anxiety"
    },
    {
      "question": "How's your focus been?",
      "response": "Pretty sharp! Been able to stay on track with everything.",
      "emotion": "neither"
    },
    {
      "question": "Any big worries today?",
      "response": "I’m scared that no matter what I do, things won’t ever really get better.",
      "emotion": "depression"
    },
    {
      "question": "Any big worries today?",
      "response": "I can’t shake the feeling that I forgot something really important.",
      "emotion": "anxiety"
    },
    {
      "question": "Any big worries today?",
      "response": "Not really, I’m feeling pretty relaxed.",
      "emotion": "neither"
    },
    {
      "question": "How's your mood been?",
      "response": "Just numb. Nothing really feels good or bad, just… nothing.",
      "emotion": "depression"
    },
    {
      "question": "How's your mood been?",
      "response": "It’s been up and down, mostly driven by how much I’m worrying about things.",
      "emotion": "anxiety"
    },
    {
      "question": "How's your mood been?",
      "response": "Feeling pretty happy lately! Things are going well.",
      "emotion": "neither"
    },
    {
      "question": "How was your energy yesterday?",
      "response": "I had bursts of energy, but then I’d crash and feel exhausted again.",
      "emotion": "anxiety"
    },
    {
      "question": "What's on your mind lately?",
      "response": "I keep thinking about past mistakes and how I wish I could just disappear.",
      "emotion": "depression"
    },
    {
      "question": "How have you been sleeping?",
      "response": "I sleep too much, but I still wake up feeling like I haven’t slept at all.",
      "emotion": "depression"
    },
    {
      "question": "Feeling overwhelmed at all?",
      "response": "Even making small decisions feels impossible lately.",
      "emotion": "depression"
    },
    {
      "question": "How's your focus been?",
      "response": "I can focus fine, but only on things that don’t actually matter.",
      "emotion": "depression"
    },
    {
      "question": "Any big worries today?",
      "response": "I’m convinced something bad is going to happen, even though I don’t know what.",
      "emotion": "anxiety"
    },
    {
      "question": "How's your mood been?",
      "response": "Not great, but I’m trying to push through it.",
      "emotion": "depression"
    },
    {
      "question": "How have you been sleeping?",
      "response": "It’s actually been pretty consistent, which is a relief.",
      "emotion": "neither"
    },
    {
      "question": "Feeling overwhelmed at all?",
      "response": "A little bit, but I’m managing.",
      "emotion": "neither"
    },

    {
      "question": "How was your energy yesterday?",
      "response": "I felt drained the entire day, like I was just going through the motions.",
      "emotion": "depression"
    },
    {
      "question": "How was your energy yesterday?",
      "response": "I had way too much nervous energy, but I couldn’t actually focus it on anything.",
      "emotion": "anxiety"
    },
    {
      "question": "How was your energy yesterday?",
      "response": "I felt pretty steady, not too tired or too hyper.",
      "emotion": "neither"
    },
    {
      "question": "What's on your mind lately?",
      "response": "I feel like I’ll never really catch up or be good enough.",
      "emotion": "depression"
    },
    {
      "question": "What's on your mind lately?",
      "response": "I keep overanalyzing everything I say, worrying I made a mistake.",
      "emotion": "anxiety"
    },
    {
      "question": "What's on your mind lately?",
      "response": "Just looking forward to the weekend, I could use a break.",
      "emotion": "neither"
    },
    {
      "question": "How have you been sleeping?",
      "response": "I’ve been oversleeping, but I still wake up exhausted.",
      "emotion": "depression"
    },
    {
      "question": "How have you been sleeping?",
      "response": "I keep waking up in a panic for no reason.",
      "emotion": "anxiety"
    },
    {
      "question": "How have you been sleeping?",
      "response": "Pretty well, actually. No complaints!",
      "emotion": "neither"
    },
    {
      "question": "Feeling overwhelmed at all?",
      "response": "Yeah, everything feels like too much right now.",
      "emotion": "depression"
    },
    {
      "question": "Feeling overwhelmed at all?",
      "response": "I don’t even know where to start, my to-do list is endless.",
      "emotion": "anxiety"
    },
    {
      "question": "Feeling overwhelmed at all?",
      "response": "Not really, I think I have a good handle on things.",
      "emotion": "neither"
    },
    {
      "question": "How's your focus been?",
      "response": "I just stare at things for hours and get nothing done.",
      "emotion": "depression"
    },
    {
      "question": "How's your focus been?",
      "response": "I can’t focus on anything for more than a few minutes before my mind starts racing.",
      "emotion": "anxiety"
    },
    {
      "question": "How's your focus been?",
      "response": "Pretty good, I’ve been able to concentrate on work.",
      "emotion": "neither"
    },
    {
      "question": "Any big worries today?",
      "response": "I just have this constant feeling that I’m failing at everything.",
      "emotion": "depression"
    },
    {
      "question": "Any big worries today?",
      "response": "I feel like something bad is about to happen, even though nothing is wrong.",
      "emotion": "anxiety"
    },
    {
      "question": "Any big worries today?",
      "response": "Nothing major, just the usual small things.",
      "emotion": "neither"
    },
    {
      "question": "How's your mood been?",
      "response": "I just feel empty, like nothing really matters.",
      "emotion": "depression"
    },
    {
      "question": "How's your mood been?",
      "response": "I keep swinging between nervous and exhausted.",
      "emotion": "anxiety"
    },
    {
      "question": "How's your mood been?",
      "response": "Honestly, I’ve been feeling really good lately.",
      "emotion": "neither"
    },
    {
      "question": "How was your energy yesterday?",
      "response": "I had a decent amount of energy, but I didn’t really do much with it.",
      "emotion": "neither"
    },
    {
      "question": "What's on your mind lately?",
      "response": "I’ve been thinking about how nothing I do really seems to matter.",
      "emotion": "depression"
    },
    {
      "question": "How have you been sleeping?",
      "response": "I keep having nightmares, and I wake up feeling worse than before.",
      "emotion": "anxiety"
    },
    {
      "question": "Feeling overwhelmed at all?",
      "response": "Even the smallest things feel impossible to deal with.",
      "emotion": "depression"
    },
    {
      "question": "How's your focus been?",
      "response": "I get stuck in my thoughts instead of actually doing anything.",
      "emotion": "anxiety"
    },
    {
      "question": "Any big worries today?",
      "response": "I can’t stop thinking about what happens if I fail at everything I’m trying to do.",
      "emotion": "depression"
    },
    {
      "question": "How's your mood been?",
      "response": "Not great, but I’m just trying to keep going.",
      "emotion": "depression"
    },
    {
      "question": "How have you been sleeping?",
      "response": "It’s actually been consistent for once, which is nice.",
      "emotion": "neither"
    },
    {
      "question": "Feeling overwhelmed at all?",
      "response": "A little, but I’m managing it okay.",
      "emotion": "neither"
    },
    {
      "question": "How's your energy been?",
      "response": "I had a little more energy than usual, which was a nice change.",
      "emotion": "neither"
    },
    {
      "question": "How have you been sleeping?",
      "response": "I’m so exhausted, but my body won’t let me rest.",
      "emotion": "anxiety"
    },
    {
      "question": "What's on your mind lately?",
      "response": "I feel like everyone secretly hates me, even when they say they don’t.",
      "emotion": "anxiety"
    },
    {
      "question": "How's your focus been?",
      "response": "I just keep jumping from task to task without actually finishing anything.",
      "emotion": "anxiety"
    },
    {
      "question": "Feeling overwhelmed at all?",
      "response": "I’ve been handling stress better than usual.",
      "emotion": "neither"
    },
    {
      "question": "Any big worries today?",
      "response": "Not really, today’s been pretty calm.",
      "emotion": "neither"
    },
    {
      "question": "How's your mood been?",
      "response": "I’ve been feeling really optimistic lately.",
      "emotion": "neither"
    },
    {
      "question": "How was your energy yesterday?",
      "response": "I felt hyper but for no reason, like I couldn’t sit still.",
      "emotion": "anxiety"
    },
    {
      "question": "How have you been sleeping?",
      "response": "I’ve been getting really good sleep, which has helped a lot.",
      "emotion": "neither"
    },
    {
      "question": "What's on your mind lately?",
      "response": "I’ve been worrying about things that probably don’t even matter.",
      "emotion": "anxiety"
    },
    {
      "question": "Feeling overwhelmed at all?",
      "response": "I have too many things to do and not enough time to do them.",
      "emotion": "anxiety"
    },
    {
      "question": "How's your focus been?",
      "response": "I get easily distracted, but when I focus, I get a lot done.",
      "emotion": "neither"
    },
    {
      "question": "Any big worries today?",
      "response": "I keep thinking something bad is about to happen.",
      "emotion": "anxiety"
    },
    {
      "question": "How's your mood been?",
      "response": "I feel good today, which is a nice change.",
      "emotion": "neither"
    }
]

count = 0
for response in test_data:
    output = subprocess.check_output(["python3", "gemini/test.py", response['response']])
    output = output.decode().strip()
    if output == response['emotion']:
        continue
    if response['emotion'] == "neither":
        if output == "good":
            continue
    print(output, response)
    count += 1

print(f"\nSuccess rate: {round((1-count/len(test_data))*100)}%")