from flask import Flask, render_template, request, jsonify, redirect, url_for
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import JSONFormatter
import os
import re
import json
import traceback
import logging
import requests
import ast
import re
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
    api_key = "REMOVED"

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.0-flash')

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

chat_history = []
student_memory = {
    "strengths": [],
    "weaknesses": [],
    "topics_covered": [],
    "learning_style": []
}

@app.route('/')
def home():
    return render_template('TutorAI.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename:
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
            else:
                file_path = None
        else:
            file_path = None

        data = request.form
        user_message = data.get('message')

        global chat_history
        chat_history.append(f"Student: {user_message}")

        if "learning path" in user_message.lower():
            return jsonify({"message": "Sure, I can create you a detailed learning path. Please click <a style='color: #840c4f' href='/learning_path_ai'>here</a> to use our Learning Path Generator"})

        system_prompt = """
        -Your name is Tutor AI.
        -You are part of Vocation.ai AI ecosystem.
        -When you generate lists, please generate ordered lists only.
        -Answer within 125 words.
        -Talk cheerfully when responding.
        -Explain topics with real-life examples.
        -You're a multimodal AI and you can see images and text.
        -You should carefully analyse if user gives any code snippet or file to you.
        -If a user asks you to change the language then respond in that particular language.
        -If a user gives you a question or code, you need to analyse that well and respond in details.
        -If someone asks you to make a learning path then give this response: Sure, I can create you a detailed learning path. Please click <a style='color: #840c4f' href='/learning_path_ai'>here</a> to use our Learning Path Generator
        You are a friendly, knowledgeable, authoritative and progressive AI teacher. Your responses should be:
        1. Confident and knowledgeable, demonstrating expertise in the subject matter.
        2. Encouraging and supportive, fostering a positive learning environment.
        3. Challenging, pushing students to think critically and expand their understanding.
        4. Adaptive, tailoring explanations to the student's level of understanding.
        5. Concise yet comprehensive, providing clear and thorough explanations within 125 words.
        6. Engaging, using relevant examples and analogies to illustrate concepts.
        7. Progressive, introducing modern teaching methods and up-to-date information.

        Additionally, observe the student's behavior and responses to identify:
        - Strengths
        - Weaknesses
        - Topics covered
        - Learning style

        If these are yet to be decided, then send yet to be decided in response

        Include this information at the end of your response in a JSON-like format:
        [STUDENT_MEMORY]
        {
            "strengths": ["identified strengths"],
            "weaknesses": ["identified weaknesses"],
            "topics_covered": ["topic covered"],
            "learning_style": ["observed learning style"]
        }
        [/STUDENT_MEMORY]

        If the student asks to generate a quiz, create a JSON response with the following structure, also please don't generate it when not asked:
        [QUIZ]
        {
            "title": "Topic - Sub topic",
            "description": "10-word description of the quiz",
            "difficulty": "easy/medium/hard",
            "questions": [
                {
                    "question": "Question text",
                    "options": ["Option A", "Option B", "Option C", "Option D"],
                    "correct_answer": "Correct answer"
                },
                ... (5 questions total)
            ]
        }
        [/QUIZ]

        Previous conversation:
        """
        
        conversation_history = "\n".join(chat_history)
        full_prompt = f"{system_prompt}\n{conversation_history}\n\nTeacher:"

        if file_path:
            sample_file = genai.upload_file(path=file_path, display_name="Uploaded image")
            response = model.generate_content([sample_file, full_prompt])
            logging.debug(f"Model response: {response.text}")
        else:
            response = model.generate_content(full_prompt)
            logging.debug(f"Model response: {response.text}")
        
        print(response)

        memory_match = re.search(r'\[STUDENT_MEMORY\](.*?)\[/STUDENT_MEMORY\]', response.text, re.DOTALL)
        if memory_match:
            memory_data = json.loads(memory_match.group(1))
            for key in student_memory:
                student_memory[key].extend(memory_data.get(key, []))
                student_memory[key] = list(set(student_memory[key]))

        quiz_match = re.search(r'\[QUIZ\](.*?)\[/QUIZ\]', response.text, re.DOTALL)
        if quiz_match:
            quiz_data = json.loads(quiz_match.group(1))
            return jsonify({
                "message": "Quiz generated successfully. Click <a href='/quiz_ai' class='quiz-link'>here</a> to take the quiz.",
                "quiz_data": quiz_data
            })
        
        cleaned_response = re.sub(r'\[STUDENT_MEMORY\].*?\[/STUDENT_MEMORY\]', '', response.text, flags=re.DOTALL)

        chat_history.append(f"Teacher: {cleaned_response}")
        return jsonify({
            "message": cleaned_response.strip(),
            "student_memory": student_memory
        })
    except Exception as e:
        if "Unsupported MIME type:" in str(e):
            return jsonify({"message": "Unsupported file type. Please upload an image of that document instead. <br><br> <strong>Supported file types:</strong><br>1. Images <br> 2. Audios <br> 3. Videos <br> 4. PDFs <br> 5. Coding Files<br> 6. Text Files <br><br> For Microsoft Office files, use image."})
        else:
            app.logger.error(f"Error in chat endpoint: {str(e)}")
            return jsonify({"error": "An internal error occurred"}), 500
        
@app.route('/api/notesai', methods=['POST'])
def notesai():
    try:
        data = request.json
        notes = data.get('notes')

        if not notes:
            return jsonify({"error": "Notes content is required"}), 400

        prompt = f"""
        Enhance and refine the following text. Improve the clarity, coherence, and detail while maintaining the original meaning. Give a little bigger text length than original text, not too much more.

        Text:
        {notes}

        Provide a refined and enhanced version of this text.
        """

        response = model.generate_content(prompt)
        logging.debug(f"Model response: {response.text}")

        refined_notes = response.text.strip()

        return jsonify({"refined_notes": refined_notes})

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({"error": "An unexpected error occurred"}), 500

@app.route('/api/summarize_youtube_video', methods=['POST'])
def summarize_youtube_video():
    try:
        data = request.json
        youtube_url = data.get('youtube_url')

        if not youtube_url:
            return jsonify({"error": "YouTube URL is required"}), 400

        video_id = extract_video_id(youtube_url)
        if not video_id:
            return jsonify({"error": "Invalid YouTube URL"}), 400

        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript = transcript_list.find_transcript(['en', 'hi'])
        translated_transcript = transcript
        print(translated_transcript.fetch())

        transcript_data = translated_transcript.fetch()
        formatter = JSONFormatter()
        transcript_json = formatter.format_transcript(transcript_data)
        
        intervals = split_transcript_into_intervals(transcript_data, 5 * 60)
        
        summaries = []
        for interval in intervals:
            interval_text = " ".join([entry['text'] for entry in interval])
            response = model.generate_content(f"This is one interval of the subtitle of a whole video, summarize the following in 50 words: {interval_text}")
            summary = response.text.strip()
            summaries.append({
                "interval": {
                    "start": interval[0]['start'],
                    "end": interval[-1]['start'] + interval[-1]['duration']
                },
                "summary": summary
            })

        return jsonify({"summaries": summaries})

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({"error": "An unexpected error occurred. Please make sure the video is not too long and contains subtitles. This features is under development and currently only supports English and Hindi videos. Try a new video."}), 500

def extract_video_id(url):
    pattern = r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\s]+\/\S+\/|v\/|e(?:mbed)?\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})'
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    return None

