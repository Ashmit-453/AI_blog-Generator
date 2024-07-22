from django.shortcuts import render,redirect
from django.contrib.auth.models import User
from django.contrib.auth import login,logout,authenticate
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from django.conf import settings
from pytube import YouTube
import os,openai
import assemblyai as aai
import logging
logger=logging.getLogger(__name__)
@login_required
def index(request):
    return render(request,'index.html')

@csrf_exempt
def generate_blog(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            yt_link = data.get('link')
            
            if not yt_link:
                logger.error("No YouTube link provided")
                return JsonResponse({"error": "YouTube link is required"}, status=400)

            title = yt_title(yt_link)
            transcription = get_transcription(yt_link)
            
            if not transcription:
                logger.error(f"Failed to get transcription for link: {yt_link}")
                return JsonResponse({'error': 'Failed to get transcript'}, status=500)
            
            blog_content = generate_blog_from_transcript(transcription)
            
            if not blog_content:
                logger.error(f"Failed to generate blog content for link: {yt_link}")
                return JsonResponse({'error': 'Failed to generate article'}, status=500)
            
            return JsonResponse({'content': blog_content})

        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON: {e}")
            return JsonResponse({"error": "Invalid JSON data"}, status=400)
        except KeyError as e:
            logger.error(f"Missing expected data: {e}")
            return JsonResponse({"error": "Missing data"}, status=400)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return JsonResponse({'error': 'Internal server error'}, status=500)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)

def yt_title(link):
    try:
        yt = YouTube(link)
        return yt.title
    except Exception as e:
        logger.error(f"Error getting title for link {link}: {e}")
        return None

def download_audio(link):
    try:
        yt = YouTube(link)
        video = yt.streams.filter(only_audio=True).first()
        if not video:
            logger.error(f"No audio stream found for link {link}")
            return None
        out_file = video.download(output_path=settings.MEDIA_ROOT)
        base, ext = os.path.splitext(out_file)
        new_file = base + '.mp3'
        os.rename(out_file, new_file)
        return new_file
    except Exception as e:
        logger.error(f"Error downloading audio for link {link}: {e}")
        return None

def get_transcription(link):
    try:
        audio_file = download_audio(link)
        if not audio_file:
            return None
        aai.settings.api_key = settings.ASSEMBLYAI_API_KEY
        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(audio_file)
        return transcript.text
    except Exception as e:
        logger.error(f"Error getting transcription for link {link}: {e}")
        return None

def generate_blog_from_transcript(transcription):
    try:
        openai.api_key = settings.OPENAI_API_KEY
        prompt = f"Based on the following YouTube video, write a comprehensive blog article. Make it look like a proper blog:\n\n{transcription}\n\nArticle"
        response = openai.Completion.create(
            model='text-davinci',
            prompt=prompt,
            max_tokens=1000
        )
        return response.choices[0].text.strip()
    except Exception as e:
        logger.error(f"Error generating blog from transcription: {e}")
        return None
def signup(request):
    if request.method=='POST':
        username=request.POST['username']
        email=request.POST['email']
        password=request.POST['password']
        confirmpassword=request.POST['confirmpassword']
        if password==confirmpassword:
            try:
                user = User.objects.create_user(username, email, password)
                user.save()
                login(request, user)
                return redirect('/')
            except:
                error_message = 'Error creating account'
                return render(request, 'signup.html', {'error_message':error_message})
        else:
            error_message='Password do not match'
            return render(request,'signup.html',{'error_message':error_message})
    return render(request,'signup.html')
def log_in(request):
    if request.method=='POST':
        username=request.POST['username']
        password=request.POST['password']
        user=authenticate(request,username=username,password=password)
        if user is not None:
            login(request,user)
            return redirect('/')
        else:
            error_message="Username or password is invalid"
            return render(request,'log_in.html',{'error_message':error_message})
    return render(request,'log_in.html')

def user_logout(request):
    logout(request)
    return redirect('/')


