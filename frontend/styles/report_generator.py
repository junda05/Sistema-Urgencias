import os
import sys
import json
import re
import traceback
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QApplication, QWidget, QLabel,
                            QPushButton, QTabWidget, QDateEdit, QComboBox,
                            QLineEdit, QMessageBox, QFrame, QScrollArea, QSizePolicy,
                            QFileDialog)
from PyQt5.QtCore import Qt, QDate, QUrl, QTimer, QObject, pyqtSlot
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile, QWebEngineSettings
from PyQt5.QtWebChannel import QWebChannel
from frontend.styles.components import StyledMessageBox, StyledButton, StyledDialog, FormField
from backend.metrics_model import MetricsModel

class ReportGenerator(QDialog):
    """Class used to generate visual reports based on metrics data"""

    def __init__(self, parent=None, base_path=None):
        super().__init__(parent)
        self.setWindowTitle("Report Generator")
        self.setWindowFlags(self.windowFlags() | Qt.Window)

        # Set the initial size (almost full screen)
        desktop = QApplication.desktop()
        screen_rect = desktop.screenGeometry(desktop.primaryScreen())
        width = int(screen_rect.width() * 0.95)
        height = int(screen_rect.height() * 0.95)
        self.resize(width, height)

        # Base paths for resources
        self.base_path = base_path
        if not self.base_path:
            if getattr(sys, 'frozen', False):
                self.base_path = sys._MEIPASS
            else:
                self.base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        # Initial configuration
        self.current_mode = "group"  # Options: "individual", "group"
        self.start_date = datetime.now() - timedelta(days=365)
        self.end_date = datetime.now()
        self.selected_area = "all"
        self.selected_patient = None

        # Initialize the UI
        self.setup_ui()
        self.create_html_template()
        QTimer.singleShot(2000, self.configure_patient_search)

    def setup_ui(self):
        """Sets up the main user interface"""
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Container for the web view
        self.web_container = QWidget()
        self.web_layout = QVBoxLayout(self.web_container)
        self.web_layout.setContentsMargins(0, 0, 0, 0)

        # Configure QWebEngineView to display the report
        self.web_view = QWebEngineView()
        self.web_layout.addWidget(self.web_view)

        # Create the web channel object to allow JS <-> Python communication
        self.web_channel = QWebChannel()
        self.web_handler = WebHandler(self)
        self.web_channel.registerObject("handler", self.web_handler)
        self.web_view.page().setWebChannel(self.web_channel)

        # Add the web container to the main layout
        self.main_layout.addWidget(self.web_container)

        # Load the HTML template and apply the data
        self.create_html_template()

    def create_html_template(self):
        """Creates the base HTML template with placeholders for dynamic data"""
        html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Medical Reports Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
    <style>
        :root {
            --background-primary: #F0F5FA;
            --background-white: white;
            --background-warning: #FFF9C2;
            --background-error: #FFE8E8;
            --background-readonly: #E8F0F7;
            --background-transparent: transparent;
            --background-table-header: #E6E6E6;
            --background-secondary: #ffffff;
            --background-login: #4A7296;
            --background-header: #D5E5F3;
            --button-primary: #5385B7;
            --button-primary-hover: #659BD1;
            --button-danger: #B75353;
            --button-danger-hover: #D16565;
            --button-danger-hover-sky: #E1A5A5;
            --button-warning: #E6B800;
            --button-warning-hover: #FFCC00;
            --button-close: red;
            --button-transparent: rgba(0, 0, 0, 0.1);
            --button-secondary: #6c757d;
            --button-success: #28a745;
            --button-logout: #FF6B6B;
            --text-primary: #333333;
            --text-light: #555555;
            --text-white: white;
            --text-required: #D35400;
            --link: #0066cc;
            --text-secondary: #6c757d;
            --comparison-positive: #28a745;
            --comparison-negative: #B75353;
            --comparison-neutral: #E6B800;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: var(--background-primary);
            color: var(--text-primary);
        }
        .card {
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            background-color: var(--background-white);
            margin-bottom: 1rem;
        }
        .kpi-card {
            transition: all 0.3s ease;
            background-color: var(--background-white);
        }

        .kpi-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        }
        .btn-primary {
            background-color: var(--button-primary);
            color: white;
            border-radius: 5px;
            padding: 8px 16px;
            font-weight: 500;
            cursor: pointer;
        }
        .btn-primary:hover {
            background-color: var(--button-primary-hover);
        }
        .btn-success {
            background-color: var(--button-success);
            color: white;
            border-radius: 5px;
            padding: 8px 16px;
            font-weight: 500;
            cursor: pointer;
        }
        .btn-danger {
            background-color: var(--button-danger);
            color: var(--text-white);
        }

        .btn-danger:hover {
            background-color: var(--button-danger-hover);
        }
        .comparison-positive {
            color: var(--comparison-positive);
            font-weight: 600;
        }

        .comparison-negative {
            color: var(--comparison-negative);
            font-weight: 600;
        }

        .comparison-neutral {
            color: var(--comparison-neutral);
            font-weight: 600;
        }

        .status-icon {
            font-size: 1.5rem;
            margin-bottom: 0.5rem;
        }

        .status-success {
            color: var(--button-success);
        }

        .status-warning {
            color: var(--button-warning);
        }

        .status-danger {
            color: var(--button-danger);
        }
        .indicator-red {
            border-left: 4px solid var(--button-danger);
        }

        .indicator-yellow {
            border-left: 4px solid var(--button-warning);
        }

        .indicator-green {
            border-left: 4px solid var(--button-success);
        }
        .table-row-even {
            background-color: var(--background-white);
        }
        .table-row-odd {
            background-color: var(--background-primary);
        }
        .expandable-row {
            cursor: pointer;
        }
        .detail-row {
            display: none;
            background-color: var(--background-readonly);
        }

        .tab {
            transition: all 0.3s ease;
            color: var(--text-light);
        }
        .tab-active {
            border-bottom: 3px solid var(--button-primary);
            color: var(--button-primary);
        }
        .gauge-container {
            position: relative;
            margin: 0 auto;
        }
        .gauge-value {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 1.2rem;
            font-weight: bold;
        }

        .chart-container {
            position: relative;
            height: 350px;  /* Fixed height for the charts */
            width: 100%;
        }
    </style>