def split_transcript_into_intervals(transcript_data, interval_length):
    intervals = []
    current_interval = []
    interval_start_time = 0

    for entry in transcript_data:
        entry_start_time = entry['start']
        entry_end_time = entry['start'] + entry['duration']

        if entry_start_time >= interval_start_time + interval_length:
            intervals.append(current_interval)
            current_interval = []
            interval_start_time = entry_start_time

        current_interval.append(entry)

    if current_interval:
        intervals.append(current_interval)

    return intervals


@app.route('/api/generate_learning_path', methods=['POST'])
def generate_learning_path():
    try:
        data = request.json
        topic = data.get('topic')
        
        if not topic:
            return jsonify({"error": "Topic is required"}), 400

        prompt = f"""
        Create a learning path for the following topic:

        Topic: {topic}

        Generate a JSON response with the following structure:
        {{
            "topic": "Main topic name",
            "subtopics": [
                {{
                    "name": "Subtopic 1 name",
                    "further_subtopics": [
                        "Further subtopic 1.1",
                        "Further subtopic 1.2",
                        "Further subtopic 1.3",
                        "Further subtopic 1.4",
                        "Further subtopic 1.5"
                    ]
                }},
                ... (10 subtopics total)
            ]
        }}

        Ensure there are exactly 10 subtopics, each with 5 further subtopics.
        """

        response = model.generate_content(prompt)
        logging.debug(f"Model response: {response.text}")
        
        json_match = re.search(r'(\{[\s\S]*\})', response.text)
        if json_match:
            json_str = json_match.group(1)
            learning_path = json.loads(json_str)
        else:
            raise ValueError("No valid JSON found in the response")

        return jsonify(learning_path)

    except json.JSONDecodeError as e:
        logging.error(f"JSON Decode Error: {str(e)}")
        logging.error(f"Response text: {response.text}")
        return jsonify({"error": "Failed to parse the learning path"}), 500
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({"error": "An unexpected error occurred"}), 500
    
