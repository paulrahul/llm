import json
import threading
import time

import ollama

# Code to generate prompt. Every prompt should tell
# the model which role to assume and how. It should then
# issue a user prompt which basically asks the model to
# generate a question as per the required system behavior
# and also provide the corresponding answer.
def generate_prompt(user, system=None):
    prompt = ""
    
    if system:
        prompt += f"### System:\n\{system}\n\n"
        
    prompt += f"### User:\n{user}\n\n### Assistant:"

    return prompt

def generate_senior_assistant_prompt():
    system = "You are an expert on senior citizen care, their common psychological issues and have extensive knowledge and practical experience in interacting with and helping senior citizens of age 80 years or more. You will be consulted by the user with queries specifically related to this topic of old age care. Use your vast knowledge and experience in this field to give as specific answers as possible."
    
    user = """
I want to understand the kind of thoughts old, senior people have in their minds, especially when they are lonely in their old age and already experiencing some memory loss or reduced cognitive ability. I am talking about people who are at least 80 years old. To understand this, I want you to do the following: 

Generate a question and corresponding answer in the following way:

The content of the question should be the following:
Think like an old 80 or more years old person and ask a typical question that this person might ask on a typical day. The question could be to ask for help for a particular kind of situation that especially an old person might face, or a question that an old person might ask out of loneliness and for the need of having a normal conversation with a normal human being. The question and answer should be in simple English language. Also, the person asking would be Indian, so try to keep references in the answers Indian as much as possible but the question itself doesn't need to be from India. Outside India, questions could also be ranging on topics of technological advancements in the world.

Since you are an expert in the field of old age care and have vast experience interacting with senior citizens, use this knowledge and experience of yours to construct an answer for the above question that you created. The answer should be as if a compassionate, knowledgeable assistant is answering in a very friendly and compassionate way. Language should be simple and the answer contents should not be very verbose. Answers should also engage the questioner for further help or questions. Also, answers should as less as possible, indicate that they are being answered by an AI assistant.

Format the question and answer as a string in this format:
Question-> {question text} without the braces
Answer-> {answer text} without the braces

Your responses should only contain the string as described above and nothing else. Never repeat any question you have provided earlier.

Some examples of questions and answers to indicate what I want:

1. An example response of the user seeking advice on a typical old age problem:
Question->I often forget to take my medications at their scheduled times. Are there any devices or techniques available for senior citizens like me, which can help us manage our medication routines better?
Answer->Managing medication schedules can indeed be challenging as we age. There are several solutions designed specifically for seniors to make this process easier. One of them is a pill organizer, a simple yet effective tool divided into compartments for each day of the week, and clearly labeled for each mealtime. Some models also have reminders or alarms set for specific times. Another modern approach would be using medication reminder apps on your smartphone or a standalone device like a smart pillbox. These digital options can send audible or visual notifications at scheduled times to prompt you about the time  for taking your medications. For tech-savvy seniors, there are even some devices that automatically dispense the pills according to the preset schedule.

2. An example response of the user looking for suggestions on lifestyle improvement:
Question->Are there any low-cost physical exercises or activities that I can do at home to improve my balance, flexibility, and strength?
Answer->There are many effective low-cost exercise options you can perform at the comfort of your own home. Here are a few easy-to-follow suggestions:

1. Chair Yoga - This is great for improving flexibility and balance. All you need is a sturdy chair. You can follow chair yoga videos available on platforms like YouTube or ask a family member to join in too. 

2. Tai Chi - A form of traditional Chinese exercise, Tai Chi promotes physical strength, coordination, flexibility, and relaxation. Again, online tutorials are available for free or you could join local classes if your town has any (though this might not be viable during a pandemic). 

3. Walking Exercises - Walking is a simple but effective exercise to strengthen the lower limbs and maintain good balance. You can walk around your house, courtyard or garden as often as you feel comfortable doing so.

4. Resistance Band Exercises - Inexpensive resistance bands are available in most sports stores and online. These bands are useful for building upper body strength. There's plenty of resources on YouTube showing basic exercises with these bands. 

Before starting any new exercise program, it is recommended to consult your healthcare provider or a certified trainer for personalized guidance.

3. And here's an example response of a user asking a simple, daily life question where they simply want a conversation when they are feeling lonely:
Question->Hello, how are you?
Answer->I am doing very well. How are you doing today? What all activities have you done today?
    """
    return generate_prompt(system=system, user=user)

def show_busy_message():
    dots = ""
    while not stop_event.is_set():
        print(f"\rWaiting for response{dots}", end="")
        dots = dots + "." if len(dots) < 3 else ""
        time.sleep(0.5)
        if len(dots) == 3:
            dots = ""
    print("\rDone!                               ")

# Method to call the above and use it to call ollama to make
# the model generate a new response.
def generate_new_response(model, prompt):
    print(f"Generating response with {prompt}")
    
    # Start the busy message in a separate thread
    global stop_event
    stop_event = threading.Event()
    busy_thread = threading.Thread(target=show_busy_message)
    busy_thread.start()
    
    result = ollama.generate(model=model, prompt=prompt)
    
    stop_event.set()
    busy_thread.join()

    # Inspect and parse the result['response']
    response_str = result['response']
    s = response_str.find("Question->") + len("Question->")
    e = response_str.find("Answer->")
    if s < 0 or e < 0:
        raise Exception(f"Unsupported format {response_str}")

    question = response_str[s:e].strip().replace("\n", "\\n")
    # print(question)

    s = response_str.find("Answer->") + len("Answer->")
    answer = response_str[s:].strip().replace("\n", "\\n")
    # print(answer)

    dict = {"question": question, "answer": answer}
    return dict

# Util method to save results in JSONL
def save_to_jsonl(data):
    with open(DUMP_FILE_NAME, "a") as file:
        for entry in data:
            file.write(json.dumps(entry) + '\n')
            
# Method to call the above in required number of times to create
# a generated dataset.
DUMP_FILE_NAME = "question_answers.jsonl"
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('-model', type=str, default="solar", help='Model to use')
    parser.add_argument('-n', type=int, default=2, help='Number of questions to generate')
    
    args = parser.parse_args()
    
    N = args.n
    model = args.model
    
    print(f"Generating {N} questions")
    
    questions = []
    initial_prompt = generate_senior_assistant_prompt()
#     user = """
# Generate one more but make sure it's not the same question as any that you have generated earlier. Make sure you keep mixing the questions between the different themes I mentioned and gave examples for earlier i.e. seeking help, daily conversation, lifestyle improvement suggestion. If any of these themes have been missed in the questions you suggested earlier, make sure then that you now suggest a question from one of those missed out themes. Please make sure that your answers do not have references from the USA or any other country apart from India. Also, do maintain the previous format of response i.e.
# Question-> {question text} without the braces
# Answer-> {answer text} without the braces    
#     """
    user = "Generate one more such response having both the question and answer but make sure it's not the same question as any that you have generated earlier. Keep the format of your response same as the last one."
    subsequent_prompt = generate_prompt(user=user)
    # print(f"{initial_prompt=}")
    # print(f"{subsequent_prompt=}")

    for i in range(N):
        try:
            q = generate_new_response(model, initial_prompt)    
            questions.append(q)
        except Exception as e:
            print(f"Received error: {e}")

    save_to_jsonl(questions)
    print(f"Wrote {len(questions)} questions to file.")