</head>
<body>
    <div class="container mx-auto px-4 py-6">
        <!-- Header -->
        <div class="flex justify-between items-center mb-6">
            <h1 class="text-3xl font-bold">Emergency Department Metrics Dashboard</h1>
            <div>
                <button id="exportPdf" class="btn-primary mr-2">
                    <i class="fas fa-file-pdf mr-2"></i>Export PDF
                </button>
            </div>
        </div>

        <!-- Main tabs -->
        <div class="border-b border-gray-200 mb-6">
            <div class="flex">
                <div id="tabGroup" class="px-4 py-2 font-medium tab-active cursor-pointer">Group Report</div>
                <div id="tabIndividual" class="px-4 py-2 font-medium text-gray-500 cursor-pointer">Individual Report</div>
            </div>
        </div>

        <!-- Control panel for filters -->
        <div class="card p-4 mb-6">
            <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div>
                    <label class="block text-sm font-medium mb-1">Start Date</label>
                    <input type="date" class="w-full rounded border p-2" value="{{START_DATE}}">
                </div>
                <div>
                    <label class="block text-sm font-medium mb-1">End Date</label>
                    <input type="date" class="w-full rounded border p-2" value="{{END_DATE}}">
                </div>

                <div id="individualFilter" class="col-span-2 hidden">
                    <label class="block text-sm font-medium text-[#333333] mb-1">Patient</label>
                    <div class="relative">
                        <input type="text" id="searchPatient" class="w-full border border-gray-300 rounded-md px-3 py-2" placeholder="Search by name or document ID...">
                        <div id="patientResults" class="absolute z-10 bg-white w-full mt-1 rounded-md shadow-lg hidden max-h-60 overflow-y-auto">
                            <!-- Search results are loaded here dynamically -->
                        </div>
                    </div>
                    <p class="text-xs text-gray-500 mt-1">Press Enter to search or type at least 3 characters</p>
                </div>

                <div>
                    <div id="areaSelector">
                        <label class="block text-sm font-medium text-[#333333] mb-1">Care Area</label>
                        <select class="w-full border border-gray-300 rounded-md px-3 py-2">
                            <option value="all"{{SELECTED_ALL}}>All areas</option>
                            <option value="Old wing"{{SELECTED_OLD_WING}}>Old wing</option>
                            <option value="Yellow"{{SELECTED_YELLOW}}>Yellow</option>
                            <option value="Pediatrics"{{SELECTED_PEDIATRICS}}>Pediatrics</option>
                            <option value="Hallways"{{SELECTED_HALLWAYS}}>Hallways</option>
                            <option value="Clinic"{{SELECTED_CLINIC}}>Clinic</option>
                            <option value="Waiting room"{{SELECTED_WAITING_ROOM}}>Waiting room</option>
                        </select>
                    </div>
                </div>
                <div class="flex items-end">
                    <button id="generateGroupReport" class="btn-primary w-full">
                        <i class="fas fa-sync-alt mr-2"></i>Generate Group Report
                    </button>
                    <button id="generateIndividualReport" class="btn-primary w-full hidden">
                        <i class="fas fa-sync-alt mr-2"></i>Generate Individual Report
                    </button>
                </div>
            </div>
        </div>

        <!-- Total Care Time (separate KPI card) -->
        <div class="bg-white rounded-lg shadow-md p-4 mb-6">
            <div class="flex justify-between items-start mb-2">
                <h3 class="text-lg font-semibold text-[#333333]">Total Care Time</h3>
                <div class="text-center">
                    <i class="fas fa-check-circle status-icon status-success"></i>
                </div>
            </div>
            <div id="individual-metrics-total" class="hidden">
                <div class="text-3xl font-bold text-[#333333] mb-1">{{TOTAL_TIME}} min</div>
                <div class="text-sm text-[#555555]">Classification time</div>
                <div class="mt-2 text-sm">
                    {{COMPARISON_TOTAL}}
                </div>
            </div>

            <div id="group-metrics-total">
                <div class="grid grid-cols-3 gap-2 mb-2">
                    <div>
                        <div class="text-2xl font-bold text-[#333333]">{{TOTAL_AVERAGE}} min</div>
                        <div class="text-xs text-[#555555]">Average</div>
                    </div>
                    <div>
                        <div class="text-2xl font-bold text-[#333333]">{{TOTAL_MEDIAN}} min</div>
                        <div class="text-xs text-[#555555]">Median</div>
                    </div>
                    <div>
                        <div class="text-2xl font-bold text-[#333333]">{{TOTAL_P90}} min</div>
                        <div class="text-xs text-[#555555]">P90</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Metrics and visualizations -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-6">
            <!-- Triage -->
            <div class="kpi-card rounded-lg shadow-md p-4 indicator-green">
                <div class="flex justify-between items-start mb-2">
                    <h3 class="text-lg font-semibold text-[#333333]">Triage</h3>
                    <div class="text-center">
                        <i class="fas fa-check-circle status-icon status-success"></i>
                    </div>
                </div>
                <div id="individual-metrics-triage" class="hidden">
                    <div class="text-3xl font-bold text-[#333333] mb-1">{{TRIAGE_TIME}} min</div>
                    <div class="text-sm text-[#555555]">Classification time</div>
                    <div class="mt-2 text-sm">
                        {{COMPARISON_TRIAGE}}
                    </div>
                </div>
                <div id="group-metrics-triage">
                    <div class="grid grid-cols-3 gap-2 mb-2">
                        <div>
                            <div class="text-2xl font-bold text-[#333333]">{{TRIAGE_AVERAGE}} min</div>
                            <div class="text-xs text-[#555555]">Average</div>
                        </div>
                        <div>
                            <div class="text-2xl font-bold text-[#333333]">{{TRIAGE_MEDIAN}} min</div>
                            <div class="text-xs text-[#555555]">Median</div>
                        </div>
                        <div>
                            <div class="text-2xl font-bold text-[#333333]">{{TRIAGE_P90}} min</div>
                            <div class="text-xs text-[#555555]">P90</div>
                        </div>
                    </div>
                </div>
                <div class="mt-2 text-xs text-[#555555]">
                    Time from "Not completed" to classification
                </div>
            </div>

            <!-- Admission Consult -->
            <div class="kpi-card rounded-lg shadow-md p-4 indicator-green">
                <div class="flex justify-between items-start mb-2">
                    <h3 class="text-lg font-semibold text-[#333333]">Admission Consult</h3>
                    <div class="text-center">
                        <i class="fas fa-check-circle status-icon status-success"></i>
                    </div>
                </div>
                <div id="individual-metrics-admission" class="hidden">
                    <div class="text-3xl font-bold text-[#333333] mb-1">{{ADMISSION_TIME}} min</div>
                    <div class="text-sm text-[#555555]">Care time</div>
                    <div class="mt-2 text-sm">
                        {{COMPARISON_ADMISSION}}
                    </div>
                </div>
                <div id="group-metrics-admission">
                    <div class="grid grid-cols-3 gap-2 mb-2">
                        <div>
                            <div class="text-2xl font-bold text-[#333333]">{{ADMISSION_AVERAGE}} min</div>
                            <div class="text-xs text-[#555555]">Average</div>
                        </div>
                        <div>
                            <div class="text-2xl font-bold text-[#333333]">{{ADMISSION_MEDIAN}} min</div>
                            <div class="text-xs text-[#555555]">Median</div>
                        </div>
                        <div>
                            <div class="text-2xl font-bold text-[#333333]">{{ADMISSION_P90}} min</div>
                            <div class="text-xs text-[#555555]">P90</div>
                        </div>
                    </div>
                </div>
                <div class="mt-2 text-xs text-[#555555]">
                    Time from "Not completed" to "Completed"
                </div>
            </div>

            <!-- Laboratories -->
            <div class="kpi-card rounded-lg shadow-md p-4 indicator-yellow">
                <div class="flex justify-between items-start mb-2">
                    <h3 class="text-lg font-semibold text-[#333333]">Laboratories</h3>
                    <div class="text-center">
                        <i class="fas fa-exclamation-triangle status-icon status-warning"></i>
                    </div>
                </div>
                <div id="individual-metrics-lab" class="hidden">
                    <div class="grid grid-cols-2 gap-2">
                        <div>
                            <div class="text-xl font-bold text-[#333333] mb-1">{{LABS_TIME_REQUEST}} min</div>
                            <div class="text-xs text-[#555555]">Request to awaiting</div>
                        </div>
                        <div>
                            <div class="text-xl font-bold text-[#333333] mb-1">{{LABS_TIME_RESULTS}} min</div>
                            <div class="text-xs text-[#555555]">Awaiting to results</div>
                        </div>
                    </div>
                    <div class="mt-2 text-sm">
                        {{COMPARISON_LABS}}
                    </div>
                </div>
                <div id="group-metrics-lab">
                    <div class="grid grid-cols-2 gap-2 mb-2">
                        <div>
                            <div class="text-sm font-medium text-[#333333]">Not completed to awaiting</div>
                            <div class="grid grid-cols-3 gap-1">
                                <div>
                                    <div class="text-base font-bold text-[#333333]">{{LABS_AVERAGE_REQ}} min</div>
                                    <div class="text-xs text-[#555555]">Avg</div>
                                </div>
                                <div>
                                    <div class="text-base font-bold text-[#333333]">{{LABS_MEDIAN_REQ}} min</div>
                                    <div class="text-xs text-[#555555]">Med</div>
                                </div>
                                <div>
                                    <div class="text-base font-bold text-[#333333]">{{LABS_P90_REQ}} min</div>
                                    <div class="text-xs text-[#555555]">P90</div>
                                </div>
                            </div>
                        </div>
                        <div>
                            <div class="text-sm font-medium text-[#333333]">Awaiting to results:</div>
                            <div class="grid grid-cols-3 gap-1">
                                <div>
                                    <div class="text-base font-bold text-[#333333]">{{LABS_AVERAGE_RES}} min</div>
                                    <div class="text-xs text-[#555555]">Avg</div>
                                </div>
                                <div>
                                    <div class="text-base font-bold text-[#333333]">{{LABS_MEDIAN_RES}} min</div>
                                    <div class="text-xs text-[#555555]">Med</div>
                                </div>
                                <div>
                                    <div class="text-base font-bold text-[#333333]">{{LABS_P90_RES}} min</div>
                                    <div class="text-xs text-[#555555]">P90</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Diagnostic Imaging -->
            <div class="kpi-card rounded-lg shadow-md p-4 indicator-green">
                <div class="flex justify-between items-start mb-2">
                    <h3 class="text-lg font-semibold text-[#333333]">Diagnostic Imaging</h3>
                    <div class="text-center">
                        <i class="fas fa-check-circle status-icon status-success"></i>
                    </div>
                </div>
                <div id="individual-metrics-imaging" class="hidden">
                    <div class="grid grid-cols-2 gap-2">
                        <div>
                            <div class="text-xl font-bold text-[#333333] mb-1">{{IMAGING_TIME_REQUEST}} min</div>
                            <div class="text-xs text-[#555555]">Not completed to awaiting</div>
                        </div>
                        <div>
                            <div class="text-xl font-bold text-[#333333] mb-1">{{IMAGING_TIME_RESULTS}} min</div>
                            <div class="text-xs text-[#555555]">Awaiting to results</div>
                        </div>
                    </div>
                    <div class="mt-2 text-sm">
                        {{COMPARISON_IMAGING}}
                    </div>
                </div>
                <div id="group-metrics-imaging">
                    <div class="grid grid-cols-2 gap-2 mb-2">
                        <div>
                            <div class="text-sm font-medium text-[#333333]">Not completed to awaiting</div>
                            <div class="grid grid-cols-3 gap-1">
                                <div>
                                    <div class="text-base font-bold text-[#333333]">{{IMAGING_AVERAGE_REQ}} min</div>
                                    <div class="text-xs text-[#555555]">Avg</div>
                                </div>
                                <div>
                                    <div class="text-base font-bold text-[#333333]">{{IMAGING_MEDIAN_REQ}} min</div>
                                    <div class="text-xs text-[#555555]">Med</div>
                                </div>
                                <div>
                                    <div class="text-base font-bold text-[#333333]">{{IMAGING_P90_REQ}} min</div>
                                    <div class="text-xs text-[#555555]">P90</div>
                                </div>
                            </div>
                        </div>
                        <div>
                            <div class="text-sm font-medium text-[#333333]">Awaiting to results:</div>
                            <div class="grid grid-cols-3 gap-1">
                                <div>
                                    <div class="text-base font-bold text-[#333333]">{{IMAGING_AVERAGE_RES}} min</div>
                                    <div class="text-xs text-[#555555]">Avg</div>
                                </div>
                                <div>
                                    <div class="text-base font-bold text-[#333333]">{{IMAGING_MEDIAN_RES}} min</div>
                                    <div class="text-xs text-[#555555]">Med</div>
                                </div>
                                <div>
                                    <div class="text-base font-bold text-[#333333]">{{IMAGING_P90_RES}} min</div>
                                    <div class="text-xs text-[#555555]">P90</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Specialist Consult -->
            <div class="kpi-card rounded-lg shadow-md p-4 indicator-yellow">
                <div class="flex justify-between items-start mb-2">
                    <h3 class="text-lg font-semibold text-[#333333]">Specialist Consult</h3>
                    <div class="text-center">
                        <i class="fas fa-exclamation-triangle status-icon status-warning"></i>
                    </div>
                </div>
                <div id="individual-metrics-specialist" class="hidden">
                    <div class="grid grid-cols-2 gap-2">
                        <div>
                            <div class="text-xl font-bold text-[#333333] mb-1">{{SPECIALIST_TIME_OPENING}} min</div>
                            <div class="text-xs text-[#555555]">Not opened to open</div>
                        </div>
                        <div>
                            <div class="text-xl font-bold text-[#333333] mb-1">{{SPECIALIST_TIME_COMPLETION}} min</div>
                            <div class="text-xs text-[#555555]">Open to completed</div>
                        </div>
                    </div>
                    <div class="mt-2 text-sm">
                        {{COMPARISON_SPECIALIST}}
                    </div>
                </div>
                <div id="group-metrics-specialist">
                    <div class="grid grid-cols-2 gap-2 mb-2">
                        <div>
                            <div class="text-sm font-medium text-[#333333]">Not opened to open</div>
                            <div class="grid grid-cols-3 gap-1">
                                <div>
                                    <div class="text-base font-bold text-[#333333]">{{SPECIALIST_AVERAGE_OPEN}} min</div>
                                    <div class="text-xs text-[#555555]">Avg</div>
                                </div>
                                <div>
                                    <div class="text-base font-bold text-[#333333]">{{SPECIALIST_MEDIAN_OPEN}} min</div>
                                    <div class="text-xs text-[#555555]">Med</div>
                                </div>
                                <div>
                                    <div class="text-base font-bold text-[#333333]">{{SPECIALIST_P90_OPEN}} min</div>
                                    <div class="text-xs text-[#555555]">P90</div>
                                </div>
                            </div>
                        </div>
                        <div>
                            <div class="text-sm font-medium text-[#333333]">Open to completed:</div>
                            <div class="grid grid-cols-3 gap-1">
                                <div>
                                    <div class="text-base font-bold text-[#333333]">{{SPECIALIST_AVERAGE_DONE}} min</div>
                                    <div class="text-xs text-[#555555]">Avg</div>
                                </div>
                                <div>
                                    <div class="text-base font-bold text-[#333333]">{{SPECIALIST_MEDIAN_DONE}} min</div>
                                    <div class="text-xs text-[#555555]">Med</div>
                                </div>
                                <div>
                                    <div class="text-base font-bold text-[#333333]">{{SPECIALIST_P90_DONE}} min</div>
                                    <div class="text-xs text-[#555555]">P90</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Reassessment -->
            <div class="kpi-card rounded-lg shadow-md p-4 indicator-red">
                <div class="flex justify-between items-start mb-2">
                    <h3 class="text-lg font-semibold text-[#333333]">Reassessment</h3>
                    <div class="text-center">
                        <i class="fas fa-times-circle status-icon status-danger"></i>
                    </div>
                </div>
                <div id="individual-metrics-reassessment" class="hidden">
                    <div class="text-3xl font-bold text-[#333333] mb-1">{{REASSESSMENT_TIME}} min</div>
                    <div class="text-sm text-[#555555]">Pending time</div>
                    <div class="mt-2 text-sm">
                        {{COMPARISON_REASSESSMENT}}
                    </div>
                </div>
                <div id="group-metrics-reassessment">
                    <div class="grid grid-cols-3 gap-2 mb-2">
                        <div>
                            <div class="text-2xl font-bold text-[#333333]">{{REASSESSMENT_AVERAGE}} min</div>
                            <div class="text-xs text-[#555555]">Average</div>
                        </div>
                        <div>
                            <div class="text-2xl font-bold text-[#333333]">{{REASSESSMENT_MEDIAN}} min</div>
                            <div class="text-xs text-[#555555]">Median</div>
                        </div>
                        <div>
                            <div class="text-2xl font-bold text-[#333333]">{{REASSESSMENT_P90}} min</div>
                            <div class="text-xs text-[#555555]">P90</div>
                        </div>
                    </div>
                </div>
                <div class="mt-2 text-xs text-[#555555]">
                    Time from "not completed" to "completed"
                </div>
            </div>
        </div>

        <!-- Charts and detailed data -->
        <div id="group-charts" class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <!-- Timeline chart -->
            <div class="card p-4">
                <h2 class="text-xl font-semibold mb-4">Timeline Evolution</h2>
                <div>
                    <canvas id="timelineChart" height="300"></canvas>
                </div>
            </div>

            <!-- Comparative bar chart -->
            <div class="card p-4">
                <h2 class="text-xl font-semibold mb-4">Average times per stage</h2>
                <div>
                    <canvas id="barChart" height="300"></canvas>
                </div>
            </div>
        </div>

        <!-- SLA compliance metrics -->
        <div id="sla-compliance">
            <h2 class="text-2xl font-bold mb-4">SLA Compliance</h2>
            <div class="grid grid-cols-2 md:grid-cols-6 gap-4 mb-6">
                <!-- Triage -->
                <div class="card p-4 text-center">
                    <h3 class="text-lg font-medium mb-2">Triage</h3>
                    <div class="gauge-container w-24 h-24 mx-auto">
                        <canvas id="gaugeTriage"></canvas>
                        <div class="gauge-value">{{COMPLIANCE_TRIAGE}}</div>
                    </div>
                </div>
                <!-- Admission Consult -->
                <div class="card p-4 text-center">
                    <h3 class="text-lg font-medium mb-2">Admission</h3>
                    <div class="gauge-container w-24 h-24 mx-auto">
                        <canvas id="gaugeAdmission"></canvas>
                        <div class="gauge-value">{{COMPLIANCE_ADMISSION}}</div>
                    </div>
                </div>
                <!-- Laboratories -->
                <div class="card p-4 text-center">
                    <h3 class="text-lg font-medium mb-2">Labs</h3>
                    <div class="gauge-container w-24 h-24 mx-auto">
                        <canvas id="gaugeLab"></canvas>
                        <div class="gauge-value">{{COMPLIANCE_LABS}}</div>
                    </div>
                </div>
                <!-- Imaging -->
                <div class="card p-4 text-center">
                    <h3 class="text-lg font-medium mb-2">Imaging</h3>
                    <div class="gauge-container w-24 h-24 mx-auto">
                        <canvas id="gaugeImaging"></canvas>
                        <div class="gauge-value">{{COMPLIANCE_IMAGING}}</div>
                    </div>
                </div>
                <!-- Specialist Consult -->
                <div class="card p-4 text-center">
                    <h3 class="text-lg font-medium mb-2">Specialist</h3>
                    <div class="gauge-container w-24 h-24 mx-auto">
                        <canvas id="gaugeSpecialist"></canvas>
                        <div class="gauge-value">{{COMPLIANCE_SPECIALIST}}</div>
                    </div>
                </div>
                <!-- Reassessment -->
                <div class="card p-4 text-center">
                    <h3 class="text-lg font-medium mb-2">Reassessment</h3>
                    <div class="gauge-container w-24 h-24 mx-auto">
                        <canvas id="gaugeReassessment"></canvas>
                        <div class="gauge-value">{{COMPLIANCE_REASSESSMENT}}</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Charts for the individual report -->
        <div id="individual-charts" class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6 hidden">
            <!-- Comparison with the area -->
            <div class="bg-white rounded-lg shadow-md p-4">
                <h3 class="text-lg font-semibold text-[#333333] mb-4">Comparison with the area</h3>
                <div class="chart-container">
                    <canvas id="comparisonChart"></canvas>
                </div>
            </div>

            <!-- Comparison with all areas -->
            <div class="bg-white rounded-lg shadow-md p-4">
                <h3 class="text-lg font-semibold text-[#333333] mb-4">Comparison with all areas</h3>
                <div class="chart-container">
                    <canvas id="allAreasChart"></canvas>
                </div>
            </div>
        </div>

        <!-- Individual patient table -->
        <div id="individual-patient-table" class="bg-white rounded-lg shadow-md p-4 mb-6 hidden">
            <h3 class="text-lg font-semibold text-[#333333] mb-4">Patient detail</h3>
            <div class="overflow-x-auto">
                <table class="min-w-full divide-y divide-gray-200">
                    <thead>
                        <tr>
                            <th class="px-4 py-3 bg-[#E6E6E6] text-left text-xs font-medium text-[#333333] uppercase tracking-wider">Patient</th>
                            <th class="px-4 py-3 bg-[#E6E6E6] text-left text-xs font-medium text-[#333333] uppercase tracking-wider">Document ID</th>
                            <th class="px-4 py-3 bg-[#E6E6E6] text-left text-xs font-medium text-[#333333] uppercase tracking-wider">Area</th>
                            <th class="px-4 py-3 bg-[#E6E6E6] text-left text-xs font-medium text-[#333333] uppercase tracking-wider">Admission</th>
                            <th class="px-4 py-3 bg-[#E6E6E6] text-left text-xs font-medium text-[#333333] uppercase tracking-wider">Total Time</th>
                            <th class="px-4 py-3 bg-[#E6E6E6] text-left text-xs font-medium text-[#333333] uppercase tracking-wider">Status</th>
                            <th class="px-4 py-3 bg-[#E6E6E6] text-left text-xs font-medium text-[#333333] uppercase tracking-wider"></th>
                        </tr>
                    </thead>
                    <tbody class="bg-white divide-y divide-gray-200">
                        <tr class="expandable-row table-row-odd">
                            <td class="px-4 py-3 whitespace-nowrap">John Michael Smith Jones</td>
                            <td class="px-4 py-3 whitespace-nowrap">1114565784</td>
                            <td class="px-4 py-3 whitespace-nowrap">Yellow</td>
                            <td class="px-4 py-3 whitespace-nowrap">2025-05-02 09:39:27</td>
                            <td class="px-4 py-3 whitespace-nowrap">56 min</td>
                            <td class="px-4 py-3 whitespace-nowrap">
                                <span class="px-2 py-1 text-xs rounded-full bg-green-100 text-green-800">Discharged</span>
                            </td>
                            <td class="px-4 py-3 whitespace-nowrap text-right">
                                <button class="text-[#0066cc] hover:text-[#004c99]">
                                    <i class="fas fa-chevron-down"></i>
                                </button>
                            </td>
                        </tr>
                        <tr class="detail-row" style="display: table-row;">
                            <td colspan="7" class="px-4 py-3">
                                <div class="grid grid-cols-3 gap-4">
                                    <div>
                                        <h4 class="font-medium text-[#333333]">Triage</h4>
                                        <p class="text-sm">Time: 12 min <span class="comparison-positive">(-5 min)</span></p>
                                        <p class="text-sm">Status: <i class="fas fa-check-circle text-[#28a745]"></i> Completed</p>
                                    </div>
                                    <div>
                                        <h4 class="font-medium text-[#333333]">Admission Consult</h4>
                                        <p class="text-sm">Time: 28 min <span class="comparison-negative">(+8 min)</span></p>
                                        <p class="text-sm">Status: <i class="fas fa-check-circle text-[#28a745]"></i> Completed</p>
                                    </div>
                                    <div>
                                        <h4 class="font-medium text-[#333333]">Laboratories</h4>
                                        <p class="text-sm">Total time: 55 min <span class="comparison-positive">(-10 min)</span></p>
                                        <p class="text-sm">Status: <i class="fas fa-check-circle text-[#28a745]"></i> Completed</p>
                                    </div>
                                    <div>
                                        <h4 class="font-medium text-[#333333]">Imaging</h4>
                                        <p class="text-sm">Total time: 53 min <span class="comparison-positive">(-17 min)</span></p>
                                        <p class="text-sm">Status: <i class="fas fa-check-circle text-[#28a745]"></i> Completed</p>
                                    </div>
                                    <div>
                                        <h4 class="font-medium text-[#333333]">Specialist Consult</h4>
                                        <p class="text-sm">Time: 22 min <span class="comparison-negative">(+7 min)</span></p>
                                        <p class="text-sm">Status: <i class="fas fa-exclamation-triangle text-[#E6B800]"></i> Open</p>
                                    </div>
                                    <div>
                                        <h4 class="font-medium text-[#333333]">Reassessment</h4>
                                        <p class="text-sm">Time: Pending</p>
                                        <p class="text-sm">Status: <i class="fas fa-times-circle text-[#B75353]"></i> Not completed</p>
                                    </div>
                                </div>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        // Initialize the web channel for communication with Python
        window.onload = function() {
            new QWebChannel(qt.webChannelTransport, function(channel) {
                window.handler = channel.objects.handler;
                console.log("QWebChannel established successfully");

                // Set up event listeners
                setupEventListeners();

                // Initialize the charts
                initializeCharts();
            });
        };

        function setupEventListeners() {
            // Export to PDF
            document.getElementById('exportPdf').addEventListener('click', function() {
                window.handler.exportPdf();
            });

            // Generate group report
            document.getElementById('generateGroupReport').addEventListener('click', function() {
                // Get date inputs
                const dateInputs = document.querySelectorAll('input[type="date"]');
                const startDate = dateInputs[0].value;
                const endDate = dateInputs[1].value;

                // Get area selector safely
                const areaSelect = document.querySelector('#areaSelector select');
                const area = areaSelect ? areaSelect.value : 'all';

                console.log("Generating group report with:", startDate, endDate, area);
                window.handler.generateReportWithFilters(startDate, endDate, area);
            });

            // Generate individual report
            document.getElementById('generateIndividualReport').addEventListener('click', function() {
                const searchInput = document.getElementById('searchPatient');
                if (!searchInput || !searchInput.value.trim()) {
                    alert("Please select a patient before generating the individual report.");
                    return;
                }

                // Force individual mode BEFORE generating the report
                document.body.setAttribute('data-current-mode', 'individual');

                // Activate the individual tab explicitly
                const tabIndividual = document.getElementById('tabIndividual');
                if (tabIndividual) {
                    tabIndividual.classList.add('tab-active');
                    tabIndividual.classList.remove('text-gray-500');

                    const tabGroup = document.getElementById('tabGroup');
                    if (tabGroup) {
                        tabGroup.classList.remove('tab-active');
                        tabGroup.classList.add('text-gray-500');
                    }
                }

                // Get date inputs for time range (might be used for historical data)
                const dateInputs = document.querySelectorAll('input[type="date"]');
                const startDate = dateInputs[0].value;
                const endDate = dateInputs[1].value;

                console.log("Generating individual report for patient:", searchInput.value);
                window.handler.generateIndividualReport(startDate, endDate);
            });

            // Tab functionality
            document.getElementById('tabIndividual').addEventListener('click', function() {
                this.classList.add('tab-active');
                this.classList.remove('text-gray-500');

                const tabGroup = document.getElementById('tabGroup');
                if (tabGroup) {
                    tabGroup.classList.remove('tab-active');
                    tabGroup.classList.add('text-gray-500');
                }

                // Apply the updated state
                applyCurrentState();
            });

            document.getElementById('tabGroup').addEventListener('click', function() {
                this.classList.add('tab-active');
                this.classList.remove('text-gray-500');

                const tabIndividual = document.getElementById('tabIndividual');
                if (tabIndividual) {
                    tabIndividual.classList.remove('tab-active');
                    tabIndividual.classList.add('text-gray-500');
                }

                // Apply the updated state
                applyCurrentState();
            });

            // Autocomplete functionality
            document.getElementById('searchPatient').addEventListener('focus', function() {
                document.getElementById('patientResults').classList.remove('hidden');
            });

            document.getElementById('searchPatient').addEventListener('blur', function() {
                setTimeout(function() {
                    document.getElementById('patientResults').classList.add('hidden');
                }, 200);
            });

            document.querySelectorAll('#patientResults div').forEach(item => {
                item.addEventListener('click', function() {
                    document.getElementById('searchPatient').value = this.textContent;
                    document.getElementById('patientResults').classList.add('hidden');
                });
            });

            // Expandable row functionality
            document.querySelectorAll('.expandable-row').forEach(row => {
                row.addEventListener('click', function() {
                    const detailRow = this.nextElementSibling;
                    if (detailRow.style.display === 'table-row') {
                        detailRow.style.display = 'none';
                        this.querySelector('i').classList.remove('fa-chevron-up');
                        this.querySelector('i').classList.add('fa-chevron-down');
                    } else {
                        detailRow.style.display = 'table-row';
                        this.querySelector('i').classList.remove('fa-chevron-down');
                        this.querySelector('i').classList.add('fa-chevron-up');
                    }
                });
            });
        }

        function updateTimelineChart(labels, data, grouping) {
            // Update the timeline chart with the new data
            window.timelineChart.data.labels = labels;
            window.timelineChart.data.datasets[0].data = data;

            // Update chart title to indicate grouping
            let titleText = 'Timeline Evolution';
            if (grouping === 'hourly') {
                titleText += ' (Hourly)';
            } else if (grouping === 'daily') {
                titleText += ' (Daily)';
            } else if (grouping === 'weekly') {
                titleText += ' (Weekly)';
            } else if (grouping === 'monthly') {
                titleText += ' (Monthly)';
            } else if (grouping === 'quarterly') {
                titleText += ' (Quarterly)';
            }

            window.timelineChart.options.plugins.title = {
                display: true,
                text: titleText,
                font: {
                    size: 16,
                    weight: 'bold'
                }
            };

            // Update x-axis to handle different groupings
            if (labels.length > 20) {
                window.timelineChart.options.scales.x.ticks = {
                    autoSkip: true,
                    maxTicksLimit: 20
                };
            } else {
                window.timelineChart.options.scales.x.ticks = {
                    autoSkip: false
                };
            }

            window.timelineChart.update();
        }

        const colorPalette = [
            'rgba(34, 197, 94, 0.7)',  // Green for Triage
            'rgba(59, 130, 246, 0.7)',  // Blue for Admission Consult
            'rgba(245, 158, 11, 0.7)',  // Orange for Labs
            'rgba(139, 92, 246, 0.7)',  // Purple for Imaging
            'rgba(236, 72, 153, 0.7)',  // Pink for Specialist Consult
            'rgba(239, 68, 68, 0.7)'    // Red for Reassessment
        ];

        function initializeCharts() {
            // Common configuration for the gauge charts
            const gaugeOptions = {
                type: 'doughnut',
                plugins: [{
                    beforeDraw: function(chart) {
                        if (chart.config.options.elements.center) {
                            // Get ctx from string
                            var ctx = chart.ctx;
                            // Get options from the center object in options
                            var centerConfig = chart.config.options.elements.center;
                            var fontSize = centerConfig.fontSize || 50;
                            var text = centerConfig.text;
                            var color = centerConfig.color || '#000';
                            // Set font settings to draw it correctly
                            ctx.textAlign = 'center';
                            ctx.textBaseline = 'middle';
                            var centerX = ((chart.chartArea.left + chart.chartArea.right) / 2);
                            var centerY = ((chart.chartArea.top + chart.chartArea.bottom) / 2);
                            ctx.font = fontSize + "px Arial";
                            ctx.fillStyle = color;
                            // Draw text in center
                            ctx.fillText(text, centerX, centerY);
                        }
                    }
                }],
                options: {
                    cutout: '70%',
                    responsive: true,
                    maintainAspectRatio: true,
                    legend: {
                        display: false
                    },
                    tooltip: {
                        enabled: false
                    }
                }
            };

            // Sample data for the charts
            const timelineLabels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']; // Replace with real data
            const timelineData = [12, 15, 18, 14, 11, 13];                     // Replace with real data

            const barLabels = ['Triage', 'Admission consult', 'Laboratories', 'Diagnostic imaging', 'Specialist consult', 'Reassessment'];      // Replace with real data
            const barData = [5, 10, 15, 8, 12, 7];                            // Replace with real data

            // Initialize the timeline chart
            const timelineCtx = document.getElementById('timelineChart').getContext('2d');
            window.timelineChart = new Chart(timelineCtx, {
                type: 'line',
                data: {
                    labels: timelineLabels,
                    datasets: [{
                        data: timelineData,
                        fill: false,
                        borderColor: '#5385B7',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false  // This is the key line that hides the legend
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Minutes'
                            }
                        }
                    }
                }
            });

            // Initialize the comparative bar chart
            const barCtx = document.getElementById('barChart').getContext('2d');
            window.barChart = new Chart(barCtx, {
                type: 'bar',
                data: {
                    labels: ['Triage', 'Admission consult', 'Laboratories', 'Diagnostic imaging', 'Specialist consult', 'Reassessment'],
                    datasets: [{
                        data: [
                            {{CHART_TRIAGE_AVERAGE}},
                            {{CHART_ADMISSION_AVERAGE}},
                            {{CHART_LABS_AVERAGE}},
                            {{CHART_IMAGING_AVERAGE}},
                            {{CHART_SPECIALIST_AVERAGE}},
                            {{CHART_REASSESSMENT_AVERAGE}}
                        ],
                        backgroundColor: colorPalette, // Use the shared color palette
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Minutes'
                            }
                        }
                    }
                }
            });

            // Initialize the gauge charts with their real values and matching colors
            createGauge('gaugeTriage', {{GAUGE_TRIAGE}}, 0);
            createGauge('gaugeAdmission', {{GAUGE_ADMISSION}}, 1);
            createGauge('gaugeLab', {{GAUGE_LABS}}, 2);
            createGauge('gaugeImaging', {{GAUGE_IMAGING}}, 3);
            createGauge('gaugeSpecialist', {{GAUGE_SPECIALIST}}, 4);
            createGauge('gaugeReassessment', {{GAUGE_REASSESSMENT}}, 5);
        }

        function createGauge(elementId, value, colorIndex) {
            const ctx = document.getElementById(elementId).getContext('2d');
            const gaugeChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    datasets: [{
                        data: [value, 100 - value],
                        backgroundColor: [
                            colorPalette[colorIndex], // Use the matching color from the palette
                            '#ecf0f1'
                        ],
                        borderWidth: 0
                    }]
                },
                options: {
                    cutout: '70%',
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            enabled: false
                        }
                    },
                    animation: {
                        animateRotate: true,
                        animateScale: false
                    },
                    elements: {
                        center: {
                            text: value + '%',
                            color: '#333',
                            fontSize: 20
                        }
                    }
                }
            });

            return gaugeChart;
        }

        // Set the initial state according to the active tab
        document.addEventListener('DOMContentLoaded', function() {
            // Check which tab is active initially
            const groupTabActive = document.getElementById('tabGroup').classList.contains('tab-active');

            // Apply the correct initial visibility
            if (groupTabActive) {
                document.getElementById('tabGroup').click();
            } else {
                document.getElementById('tabIndividual').click();
            }
        });

        // Dedicated function to apply the correct state at any time
        function applyCurrentState() {
            const groupTabActive = document.getElementById('tabGroup').classList.contains('tab-active');

            // Handle the visibility of the individual filter
            const individualFilter = document.getElementById('individualFilter');
            if (individualFilter) {
                if (groupTabActive) {
                    individualFilter.classList.add('hidden');
                } else {
                    individualFilter.classList.remove('hidden');
                }
            }

            // Handle the visibility of the metrics
            if (groupTabActive) {
                document.getElementById('generateGroupReport').classList.remove('hidden');
                document.getElementById('generateIndividualReport').classList.add('hidden');
                document.querySelectorAll('[id^="individual-metrics-"]').forEach(el => el.classList.add('hidden'));
                document.querySelectorAll('[id^="group-metrics-"]').forEach(el => el.classList.remove('hidden'));

                const groupCharts = document.getElementById('group-charts');
                if (groupCharts) groupCharts.classList.remove('hidden');

                const slaCompliance = document.getElementById('sla-compliance');
                if (slaCompliance) slaCompliance.classList.remove('hidden');

                const individualCharts = document.getElementById('individual-charts');
                if (individualCharts) individualCharts.classList.add('hidden');

                const individualPatientTable = document.getElementById('individual-patient-table');
                if (individualPatientTable) individualPatientTable.classList.add('hidden');
            } else {
                document.getElementById('generateGroupReport').classList.add('hidden');
                document.getElementById('generateIndividualReport').classList.remove('hidden');
                document.querySelectorAll('[id^="individual-metrics-"]').forEach(el => el.classList.remove('hidden'));
                document.querySelectorAll('[id^="group-metrics-"]').forEach(el => el.classList.add('hidden'));

                const groupCharts = document.getElementById('group-charts');
                if (groupCharts) groupCharts.classList.add('hidden');

                const slaCompliance = document.getElementById('sla-compliance');
                if (slaCompliance) slaCompliance.classList.add('hidden');

                const individualCharts = document.getElementById('individual-charts');
                if (individualCharts) individualCharts.classList.remove('hidden');

                const individualPatientTable = document.getElementById('individual-patient-table');
                if (individualPatientTable) individualPatientTable.classList.remove('hidden');
            }
        }

        // Call the function immediately and also on DOMContentLoaded
        applyCurrentState();
        window.addEventListener('load', applyCurrentState);
    </script>