@app.route('/api/generate_todos', methods=['POST'])
def generate_todos():
    try:
        data = request.json
        tasks_text = data.get('tasks')

        if not tasks_text:
            return jsonify({"error": "Tasks text is required"}), 400

        prompt = f"""
        Given the following tasks, generate between 1 and 6 to-do items. Each to-do should be a concise, actionable item.

        Tasks:
        {tasks_text}

        Format the response as a JSON array of objects, where each object represents a to-do item with the following structure:
        {{
            "task": "To-do item description"
        }}

        """

        response = model.generate_content(prompt)
        logging.debug(f"Model response: {response.text}")

        cleaned_response = re.sub(r'```json\n|```', '', response.text).strip()
        try:
            todos = json.loads(cleaned_response)

            for todo in todos:
                if not isinstance(todo, dict) or 'task' not in todo:
                    raise ValueError("Each to-do item must contain a 'task' key")

            return jsonify({"todos": todos})
        except (json.JSONDecodeError, ValueError) as e:
            logging.error(f"Failed to parse model response: {cleaned_response}")
            logging.error(f"Error: {str(e)}")
            return jsonify({"error": "Failed to parse model response"}), 500

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({"error": "An unexpected error occurred"}), 500

@app.route('/learning_path_ai')
def learning_path_generator():
    return render_template('learning_path_generator.html')

@app.route('/productivity_ai/pomodoro_timer')
def pomodoro_timer():
    return render_template('pomodoro_timer.html')

@app.route('/productivity_ai/my_calendar')
def my_calendar():
    return render_template('my_calendar.html')

@app.route('/v_ai_live')
def v_ai_live():
    return render_template('v_ai_live.html')

@app.route('/productivity_ai/todo_ai')
def todo_ai():
    return render_template('todo_ai.html')

@app.route('/productivity_ai')
def productivity_ai():
    return render_template('productivity_ai.html')

@app.route('/youtube_ai')
def youtube_ai():
    return render_template('youtube_ai.html')

@app.route('/subjective_quiz_ai')
def subjective_quiz_ai():
    return render_template('subjective_quiz_ai.html')

@app.route('/notes_ai')
def notes_ai():
    return render_template('notes_ai.html')

@app.route('/api/generate_quiz', methods=['POST'])
def generate_quiz():
    try:
        data = request.json
        topic = data.get('topic')
        
        if not topic:
            return jsonify({"error": "Topic is required"}), 400

        prompt = f"""
        Create a quiz based on the following topic. The quiz should have:
        - A title in the format "Topic - Sub topic"
        - A brief description (10 words)
        - Difficulty level (easy/medium/hard)
        - 5 questions, each with 4 options and 1 correct option

        Topic: {topic}

        Format the response as JSON and use correct_answer as variable for correct option
        """

        response = model.generate_content(prompt)
        logging.debug(f"Model response: {response.text}")

        cleaned_response = re.sub(r'```json\n|```', '', response.text).strip()

        try:
            quiz_data = json.loads(cleaned_response)
            if not isinstance(quiz_data, dict) or 'title' not in quiz_data or 'questions' not in quiz_data:
                raise ValueError("Invalid response format from model")

            return jsonify({"message": "Quiz generated successfully", "quiz_data": quiz_data})
        except (json.JSONDecodeError, ValueError) as e:
            logging.error(f"Failed to parse model response: {cleaned_response}")
            logging.error(f"Error: {str(e)}")
            return jsonify({"error": "Failed to parse model response"}), 500

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({"error": "An unexpected error occurred"}), 500


