#@brief: A PyQt6 application for managing focus sessions with Google Calendar integration.
# This application allows users to set a conscious aim for a focus session, start a timer, and receive notifications when the session ends.
# It also integrates with Google Calendar to create events for each session.
# The application displays a random remembrance prompt and an image to enhance the user experience.
# The user can pause, resume, or stop the session at any time.
# The application also includes a presence check to pause the session if the user is inactive for a set period.
# The application uses a sound file to play a bell sound at the start and end of each session.
# The application includes a list of 100 remembrance prompts from various spiritual and philosophical traditions.
# The application icon and image are included in the bundle for a complete user experience.

import sys
import time
import threading
import os
import pickle
import random

from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QLineEdit, QMessageBox, QComboBox, QFormLayout
)
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QFont, QIcon, QPixmap

import pygame
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from datetime import datetime, timedelta, timezone

class FocusSessionApp(QWidget):
    """
    A PyQt6 application for managing focus sessions.

    This application allows users to set focus sessions with predefined durations,
    displays inspirational quotes, integrates with Google Calendar to create events,
    and provides sound notifications.
    """

    def __init__(self, app_icon_path):
        """
        Initializes the FocusSessionApp.

        Args:
            app_icon_path (str): The file path to the application icon.
        """
        super().__init__()

        self.setWindowTitle("Self Remembering App")
        self.setGeometry(100, 100, 400, 400)

        if os.path.exists(app_icon_path):
            icon = QIcon(app_icon_path)
            self.setWindowIcon(icon)
        else:
            QMessageBox.warning(self, "Icon Missing", f"Icon not found at {app_icon_path}. Taskbar icon may not display correctly.")

        self.aim = None
        self.start_time = None
        self.last_active_time = None
        self.is_running = False
        self.is_paused = False
        self.total_pause_time = 0
        self.remaining_seconds = 0
        self.total_seconds = 0
        self.elapsed_seconds = 0
        self.event_id = None

        pygame.mixer.init()

        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))

        sound_path = os.path.join(base_path, 'sounds', 'tibetanbowl.mp3')

        try:
            if not os.path.exists(sound_path):
                raise FileNotFoundError(f"Sound file not found at {sound_path}")
            self.bell_sound = pygame.mixer.Sound(sound_path)
        except pygame.error as e:
            QMessageBox.critical(self, "Sound Error", f"Failed to load sound file: {e}")
            self.bell_sound = None
        except FileNotFoundError as fnf_error:
            QMessageBox.critical(self, "Sound File Missing", str(fnf_error))
            self.bell_sound = None

        self.remembrance_prompts = [
            "Know thyself, for in that knowledge lies the universe. - G.I. Gurdjieff",
            "Be present in the now, the only moment you truly have. - G.I. Gurdjieff",
            "Confront your inner world to understand the outer world. - G.I. Gurdjieff",
            "Seek the truth within, for only then can you see it without. - G.I. Gurdjieff",
            "Awaken to your own sleep, and begin the journey to consciousness. - G.I. Gurdjieff",
            "Every action, every thought, requires your full presence. - G.I. Gurdjieff",
            "Remember your aim, for without it, you are but a leaf in the wind. - G.I. Gurdjieff",
            "Self-observation is the mirror to your soul's awakening. - G.I. Gurdjieff",
            "Let your intentions guide your actions, not your habits. - G.I. Gurdjieff",
            "The struggle within is the path to true freedom. - G.I. Gurdjieff",
            "Do not merely exist; strive to live consciously. - G.I. Gurdjieff",
            "Embrace the unknown, for it is the cradle of growth. - G.I. Gurdjieff",
            "The present moment is the doorway to eternity. - G.I. Gurdjieff",
            "Conscious work is the key to unlock your potential. - G.I. Gurdjieff",
            "Resist the comfort of sleep; embrace the challenge of awakening. - G.I. Gurdjieff",
            "The soul of the true poet is a little unclouded. - William Blake",
            "To see a world in a grain of sand, and a heaven in a wild flower. - William Blake",
            "What is now proved was once only imagined. - William Blake",
            "No bird soars too high if he soars with his own wings. - William Blake",
            "The man who never in his mind and heart waked, can never feel the dreamer's passion stirred. - William Blake",
            "A truth that's told with bad intent beats all the lies you can invent. - William Blake",
            "Great things are done when men and mountains meet. - William Blake",
            "If the doors of perception were cleansed everything would appear to man as it is, infinite. - William Blake",
            "The tree which moves some to tears of joy is in the eyes of others only a green thing that stands in the way. - William Blake",
            "He who binds to himself a joy does the winged life destroy; but he who kisses the joy as it flies lives in eternity’s sunrise. - William Blake",
            "The wound is the place where the Light enters you. - Rumi",
            "What you seek is seeking you. - Rumi",
            "Don’t be satisfied with stories, how things have gone with others. - Rumi",
            "Let yourself be silently drawn by the strange pull of what you really love. - Rumi",
            "Stop acting so small. You are the universe in ecstatic motion. - Rumi",
            "Yesterday I was clever, so I wanted to change the world. Today I am wise, so I am changing myself. - Rumi",
            "Raise your words, not voice. It is rain that grows flowers, not thunder. - Rumi",
            "The universe is not outside of you. Look inside yourself; everything that you want, you already are. - Rumi",
            "You were born with wings, why prefer to crawl through life? - Rumi",
            "When you do things from your soul, you feel a river moving in you, a joy. - Rumi",
            "The river that flows in you also flows in me. - Kabir",
            "Wherever you are is the entry point. - Kabir",
            "The moon stays bright when it doesn't avoid the night. - Kabir",
            "Your own self-realization is the greatest service you can render the world. - Kabir",
            "Even after all this time, the sun never says to the earth, 'You owe me.' - Kabir",
            "Life is a balance between holding on and letting go. - Kabir",
            "The bird of time has but a little way to fly, but it wings to see the world go by. - Kabir",
            "Love is the bridge between you and everything. - Kabir",
            "Where are you? Declare the purpose and set your heart free. - Kabir",
            "In the midst of movement and chaos, keep stillness inside of you. - Kabir",
            "Love is the bond of all life. - Meher Baba",
            "Your heart is the door to the soul, but you must turn the key. - Meher Baba",
            "In the end, there is no saving anyone but yourself. - Meher Baba",
            "Your journey has just begun. - Meher Baba",
            "The love you give comes back to you as love you receive. - Meher Baba",
            "To realize the truth, you must eliminate all that is not truth. - Meher Baba",
            "Happiness is not outside; it is inside. - Meher Baba",
            "Be still, for the One is near. - Meher Baba",
            "The seeker must become the sought. - Meher Baba",
            "Live your life as if you were to die tomorrow. - Meher Baba",
            "Man is not a human being having a spiritual experience. He is a spiritual being having a human experience. - P.D. Ouspensky",
            "Nothing in this world can be done without pure consciousness. - P.D. Ouspensky",
            "The only thing that is real is the present moment. - P.D. Ouspensky",
            "Man is the most powerful and the most ignorant of all beings. - P.D. Ouspensky",
            "Self-remembering is the core of all progress in life. - P.D. Ouspensky",
            "A true focus is in the development of self-awareness. - P.D. Ouspensky",
            "The rational mind is a device for seeking truth. - P.D. Ouspensky",
            "To think is to believe something that is not true. - P.D. Ouspensky",
            "Understanding arises from deep inquiry. - P.D. Ouspensky",
            "Only through direct experience can we truly know. - P.D. Ouspensky",
            "Justice, justice shall you pursue. - Moses",
            "Grief is the price we pay for love. - Queen Elizabeth I",
            "The earth shall give back what it owes to life. - Yunus Emre",
            "To know others is intelligence; to know yourself is true wisdom. - Lao-Tzu",
            "Meditate on love, compassion, and enlightenment. - Milarepa",
            "The road to hell is paved with good intentions. - Bernard of Clairvaux",
            "Keep your mind in the depths of hell, and despair not. - Silouan the Athonite",
            "Where words fail, music speaks. - Hans Christian Andersen",
            "Find the truth in your heart, and let it light your path. - Bahauddin Naqshband",
            "Seek wisdom with humility and you will find it in abundance. - Al Ghazali"
        ]

        self.remembrance_prompts = list(set(self.remembrance_prompts))
        self.calendar_service = self.setup_google_calendar()
        self.build_ui()
        self.qtimer = QTimer()
        self.qtimer.timeout.connect(self.update_timer)
        self.presence_thread = threading.Thread(target=self.check_presence, daemon=True)
        self.presence_thread.start()

    def setup_google_calendar(self):
        """
        Sets up the Google Calendar API connection.

        Returns:
            googleapiclient.discovery.Resource: The Google Calendar service object.
        """
        SCOPES = ['https://www.googleapis.com/auth/calendar.events']
        creds = None

        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))

        token_path = os.path.join(os.path.expanduser('~'), '.mindapp', 'token.pickle')
        credentials_path = os.path.join(base_path, 'client_secret.json')

        os.makedirs(os.path.dirname(token_path), exist_ok=True)

        if os.path.exists(token_path):
            try:
                with open(token_path, 'rb') as token:
                    creds = pickle.load(token)
            except Exception:
                creds = None

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception:
                    creds = None

            if not creds:
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        credentials_path, SCOPES)
                    creds = flow.run_local_server(port=0)
                    with open(token_path, 'wb') as token:
                        pickle.dump(creds, token)
                except Exception as e:
                    print(f"Calendar setup error: {str(e)}")
                    QMessageBox.warning(
                        self,
                        "Calendar Setup",
                        f"Google Calendar integration failed: {str(e)}\nPlease ensure client_secret.json is present."
                    )
                    return None

        try:
            return build('calendar', 'v3', credentials=creds)
        except Exception as e:
            print(f"API build error: {str(e)}")
            QMessageBox.warning(
                self,
                "Calendar Setup",
                f"Failed to connect to Google Calendar: {str(e)}"
            )
            return None

    def build_ui(self):
        """
        Constructs the user interface components.
        """
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        form_layout = QFormLayout()
        form_layout.setSpacing(15)

        aim_label = QLabel("Aim:")
        aim_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.aim_input = QLineEdit()
        self.aim_input.setPlaceholderText("Enter your aim for this session...")
        self.aim_input.setFont(QFont("Arial", 10))
        self.aim_input.setMaximumHeight(30)
        form_layout.addRow(aim_label, self.aim_input)

        timer_label = QLabel("Duration:")
        timer_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.timer_combo = QComboBox()
        self.timer_combo.addItems([
            "5 min",
            "15 min",
            "25 min",
            "30 min",
            "45 min",
            "1 hour"
        ])
        self.timer_combo.setCurrentIndex(1)
        self.timer_combo.setFont(QFont("Arial", 10))
        self.timer_combo.setMaximumHeight(30)
        form_layout.addRow(timer_label, self.timer_combo)

        layout.addLayout(form_layout)

        self.timer_display = QLabel("0:00 remaining")
        self.timer_display.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.timer_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.timer_display)

        self.prompt_label = QLabel()
        self.prompt_label.setFont(QFont("Arial", 10))
        self.prompt_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.prompt_label.setWordWrap(True)
        self.display_random_remembrance()
        layout.addWidget(self.prompt_label)

        self.image_label = QLabel(self)
        self.load_image()
        layout.addWidget(self.image_label, alignment=Qt.AlignmentFlag.AlignCenter)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)

        self.start_button = QPushButton("Start")
        self.start_button.setToolTip("Start Session")
        self.start_button.setFont(QFont("Arial", 10))
        self.start_button.clicked.connect(self.start_session)
        button_layout.addWidget(self.start_button)

        self.pause_button = QPushButton("Pause")
        self.pause_button.setToolTip("Pause Session")
        self.pause_button.setEnabled(False)
        self.pause_button.setFont(QFont("Arial", 10))
        self.pause_button.clicked.connect(self.pause_session)
        button_layout.addWidget(self.pause_button)

        self.resume_button = QPushButton("Resume")
        self.resume_button.setToolTip("Resume Session")
        self.resume_button.setEnabled(False)
        self.resume_button.setFont(QFont("Arial", 10))
        self.resume_button.clicked.connect(self.resume_session)
        button_layout.addWidget(self.resume_button)

        self.stop_button = QPushButton("Stop")
        self.stop_button.setToolTip("Stop Session")
        self.stop_button.setEnabled(False)
        self.stop_button.setFont(QFont("Arial", 10))
        self.stop_button.clicked.connect(self.stop_session)
        button_layout.addWidget(self.stop_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def start_session(self):
        """
        Begins a new focus session based on user input.
        """
        if self.is_running:
            QMessageBox.information(self, "Session Running", "A session is already running.")
            return

        aim = self.aim_input.text().strip()
        if not aim:
            aim = "Engaged in activity"
        self.aim_input.setText(aim)
        self.aim = aim
        self.start_time = time.time()
        self.last_active_time = self.start_time
        self.is_running = True
        self.is_paused = False
        self.total_pause_time = 0
        self.elapsed_seconds = 0

        timer_selection = self.timer_combo.currentText().strip().lower()

        duration_map = {
            "5 min": 5 * 60,
            "15 min": 15 * 60,
            "25 min": 25 * 60,
            "30 min": 30 * 60,
            "45 min": 45 * 60,
            "1 hour": 60 * 60
        }

        self.total_seconds = duration_map.get(timer_selection, 60 * 60)
        self.remaining_seconds = self.total_seconds

        if self.bell_sound:
            self.bell_sound.play()

        self.create_or_update_calendar_event()
        self.display_random_remembrance()
        self.qtimer.start(1000)
        self.update_timer_display()

        self.start_button.setEnabled(False)
        self.pause_button.setEnabled(True)
        self.stop_button.setEnabled(True)
        self.aim_input.setEnabled(False)
        self.timer_combo.setEnabled(False)

    def create_or_update_calendar_event(self, update=False):
        """
        Creates or updates a Google Calendar event for the current session.

        Args:
            update (bool): Indicates whether to update an existing event.
        """
        if not self.calendar_service:
            return

        start_time = datetime.now(timezone.utc).isoformat()
        end_time = (datetime.now(timezone.utc) + timedelta(seconds=self.total_seconds)).isoformat()

        event = {
            'summary': self.aim,
            'description': self.aim,
            'start': {
                'dateTime': start_time,
                'timeZone': 'Asia/Kolkata',
            },
            'end': {
                'dateTime': end_time,
                'timeZone': 'Asia/Kolkata',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 5},
                ],
            },
        }

        try:
            if not update:
                created_event = self.calendar_service.events().insert(calendarId='primary', body=event).execute()
                self.event_id = created_event.get('id')
                print("Event created:", created_event.get('htmlLink'))
            else:
                if self.event_id:
                    updated_event = self.calendar_service.events().update(calendarId='primary', eventId=self.event_id, body=event).execute()
                    print("Event updated:", updated_event.get('htmlLink'))
        except Exception as e:
            QMessageBox.critical(self, "Calendar Error", f"Failed to create/update calendar event: {e}")

    def display_random_remembrance(self):
        """
        Displays a randomly selected remembrance prompt with bold and italic styling.
        """
        if self.remembrance_prompts:
            remembrance = self.get_random_remembrance()
            formatted_remembrance = f"<span style='font-weight: bold; font-style: italic;'>{remembrance}</span>"
            self.prompt_label.setText(formatted_remembrance)
        else:
            self.prompt_label.repaint()

    def get_random_remembrance(self):
        """
        Retrieves a random remembrance prompt.

        Returns:
            str: A randomly selected quote.
        """
        return random.choice(self.remembrance_prompts)

    def check_presence(self):
        """
        Continuously checks for user activity and pauses the session if inactive for too long.
        """
        while True:
            if self.is_running and not self.is_paused:
                current_time = time.time()
                time_since_active = current_time - self.last_active_time

                if time_since_active > 300:
                    QTimer.singleShot(0, self.pause_session_from_thread)
            time.sleep(1)

    def pause_session_from_thread(self):
        """
        Safely pauses the session from a separate thread and notifies the user.
        """
        if self.is_running and not self.is_paused:
            self.pause_session()
            QMessageBox.warning(self, "Session Paused", "You have been inactive for too long. Session paused.")

    def record_activity(self):
        """
        Records user activity to reset the inactivity timer.
        """
        self.last_active_time = time.time()

    def update_timer_display(self):
        """
        Updates the countdown timer display.
        """
        minutes = self.remaining_seconds // 60
        seconds = self.remaining_seconds % 60
        time_str = f"{int(minutes)}:{int(seconds):02d} remaining"
        self.timer_display.setText(time_str)

    def update_timer(self):
        """
        Slot connected to QTimer to update the countdown every second.
        """
        if self.is_running and not self.is_paused:
            self._timer_countdown()

    def _timer_countdown(self):
        """
        Handles the countdown logic for the timer.
        """
        if self.remaining_seconds > 0:
            self.remaining_seconds -= 1
            self.elapsed_seconds += 1
            self.update_timer_display()
        else:
            self.qtimer.stop()
            if self.bell_sound:
                self.bell_sound.play()
            self.send_remembrance_notification()
            self.stop_session()

    def send_remembrance_notification(self):
        """
        Sends a notification with a remembrance prompt when the session ends.
        """
        if self.remembrance_prompts:
            remembrance = self.get_random_remembrance()
            QMessageBox.information(self, "Time's Up", f"Your session has ended.\n\n{remembrance}")
        else:
            QMessageBox.information(self, "Time's Up", "Your session has ended.")

    def pause_session(self):
        """
        Pauses the current session.
        """
        if self.is_running and not self.is_paused:
            self.is_paused = True
            self.is_running = False
            self.pause_button.setEnabled(False)
            self.resume_button.setEnabled(True)
            self.qtimer.stop()

    def resume_session(self):
        """
        Resumes a paused session.
        """
        if not self.is_running and self.is_paused:
            self.is_running = True
            self.is_paused = False
            self.last_active_time = time.time()
            if self.bell_sound:
                self.bell_sound.play()
            self.qtimer.start(1000)
            self.pause_button.setEnabled(True)
            self.resume_button.setEnabled(False)

    def stop_session(self):
        """
        Ends the current focus session and resets the UI.
        """
        if not self.is_running and not self.is_paused and not self.aim:
            return

        self.qtimer.stop()

        self.is_running = False
        self.is_paused = False

        if self.bell_sound:
            self.bell_sound.play()

        self.update_calendar_event_on_stop()

        self.aim = None
        self.start_time = None
        self.last_active_time = None
        self.total_pause_time = 0
        self.remaining_seconds = 0
        self.elapsed_seconds = 0
        self.event_id = None

        self.start_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        self.resume_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.aim_input.setEnabled(True)
        self.aim_input.clear()
        self.display_random_remembrance()
        self.timer_display.setText("0:00 remaining")
        self.timer_combo.setEnabled(True)

    def update_calendar_event_on_stop(self):
        """
        Updates the Google Calendar event's end time based on the actual session duration.
        """
        if not self.calendar_service or not self.event_id:
            return

        actual_end_time = datetime.now(timezone.utc).isoformat()

        event = {
            'end': {
                'dateTime': actual_end_time,
                'timeZone': 'UTC',
            },
        }

        try:
            updated_event = self.calendar_service.events().patch(
                calendarId='primary',
                eventId=self.event_id,
                body=event
            ).execute()
            print("Calendar event updated with actual end time:", updated_event.get('htmlLink'))
        except Exception as e:
            QMessageBox.critical(self, "Calendar Update Error", f"Failed to update calendar event: {e}")

    def mousePressEvent(self, event):
        """
        Overrides the mouse press event to record user activity.
        """
        if self.is_running:
            self.record_activity()

    def keyPressEvent(self, event):
        """
        Overrides the key press event to record user activity.
        """
        if self.is_running:
            self.record_activity()

    def refresh_quote(self):
        """
        Refreshes the displayed quote.
        """
        self.display_random_remembrance()

    def load_image(self):
        """
        Loads and displays an image in the UI.
        """
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        image_path = os.path.join(base_path, 'icons', 'picture.jpg')

        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            scaled_pixmap = pixmap.scaled(QSize(300, 150), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.image_label.setPixmap(scaled_pixmap)
        else:
            self.image_label.setText("Image not found.")
            self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

def main():
    """
    The main function to run the FocusSessionApp.
    """
    app = QApplication(sys.argv)

    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    app_icon_path = os.path.join(base_path, 'icons', 'selfremembering.ico')
    if not os.path.exists(app_icon_path):
        QMessageBox.warning(None, "Icon Missing", f"Application icon not found at {app_icon_path}. Taskbar icon may not display correctly.")
    else:
        app_icon = QIcon(app_icon_path)
        app.setWindowIcon(app_icon)

    window = FocusSessionApp(app_icon_path)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