</body>
</html>
        """

        # Cache the template
        self.html_template = html_template

        # Load the data and update the template
        self.update_report_data()

    def update_report_data(self):
        """Updates the report data with the metrics obtained from the database"""
        if not hasattr(self, 'html_template'):
            return

        print(f"Updating report data. Current mode: {self.current_mode}")
        print(f"Selected patient: {self.selected_patient}")

        # Get real metrics data from the model
        data = self.get_real_data()
        if self.current_mode == "individual" and self.selected_patient:
            if not data or 'charts' not in data or not data['charts']:
                print("WARNING: No chart data available for the individual patient")
                # Use sample data to avoid errors
                if 'charts' not in data:
                    data['charts'] = {}
                if 'comparison' not in data['charts']:
                    data['charts']['comparison'] = {
                        "labels": ["Triage", "Admission Consult", "Laboratories", "Imaging", "Specialist Consult", "Reassessment"],
                        "patient_data": [0, 0, 0, 0, 0, 0],
                        "area_data": [0, 0, 0, 0, 0, 0]
                    }
                if 'all_areas' not in data['charts']:
                    data['charts']['all_areas'] = {
                        "labels": ["Triage", "Admission Consult", "Laboratories", "Imaging", "Specialist Consult", "Reassessment"],
                        "patient_data": [0, 0, 0, 0, 0, 0],
                        "overall_data": [0, 0, 0, 0, 0, 0]
                    }

        # Prepare the data to be replaced in the HTML
        html_content = self.html_template

        # Replace the placeholders with real data
        html_content = self.replace_data_in_html(html_content, data)

        # Load the updated HTML content into the web view
        self.web_view.setHtml(html_content, baseUrl=QUrl.fromLocalFile(self.base_path + "/"))

        # Make sure the correct mode is kept after loading
        # through additional JavaScript
        if self.current_mode == "individual" and self.selected_patient:
            js_code = """
            setTimeout(function() {
                // Make sure the individual view is active
                const tabIndividual = document.getElementById('tabIndividual');
                if (tabIndividual && !tabIndividual.classList.contains('tab-active')) {
                    tabIndividual.click();
                }
            }, 200);
            """
            self.web_view.page().runJavaScript(js_code)

    def search_patient(self, search_term):
        """Searches patients by name or document ID"""
        try:
            from backend.database import PatientModel
            model = PatientModel()

            # Create a specific instance for searching, independent of other filters
            # This guarantees the patient search is not affected by group filters
            print(f"Performing patient search with term: '{search_term}'")

            # The search must be independent of any area or date filter
            results = model.search_patients(search_term)
            print(f"Search results: {len(results)} patients found")
            return results
        except Exception as e:
            print(f"Error searching patient: {str(e)}")
            traceback.print_exc()
            self.show_warning_message("Error", f"Error searching patient: {str(e)}")
            return []

    def show_search_results(self, results):
        """Updates the interface with the search results using JavaScript"""
        try:
            # Generate the HTML for the results
            results_html = ""
            if results:
                for patient in results:
                    if len(patient) >= 4:  # Make sure it has all the required fields
                        name = patient[0] if patient[0] else ""
                        document_id = patient[1] if patient[1] else ""
                        location = patient[2] if len(patient) > 2 else ""
                        patient_id = str(patient[3]) if len(patient) > 3 else ""

                        # Escape HTML special characters to prevent XSS
                        name = name.replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
                        document_id = document_id.replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
                        location = location.replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')

                        # Create the HTML element for each patient
                        results_html += f"""
                        <div class="p-2 hover:bg-[#E8F0F7] cursor-pointer"
                            data-patient-id="{patient_id}"
                            data-name="{name}"
                            data-document="{document_id}"
                            data-location="{location}">
                            {name} - {document_id} - {location}
                        </div>
                        """
            else:
                results_html = '<div class="p-2 text-gray-500">No results found</div>'

            # Run JavaScript to update the results list
            js_code = f"""
            (function() {{
                console.log("Updating search results...");
                const resultsContainer = document.getElementById('patientResults');
                if (resultsContainer) {{
                    resultsContainer.innerHTML = `{results_html}`;
                    resultsContainer.classList.remove('hidden');

                    // Add click events to each result with improved behavior
                    resultsContainer.querySelectorAll('div[data-patient-id]').forEach(item => {{
                        item.addEventListener('click', function() {{
                            const patientId = this.dataset.patientId;
                            const name = this.dataset.name;
                            const documentId = this.dataset.document;
                            const location = this.dataset.location;

                            // Update the search field with the selected result
                            // and keep it visible
                            const searchInput = document.getElementById('searchPatient');
                            if (searchInput) {{
                                searchInput.value = name + ' - ' + documentId;
                                // Focus briefly and blur to visually confirm the selection
                                searchInput.focus();
                                setTimeout(() => searchInput.blur(), 100);
                            }}

                            console.log("Selected patient:", patientId, name, documentId, location);

                            // Call the Python function to select the patient
                            // and update the view
                            if (window.handler) {{
                                // Explicitly flag that we are in individual mode before the selection
                                document.body.setAttribute('data-current-mode', 'individual');
                                window.handler.selectPatient(patientId, name, documentId, location);

                                // Hide the results after a short delay
                                setTimeout(function() {{
                                    resultsContainer.classList.add('hidden');
                                }}, 300);
                            }} else {{
                                console.error("window.handler is not available");
                            }}
                        }});
                    }});
                }} else {{
                    console.error("Results container not found");
                }}
            }})();
            """

            self.web_view.page().runJavaScript(js_code)
        except Exception as e:
            print(f"Error showing search results: {str(e)}")
            import traceback
            traceback.print_exc()
            self.show_warning_message("Error", f"Error showing results: {str(e)}")

    def configure_patient_search(self):
        """Configures the JavaScript events for the patient search with robust DOM handling"""
        try:
            js_code = """
            // Function to initialize the search with improved error handling
            function initializeSearch(retryCount = 0) {
                console.log("Trying to initialize the patient search... (attempt " + (retryCount + 1) + ")");

                // Look for the search field in several ways
                let searchInput = document.getElementById('searchPatient');

                // If we cannot find it by ID, try other selectors
                if (!searchInput) {
                    console.log("Looking for the search field with alternative selectors...");
                    // Try different selectors that could match
                    searchInput = document.querySelector('input[type="search"]');

                    if (!searchInput) {
                        searchInput = document.querySelector('input[placeholder*="patient"]');
                    }

                    if (!searchInput) {
                        searchInput = document.querySelector('input[placeholder*="search"]');
                    }

                    if (!searchInput) {
                        // Look for any input inside the individual search section
                        const individualSection = document.querySelector('#individual-section');
                        if (individualSection) {
                            searchInput = individualSection.querySelector('input');
                        }
                    }

                    if (searchInput) {
                        console.log("Search field found with an alternative selector");
                        // Assign the ID for future references
                        searchInput.id = 'searchPatient';
                    }
                }

                // If we still cannot find it, retry after a delay
                if (!searchInput) {
                    console.warn("Search element not found in the DOM");
                    if (retryCount < 10) { // Maximum of 10 attempts
                        console.log("Retrying in " + (500 + retryCount * 100) + "ms...");
                        setTimeout(() => initializeSearch(retryCount + 1), 500 + retryCount * 100);
                    } else {
                        console.error("The search field could not be found after several attempts");
                        // Last resort: create the search field if it does not exist
                        createSearchFieldIfNeeded();
                    }
                    return;
                }

                console.log("Search field found with ID:", searchInput.id);

                // Configure the search on Enter with a shorter delay
                searchInput.addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') {
                        e.preventDefault();
                        const term = this.value.trim();
                        if (term) {
                            console.log("Searching patient:", term);
                            document.body.setAttribute('data-current-mode', 'individual');
                            if (window.handler) {
                                window.handler.searchPatients(term);
                            } else {
                                console.error("window.handler is not available");
                            }
                        }
                    }
                });

                // Also search when the input changes, with a debounce
                let typingTimer;
                const doneTypingInterval = 500; // ms

                searchInput.addEventListener('input', function() {
                    clearTimeout(typingTimer);
                    const term = this.value.trim();
                    if (term.length >= 3) {
                        typingTimer = setTimeout(function() {
                            console.log("Automatic search:", term);
                            document.body.setAttribute('data-current-mode', 'individual');
                            if (window.handler) {
                                window.handler.searchPatients(term);
                            } else {
                                console.error("window.handler is not available");
                            }
                        }, doneTypingInterval);
                    }
                });

                // Function to show/hide the results
                function toggleResultsVisibility(show) {
                    const resultsContainer = document.getElementById('patientResults');
                    if (resultsContainer) {
                        if (show) {
                            resultsContainer.classList.remove('hidden');
                        } else {
                            setTimeout(() => resultsContainer.classList.add('hidden'), 200);
                        }
                    } else if (show) {
                        // If the container does not exist and we need to show it, create it
                        createResultsContainer();
                    }
                }

                // Keep the dropdown open during the interaction
                searchInput.addEventListener('focus', function() {
                    // Make sure we are on the individual tab
                    const tabIndividual = document.getElementById('tabIndividual');
                    if (tabIndividual) {
                        tabIndividual.click();
                    }

                    toggleResultsVisibility(true);

                    // If there is already text, perform an immediate search
                    const term = this.value.trim();
                    if (term.length >= 3 && window.handler) {
                        window.handler.searchPatients(term);
                    }
                });

                // Close the dropdown when focus is lost, with a delay to allow clicks
                searchInput.addEventListener('blur', function() {
                    toggleResultsVisibility(false);
                });

                console.log("Patient search initialized successfully");
            }

            // Function to create the results container if it does not exist
            function createResultsContainer() {
                if (!document.getElementById('patientResults')) {
                    console.log("Creating the results container...");
                    const searchInput = document.getElementById('searchPatient');
                    if (searchInput) {
                        // Create the results container
                        const resultsContainer = document.createElement('div');
                        resultsContainer.id = 'patientResults';
                        resultsContainer.className = 'hidden absolute z-50 bg-white shadow-lg rounded mt-1 w-full border';

                        // Insert it after the input
                        if (searchInput.parentNode) {
                            searchInput.parentNode.insertBefore(resultsContainer, searchInput.nextSibling);
                        }
                    }
                }
            }

            // Function to create the search field as a last resort
            function createSearchFieldIfNeeded() {
                console.log("Trying to create the search field as a last resort...");

                // Look for the section where the search box should go
                const searchSection = document.querySelector('#individual-section, #individual-search-section');

                if (!searchSection) {
                    console.error("No section found to add the search box");
                    return;
                }

                // Create the search field
                const searchContainer = document.createElement('div');
                searchContainer.className = 'relative w-full max-w-md mb-4';
                searchContainer.innerHTML = `
                    <input id="searchPatient" type="text"
                        placeholder="Search patient by name or document ID"
                        class="w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                    <div id="patientResults" class="hidden absolute z-50 bg-white shadow-lg rounded mt-1 w-full border"></div>
                `;

                // Insert it at the beginning of the section
                searchSection.insertBefore(searchContainer, searchSection.firstChild);

                console.log("Search field created. Trying to initialize the events...");
                // Retry the initialization after creating the field
                setTimeout(() => initializeSearch(0), 200);
            }

            // Initialize when the DOM is completely loaded
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', () => initializeSearch(0));
            } else {
                // If the DOM is already loaded, initialize immediately
                initializeSearch(0);
            }

            // Also try to initialize when the window is completely loaded
            window.addEventListener('load', () => {
                console.log("Load event detected, checking whether the search is initialized");
                if (!document.getElementById('searchPatient')) {
                    initializeSearch(0);
                }
            });
            """

            self.web_view.page().runJavaScript(js_code)
            print("Patient search script configured")
        except Exception as e:
            print(f"Error configuring the patient search: {str(e)}")
            import traceback
            traceback.print_exc()

    def select_patient(self, patient_id, name, document_id, location):
        """Selects a patient to generate the individual report"""
        try:
            # Store the ID of the selected patient
            self.selected_patient = patient_id
            # IMPORTANT: set the current mode before updating the data
            self.current_mode = "individual"
            print(f"Selected patient: ID={patient_id}, Name={name}, Document ID={document_id}")

            escaped_name = name.replace("'", "\\'").replace('"', '\\"')
            escaped_document = document_id.replace("'", "\\'").replace('"', '\\"')

            # Change the sequence to guarantee that it stays in individual mode
            js_code = """
            // First we make sure the value of the search field is kept
            const searchInput = document.getElementById('searchPatient');
            if (searchInput && searchInput.value.indexOf('""" + escaped_name + """') === -1) {
                searchInput.value = '""" + escaped_name + """ - """ + escaped_document + """';
            }

            // Then we activate the individual tab in a more robust way
            const tabIndividual = document.getElementById('tabIndividual');
            if (tabIndividual) {
                // Mark this tab as active
                tabIndividual.classList.add('tab-active');
                tabIndividual.classList.remove('text-gray-500');

                // Unmark the group tab
                const tabGroup = document.getElementById('tabGroup');
                if (tabGroup) {
                    tabGroup.classList.remove('tab-active');
                    tabGroup.classList.add('text-gray-500');
                }

                // Make sure the individual filter is visible
                const individualFilter = document.getElementById('individualFilter');
                if (individualFilter) {
                    individualFilter.classList.remove('hidden');
                }

                // Make sure the individual components are visible
                document.querySelectorAll('[id^="individual-metrics-"]').forEach(el => el.classList.remove('hidden'));

                // Show the individual charts and the patient table
                const individualCharts = document.getElementById('individual-charts');
                if (individualCharts) individualCharts.classList.remove('hidden');

                const individualPatientTable = document.getElementById('individual-patient-table');
                if (individualPatientTable) individualPatientTable.classList.remove('hidden');

                // Hide the group components
                const groupCharts = document.getElementById('group-charts');
                if (groupCharts) groupCharts.classList.add('hidden');

                const slaCompliance = document.getElementById('sla-compliance');
                if (slaCompliance) slaCompliance.classList.add('hidden');

                // Hide the group content
                document.querySelectorAll('[id^="group-metrics-"]').forEach(el => el.classList.add('hidden'));

                // Show the individual report button and hide the group one
                document.getElementById('generateGroupReport').classList.add('hidden');
                document.getElementById('generateIndividualReport').classList.remove('hidden');

                // Store the mode as data to make sure it persists
                document.body.setAttribute('data-current-mode', 'individual');
            }
            """

            # Run the JavaScript code
            self.web_view.page().runJavaScript(js_code)

        except Exception as e:
            print(f"Error selecting patient: {str(e)}")
            traceback.print_exc()
            self.show_warning_message("Error", f"Error selecting patient: {str(e)}")

    def calculate_individual_sla_compliance(self, patient_metrics):
        """Calculates the SLA compliance percentage for an individual patient"""
        # Get the triage level of the patient (default value: 3)
        triage_level = patient_metrics.get("triage", {}).get("value", "3")

        # Define the SLAs according to the triage level (same as in generate_status_indicators_update_js)
        slas = {
            'triage': {'1': 0, '2': 30, '3': 120, '4': 30, '5': 60},
            'admission_consult': {'1': 210, '2': 210, '3': 360, '4': 420, '5': 420},
            'labs': {'1': 360, '2': 360, '3': 360, '4': 360, '5': 360},
            'imaging': {'1': 360, '2': 360, '3': 360, '4': 360, '5': 360},
            'specialist_consult': {'1': 30, '2': 45, '3': 60, '4': 120, '5': 180},
            'reassessment': {'1': 30, '2': 60, '3': 120, '4': 240, '5': 360}
        }

        # Prepare the dictionary for the compliance percentages
        compliance = {}

        # For each process type, calculate the compliance
        processes = ['triage', 'admission_consult', 'labs', 'imaging', 'specialist_consult', 'reassessment']
        for process in processes:
            time_value = patient_metrics.get(process, {}).get("time", 0) or 0
            sla_value = slas[process].get(triage_level, slas[process]['3'])

            if time_value > 0 and sla_value > 0:
                # If the time is lower than or equal to the SLA, compliance is 100%
                if time_value <= sla_value:
                    compliance[process] = 100
                else:
                    # Compliance decreases proportionally to the excess
                    excess = (time_value - sla_value) / sla_value
                    compliance[process] = max(0, min(100, 100 - excess * 100))
            else:
                compliance[process] = None

        return compliance

    def generate_charts_update_js(self, charts_data):
        """Generates the JavaScript code used to update the charts"""
        try:
            # Start with a simple base
            js_code = "console.log('Updating charts...');\n"

            # Add code to update the timeline chart if there is timeline data
            if "timeline" in charts_data and charts_data["timeline"]:
                try:
                    # Extract the data safely and use json.dumps() to guarantee a valid format
                    grouping = charts_data["timeline"].get("grouping", "daily")
                    labels_json = json.dumps(charts_data["timeline"].get("labels", []))
                    data_json = json.dumps(charts_data["timeline"].get("data", []))

                    # Use a safer template string form, avoiding characters that could break the syntax
                    js_code += """
                    // Update the timeline chart
                    if (window.timelineChart) {
                        try {
                            const labels = """ + labels_json + """;
                            const data = """ + data_json + """;
                            if (Array.isArray(labels) && Array.isArray(data) && labels.length > 0) {
                                updateTimelineChart(labels, data, '""" + grouping + """');
                            } else {
                                // There is no data, show a message on the chart
                                window.timelineChart.data.labels = [];
                                window.timelineChart.data.datasets[0].data = [];
                                window.timelineChart.options.plugins.title = {
                                    display: true,
                                    text: 'No data available for this filter',
                                    font: {size: 16, weight: 'bold'}
                                };
                                window.timelineChart.update();
                            }
                        } catch(e) {
                            console.error("Error updating the timeline chart:", e);
                        }
                    }
                    """

                except Exception as e:
                    print(f"Error processing timeline data: {e}")

            # If there is comparison data, add code to update those charts
            if "comparison" in charts_data:
                try:
                    comparison_data = charts_data["comparison"]
                    labels_json = json.dumps(comparison_data.get("labels", []))
                    patient_data_json = json.dumps(comparison_data.get("patient_data", []))
                    area_data_json = json.dumps(comparison_data.get("area_data", []))

                    js_code += f"""
                    // Update the comparison chart
                    (function() {{
                        const comparisonCtx = document.getElementById('comparisonChart');
                        if (!comparisonCtx) {{
                            console.error("The canvas for the comparison chart was not found");
                            return;
                        }}

                        try {{
                            // Data for the chart
                            const labels = {labels_json};
                            const patientData = {patient_data_json};
                            const areaData = {area_data_json};

                            // If the chart already exists and is valid, update it
                            if (window.comparisonChart && typeof window.comparisonChart.update === 'function') {{
                                window.comparisonChart.data.labels = labels;
                                window.comparisonChart.data.datasets[0].data = patientData;
                                window.comparisonChart.data.datasets[1].data = areaData;
                                window.comparisonChart.update();
                                console.log("Comparison chart updated successfully");
                            }} else {{
                                // If the previous chart exists but is not valid, try to clear it
                                if (window.comparisonChart) {{
                                    try {{
                                        if (typeof window.comparisonChart.destroy === 'function') {{
                                            window.comparisonChart.destroy();
                                        }}
                                    }} catch (e) {{
                                        console.warn("The previous chart could not be destroyed:", e);
                                    }}
                                }}

                                // Create a new chart
                                window.comparisonChart = new Chart(comparisonCtx, {{
                                    type: 'bar',
                                    data: {{
                                        labels: labels,
                                        datasets: [
                                            {{
                                                label: 'Patient',
                                                data: patientData,
                                                backgroundColor: '#5385B7',
                                                borderWidth: 1
                                            }},
                                            {{
                                                label: 'Area average',
                                                data: areaData,
                                                backgroundColor: '#E6B800',
                                                borderWidth: 1
                                            }}
                                        ]
                                    }},
                                    options: {{
                                        responsive: true,
                                        maintainAspectRatio: false,
                                        plugins: {{
                                            legend: {{
                                                display: true,
                                                position: 'top'
                                            }}
                                        }},
                                        scales: {{
                                            y: {{
                                                beginAtZero: true,
                                                title: {{
                                                    display: true,
                                                    text: 'Minutes'
                                                }}
                                            }}
                                        }}
                                    }}
                                }});
                                console.log("New comparison chart created");
                            }}
                        }} catch(e) {{
                            console.error("Error creating/updating the comparison chart:", e);
                        }}
                    }})();
                    """
                except Exception as e:
                    print(f"Error processing comparison chart data: {e}")

            # Code to update the radar chart with all the areas
            if "all_areas" in charts_data:
                try:
                    all_areas_data = charts_data["all_areas"]
                    labels_json = json.dumps(all_areas_data.get("labels", []))
                    patient_data_json = json.dumps(all_areas_data.get("patient_data", []))
                    overall_data_json = json.dumps(all_areas_data.get("overall_data", []))

                    js_code += f"""
                    // Update the radar chart
                    (function() {{
                        const radarCtx = document.getElementById('allAreasChart');
                        if (!radarCtx) {{
                            console.error("The canvas for the radar chart was not found");
                            return;
                        }}

                        try {{
                            // Data for the chart
                            const labels = {labels_json};
                            const patientData = {patient_data_json};
                            const overallData = {overall_data_json};

                            // If the chart already exists and is valid, update it
                            if (window.allAreasChart && typeof window.allAreasChart.update === 'function') {{
                                window.allAreasChart.data.labels = labels;
                                window.allAreasChart.data.datasets[0].data = patientData;
                                window.allAreasChart.data.datasets[1].data = overallData;
                                window.allAreasChart.update();
                                console.log("Radar chart updated successfully");
                            }} else {{
                                // If the previous chart exists but is not valid, try to clear it
                                if (window.allAreasChart) {{
                                    try {{
                                        if (typeof window.allAreasChart.destroy === 'function') {{
                                            window.allAreasChart.destroy();
                                        }}
                                    }} catch (e) {{
                                        console.warn("The previous chart could not be destroyed:", e);
                                    }}
                                }}

                                // Create a new chart
                                window.allAreasChart = new Chart(radarCtx, {{
                                    type: 'radar',
                                    data: {{
                                        labels: labels,
                                        datasets: [
                                            {{
                                                label: 'Patient',
                                                data: patientData,
                                                backgroundColor: 'rgba(83, 133, 183, 0.2)',
                                                borderColor: '#5385B7',
                                                pointBackgroundColor: '#5385B7',
                                                borderWidth: 2,
                                            }},
                                            {{
                                                label: 'Overall average',
                                                data: overallData,
                                                backgroundColor: 'rgba(230, 184, 0, 0.2)',
                                                borderColor: '#E6B800',
                                                pointBackgroundColor: '#E6B800',
                                                borderWidth: 2,
                                            }}
                                        ]
                                    }},
                                    options: {{
                                        responsive: true,
                                        maintainAspectRatio: false,
                                        elements: {{
                                            line: {{
                                                tension: 0.1
                                            }}
                                        }},
                                        plugins: {{
                                            legend: {{
                                                position: 'top'
                                            }}
                                        }},
                                        scales: {{
                                            r: {{
                                                beginAtZero: true
                                            }}
                                        }}
                                    }}
                                }});
                                console.log("New radar chart created");
                            }}
                        }} catch(e) {{
                            console.error("Error creating/updating the radar chart:", e);
                        }}
                    }})();
                    """
                except Exception as e:
                    print(f"Error processing radar chart data: {e}")

            # Code to make the chart container visible and ensure the charts are initialized
            js_code += """
            // Make the chart container visible
            (function() {
                const individualCharts = document.getElementById('individual-charts');
                if (individualCharts) {
                    // Make the container visible
                    individualCharts.classList.remove('hidden');
                    individualCharts.style.display = 'grid';
                    console.log("Individual chart visibility enabled");
                }
            })();
            """
            # Debug to help diagnose issues
            print("JavaScript generated without syntax errors")
            return js_code

        except Exception as e:
            print(f"Error generating the JavaScript for the charts: {e}")
            import traceback
            traceback.print_exc()
            return "console.error('Error generating the chart data: " + str(e).replace("'", "\\'") + "');"

    def prepare_html_for_webengine(self, html_content):
        """Prepares the HTML so it is compatible with QWebEngineView"""
        # Insert the web channel code right before the closing </head>
        web_channel_js = """
        <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
        <script>
        document.addEventListener('DOMContentLoaded', function() {
            new QWebChannel(qt.webChannelTransport, function(channel) {
                window.handler = channel.objects.handler;
            });
        });
        </script>
        """

        html_with_channel = html_content.replace('</head>', web_channel_js + '</head>')

        return html_with_channel

    def get_real_data(self):
        """Gets the real metrics data from the model"""
        from backend.metrics_model import MetricsModel

        # Calculate the dates dynamically for both modes
        start_date_str = self.start_date.strftime('%Y-%m-%d')
        end_date_str = self.end_date.strftime('%Y-%m-%d')

        # For the individual report (one specific patient)
        if self.current_mode == "individual" and self.selected_patient:
            try:
                # Get the specific metrics of the patient
                patient_data = MetricsModel.get_patient_metrics(self.selected_patient)
                if not patient_data:
                    print(f"No metrics found for the patient with ID {self.selected_patient}")
                    return None

                # Get the area of the patient for the comparisons
                patient_area = patient_data.get('area', "all")

                # Get the general metrics of all the areas for the comparisons
                area_metrics = patient_data.get("area_averages", {})
                overall_data = MetricsModel.get_all_metrics(
                    start_date=start_date_str, end_date=end_date_str
                )

                # Prepare the data for the charts
                labels = ['Triage', 'Admission Consult', 'Laboratories', 'Imaging', 'Specialist Consult', 'Reassessment']

                # Use a safe get() for all the patient data paths
                patient_comparison_data = [
                    patient_data.get('metrics', {}).get('triage', {}).get('time', 0) or 0,
                    patient_data.get('metrics', {}).get('admission_consult', {}).get('time', 0) or 0,
                    patient_data.get('metrics', {}).get('labs', {}).get('time', 0) or 0,
                    patient_data.get('metrics', {}).get('imaging', {}).get('time', 0) or 0,
                    patient_data.get('metrics', {}).get('specialist_consult', {}).get('time', 0) or 0,
                    patient_data.get('metrics', {}).get('reassessment', {}).get('time', 0) or 0
                ]

                # Access the data with .get() to prevent errors when a key does not exist
                area_comparison_data = [
                    area_metrics.get('triage', {}).get('statistics', {}).get('average', 0) or 0,
                    area_metrics.get('admission_consult', {}).get('statistics', {}).get('average', 0) or 0,
                    # Labs and imaging may have total_statistics instead of statistics
                    area_metrics.get('labs', {}).get('total_statistics', {}).get('average', 0) or 0,
                    area_metrics.get('imaging', {}).get('total_statistics', {}).get('average', 0) or 0,
                    area_metrics.get('specialist_consult', {}).get('total_statistics', {}).get('average', 0) or 0,
                    area_metrics.get('reassessment', {}).get('statistics', {}).get('average', 0) or 0
                ]

                # Data for all the areas (radar chart)
                overall_comparison_data = [
                    overall_data.get('triage', {}).get('statistics', {}).get('average', 0) or 0,
                    overall_data.get('admission_consult', {}).get('statistics', {}).get('average', 0) or 0,
                    overall_data.get('labs', {}).get('total_statistics', {}).get('average', 0) or 0,
                    overall_data.get('imaging', {}).get('total_statistics', {}).get('average', 0) or 0,
                    overall_data.get('specialist_consult', {}).get('total_statistics', {}).get('average', 0) or 0,
                    overall_data.get('reassessment', {}).get('statistics', {}).get('average', 0) or 0
                ]

                charts_data = {
                    "comparison": {
                        "labels": labels,
                        "patient_data": patient_comparison_data,
                        "area_data": area_comparison_data,
                    },
                    "all_areas": {
                        "labels": labels,
                        "patient_data": patient_comparison_data,
                        "overall_data": overall_comparison_data,
                    }
                }

                return {
                    "individual": True,
                    "patient": patient_data.get("patient", {}),
                    "metrics": patient_data.get("metrics", {}),
                    "charts": charts_data,
                    "area_averages": area_metrics,
                    "overall_averages": overall_data,
                    "total_time": patient_data.get("total_time", 0),
                    "configuration": {
                        "start_date": start_date_str,
                        "end_date": end_date_str,
                        "area": patient_area
                    }
                }
            except Exception as e:
                print(f"Error getting real data for the individual report: {str(e)}")
                import traceback
                traceback.print_exc()
                return None
        else:
            # For the group view, get the aggregated metrics
            try:
                # Determine the area to filter by (None if it is "all")
                area = None if self.selected_area == "all" else self.selected_area

                # Get all the metrics through the general method
                metrics = MetricsModel.get_all_metrics(
                    area=area,
                    start_date=start_date_str,
                    end_date=end_date_str
                )

                # Get the data for the charts
                charts_data = {
                    "timeline": MetricsModel.generate_timeline_data(
                        area=area,
                        start_date=start_date_str,
                        end_date=end_date_str
                    ),
                    "bars": MetricsModel.generate_comparative_bar_data(
                        area=area,
                        start_date=start_date_str,
                        end_date=end_date_str
                    )
                }

                # Get the SLA compliance data
                sla_data = MetricsModel.get_sla_compliance_metrics(
                    area=area,
                    start_date=start_date_str,
                    end_date=end_date_str
                )

                # Integrate all the data
                return {
                    "individual": False,
                    "metrics": metrics,
                    "charts": charts_data,
                    "sla": sla_data,
                    "configuration": {
                        "start_date": start_date_str,
                        "end_date": end_date_str,
                        "area": self.selected_area
                    }
                }

            except Exception as e:
                print(f"Error getting real data: {str(e)}")
                self.show_warning_message("Warning",
                                            f"Error getting metrics data: {str(e)}.")
                return None

    def as_minutes(self, value):
        """
        Coerces a metric to a number of minutes for arithmetic.

        A stage the patient never reached reports a placeholder such as "-"
        rather than a number, and a placeholder is truthy, so the usual
        `or 0` guard lets it through and the first comparison raises. Anything
        that is not a real measurement becomes 0, which the callers already
        treat as "no comparable data".
        """
        try:
            if value is None or isinstance(value, bool):
                return 0
            return float(value)
        except (TypeError, ValueError):
            return 0

    def calculate_area_comparisons(self, patient_metrics, area_averages, total_time=0):
        """Calculates the comparisons of the patient times against the area average"""
        comparisons = {}
        total_time = self.as_minutes(total_time)

        # Triage
        triage_time = self.as_minutes(patient_metrics.get("triage", {}).get("time", 0))
        triage_average = self.as_minutes(area_averages.get("triage", {}).get("statistics", {}).get("average", 0))
        if triage_time > 0 and triage_average > 0:
            difference = triage_time - triage_average
            if difference < 0:
                comparisons["triage"] = f'<span class="comparison-positive">{abs(difference):.2f} min less</span> than the area average'
            elif difference > 0:
                comparisons["triage"] = f'<span class="comparison-negative">{difference:.2f} min more</span> than the area average'
            else:
                comparisons["triage"] = f'<span class="comparison-neutral">Equal</span> to the area average'
        else:
            comparisons["triage"] = '<span class="comparison-neutral">No comparative data available</span>'

        # Admission Consult
        admission_time = self.as_minutes(patient_metrics.get("admission_consult", {}).get("time", 0))
        admission_average = self.as_minutes(area_averages.get("admission_consult", {}).get("statistics", {}).get("average", 0))
        if admission_time > 0 and admission_average > 0:
            difference = admission_time - admission_average
            if difference < 0:
                comparisons["admission_consult"] = f'<span class="comparison-positive">{abs(difference):.2f} min less</span> than the area average'
            elif difference > 0:
                comparisons["admission_consult"] = f'<span class="comparison-negative">{difference:.2f} min more</span> than the area average'
            else:
                comparisons["admission_consult"] = f'<span class="comparison-neutral">Equal</span> to the area average'
        else:
            comparisons["admission_consult"] = '<span class="comparison-neutral">No comparative data available</span>'

        # Labs
        labs_time = self.as_minutes(patient_metrics.get("labs", {}).get("time", 0))
        labs_average = self.as_minutes(area_averages.get("labs", {}).get("total_statistics", {}).get("average", 0))
        if labs_time > 0 and labs_average > 0:
            difference = labs_time - labs_average
            if difference < 0:
                comparisons["labs"] = f'<span class="comparison-positive">{abs(difference):.2f} min less</span> than the area average'
            elif difference > 0:
                comparisons["labs"] = f'<span class="comparison-negative">{difference:.2f} min more</span> than the area average'
            else:
                comparisons["labs"] = f'<span class="comparison-neutral">Equal</span> to the area average'
        else:
            comparisons["labs"] = '<span class="comparison-neutral">No comparative data available</span>'

        # Imaging
        imaging_time = self.as_minutes(patient_metrics.get("imaging", {}).get("time", 0))
        imaging_average = self.as_minutes(area_averages.get("imaging", {}).get("total_statistics", {}).get("average", 0))
        if imaging_time > 0 and imaging_average > 0:
            difference = imaging_time - imaging_average
            if difference < 0:
                comparisons["imaging"] = f'<span class="comparison-positive">{abs(difference):.2f} min less</span> than the area average'
            elif difference > 0:
                comparisons["imaging"] = f'<span class="comparison-negative">{difference:.2f} min more</span> than the area average'
            else:
                comparisons["imaging"] = f'<span class="comparison-neutral">Equal</span> to the area average'
        else:
            comparisons["imaging"] = '<span class="comparison-neutral">No comparative data available</span>'

        # Specialist Consult
        specialist_time = self.as_minutes(patient_metrics.get("specialist_consult", {}).get("time", 0))
        specialist_average = self.as_minutes(area_averages.get("specialist_consult", {}).get("total_statistics", {}).get("average", 0))
        if specialist_time > 0 and specialist_average > 0:
            difference = specialist_time - specialist_average
            if difference < 0:
                comparisons["specialist_consult"] = f'<span class="comparison-positive">{abs(difference):.2f} min less</span> than the area average'
            elif difference > 0:
                comparisons["specialist_consult"] = f'<span class="comparison-negative">{difference:.2f} min more</span> than the area average'
            else:
                comparisons["specialist_consult"] = f'<span class="comparison-neutral">Equal</span> to the area average'
        else:
            comparisons["specialist_consult"] = '<span class="comparison-neutral">No comparative data available</span>'

        # Reassessment
        reassessment_time = self.as_minutes(patient_metrics.get("reassessment", {}).get("time", 0))
        reassessment_average = self.as_minutes(area_averages.get("reassessment", {}).get("statistics", {}).get("average", 0))
        if reassessment_time > 0 and reassessment_average > 0:
            difference = reassessment_time - reassessment_average
            if difference < 0:
                comparisons["reassessment"] = f'<span class="comparison-positive">{abs(difference):.2f} min less</span> than the area average'
            elif difference > 0:
                comparisons["reassessment"] = f'<span class="comparison-negative">{difference:.2f} min more</span> than the area average'
            else:
                comparisons["reassessment"] = f'<span class="comparison-neutral">Equal</span> to the area average'
        else:
            comparisons["reassessment"] = '<span class="comparison-neutral">No comparative data available</span>'

        # Total time
        total_average = self.as_minutes(area_averages.get("total_time", {}).get("statistics", {}).get("average", 0))
        print(f"Patient total time: {total_time}, Area average: {total_average}")
        if total_time > 0 and total_average > 0:
            difference = total_time - total_average
            if difference < 0:
                comparisons["total_time"] = f'<span class="comparison-positive">{abs(difference):.2f} min less</span> than the area average'
            elif difference > 0:
                comparisons["total_time"] = f'<span class="comparison-negative">{difference:.2f} min more</span> than the area average'
            else:
                comparisons["total_time"] = f'<span class="comparison-neutral">Equal</span> to the area average'
        else:
            comparisons["total_time"] = '<span class="comparison-neutral">No comparative data available</span>'

        return comparisons

    def _get_status_icon_and_text(self, status, kind):
        """Returns the HTML icon and the formatted text according to the status"""
        # Determine the icon according to the status
        if kind == "triage" and status in ["1", "2", "3", "4", "5"]:
            icon = '<i class="fas fa-check-circle text-[#28a745]"></i>'
            text = f"Triage {status}"
        elif status in ["Completed", "Results complete"]:
            icon = '<i class="fas fa-check-circle text-[#28a745]"></i>'
            if status == "Results complete":
                text = "Completed"
            else:
                text = status
        elif status in ["Awaiting results", "Open"]:
            icon = '<i class="fas fa-exclamation-triangle text-[#E6B800]"></i>'
            if status == "Awaiting results":
                text = "Awaiting"
            else:
                text = status
        else:
            icon = '<i class="fas fa-times-circle text-[#B75353]"></i>'
            if status == "Not started":
                text = "Not completed"
            elif status == "Not opened":
                text = "Not opened"
            else:
                text = status

        return icon, text

    def format_time(self, value):
        """Formats the time to show -- when it is 0, None or any value that evaluates to False"""
        if value is None or value == 0 or not value:
            return "--"
        return str(value)

    def format_chart_number(self, value):
        """
        Formats a value for use inside a JavaScript array.

        The card placeholders render missing data as "--", which reads correctly
        in text but is not a valid number. The chart datasets need their own
        formatting, otherwise a period with no data produces `data: [--, --]`
        and the syntax error takes down every script on the page.
        """
        try:
            if value is None or value == "" or value == "--":
                return "null"
            return str(float(value))
        except (TypeError, ValueError):
            return "null"

    def chart_stage_averages(self, data):
        """Average per care stage for the comparison chart, as JavaScript literals."""
        metrics = data.get("metrics", {}) or {}
        stages = ["triage", "admission_consult", "labs", "imaging",
                  "specialist_consult", "reassessment"]
        values = {}
        for stage in stages:
            entry = metrics.get(stage, {}) or {}
            average = None
            if isinstance(entry, dict):
                # Group mode keeps statistics blocks; labs and imaging report a
                # total as well as the individual legs. Individual mode stores
                # the elapsed time directly.
                for key in ("statistics", "total_statistics"):
                    block = entry.get(key)
                    if isinstance(block, dict) and block.get("average") is not None:
                        average = block.get("average")
                        break
                if average is None:
                    average = entry.get("time")
            values[stage] = self.format_chart_number(average)
        return values

    def compliance_percentages(self, data):
        """
        Service level compliance per stage, as whole percentages.

        The group report carries them ready made; the individual report derives
        them from that patient's own times. Both paths end here so the gauges and
        their captions are filled the same way whichever report is being shown.

        A stage with nothing to measure in the selected range stays None rather
        than becoming 0: no qualifying patients is not the same as no patient
        complying, and 0 would paint the stage red as though it had failed.
        """
        stages = ["triage", "admission_consult", "labs", "imaging",
                  "specialist_consult", "reassessment"]
        values = {stage: None for stage in stages}

        source = data.get("sla")
        if not source and data.get("individual", False):
            try:
                source = self.calculate_individual_sla_compliance(data.get("metrics", {}) or {})
            except Exception as error:
                print(f"Could not calculate the individual compliance: {error}")
                source = None

        if isinstance(source, dict):
            for stage in stages:
                raw = source.get(stage)
                if raw is None:
                    continue
                try:
                    values[stage] = int(round(float(raw)))
                except (TypeError, ValueError):
                    values[stage] = None
        return values

    def replace_data_in_html(self, html_content, data):
        """Replaces the placeholders in the HTML with real data"""
        try:
            # Set the initial default values
            current_area = data.get('configuration', {}).get('area', 'all')

            # Replace the date placeholders
            start_date = data.get('configuration', {}).get('start_date', '')
            end_date = data.get('configuration', {}).get('end_date', '')
            html_content = html_content.replace("{{START_DATE}}", start_date)
            html_content = html_content.replace("{{END_DATE}}", end_date)

            current_area = self.selected_area if hasattr(self, 'selected_area') else "all"
            areas = ["all", "Old wing", "Yellow", "Pediatrics", "Hallways", "Clinic", "Waitingroom"]

            for area in areas:
                key = area.upper().replace(" ", "_")
                if area == "Waitingroom":
                    key = "WAITING_ROOM"
                marker = f"{{{{SELECTED_{key}}}}}"

                if area == current_area:
                    html_content = html_content.replace(marker, " selected")
                else:
                    html_content = html_content.replace(marker, "")

            # Chart datasets are filled before the mode branches below, so the
            # scripts stay syntactically valid whichever branch runs and even
            # when a stage has no data at all.
            chart_values = self.chart_stage_averages(data)
            for stage, placeholder in (
                    ("triage", "CHART_TRIAGE_AVERAGE"),
                    ("admission_consult", "CHART_ADMISSION_AVERAGE"),
                    ("labs", "CHART_LABS_AVERAGE"),
                    ("imaging", "CHART_IMAGING_AVERAGE"),
                    ("specialist_consult", "CHART_SPECIALIST_AVERAGE"),
                    ("reassessment", "CHART_REASSESSMENT_AVERAGE")):
                html_content = html_content.replace(
                    "{{" + placeholder + "}}", chart_values[stage])

            # Compliance feeds both a percentage on the card and a numeric argument to
            # the gauge script, and it is produced differently in each mode. Resolve it
            # once here so neither context is left with an unreplaced placeholder.
            compliance = self.compliance_percentages(data)
            for stage, text_marker, gauge_marker in (
                    ("triage", "COMPLIANCE_TRIAGE", "GAUGE_TRIAGE"),
                    ("admission_consult", "COMPLIANCE_ADMISSION", "GAUGE_ADMISSION"),
                    ("labs", "COMPLIANCE_LABS", "GAUGE_LABS"),
                    ("imaging", "COMPLIANCE_IMAGING", "GAUGE_IMAGING"),
                    ("specialist_consult", "COMPLIANCE_SPECIALIST", "GAUGE_SPECIALIST"),
                    ("reassessment", "COMPLIANCE_REASSESSMENT", "GAUGE_REASSESSMENT")):
                value = compliance[stage]
                # The caption is prose and says so when there is nothing to report;
                # the gauge argument is JavaScript and must stay a number, so an
                # unmeasured stage simply draws an empty arc behind the "--".
                caption = "--" if value is None else f"{value}%"
                html_content = html_content.replace("{{" + text_marker + "}}", caption)
                html_content = html_content.replace("{{" + gauge_marker + "}}",
                                                    str(0 if value is None else value))

            if data.get("individual", False):
                patient = data["patient"]
                metrics = data["metrics"]
                area_averages = data.get("area_averages", {})
                print("DEBUG: data['charts'] structure:", json.dumps(data.get("charts", {}), default=str))

                # Explicitly flag that we are in individual mode
                html_content = html_content.replace('<body', '<body data-current-mode="individual"')

                # Patient data for the individual table
                html_content = html_content.replace("{{PATIENT_NAME}}", patient.get("name", "-"))
                html_content = html_content.replace("{{PATIENT_DOCUMENT}}", patient.get("document_id", "-"))
                html_content = html_content.replace("{{PATIENT_AREA}}", patient.get("area", "-"))

                if metrics:
                                # Calculate the SLA compliance for the individual patient
                                sla_data = self.calculate_individual_sla_compliance(metrics)

                                # Generate the JavaScript used to update the status indicators
                                js_indicators = self.generate_status_indicators_update_js(sla_data, metrics)

                                # Insert the script that updates the status indicators before the closing body tag
                                html_content = html_content.replace('</body>', f'<script>{js_indicators}</script></body>')

                # Update the patient detail table with real data
                # Generate the HTML for the main row
                name = patient.get("name", "-")
                document_id = patient.get("document_id", "-")
                area = patient.get("area", "-")
                admission = patient.get("admission", "-")
                total_time = data.get("total_time", 0) or "-"
                disposition = patient.get("current_status", {}).get("disposition", "-")

                # Determine the style for the disposition status
                disposition_style = "bg-green-100 text-green-800"  # Default (discharged)
                if disposition == "Hospitalized":
                    disposition_style = "bg-blue-100 text-blue-800"
                elif disposition == "Observation":
                    disposition_style = "bg-yellow-100 text-yellow-800"
                elif disposition != "Discharged":
                    disposition_style = "bg-gray-100 text-gray-800"
                    if not disposition:
                        disposition = "In progress"

                # HTML for the main row
                row_html = f"""
                <tr class="expandable-row table-row-odd">
                    <td class="px-4 py-3 whitespace-nowrap">{name}</td>
                    <td class="px-4 py-3 whitespace-nowrap">{document_id}</td>
                    <td class="px-4 py-3 whitespace-nowrap">{area}</td>
                    <td class="px-4 py-3 whitespace-nowrap">{admission}</td>
                    <td class="px-4 py-3 whitespace-nowrap">{total_time} min</td>
                    <td class="px-4 py-3 whitespace-nowrap">
                        <span class="px-2 py-1 text-xs rounded-full {disposition_style}">{disposition}</span>
                    </td>
                    <td class="px-4 py-3 whitespace-nowrap text-right">
                        <button class="text-[#0066cc] hover:text-[#004c99]">
                            <i class="fas fa-chevron-down"></i>
                        </button>
                    </td>
                </tr>
                """

                # Get the calculated comparisons for each stage
                comparisons = self.calculate_area_comparisons(metrics, area_averages, total_time)

                # HTML for the detail row
                details_html = """
                <tr class="detail-row" style="display: table-row;">
                    <td colspan="7" class="px-4 py-3">
                        <div class="grid grid-cols-3 gap-4">
                """

                # Triage
                triage_time = self.format_time(metrics.get("triage", {}).get("time", "-"))
                triage_status = patient.get("current_status", {}).get("triage", "Not completed")
                triage_icon, triage_text = self._get_status_icon_and_text(triage_status, "triage")
                details_html += f"""
                <div>
                    <h4 class="font-medium text-[#333333]">Triage</h4>
                    <p class="text-sm">Time: {triage_time} min</p>
                    <p class="text-sm">{comparisons.get("triage", "")}</p>
                    <p class="text-sm">Status: {triage_icon} {triage_text}</p>
                </div>
                """

                # Admission Consult
                admission_time = self.format_time(metrics.get("admission_consult", {}).get("time", "-"))
                admission_status = patient.get("current_status", {}).get("admission_consult", "Not completed")
                admission_icon, admission_text = self._get_status_icon_and_text(admission_status, "admission_consult")
                details_html += f"""
                <div>
                    <h4 class="font-medium text-[#333333]">Admission Consult</h4>
                    <p class="text-sm">Time: {admission_time} min</p>
                    <p class="text-sm">{comparisons.get("admission_consult", "")}</p>
                    <p class="text-sm">Status: {admission_icon} {admission_text}</p>
                </div>
                """

                # Labs
                labs_time = self.format_time(metrics.get("labs", {}).get("time", "-"))
                labs_status = patient.get("current_status", {}).get("labs", "Not started")
                labs_icon, labs_text = self._get_status_icon_and_text(labs_status, "labs")
                details_html += f"""
                <div>
                    <h4 class="font-medium text-[#333333]">Laboratories</h4>
                    <p class="text-sm">Total time: {labs_time} min</p>
                    <p class="text-sm">{comparisons.get("labs", "")}</p>
                    <p class="text-sm">Status: {labs_icon} {labs_text}</p>
                </div>
                """

                # Imaging
                imaging_time = self.format_time(metrics.get("imaging", {}).get("time", "-"))
                imaging_status = patient.get("current_status", {}).get("imaging", "Not started")
                imaging_icon, imaging_text = self._get_status_icon_and_text(imaging_status, "imaging")
                details_html += f"""
                <div>
                    <h4 class="font-medium text-[#333333]">Imaging</h4>
                    <p class="text-sm">Total time: {imaging_time} min</p>
                    <p class="text-sm">{comparisons.get("imaging", "")}</p>
                    <p class="text-sm">Status: {imaging_icon} {imaging_text}</p>
                </div>
                """

                # Specialist Consult
                specialist_time = self.format_time(metrics.get("specialist_consult", {}).get("time", "-"))
                specialist_status = patient.get("current_status", {}).get("specialist_consult", "Not opened")
                specialist_icon, specialist_text = self._get_status_icon_and_text(specialist_status, "specialist_consult")
                details_html += f"""
                <div>
                    <h4 class="font-medium text-[#333333]">Specialist Consult</h4>
                    <p class="text-sm">Time: {specialist_time} min</p>
                    <p class="text-sm">{comparisons.get("specialist_consult", "")}</p>
                    <p class="text-sm">Status: {specialist_icon} {specialist_text}</p>
                </div>
                """

                # Reassessment
                reassessment_time = self.format_time(metrics.get("reassessment", {}).get("time", "-"))
                reassessment_status = patient.get("current_status", {}).get("reassessment", "Not completed")
                reassessment_icon, reassessment_text = self._get_status_icon_and_text(reassessment_status, "reassessment")
                details_html += f"""
                <div>
                    <h4 class="font-medium text-[#333333]">Reassessment</h4>
                    <p class="text-sm">Time: {reassessment_time} min</p>
                    <p class="text-sm">{comparisons.get("reassessment", "")}</p>
                    <p class="text-sm">Status: {reassessment_icon} {reassessment_text}</p>
                </div>
                """

                details_html += """
                        </div>
                    </td>
                </tr>
                """

                # Replace the sample table with the real data
                import re
                table_pattern = re.compile(
                    r'<tr class="expandable-row.*?</tr>\s*<tr class="detail-row".*?</tr>',
                    re.DOTALL
                )
                html_content = re.sub(table_pattern, row_html + details_html, html_content)

                # Replace the main times of each stage
                html_content = html_content.replace("{{TRIAGE_TIME}}", self.format_time(metrics.get("triage", {}).get("time", "-")))
                html_content = html_content.replace("{{ADMISSION_TIME}}", self.format_time(metrics.get("admission_consult", {}).get("time", "-")))
                html_content = html_content.replace("{{LABS_TIME}}", self.format_time(metrics.get("labs", {}).get("time", "-")))
                html_content = html_content.replace("{{IMAGING_TIME}}", self.format_time(metrics.get("imaging", {}).get("time", "-")))
                html_content = html_content.replace("{{SPECIALIST_TIME}}", self.format_time(metrics.get("specialist_consult", {}).get("time", "-")))
                html_content = html_content.replace("{{REASSESSMENT_TIME}}", self.format_time(metrics.get("reassessment", {}).get("time", "-")))

                # Replace the specific times for Labs
                html_content = html_content.replace("{{LABS_TIME_REQUEST}}", self.format_time(metrics.get("labs", {}).get("request_time", "-")))
                html_content = html_content.replace("{{LABS_TIME_RESULTS}}", self.format_time(metrics.get("labs", {}).get("results_time", "-")))

                # Replace the specific times for Imaging
                html_content = html_content.replace("{{IMAGING_TIME_REQUEST}}", self.format_time(metrics.get("imaging", {}).get("request_time", "-")))
                html_content = html_content.replace("{{IMAGING_TIME_RESULTS}}", self.format_time(metrics.get("imaging", {}).get("results_time", "-")))

                # Replace the specific times for the Specialist Consult
                html_content = html_content.replace("{{SPECIALIST_TIME_OPENING}}", self.format_time(metrics.get("specialist_consult", {}).get("opening_time", "-")))
                html_content = html_content.replace("{{SPECIALIST_TIME_COMPLETION}}", self.format_time(metrics.get("specialist_consult", {}).get("completion_time", "-")))

                # Total time
                total_time = data["total_time"]
                html_content = html_content.replace("{{TOTAL_TIME}}", self.format_time(total_time))

                # Calculate the comparisons against the area average
                comparisons = self.calculate_area_comparisons(metrics, area_averages, data["total_time"])

                html_content = html_content.replace("{{COMPARISON_TRIAGE}}", comparisons.get("triage", "-"))
                html_content = html_content.replace("{{COMPARISON_ADMISSION}}", comparisons.get("admission_consult", "-"))
                html_content = html_content.replace("{{COMPARISON_LABS}}", comparisons.get("labs", "-"))
                html_content = html_content.replace("{{COMPARISON_IMAGING}}", comparisons.get("imaging", "-"))
                html_content = html_content.replace("{{COMPARISON_SPECIALIST}}", comparisons.get("specialist_consult", "-"))
                html_content = html_content.replace("{{COMPARISON_REASSESSMENT}}", comparisons.get("reassessment", "-"))
                html_content = html_content.replace("{{COMPARISON_TOTAL}}", comparisons.get("total_time", "-"))

                # Data for the comparison charts
                charts_data = data.get("charts", {})
                if "comparison" in charts_data:
                    js_charts = self.generate_charts_update_js(charts_data)
                    if js_charts:
                        # Insert before closing body tag
                        html_content = html_content.replace('</body>', f'<script>{js_charts}</script></body>')
                    else:
                        html_content = html_content.replace('</body>', '<script>// There is no data for the charts</script></body>')

                # Make sure the individual metric divs are visible
                js_show_individual = """
                <script>
                document.addEventListener('DOMContentLoaded', function() {
                    // Set individual mode
                    document.body.setAttribute('data-current-mode', 'individual');

                    // Activate the individual tab
                    const tabIndividual = document.getElementById('tabIndividual');
                    if (tabIndividual) {
                        tabIndividual.classList.add('tab-active');
                        tabIndividual.classList.remove('text-gray-500');

                        const tabGroup = document.getElementById('tabGroup');
                        if (tabGroup) {
                            tabGroup.classList.remove('tab-active');
                            tabGroup.classList.add('text-gray-500');
                        }
                    }

                    // Show the individual components
                    document.querySelectorAll('[id^="individual-metrics-"]').forEach(el => {
                        el.classList.remove('hidden');
                    });

                    // Show the individual charts
                    const individualCharts = document.getElementById('individual-charts');
                    if (individualCharts) {
                        individualCharts.classList.remove('hidden');
                    }

                    // Show the patient table
                    const individualPatientTable = document.getElementById('individual-patient-table');
                    if (individualPatientTable) {
                        individualPatientTable.classList.remove('hidden');
                    }

                    // Hide the group components
                    document.querySelectorAll('[id^="group-metrics-"]').forEach(el => {
                        el.classList.add('hidden');
                    });

                    // Hide the group charts and SLA section
                    const groupCharts = document.getElementById('group-charts');
                    if (groupCharts) {
                        groupCharts.classList.add('hidden');
                    }

                    const slaCompliance = document.getElementById('sla-compliance');
                    if (slaCompliance) {
                        slaCompliance.classList.add('hidden');
                    }

                    // Show the correct button
                    const btnIndividual = document.getElementById('generateIndividualReport');
                    const btnGroup = document.getElementById('generateGroupReport');
                    if (btnIndividual) btnIndividual.classList.remove('hidden');
                    if (btnGroup) btnGroup.classList.add('hidden');

                    console.log("Individual mode set successfully by the initialization script.");
                });
                </script>
                """

                # Insert the script before the closing body tag
                html_content = html_content.replace('</body>', f'{js_show_individual}</body>')

                js_show_charts = """
                <script>
                document.addEventListener('DOMContentLoaded', function() {
                    setTimeout(function() {
                        // Make sure the elements are visible
                        const individualCharts = document.getElementById('individual-charts');
                        if (individualCharts) {
                            individualCharts.style.display = 'grid';
                            individualCharts.classList.remove('hidden');

                            // Regenerate the individual charts if functions are available for it
                            setTimeout(function() {
                                if (typeof updateComparisonChart === 'function') {
                                    console.log("Regenerating the comparison chart...");
                                    updateComparisonChart();
                                }

                                if (typeof updateRadarChart === 'function') {
                                    console.log("Regenerating the radar chart...");
                                    updateRadarChart();
                                }

                                console.log("Visibility and regeneration of the individual charts completed");
                            }, 200);
                        }
                    }, 800);
                });
                </script>
                """

                html_content = html_content.replace('</body>', f'{js_show_charts}</body>')

            else:
                # Group mode - Get the data from the metrics
                metrics = data["metrics"]

                # Triage
                triage = metrics.get('triage', {})
                if triage and 'statistics' in triage:
                    html_content = html_content.replace("{{TRIAGE_AVERAGE}}", self.format_time(triage['statistics'].get('average', '-')))
                    html_content = html_content.replace("{{TRIAGE_MEDIAN}}", self.format_time(triage['statistics'].get('median', '-')))
                    html_content = html_content.replace("{{TRIAGE_P90}}", self.format_time(triage['statistics'].get('p90', '-')))

                # Admission Consult
                admission = metrics.get('admission_consult', {})
                if admission and 'statistics' in admission:
                    html_content = html_content.replace("{{ADMISSION_AVERAGE}}", self.format_time(admission['statistics'].get('average', '-')))
                    html_content = html_content.replace("{{ADMISSION_MEDIAN}}", self.format_time(admission['statistics'].get('median', '-')))
                    html_content = html_content.replace("{{ADMISSION_P90}}", self.format_time(admission['statistics'].get('p90', '-')))

                # Laboratories
                labs = metrics.get('labs', {})
                if labs:
                    # Request to awaiting (Not completed to Awaiting)
                    if 'request_statistics' in labs:
                        html_content = html_content.replace("{{LABS_AVERAGE_REQ}}", self.format_time(labs['request_statistics'].get('average', '-')))
                        html_content = html_content.replace("{{LABS_MEDIAN_REQ}}", self.format_time(labs['request_statistics'].get('median', '-')))
                        html_content = html_content.replace("{{LABS_P90_REQ}}", self.format_time(labs['request_statistics'].get('p90', '-')))

                    # Awaiting to results (Awaiting to Results)
                    if 'results_statistics' in labs:
                        html_content = html_content.replace("{{LABS_AVERAGE_RES}}", self.format_time(labs['results_statistics'].get('average', '-')))
                        html_content = html_content.replace("{{LABS_MEDIAN_RES}}", self.format_time(labs['results_statistics'].get('median', '-')))
                        html_content = html_content.replace("{{LABS_P90_RES}}", self.format_time(labs['results_statistics'].get('p90', '-')))

                    if 'total_statistics' in labs:
                        html_content = html_content.replace("{{LABS_AVERAGE}}", self.format_time(labs['total_statistics'].get('average', '-')))
                        html_content = html_content.replace("{{LABS_MEDIAN}}", self.format_time(labs['total_statistics'].get('median', '-')))
                        html_content = html_content.replace("{{LABS_P90}}", self.format_time(labs['total_statistics'].get('p90', '-')))

                # Imaging
                imaging = metrics.get('imaging', {})
                if imaging:
                    # Request to awaiting
                    if 'request_statistics' in imaging:
                        html_content = html_content.replace("{{IMAGING_AVERAGE_REQ}}", self.format_time(imaging['request_statistics'].get('average', '-')))
                        html_content = html_content.replace("{{IMAGING_MEDIAN_REQ}}", self.format_time(imaging['request_statistics'].get('median', '-')))
                        html_content = html_content.replace("{{IMAGING_P90_REQ}}", self.format_time(imaging['request_statistics'].get('p90', '-')))

                    # Awaiting to results
                    if 'results_statistics' in imaging:
                        html_content = html_content.replace("{{IMAGING_AVERAGE_RES}}", self.format_time(imaging['results_statistics'].get('average', '-')))
                        html_content = html_content.replace("{{IMAGING_MEDIAN_RES}}", self.format_time(imaging['results_statistics'].get('median', '-')))
                        html_content = html_content.replace("{{IMAGING_P90_RES}}", self.format_time(imaging['results_statistics'].get('p90', '-')))

                    if 'total_statistics' in imaging:
                        html_content = html_content.replace("{{IMAGING_AVERAGE}}", self.format_time(imaging['total_statistics'].get('average', '-')))
                        html_content = html_content.replace("{{IMAGING_MEDIAN}}", self.format_time(imaging['total_statistics'].get('median', '-')))
                        html_content = html_content.replace("{{IMAGING_P90}}", self.format_time(imaging['total_statistics'].get('p90', '-')))

                # Specialist Consult
                specialist = metrics.get('specialist_consult', {})
                if specialist:
                    # Not opened to open
                    if 'opening_statistics' in specialist:
                        html_content = html_content.replace("{{SPECIALIST_AVERAGE_OPEN}}", self.format_time(specialist['opening_statistics'].get('average', '-')))
                        html_content = html_content.replace("{{SPECIALIST_MEDIAN_OPEN}}", self.format_time(specialist['opening_statistics'].get('median', '-')))
                        html_content = html_content.replace("{{SPECIALIST_P90_OPEN}}", self.format_time(specialist['opening_statistics'].get('p90', '-')))

                    # Open to completed
                    if 'completion_statistics' in specialist:
                        html_content = html_content.replace("{{SPECIALIST_AVERAGE_DONE}}", self.format_time(specialist['completion_statistics'].get('average', '-')))
                        html_content = html_content.replace("{{SPECIALIST_MEDIAN_DONE}}", self.format_time(specialist['completion_statistics'].get('median', '-')))
                        html_content = html_content.replace("{{SPECIALIST_P90_DONE}}", self.format_time(specialist['completion_statistics'].get('p90', '-')))

                    if 'total_statistics' in specialist:
                        html_content = html_content.replace("{{SPECIALIST_AVERAGE}}", self.format_time(specialist['total_statistics'].get('average', '-')))
                        html_content = html_content.replace("{{SPECIALIST_MEDIAN}}", self.format_time(specialist['total_statistics'].get('median', '-')))
                        html_content = html_content.replace("{{SPECIALIST_P90}}", self.format_time(specialist['total_statistics'].get('p90', '-')))

                # Reassessment
                reassessment = metrics.get('reassessment', {})
                if reassessment and 'statistics' in reassessment:
                    html_content = html_content.replace("{{REASSESSMENT_AVERAGE}}", self.format_time(reassessment['statistics'].get('average', '-')))
                    html_content = html_content.replace("{{REASSESSMENT_MEDIAN}}", self.format_time(reassessment['statistics'].get('median', '-')))
                    html_content = html_content.replace("{{REASSESSMENT_P90}}", self.format_time(reassessment['statistics'].get('p90', '-')))

                # Total time
                total_time = metrics.get('total_time', {})
                if total_time and 'statistics' in total_time:
                    html_content = html_content.replace("{{TOTAL_AVERAGE}}", self.format_time(total_time['statistics'].get('average', '-')))
                    html_content = html_content.replace("{{TOTAL_MEDIAN}}", self.format_time(total_time['statistics'].get('median', '-')))
                    html_content = html_content.replace("{{TOTAL_P90}}", self.format_time(total_time['statistics'].get('p90', '-')))

                # Compliance for the gauges is resolved once for both modes, above.

            # If there is SLA and metrics data, generate the JavaScript to update the status indicators
            if "sla" in data and "metrics" in data:
                js_indicators = self.generate_status_indicators_update_js(data["sla"], data["metrics"])
                # Inject the script right before the closing body tag
                html_content = html_content.replace('</body>', f'<script>{js_indicators}</script></body>')

            # If there is chart data and we are not in individual mode, generate the JavaScript to update the group charts
            if not data.get("individual", False) and "charts" in data and "timeline" in data["charts"]:
                timeline_data = data["charts"]["timeline"]
                bars_data = data["charts"]["bars"]

                # Check that timeline_data is not None before using it
                if timeline_data is not None:
                    # Create JavaScript to update the bar chart
                    bars_js = f"""
                    <script>
                    document.addEventListener('DOMContentLoaded', function() {{
                        setTimeout(function() {{
                            if (window.barChart) {{
                                window.barChart.data.datasets[0].data = {json.dumps(bars_data.get("data", []))};
                                window.barChart.update();
                                console.log("Updated bar chart with:", {json.dumps(bars_data.get("data", []))});
                            }}
                        }}, 500);
                    }});
                    </script>
                    """
                    # Create JavaScript to update the timeline chart
                    timeline_js = f"""
                    <script>
                    document.addEventListener('DOMContentLoaded', function() {{
                        // Wait for charts to be initialized
                        setTimeout(function() {{
                            if (window.timelineChart) {{
                                const labels = {json.dumps(timeline_data.get("labels", []))};
                                const data = {json.dumps(timeline_data.get("data", []))};
                                const grouping = "{timeline_data.get('grouping', 'daily')}";

                                console.log("Updating timeline chart with:", {{ labels, data, grouping }});
                                updateTimelineChart(labels, data, grouping);
                            }}
                        }}, 500);
                    }});
                    </script>
                    """
                    # Insert the script before the closing </body> tag
                    html_content = html_content.replace('</body>', f'{timeline_js}</body>')
                    # Insert the script before the closing </body> tag
                    html_content = html_content.replace('</body>', f'{bars_js}</body>')
                else:
                    print("Warning: timeline_data is None, the JavaScript generation for the charts is skipped")

            js_tab_switch = """
            <script>
            document.addEventListener('DOMContentLoaded', function() {
                console.log("DOM loaded, configuring the mode handling");

                // Check the current mode on the body
                const currentMode = document.body.getAttribute('data-current-mode') || 'group';
                console.log("Current mode detected:", currentMode);

                // Apply the visibility based on the mode
                if (currentMode === 'individual') {
                    console.log("Applying individual mode");
                    // Activate the individual tab
                    const tabIndividual = document.getElementById('tabIndividual');
                    if (tabIndividual) {
                        tabIndividual.classList.add('tab-active');
                        tabIndividual.classList.remove('text-gray-500');

                        const tabGroup = document.getElementById('tabGroup');
                        if (tabGroup) {
                            tabGroup.classList.remove('tab-active');
                            tabGroup.classList.add('text-gray-500');
                        }
                    }

                    // Show the individual components
                    document.querySelectorAll('[id^="individual-metrics-"]').forEach(el => {
                        el.classList.remove('hidden');
                        console.log("Showing individual element:", el.id);
                    });

                    const individualCharts = document.getElementById('individual-charts');
                    if (individualCharts) {
                        individualCharts.classList.remove('hidden');
                        console.log("Showing individual charts");
                    }

                    const individualPatientTable = document.getElementById('individual-patient-table');
                    if (individualPatientTable) {
                        individualPatientTable.classList.remove('hidden');
                        console.log("Showing individual patient table");
                    }

                    // Hide the group content
                    document.querySelectorAll('[id^="group-metrics-"]').forEach(el => {
                        el.classList.add('hidden');
                        console.log("Hiding group element:", el.id);
                    });

                    const groupCharts = document.getElementById('group-charts');
                    if (groupCharts) {
                        groupCharts.classList.add('hidden');
                        console.log("Hiding group charts");
                    }

                    const slaCompliance = document.getElementById('sla-compliance');
                    if (slaCompliance) {
                        slaCompliance.classList.add('hidden');
                        console.log("Hiding SLA compliance");
                    }

                    // Show the matching button
                    const btnIndividual = document.getElementById('generateIndividualReport');
                    const btnGroup = document.getElementById('generateGroupReport');
                    if (btnIndividual) btnIndividual.classList.remove('hidden');
                    if (btnGroup) btnGroup.classList.add('hidden');
                }
            });
            </script>
            """

            html_content = html_content.replace('</body>', f'{js_tab_switch}</body>')

            return self.clear_unreplaced_placeholders(html_content)

        except Exception as e:
            print(f"Error replacing data in the HTML: {str(e)}")
            traceback.print_exc()
            return self.clear_unreplaced_placeholders(html_content)

    def clear_unreplaced_placeholders(self, html_content):
        """
        Replaces any placeholder no branch above filled in.

        A stage with no data can leave its placeholder untouched. What the
        fallback has to be depends on where the placeholder sits: in the page it
        should read as missing data, but inside a script it has to stay valid
        JavaScript, because one bad token there stops every script on the page —
        including the tab switching, which strands the user in whichever report
        they were looking at.

        So the fallback is chosen per region rather than per placeholder name,
        which also covers placeholders added later.
        """
        placeholder = re.compile(r"\{\{[A-Z0-9_]+\}\}")
        parts = re.split(r"(<script\b[^>]*>.*?</script>)", html_content, flags=re.S | re.I)

        for index, part in enumerate(parts):
            if not placeholder.search(part):
                continue
            inside_script = bool(re.match(r"<script\b", part, re.I))
            parts[index] = placeholder.sub("0" if inside_script else "--", part)

        return "".join(parts)

    def export_pdf(self):
        """Exports the current report to PDF"""
        try:
            from frontend.styles.pdf_export import export_report_to_pdf

            # Show a message indicating that the export is starting
            self.show_information_message("Starting export",
                                        "The PDF export process is about to start.\n"
                                        "This may take a few moments, please wait...")

            # Give a short time so the informative message is displayed
            QTimer.singleShot(500, lambda: self._start_pdf_export())

        except Exception as e:
            print(f"Error exporting PDF: {str(e)}")
            import traceback
            traceback.print_exc()
            self.show_error_message("Export error",
                                    f"The report could not be exported to PDF: {str(e)}")

    def _start_pdf_export(self):
        """Starts the PDF export process after showing the initial message"""
        try:
            from frontend.styles.pdf_export import export_report_to_pdf

            # Call the export function with our web view
            export_report_to_pdf(self.web_view)

        except Exception as e:
            print(f"Error starting the PDF export: {str(e)}")
            import traceback
            traceback.print_exc()
            self.show_error_message("Export error",
                                    f"The report export to PDF could not be started: {str(e)}")

    def generate_status_indicators_update_js(self, sla_data, metrics_data):
        """Generates the JavaScript code that updates the KPI card status indicators based on the SLA comparison"""

        slas = {
            # Format: {triage_level: target_time_in_minutes}
            'triage': {'1': 0, '2': 30, '3': 120, '4': 30, '5': 60},
            'admission_consult': {'1': 210, '2': 210, '3': 360, '4': 420, '5': 420},
            'labs': {'1': 360, '2': 360, '3': 360, '4': 360, '5': 360},
            'imaging': {'1': 360, '2': 360, '3': 360, '4': 360, '5': 360},
            'specialist_consult': {'1': 30, '2': 45, '3': 60, '4': 120, '5': 180},
            'reassessment': {'1': 30, '2': 60, '3': 120, '4': 240, '5': 360}
        }

        js_code = """
        // Update the card classes according to the time vs the SLA
        document.addEventListener('DOMContentLoaded', function() {
            const kpiCards = document.querySelectorAll('.kpi-card');
            // Mapping from title to SLA key
            const slaMapping = {
                "Triage": "triage",
                "Admission Consult": "admission_consult",
                "Laboratories": "labs",
                "Diagnostic Imaging": "imaging",
                "Specialist Consult": "specialist_consult",
                "Reassessment": "reassessment"
            };

            // SLAs defined by triage level
            const slas = %s;

            // Real average times
            const averageTimes = %s;

            // Compliance percentages
            const compliancePercentage = %s;

            kpiCards.forEach(card => {
                const titleElement = card.querySelector('h3');
                if (!titleElement) return;

                const title = titleElement.textContent.trim();
                const slaKey = slaMapping[title];

                if (!slaKey) return;

                // Get the average time for this type
                const averageTime = averageTimes[slaKey];
                const compliance = compliancePercentage[slaKey];

                console.log(`KPI ${title}: Time ${averageTime}, Compliance ${compliance}%%`);

                // Determine the class and color based on the compliance
                const [indicator, statusClass, iconClass] = determineClasses(compliance);

                // Update the card classes
                card.classList.remove('indicator-green', 'indicator-yellow', 'indicator-red');
                card.classList.add(indicator);

                // Update the icon classes
                const iconElement = card.querySelector('.status-icon');
                if (iconElement) {
                    // Reset all status classes
                    iconElement.classList.remove('status-success', 'status-warning', 'status-danger');
                    iconElement.classList.add(statusClass);

                    // Reset icon class to bare essentials
                    iconElement.className = 'fas status-icon ' + statusClass;
                    // Add appropriate icon class
                    iconElement.classList.add(iconClass);
                }
            });
        });

        function determineClasses(percentage) {
            if (percentage === null || percentage === undefined || isNaN(percentage)) {
                return ['indicator-yellow', 'status-warning', 'fa-exclamation-triangle'];
            }

            if (percentage >= 90) {
                return ['indicator-green', 'status-success', 'fa-check-circle'];
            } else if (percentage >= 60) {
                return ['indicator-yellow', 'status-warning', 'fa-exclamation-triangle'];
            } else {
                return ['indicator-red', 'status-danger', 'fa-times-circle'];
            }
        }
        """ % (
            json.dumps(slas),
            json.dumps(self._get_average_times(metrics_data)),
            json.dumps(sla_data)
        )

        return js_code

    def _get_average_times(self, metrics):
        """Extracts the average times from the metrics for each process type"""
        times = {}

        # Triage
        if 'triage' in metrics and 'statistics' in metrics['triage']:
            times['triage'] = metrics['triage']['statistics'].get('average', 0)

        # Admission consult
        if 'admission_consult' in metrics and 'statistics' in metrics['admission_consult']:
            times['admission_consult'] = metrics['admission_consult']['statistics'].get('average', 0)

        # Laboratories (total time)
        if 'labs' in metrics and 'total_statistics' in metrics['labs']:
            times['labs'] = metrics['labs']['total_statistics'].get('average', 0)

        # Imaging (total time)
        if 'imaging' in metrics and 'total_statistics' in metrics['imaging']:
            times['imaging'] = metrics['imaging']['total_statistics'].get('average', 0)

        # Specialist consult (total time)
        if 'specialist_consult' in metrics and 'total_statistics' in metrics['specialist_consult']:
            times['specialist_consult'] = metrics['specialist_consult']['total_statistics'].get('average', 0)

        # Reassessment
        if 'reassessment' in metrics and 'statistics' in metrics['reassessment']:
            times['reassessment'] = metrics['reassessment']['statistics'].get('average', 0)

        return json.dumps(times)

    def generate_report_with_filters(self, start_date_str, end_date_str, area, report_type=None):
        """Generates a new report applying the selected filters"""
        try:
            # Validate dates
            if not start_date_str or not end_date_str:
                self.show_warning_message("Error", "Please select valid dates")
                return

            # Update the instance variables with the new filters
            self.start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            self.end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
            self.selected_area = area

            # Regenerate the report with the new data
            self.update_report_data()

            if self.current_mode == "individual" and self.selected_patient:
                additional_js_code = """
                setTimeout(function() {
                    // Force individual mode after updating the data
                    document.body.setAttribute('data-current-mode', 'individual');

                    // Simulate a click on the individual tab to make sure it is active
                    const tabIndividual = document.getElementById('tabIndividual');
                    if (tabIndividual) {
                        tabIndividual.click();

                        // Also make sure the individual content is visible
                        document.querySelectorAll('[id^="individual-metrics-"]').forEach(el => {
                            el.classList.remove('hidden');
                        });

                        // And hide the group content
                        document.querySelectorAll('[id^="group-metrics-"]').forEach(el => {
                            el.classList.add('hidden');
                        });

                        // Make sure the individual charts are visible
                        const individualCharts = document.getElementById('individual-charts');
                        if (individualCharts) individualCharts.classList.remove('hidden');

                        const groupCharts = document.getElementById('group-charts');
                        if (groupCharts) groupCharts.classList.add('hidden');
                    }
                }, 500);
                """
                self.web_view.page().runJavaScript(additional_js_code)

            # MODIFY the JavaScript - Make the area selector more robust
            js_code = f"""
            (function() {{
                // Function that tries to set the area selection
                function setAreaSelection() {{
                    var areaSelector = document.querySelector('#areaSelector select');
                    if (areaSelector) {{
                        console.log("Trying to set the selected area to: {area}");

                        // Clear any previous selection
                        for (var i = 0; i < areaSelector.options.length; i++) {{
                            areaSelector.options[i].selected = false;
                        }}

                        // Check whether the area value is "Waiting room" and convert it to "Waitingroom" for the selector
                        var areaValue = "{area}";
                        if (areaValue === "Waiting room") {{
                            areaValue = "Waitingroom";
                        }}

                        // Look for the matching option
                        var found = false;
                        for (var i = 0; i < areaSelector.options.length; i++) {{
                            if (areaSelector.options[i].value === areaValue) {{
                                areaSelector.options[i].selected = true;
                                areaSelector.selectedIndex = i;
                                found = true;
                                console.log("Area found and selected: " + areaValue);
                                break;
                            }}
                        }}

                        if (!found) {{
                            console.warn("Area not found in the selector: " + areaValue);
                        }}

                        // Store the selection for future reference
                        areaSelector.setAttribute('data-selected-area', areaValue);

                        // Make sure the change events respect this selection
                        areaSelector.addEventListener('change', function() {{
                            console.log("Selector change: new value = " + this.value);
                        }});

                        console.log("Final state of the selector:", areaSelector.value);
                        return found;
                    }}
                    return false;
                }}

                // Try to set the selection several times for extra safety
                if (!setAreaSelection()) {{
                    setTimeout(setAreaSelection, 100);
                    setTimeout(setAreaSelection, 500);
                    setTimeout(setAreaSelection, 1000);
                }}

                // Code that makes sure the search keeps working after generating the report
                function restartPatientSearch() {{
                    const searchInput = document.getElementById('searchPatient');
                    if (searchInput) {{
                        // Do not clear the field if we are in individual mode
                        if (document.body.getAttribute('data-current-mode') !== 'individual') {{
                            searchInput.value = '';
                        }}

                        // Make sure the input is enabled
                        searchInput.disabled = false;

                        // Reconnect the events if needed
                        if (!searchInput._hasSearchEvents) {{
                            searchInput.addEventListener('keypress', function(e) {{
                                if (e.key === 'Enter') {{
                                    e.preventDefault();
                                    const term = this.value.trim();
                                    if (term && window.handler) {{
                                        window.handler.searchPatients(term);
                                    }}
                                }}
                            }});
                            searchInput._hasSearchEvents = true;
                        }}
                    }}
                }}

                // Run both functions with delays to make sure the DOM is ready
                setTimeout(setAreaSelection, 100);
                setTimeout(restartPatientSearch, 500);
            }})();
            """

            self.web_view.page().runJavaScript(js_code)

            self.show_information_message("Report Generated",
                                        f"Report generated successfully for the period: {start_date_str} to {end_date_str}")
            QTimer.singleShot(700, self.configure_patient_search)

        except Exception as e:
            print(f"Error generating report: {str(e)}")
            import traceback
            traceback.print_exc()
            self.show_information_message("Error", f"Error generating the report: {str(e)}", QMessageBox.Critical)

    # Create an alias to keep compatibility with existing code
    generateReportWithFilters = generate_report_with_filters

    def change_mode(self, mode):
        """Switches between individual and group mode"""
        if mode != self.current_mode:
            self.current_mode = mode

            # Reset the selected patient if we switch to group mode
            if mode == "group":
                self.selected_patient = None

            # Update the interface immediately
            self.update_report_data()

            # Show/hide the buttons according to the mode
            js_code = """
            if ("%s" === "individual") {
                document.getElementById('generateGroupReport').classList.add('hidden');
                document.getElementById('generateIndividualReport').classList.remove('hidden');
            } else {
                document.getElementById('generateGroupReport').classList.remove('hidden');
                document.getElementById('generateIndividualReport').classList.add('hidden');
            }
            """ % mode

            self.web_view.page().runJavaScript(js_code)

    def show_error_message(self, title, message):
        """Shows a styled error message"""
        msg_box = StyledMessageBox(self, title, message, QMessageBox.Critical, "error")

        # Create a styled OK button
        btn_ok = QPushButton("OK")
        btn_ok.setCursor(Qt.PointingHandCursor)

        msg_box.addButton(btn_ok, QMessageBox.AcceptRole)
        msg_box.setDefaultButton(btn_ok)

        return msg_box.exec_()

    def show_confirmation_message(self, title, message, icon=QMessageBox.Question):
        """Shows a styled confirmation message"""
        msg_box = StyledMessageBox(self, title, message, icon, "confirmation")

        # Create the styled buttons
        btn_yes = QPushButton("Yes")
        btn_no = QPushButton("No")

        # Style the buttons if needed
        btn_yes.setCursor(Qt.PointingHandCursor)
        btn_no.setCursor(Qt.PointingHandCursor)

        msg_box.addButton(btn_yes, QMessageBox.YesRole)
        msg_box.addButton(btn_no, QMessageBox.NoRole)

        # Set the default button
        msg_box.setDefaultButton(btn_no)

        # Run the dialog
        result = msg_box.exec_()

        # Return True if "Yes" was pressed, False otherwise
        return msg_box.clickedButton() == btn_yes

    def show_information_message(self, title, message, icon=QMessageBox.Information):
        """Shows a styled informative message"""
        # Determine the style type according to the icon
        style_type = "error" if icon == QMessageBox.Critical else "info"

        msg_box = StyledMessageBox(self, title, message, icon, style_type)

        # Create a styled OK button
        btn_ok = QPushButton("OK")
        btn_ok.setCursor(Qt.PointingHandCursor)

        msg_box.addButton(btn_ok, QMessageBox.AcceptRole)

        # Set the default button
        msg_box.setDefaultButton(btn_ok)

        # Run the dialog
        return msg_box.exec_()

    def show_warning_message(self, title, message):
        """Shows a styled warning message"""
        msg_box = StyledMessageBox(self, title, message, QMessageBox.Warning, "warning")

        # Create a styled OK button
        btn_ok = QPushButton("OK")
        btn_ok.setCursor(Qt.PointingHandCursor)

        msg_box.addButton(btn_ok, QMessageBox.AcceptRole)

        # Set the default button
        msg_box.setDefaultButton(btn_ok)

        # Run the dialog
        return msg_box.exec_()

class WebHandler(QObject):
    """Bridge class for the communication between JavaScript and Python"""

    def __init__(self, report_generator):
        super().__init__()
        self.report_generator = report_generator

    @pyqtSlot()
    def exportPdf(self):
        """Exports the current report to PDF when the matching button is clicked"""
        self.report_generator.export_pdf()

    @pyqtSlot(str, str, str)
    def generateReportWithFilters(self, start_date, end_date, area):
        """Generates a new report applying the filters selected by the user"""
        self.report_generator.generate_report_with_filters(start_date, end_date, area)

    @pyqtSlot(str)
    def changeMode(self, mode):
        """Switches between display modes (individual/group)"""
        self.report_generator.change_mode(mode)

    @pyqtSlot(str)
    def searchPatients(self, term):
        """Searches patients when Enter is pressed in the search field"""
        print(f"Searching patient with term: {term}")

        # Avoid an extra search if the term looks like an already selected result
        if " - " in term and len(term.split(" - ")) >= 2:
            print(f"Ignoring search for a term that looks like an already selected result: {term}")
            return

        if term and len(term.strip()) >= 1:  # Allow searches with at least 1 character
            # Force individual mode when searching patients
            self.report_generator.current_mode = "individual"

            # Perform the search
            results = self.report_generator.search_patient(term)

            # Show the results
            self.report_generator.show_search_results(results)

    @pyqtSlot(str, str, str, str)
    def selectPatient(self, patient_id, name, document_id, location):
        """Selects a patient for the individual report"""
        print(f"WebHandler: Selecting patient ID={patient_id}, Name={name}")
        # Force individual mode before calling select_patient
        self.report_generator.current_mode = "individual"
        self.report_generator.select_patient(patient_id, name, document_id, location)

    @pyqtSlot(str, str)
    def generateIndividualReport(self, start_date, end_date):
        """Generates an individual report for the selected patient"""
        if not self.report_generator.selected_patient:
            self.report_generator.show_warning_message(
                "Error", "No patient has been selected"
            )
            return

        # Make sure we are in individual mode
        self.report_generator.current_mode = "individual"

        # Update the dates
        try:
            self.report_generator.start_date = datetime.strptime(start_date, "%Y-%m-%d")
            self.report_generator.end_date = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            # If there is an error in the date format, use the default range
            self.report_generator.start_date = datetime.now() - timedelta(days=30)
            self.report_generator.end_date = datetime.now()

        # Generate the report
        self.report_generator.update_report_data()