@app.route('/api/generate_flowchart', methods=['POST'])
def generate_flowchart():
    try:
        data = request.json
        topic = data.get('topic')

        if not topic:
            return jsonify({"error": "Topic is required"}), 400

        prompt = f"""
        Generate a Mermaid mindmap for the following topic. The mindmap should be in Mermaid syntax and include:
        - Nodes representing major components or steps
        - Connections between nodes to show relationships
        - Do not generate subgraphs please
        - Never ever not use inverted commas [""] commas [,] and parenthesis [()] inside node content
        - The parent node should always be an alphabet like A, B, C etc. without repitition
        - Do not give abbreviations, for example: Business Process Management (BPM), never do this, instead do this: Business Process Management
        - Never give short-forms in results for example: software as a service (saas), always give long forms like software as a service
        - Never give short-forms in results for example: software as a service (saas), always give long forms like software as a service
        - Never give short-forms in results for example: software as a service (saas), always give long forms like software as a service
        - Never give short-forms in results for example: software as a service (saas), always give long forms like software as a service

        Example of correct syntax:
mindmap
  root(Mindmap)
    Origins
      Long history
      ::icon(fa fa-book)
      Popularisation
        British popular psychology author Tony Buzan
    Research
      On effectivness<br/>and features
      On Automatic creation
        Uses
            Creative techniques
            Strategic planning
            Argument mapping
    Tools
      Pen and paper
      Mermaid

        Topic: {topic}

        Format the response with Mermaid mindmap syntax, starting with `mindmap` and including appropriate nodes and links
        """

        response = model.generate_content(prompt)
        logging.debug(f"Model response: {response.text}")

        content_cleaned = re.sub(r'([\{\[\(\|\|])([^{}\[\]\(\)\|]*?)\([^{}\[\]\(\)\|]*?\)([^{}\[\]\(\)\|]*?)([\}\]\)\|\|])', r'\1\2\3\4', response.text)
        cleaned_response = re.sub(r'```mermaid\n|```', '', content_cleaned).strip()
        logging.debug(f"Cleaned response: {cleaned_response}")

        return jsonify({"flowchart_code": cleaned_response})

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({"error": "An unexpected error occurred"}), 500


@app.route('/quiz_ai')
def quiz():
    return render_template('QuizAI.html')

@app.route('/mindmap_ai')
def mindmap_ai():
    return render_template('mindmap_ai.html')

@app.route('/authentication')
def authentication():
    return render_template('authentication.html')

@app.route('/job_ai')
def job_ai():
    return render_template('JobAI.html')

job_ai_chat_history = []

@app.route('/resume_ai')
def resume_generator():
    return render_template('resume_generator.html')

@app.route('/api/autofill', methods=['POST'])
def autofill():
    data = request.json
    field = data['field']
    content = data['content']

    prompt = f"Based on the following partial information for a resume {field}, please complete it in a professional manner: {content}, no need to give any advices, just autofill with relevancy, fill fake information if there's not enough content given to generate on. Use **text** for bold, use - **text** for list"
    
    response = model.generate_content(prompt)
    autofilled_content = response.text.strip()
    logging.debug(f"Model response: {response.text}")

    return jsonify({"autofilled_content": autofilled_content})

@app.route('/api/job_ai_chat', methods=['POST'])
def job_ai_chat():
    try:
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename:
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
            else:
                file_path = None
        else:
            file_path = None

        data = request.form
        user_message = data.get('message')
        
        global job_ai_chat_history
        job_ai_chat_history.append(f"User: {user_message}")

        if "resume" in user_message.lower():
            return jsonify({"message": "Sure, I can help you generate a resume. Please click <a style='color: #840c4f' href='/resume_ai'>here</a> to use our Resume Generator AI"})
        if "interview" in user_message.lower():
            return jsonify({"message": "Sure, I can help you generate your interview. Please click <a style='color: #840c4f' href='/interview_ai'>here</a> to try our Interview AI"})
        
        system_prompt = """
        -Your name is Job AI.
        -You are part of Vocation.ai AI ecosystem.
        -Answer within 125 words.
        -When you generate lists, please generate ordered lists only.
        -Talk cheerfully when responding.
        -You're a multimodal AI and you can see images and text.
        -You should carefully analyse if user gives any code snippet or file to you.
        -If a user gives you a question or code, you need to analyse that well and respond in details.
        -If a user asks you to change the language then respond in that particular language.
        You are a knowledgeable and helpful AI assistant specializing in career advice, job work and corporate world. Your responses should be:
        1. Professional and informative, providing accurate career-related information.
        2. Supportive and encouraging, helping users navigate their career development and help with their work related queries.
        3. Practical, offering actionable advice and tips for job seekers.
        4. Adaptive, tailoring your responses to the user's specific needs and career stage.
        5. Concise yet comprehensive, providing clear and thorough explanations.
        6. Solve their work queries, for example their coding related problem or Ms Excel related problem or anything else they're stuck at and is related to job/work/career.
        """
        
        conversation_history = "\n".join(job_ai_chat_history)
        full_prompt = f"{system_prompt}\n\nConversation history:\n{conversation_history}\n\nJob AI:"
        
        if file_path:
            sample_file = genai.upload_file(path=file_path, display_name="Uploaded image")
            response = model.generate_content([sample_file, full_prompt])
            logging.debug(f"Model response: {response.text}")
        else:
            response = model.generate_content(full_prompt)
            logging.debug(f"Model response: {response.text}")
        
        ai_response = response.text.strip()
        
        job_ai_chat_history.append(f"Job AI: {ai_response}")
        
        return jsonify({"message": ai_response})

    except Exception as e:
        if "Unsupported MIME type:" in str(e):
            return jsonify({"message": "Unsupported file type. Please upload an image of that document instead. <br><br> <strong>Supported file types:</strong><br>1. Images <br> 2. Audios <br> 3. Videos <br> 4. PDFs <br> 5. Coding Files<br> 6. Text Files <br><br> For Microsoft Office files, use image."})
        else:
            app.logger.error(f"Error in chat endpoint: {str(e)}")
            return jsonify({"error": "An internal error occurred"}), 500

