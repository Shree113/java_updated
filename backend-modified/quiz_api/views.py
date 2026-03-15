import logging
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.http import JsonResponse
from rest_framework.authtoken.models import Token
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.shortcuts import get_object_or_404
import json
from django.utils.decorators import method_decorator
from .models import Student, Question, StudentAnswer
from .serializers import StudentSerializer, QuestionSerializer, StudentAnswerSerializer

logger = logging.getLogger(__name__)


@csrf_exempt  # ✅ Disable CSRF for this API (ONLY if needed)
def create_student(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)  # ✅ Ensure JSON is parsed
            student = Student.objects.create(
                name=data["name"],
                email=data["email"],
                department=data["department"],
                college=data["college"],
                year=data["year"]
            )
            return JsonResponse({"id": student.id, "message": "Student created successfully"}, status=201)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Invalid request method"}, status=405)

@api_view(['POST'])
def superuser_login(request):
    username = request.data.get('username')
    password = request.data.get('password')

    user = authenticate(username=username, password=password)

    if user is not None:
        if user.is_superuser:  # ✅ Allow only superusers
            token, created = Token.objects.get_or_create(user=user)
            return Response({"token": token.key, "message": "Login successful"}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "You are not authorized as an admin"}, status=status.HTTP_403_FORBIDDEN)
    else:
        return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)


# quiz/views.py
@api_view(['DELETE'])
def delete_student(request, pk):
    try:
        student = Student.objects.get(pk=pk)
        student.delete()
        return Response({'message': 'Student deleted'}, status=200)
    except Student.DoesNotExist:
        return Response({'error': 'Student not found'}, status=404)


@api_view(['GET'])
def get_questions(request):
    """
    Retrieve all quiz questions in a randomized order.
    Each student gets a unique shuffled sequence to prevent cheating.
    """
    import random
    questions = list(Question.objects.all())
    random.shuffle(questions)
    serializer = QuestionSerializer(questions, many=True)
    return Response(serializer.data)


