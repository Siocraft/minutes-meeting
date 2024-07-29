from openai import OpenAI
from docx import Document
from pydub import AudioSegment

client = OpenAI()

def divide_audio(input_file, segment_duration=60):
  audio = AudioSegment.from_wav(input_file)
  print(f"\033[94m[Santi]\033[0m Dividing audio file into chunks of {segment_duration} seconds...")
  segment_length_ms = segment_duration * 1000

  for i, start_time in enumerate(range(0, len(audio), segment_length_ms)):
    segment = audio[start_time:start_time + segment_length_ms]
    output_file = f"segments/segment_{i + 1}.wav"
    segment.export(output_file, format="wav")

  global segments_quantity
  segments_quantity = i + 1

  print(f"\033[92m[Santi]\033[0m Audio file divided into {segments_quantity} chunks.")

def transcribe_single_audio(audio_file_path):
  with open(audio_file_path, 'rb') as audio_file:
    transcription = client.audio.transcriptions.create(
    model="whisper-1",
    file=audio_file,
  )
  return transcription.text

def transcribe_audio(audio_file_path):
  divide_audio(audio_file_path)
  audio_chunks = [open(f"segments/segment_{i + 1}.wav", "rb").read() for i in range(segments_quantity)]

  audio_text_file = open("audio_text.txt", "w")
  transcriptions = []
  for i, chunk in enumerate(audio_chunks):
    print(f"Transcribing chunk {i+1}...")
    with open(f"segments/chunk_{i+1}.wav", 'wb') as chunk_file:
      chunk_file.write(chunk)
    transcription = transcribe_single_audio(f"segments/chunk_{i+1}.wav")
    transcriptions.append(transcription)
  
  all_transcriptions = ' '.join(transcriptions)
  audio_text_file.write(all_transcriptions)
  return all_transcriptions

def abstract_summary_extraction(transcription):
  response = client.chat.completions.create(
    model="gpt-4",
    temperature=0,
    messages=[
      {
        "role": "system",
        "content": "You are a highly skilled AI trained in language comprehension and summarization. I would like you to read the following text and summarize it into a concise abstract paragraph. Aim to retain the most important points, providing a coherent and readable summary that could help a person understand the main points of the discussion without needing to read the entire text. Please avoid unnecessary details or tangential points."
      },
      {
        "role": "user",
        "content": transcription
      }
    ]
  )
  return response.choices[0].message.content

def key_points_extraction(transcription):
  response = client.chat.completions.create(
    model="gpt-4",
    temperature=0,
    messages=[
      {
        "role": "system",
        "content": "You are a proficient AI with a specialty in distilling information into key points. Based on the following text, identify and list the main points that were discussed or brought up. These should be the most important ideas, findings, or topics that are crucial to the essence of the discussion. Your goal is to provide a list that someone could read to quickly understand what was talked about."
      },
      {
        "role": "user",
        "content": transcription
      }
    ]
  )
  return response.choices[0].message.content

def action_item_extraction(transcription):
  response = client.chat.completions.create(
    model="gpt-4",
    temperature=0,
    messages=[
      {
        "role": "system",
        "content": "You are an AI expert in analyzing conversations and extracting action items. Please review the text and identify any tasks, assignments, or actions that were agreed upon or mentioned as needing to be done. These could be tasks assigned to specific individuals, or general actions that the group has decided to take. Please list these action items clearly and concisely."
      },
      {
        "role": "user",
        "content": transcription
      }
    ]
  )
  return response.choices[0].message.content

def sentiment_analysis(transcription):
  response = client.chat.completions.create(
    model="gpt-4",
    temperature=0,
    messages=[
      {
        "role": "system",
        "content": "As an AI with expertise in language and emotion analysis, your task is to analyze the sentiment of the following text. Please consider the overall tone of the discussion, the emotion conveyed by the language used, and the context in which words and phrases are used. Indicate whether the sentiment is generally positive, negative, or neutral, and provide brief explanations for your analysis where possible."
      },
      {
        "role": "user",
        "content": transcription
      }
    ]
  )
  return response.choices[0].message.content

def meeting_minutes(transcription):
  abstract_summary = abstract_summary_extraction(transcription)
  key_points = key_points_extraction(transcription)
  action_items = action_item_extraction(transcription)
  sentiment = sentiment_analysis(transcription)
  return {
    'abstract_summary': abstract_summary,
    'key_points': key_points,
    'action_items': action_items,
    'sentiment': sentiment
  }

def save_as_docx(minutes, filename):
  doc = Document()
  for key, value in minutes.items():
    heading = ' '.join(word.capitalize() for word in key.split('_'))
    doc.add_heading(heading, level=1)
    doc.add_paragraph(value)
    doc.add_paragraph()
  doc.save(filename)

segments_quantity = 0
audio_file_path = "EarningsCall.wav"

transcription = transcribe_audio(audio_file_path)
minutes = meeting_minutes(transcription)

print(minutes)

save_as_docx(minutes, 'meeting_minutes.docx')