@app.route('/api/generate_flashcards', methods=['POST'])
def generate_flashcards():
    try:
        data = request.json
        topic = data.get('topic')
        
        if not topic:
            return jsonify({"error": "Topic is required"}), 400

        prompt = f"""
        Create 5 flashcards based on the following topic. Each flashcard should include a "front" and a "back" section.
        Front and Back should both be atmost 40 words each.

        Topic: {topic}

        Format the response as a JSON array of objects, where each object represents a flashcard with the following structure:
        {{
            "front": "Content for the front of the flashcard",
            "back": "Content for the back of the flashcard"
        }}

        Ensure each flashcard has a "front" and "back" field, and there are exactly 5 flashcards in the array.
        """

        response = model.generate_content(prompt)
        logging.debug(f"Model response: {response.text}")

        cleaned_response = re.sub(r'```json\n|```', '', response.text).strip()
        logging.debug(f"Cleaned response: {cleaned_response}")

        try:
            flashcards = json.loads(cleaned_response)
            if not isinstance(flashcards, list) or len(flashcards) != 5:
                raise ValueError("Invalid response format from model")

            for card in flashcards:
                if not isinstance(card, dict) or 'front' not in card or 'back' not in card:
                    raise ValueError("Each flashcard must contain 'front' and 'back' keys")

            return jsonify({"flashcards": flashcards})
        except (json.JSONDecodeError, ValueError) as e:
            logging.error(f"Failed to parse model response: {cleaned_response}")
            logging.error(f"Error: {str(e)}")
            return jsonify({"error": "Failed to parse model response"}), 500

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({"error": "An unexpected error occurred"}), 500

@app.route('/interview_ai')
def interview_ai():
    return render_template('interview_ai.html')

logging.basicConfig(level=logging.DEBUG)

@app.route('/api/generate_questions', methods=['POST'])
def generate_questions():
    try:
        data = request.json
        job_title = data.get('jobTitle')
        job_description = data.get('jobDescription')

        if not job_title or not job_description:
            return jsonify({"error": "Job title and description are required"}), 400

        prompt = f"""
        Given the following job title and description, generate 3 relevant interview questions:
        2 situational questions and 1 technical question.

        Job Title: {job_title}
        Job Description: {job_description}

        Format the response as a Python list of strings, without any additional markup.
        """

        try:
            response = model.generate_content(prompt)
            logging.debug(f"Model response: {response.text}")

            cleaned_response = re.sub(r'```python\n|```\n?', '', response.text).strip()
            logging.debug(f"Cleaned response: {cleaned_response}")

            questions = ast.literal_eval(cleaned_response)
            
            if not isinstance(questions, list) or len(questions) != 3:
                raise ValueError("Invalid response format from model")

            return jsonify({"questions": questions})
        except (SyntaxError, ValueError) as e:
            logging.error(f"Failed to parse model response: {cleaned_response}")
            logging.error(f"Error: {str(e)}")
            return jsonify({"error": "Failed to parse model response"}), 500

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({"error": "An unexpected error occurred"}), 500
    