@api_view(['POST'])
def submit_answer(request):
    """
    Submit an answer for a question.
    """
    student_id = request.data.get('student_id')
    question_id = request.data.get('question_id')
    chosen_option = request.data.get('chosen_option')

    student = get_object_or_404(Student, id=student_id)
    question = get_object_or_404(Question, id=question_id)

    # Check correctness
    is_correct = (chosen_option.upper() == question.correct_option.upper())

    # Create or update the StudentAnswer
    answer, created = StudentAnswer.objects.update_or_create(
        student=student,
        question=question,
        defaults={'chosen_option': chosen_option, 'is_correct': is_correct}
    )

    # If correct, add 5 points
    if is_correct:
        student.total_score += 5
        student.save()

    return Response({
        'is_correct': is_correct,
        'current_score': student.total_score
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
def leaderboard(request):
    """
    Return students ordered by total_score descending.
    """
    students = Student.objects.all().order_by('-total_score')
    serializer = StudentSerializer(students, many=True)
    return Response(serializer.data)


@api_view(['POST'])
def complete_quiz(request):
    # Extract data from the request
    student_id = request.data.get('student_id')
    score = request.data.get('score')
    
    if not student_id or score is None:
        logger.error("Missing student_id or score in the request.")
        return Response({"error": "Missing student_id or score"}, status=status.HTTP_400_BAD_REQUEST)
    
    # Retrieve the student or return an error if not found
    try:
        student = Student.objects.get(id=student_id)
    except Student.DoesNotExist:
        logger.error(f"Student with id {student_id} not found.")
        return Response({"error": "Student not found"}, status=status.HTTP_404_NOT_FOUND)
    
    # Update the student's total score
    student.total_score = score
    student.save()

    # Compose the email
    subject = "Your Quiz Results"
    message = f"Hello {student.name},\n\nThank you for completing the quiz! Your final score is {score}."
    recipient_list = [student.email]

    # Send the email
    try:
        send_mail(subject, message, settings.EMAIL_HOST_USER, recipient_list)
    except Exception as e:
        logger.error("Email could not be sent: " + str(e))
        return Response({"error": "Email could not be sent", "details": str(e)},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({"message": "Quiz completed and email sent!"}, status=status.HTTP_200_OK)


# ── Compiler / Code Execution Endpoint ──────────────────────────────────────
import subprocess
import tempfile
import os
import re
import shutil
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

# Maximum allowed code size (10 KB)
_MAX_CODE_BYTES = 10 * 1024

# Execution timeout (seconds)
_EXEC_TIMEOUT = 10

# Python modules / builtins that are disallowed for security
_PYTHON_BLACKLIST = [
    'import os', 'import sys', 'import subprocess', 'import shutil',
    'import socket', 'import requests', 'import urllib',
    'import ctypes', 'import importlib', 'import builtins',
    '__import__', 'open(', 'exec(', 'eval(', 'compile(',
    'globals(', 'locals(', 'vars(', 'getattr(', 'setattr(',
    'delattr(', '__class__', '__bases__', '__subclasses__',
]


def _sanitize_path(text: str) -> str:
    """Remove absolute server paths from error messages."""
    import re as _re
    # Strip Windows and Linux temp paths
    text = _re.sub(r'[A-Za-z]:\\[^\s,\'"]+', '<path>', text)
    text = _re.sub(r'/tmp/[^\s,\'"]+', '<path>', text)
    return text


def _find_tool(cmd: str) -> str | None:
    """
    Return the full path to a CLI tool, or None if not found.
    Searches PATH first, then well-known JDK install directories on Windows/Linux.
    """
    import glob as _glob

    # 1. Try PATH first
    try:
        result = subprocess.run(
            [cmd, '-version'], capture_output=True, timeout=5
        )
        # If we get here without exception, `cmd` is on PATH
        return cmd
    except FileNotFoundError:
        pass
    except Exception:
        # Command found but returned an error — that's fine, it exists
        return cmd

    # 2. Scan well-known JDK directories (Windows & Linux)
    search_dirs = _glob.glob(r'C:\Program Files\Microsoft\jdk-*\bin') + \
                  _glob.glob(r'C:\Program Files\Eclipse Adoptium\jdk-*\bin') + \
                  _glob.glob(r'C:\Program Files\Java\jdk-*\bin') + \
                  _glob.glob('/usr/lib/jvm/*/bin') + \
                  _glob.glob(os.path.expanduser('~/.jdk/*/bin'))

    for d in search_dirs:
        candidate = os.path.join(d, cmd)
        if os.path.isfile(candidate):
            return candidate
        # Windows: try with .exe
        candidate_exe = candidate + '.exe'
        if os.path.isfile(candidate_exe):
            return candidate_exe

    return None


def get_file_extension(language: str) -> str:
    """Return the file extension for a given language identifier."""
    return {
        'python':     '.py',
        'java':       '.java',
        'c':          '.c',
        'cpp':        '.cpp',
        'javascript': '.js',
    }.get(language, '.txt')


def run_code(file_path, language, code=None):
    """
    Execute code for the given language and return the combined output string.
    All errors are sanitized to avoid leaking server filesystem paths.
    """
    try:
        # ── PYTHON ──────────────────────────────────────────────────────────
        if language == 'python':
            # Detect available Python interpreter
            try:
                subprocess.run(['python3', '--version'], capture_output=True, check=True, timeout=5)
                python_cmd = 'python3'
            except (subprocess.SubprocessError, FileNotFoundError):
                python_cmd = 'python'

            result = subprocess.run(
                [python_cmd, file_path],
                capture_output=True,
                text=True,
                timeout=_EXEC_TIMEOUT
            )

        # ── C ───────────────────────────────────────────────────────────────
        elif language == 'c':
            gcc_path = _find_tool('gcc')
            if not gcc_path:
                return "Error: C compiler (gcc) is not installed on the server."

            output_path = file_path.replace('.c', '')
            compile_result = subprocess.run(
                [gcc_path, file_path, '-o', output_path],
                capture_output=True, text=True, timeout=_EXEC_TIMEOUT
            )
            if compile_result.returncode != 0:
                return "Compilation Error:\n" + _sanitize_path(compile_result.stderr)

            result = subprocess.run(
                [output_path],
                capture_output=True, text=True, timeout=_EXEC_TIMEOUT
            )
            try:
                os.unlink(output_path)
            except OSError:
                pass

        # ── JAVA ────────────────────────────────────────────────────────────
        elif language == 'java':
            javac_path = _find_tool('javac')
            if not javac_path:
                return "Error: Java compiler (javac) is not installed on the server."

            java_path = _find_tool('java')
            if not java_path:
                return "Error: Java runtime (java) is not installed on the server."

            # Extract the public class name from the source
            match = re.search(r'\bpublic\s+class\s+(\w+)', code or '')
            if not match:
                return "Error: Could not find a public class declaration in the Java code."
            class_name = match.group(1)

            # Write to a uniquely named temp directory so concurrent requests
            # don't clobber each other's files.
            java_dir = tempfile.mkdtemp()
            try:
                java_file = os.path.join(java_dir, f'{class_name}.java')
                with open(java_file, 'w', encoding='utf-8') as f:
                    f.write(code)

                # Compile
                compile_result = subprocess.run(
                    [javac_path, java_file],
                    capture_output=True, text=True, timeout=_EXEC_TIMEOUT
                )
                if compile_result.returncode != 0:
                    return "Compilation Error:\n" + _sanitize_path(compile_result.stderr)

                # Run
                result = subprocess.run(
                    [java_path, '-cp', java_dir, class_name],
                    capture_output=True, text=True, timeout=_EXEC_TIMEOUT
                )
            finally:
                shutil.rmtree(java_dir, ignore_errors=True)

        else:
            return f"Unsupported language: '{language}'. Supported: python, java, c."

        # Build output
        output = result.stdout
        if result.returncode != 0:
            output += f"\nError (exit code {result.returncode}):\n" + _sanitize_path(result.stderr)
        return output

    except subprocess.TimeoutExpired:
        return f"Execution timed out (limit: {_EXEC_TIMEOUT} seconds)."
    except Exception as e:
        return f"Execution error: {_sanitize_path(str(e))}"


@api_view(['POST'])
def compile_code(request):
    """
    Compile and execute code submitted in the request body.

    Required fields:
      - code     (str)  : Source code to run.
      - language (str)  : One of 'python', 'java', 'c'.

    Security measures applied:
      - Code size capped at 10 KB.
      - Dangerous Python built-ins / modules are blacklisted.
      - Server paths are stripped from all error output.
      - Hard 10-second execution timeout.
    """
    code = request.data.get('code', '').strip()
    language = request.data.get('language', 'python').strip().lower()

    # ── Validation ──────────────────────────────────────────────────────────
    if not code:
        return Response({'error': 'No code provided.'}, status=status.HTTP_400_BAD_REQUEST)

    if len(code.encode('utf-8')) > _MAX_CODE_BYTES:
        return Response({'error': 'Code exceeds maximum allowed size (10 KB).'}, status=status.HTTP_400_BAD_REQUEST)

    supported = {'python', 'java', 'c'}
    if language not in supported:
        return Response(
            {'error': f"Unsupported language '{language}'. Supported: {', '.join(sorted(supported))}."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # ── Python safety check ─────────────────────────────────────────────────
    if language == 'python':
        code_lower = code.lower()
        for forbidden in _PYTHON_BLACKLIST:
            if forbidden.lower() in code_lower:
                return Response(
                    {'error': 'Code contains disallowed modules or functions.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

    # ── Execution ───────────────────────────────────────────────────────────
    try:
        if language == 'java':
            output = run_code(None, language, code=code)
        else:
            suffix = get_file_extension(language)
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False, mode='w', encoding='utf-8') as tmp:
                tmp.write(code)
                tmp_path = tmp.name
            try:
                output = run_code(tmp_path, language)
            finally:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass

        return Response({'output': output}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {'error': f'Unexpected error: {_sanitize_path(str(e))}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