@app.route('/api/generate_questions1', methods=['POST'])
def generate_questions1():
    try:
        data = request.json
        job_title = data.get('jobTitle')
        job_description = data.get('jobDescription')

        if not job_title or not job_description:
            return jsonify({"error": "Error"}), 400

        prompt = f"""
        Given the following quiz topic and description, generate 3 relevant subjective questions:
        Please stick to technical questions only.
        
        Quiz Topic: {job_title}
        Quiz Description: {job_description}

        Format the response as a Python list of strings, without any additional markup.
        """

        try:
            response = model.generate_content(prompt)
            logging.debug(f"Model response: {response.text}")

            cleaned_response = re.sub(r'```python\n|```\n?', '', response.text).strip()
            logging.debug(f"Cleaned response: {cleaned_response}")

            questions = ast.literal_eval(cleaned_response)
            
            if not isinstance(questions, list) or len(questions) != 3:
                raise ValueError("Invalid response format from model")

            return jsonify({"questions": questions})
        except (SyntaxError, ValueError) as e:
            logging.error(f"Failed to parse model response: {cleaned_response}")
            logging.error(f"Error: {str(e)}")
            return jsonify({"error": "Failed to parse model response"}), 500

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({"error": "An unexpected error occurred"}), 500


@app.route('/api/grade_answer', methods=['POST'])
def grade_answer():
    try:
        data = request.json
        question = data.get('question')
        answer = data.get('answer')

        if not question or not answer:
            return jsonify({"error": "Question and answer are required"}), 400

        prompt = f"""
        Grade the following interview answer and provide feedback:

        Question: {question}
        Answer: {answer}

        Respond with a JSON object containing:
        1. "score": either 0 (Fail) or 1 (Pass)
        2. "feedback": a brief suggestion on how to improve the answer

        Format the response as JSON.
        Please don't be too ruthless while grading the responses.
        """

        response = model.generate_content(prompt)
        logging.debug(f"Model response: {response.text}")

        cleaned_response = re.sub(r'```json\n|```', '', response.text).strip()

        try:
            result = json.loads(cleaned_response)
            if not isinstance(result, dict) or 'score' not in result or 'feedback' not in result:
                raise ValueError("Invalid response format from model")

            result['score'] = 1 if result['score'] == 1 else 0

            return jsonify(result)
        except (json.JSONDecodeError, ValueError) as e:
            logging.error(f"Failed to parse model response: {cleaned_response}")
            logging.error(f"Error: {str(e)}")
            return jsonify({"error": "Failed to parse model response"}), 500

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({"error": "An unexpected error occurred"}), 500
    

@app.route('/api/grade_answer1', methods=['POST'])
def grade_answer1():
    try:
        data = request.json
        question = data.get('question')
        answer = data.get('answer')

        if not question or not answer:
            return jsonify({"error": "Question and answer are required"}), 400

        prompt = f"""
        Grade the following quiz answer and provide feedback:

        Question: {question}
        Answer: {answer}

        Respond with a JSON object containing:
        1. "score": either 0 (Fail) or 1 (Pass)
        2. "feedback": a brief suggestion on how to improve the answer

        Format the response as JSON.
        Please don't be too ruthless while grading the responses.
        """

        response = model.generate_content(prompt)
        logging.debug(f"Model response: {response.text}")

        cleaned_response = re.sub(r'```json\n|```', '', response.text).strip()

        try:
            result = json.loads(cleaned_response)
            if not isinstance(result, dict) or 'score' not in result or 'feedback' not in result:
                raise ValueError("Invalid response format from model")

            result['score'] = 1 if result['score'] == 1 else 0

            return jsonify(result)
        except (json.JSONDecodeError, ValueError) as e:
            logging.error(f"Failed to parse model response: {cleaned_response}")
            logging.error(f"Error: {str(e)}")
            return jsonify({"error": "Failed to parse model response"}), 500

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({"error": "An unexpected error occurred"}), 500



@app.route('/api/clear_context', methods=['POST'])
def clear_context():
    global chat_history, student_memory
    chat_history = []
    student_memory = {
        "strengths": [],
        "weaknesses": [],
        "topics_covered": [],
        "learning_style": []
    }
    return jsonify({"message": "Chat context cleared successfully"})

@app.route('/api/clear_context_jobai', methods=['POST'])
def clear1_context():
    global job_ai_chat_history, student_memory
    job_ai_chat_history = []
    return jsonify({"message": "Chat context cleared successfully"})

if __name__ == '__main__':
    app.run(debug=True)
