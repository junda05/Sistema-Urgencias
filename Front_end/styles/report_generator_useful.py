import os
import sys
import json
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
from Front_end.styles.components import StyledMessageBox, StyledButton, StyledDialog, FormField
from Back_end.ModeloMetricas import ModeloMetricas

class ReportGenerator(QDialog):
    """Clase para generar reportes visuales basados en datos de métricas"""
    
    def __init__(self, parent=None, ruta_base=None):
        super().__init__(parent)
        self.setWindowTitle("Generador de Reportes")
        self.setWindowFlags(self.windowFlags() | Qt.Window)
        
        # Establecer tamaño inicial (casi pantalla completa)
        desktop = QApplication.desktop()
        screen_rect = desktop.screenGeometry(desktop.primaryScreen())
        width = int(screen_rect.width() * 0.95)
        height = int(screen_rect.height() * 0.95)
        self.resize(width, height)
        
        # Rutas base para recursos
        self.ruta_base = ruta_base
        if not self.ruta_base:
            if getattr(sys, 'frozen', False):
                self.ruta_base = sys._MEIPASS
            else:
                self.ruta_base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # Configuración inicial
        self.modo_actual = "grupal"  # Opciones: "individual", "grupal"
        self.fecha_inicio = datetime.now() - timedelta(days=365)
        self.fecha_fin = datetime.now()
        self.area_seleccionada = "todas"
        self.paciente_seleccionado = None
        
        # Inicializar UI
        self.setup_ui()
        
    def setup_ui(self):
        """Configura la interfaz de usuario principal"""
        # Layout principal
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Contenedor para la vista web
        self.web_container = QWidget()
        self.web_layout = QVBoxLayout(self.web_container)
        self.web_layout.setContentsMargins(0, 0, 0, 0)
        
        # Configurar QWebEngineView para mostrar el informe
        self.web_view = QWebEngineView()
        self.web_layout.addWidget(self.web_view)
        
        # Crear el objeto de canal web para permitir la comunicación JS <-> Python
        self.web_channel = QWebChannel()
        self.web_handler = WebHandler(self)
        self.web_channel.registerObject("handler", self.web_handler)
        self.web_view.page().setWebChannel(self.web_channel)
        
        # Añadir el contenedor web al layout principal
        self.main_layout.addWidget(self.web_container)
        
        # Cargar plantilla HTML y aplicar datos
        self.crear_plantilla_html()
        
    def crear_plantilla_html(self):
        """Crea la plantilla HTML base con marcadores de posición para datos dinámicos"""
        html_template = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard de Informes Médicos</title>
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
        .semaforo-rojo {
            border-left: 4px solid var(--button-danger);
        }

        .semaforo-amarillo {
            border-left: 4px solid var(--button-warning);
        }

        .semaforo-verde {
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
    </style>
</head>
<body>
    <div class="container mx-auto px-4 py-6">
        <!-- Encabezado -->
        <div class="flex justify-between items-center mb-6">
            <h1 class="text-3xl font-bold">Dashboard de Métricas de Urgencias</h1>
            <div>
                <button id="exportPdf" class="btn-primary mr-2">
                    <i class="fas fa-file-pdf mr-2"></i>Exportar PDF
                </button>
            </div>
        </div>

        <!-- Pestañas principales -->
        <div class="border-b border-gray-200 mb-6">
            <div class="flex">
                <div id="tabGrupal" class="px-4 py-2 font-medium tab-active cursor-pointer">Reporte Grupal</div>
                <div id="tabIndividual" class="px-4 py-2 font-medium text-gray-500 cursor-pointer">Reporte Individual</div>
            </div>
        </div>

        <!-- Panel de control para filtros -->
        <div class="card p-4 mb-6">
            <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div>
                    <label class="block text-sm font-medium mb-1">Fecha Inicio</label>
                    <input type="date" class="w-full rounded border p-2" value="{{FECHA_INICIO}}">
                </div>
                <div>
                    <label class="block text-sm font-medium mb-1">Fecha Fin</label>
                    <input type="date" class="w-full rounded border p-2" value="{{FECHA_FIN}}">
                </div>
                
                <div id="filtroIndividual" class="col-span-2 hidden">
                    <label class="block text-sm font-medium text-[#333333] mb-1">Paciente</label>
                    <div class="relative">
                        <input type="text" id="searchPatient" class="w-full border border-gray-300 rounded-md px-3 py-2" placeholder="Buscar paciente...">
                        <div id="patientResults" class="absolute z-10 bg-white w-full mt-1 rounded-md shadow-lg hidden">
                            <div class="p-2 hover:bg-[#E8F0F7] cursor-pointer">Juan Pérez - CC 12345678</div>
                            <div class="p-2 hover:bg-[#E8F0F7] cursor-pointer">María López - CC 87654321</div>
                            <div class="p-2 hover:bg-[#E8F0F7] cursor-pointer">Carlos Rodríguez - CC 23456789</div>
                        </div>
                    </div>
                </div>
                
                <div>
                    <div id="areaSelector">
                        <label class="block text-sm font-medium text-[#333333] mb-1">Área Asistencial</label>
                        <select class="w-full border border-gray-300 rounded-md px-3 py-2">
                            <option value="todas"{{SELECTED_TODAS}}>Todas las áreas</option>
                            <option value="Antigua"{{SELECTED_ANTIGUA}}>Antigua</option>
                            <option value="Amarilla"{{SELECTED_AMARILLA}}>Amarilla</option>
                            <option value="Pediatría"{{SELECTED_PEDIATRIA}}>Pediatría</option>
                            <option value="Pasillos"{{SELECTED_PASILLOS}}>Pasillos</option>
                            <option value="Clini"{{SELECTED_CLINI}}>Clini</option>
                            <option value="Sala de espera"{{SELECTED_SALA_ESPERA}}>Sala de espera</option>
                        </select>
                    </div>
                </div>
                <div class="flex items-end">
                    <button id="generarInforme" class="btn-primary w-full">
                        <i class="fas fa-sync-alt mr-2"></i>Generar Informe
                    </button>
                </div>
            </div>
        </div>

        <!-- Tiempo Total de Atención (KPI Card separada) -->
        <div class="bg-white rounded-lg shadow-md p-4 mb-6">
            <div class="flex justify-between items-start mb-2">
                <h3 class="text-lg font-semibold text-[#333333]">Tiempo Total de Atención</h3>
                <div class="text-center">
                    <i class="fas fa-check-circle status-icon status-success"></i>
                </div>
            </div>
            <div id="metricas-individuales-total" class="hidden">
                <div class="text-3xl font-bold text-[#333333] mb-1">3h 45min</div>
                <div class="text-sm text-[#555555]">Tiempo total en urgencias</div>
                <div class="mt-2 text-sm">
                    <span class="comparison-positive">30 min menos</span> que el promedio del área
                </div>
            </div>
            
            <div id="metricas-grupales-total">
                <div class="grid grid-cols-3 gap-2 mb-2">
                    <div>
                        <div class="text-2xl font-bold text-[#333333]">{{TIEMPO_PROMEDIO_TOTAL}} min</div>
                        <div class="text-xs text-[#555555]">Promedio</div>
                    </div>
                    <div>
                        <div class="text-2xl font-bold text-[#333333]">{{TIEMPO_MEDIANA_TOTAL}} min</div>
                        <div class="text-xs text-[#555555]">Mediana</div>
                    </div>
                    <div>
                        <div class="text-2xl font-bold text-[#333333]">{{TIEMPO_P90_TOTAL}} min</div>
                        <div class="text-xs text-[#555555]">P90</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Métricas y Visualizaciones -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-6">
            <!-- Triaje -->
            <div class="kpi-card rounded-lg shadow-md p-4 semaforo-verde">
                <div class="flex justify-between items-start mb-2">
                    <h3 class="text-lg font-semibold text-[#333333]">Triage</h3>
                    <div class="text-center">
                        <i class="fas fa-check-circle status-icon status-success"></i>
                    </div>
                </div>
                <div id="metricas-individuales-triaje" class="hidden">
                    <div class="text-3xl font-bold text-[#333333] mb-1">-- min</div>
                    <div class="text-sm text-[#555555]">Tiempo de clasificación</div>
                    <div class="mt-2 text-sm">
                        <span class="comparison-positive">5 min menos</span> que el promedio del área
                    </div>
                </div>
                <div id="metricas-grupales-triaje">
                    <div class="grid grid-cols-3 gap-2 mb-2">
                        <div>
                            <div class="text-2xl font-bold text-[#333333]">{{TRIAGE_PROMEDIO}} min</div>
                            <div class="text-xs text-[#555555]">Promedio</div>
                        </div>
                        <div>
                            <div class="text-2xl font-bold text-[#333333]">{{TRIAGE_MEDIANA}} min</div>
                            <div class="text-xs text-[#555555]">Mediana</div>
                        </div>
                        <div>
                            <div class="text-2xl font-bold text-[#333333]">{{TRIAGE_P90}} min</div>
                            <div class="text-xs text-[#555555]">P90</div>
                        </div>
                    </div>
                </div>
                <div class="mt-2 text-xs text-[#555555]">
                    Tiempo desde "no realizado" hasta clasificación
                </div>
            </div>

            <!-- Consulta de Ingreso -->
            <div class="kpi-card rounded-lg shadow-md p-4 semaforo-verde">
                <div class="flex justify-between items-start mb-2">
                    <h3 class="text-lg font-semibold text-[#333333]">Consulta de Ingreso</h3>
                    <div class="text-center">
                        <i class="fas fa-check-circle status-icon status-success"></i>
                    </div>
                </div>
                <div id="metricas-individuales-ci" class="hidden">
                    <div class="text-3xl font-bold text-[#333333] mb-1">28 min</div>
                    <div class="text-sm text-[#555555]">Tiempo de atención</div>
                    <div class="mt-2 text-sm">
                        <span class="comparison-negative">8 min más</span> que el promedio del área
                    </div>
                </div>
                <div id="metricas-grupales-ci">
                    <div class="grid grid-cols-3 gap-2 mb-2">
                        <div>
                            <div class="text-2xl font-bold text-[#333333]">{{CI_PROMEDIO}} min</div>
                            <div class="text-xs text-[#555555]">Promedio</div>
                        </div>
                        <div>
                            <div class="text-2xl font-bold text-[#333333]">{{CI_MEDIANA}} min</div>
                            <div class="text-xs text-[#555555]">Mediana</div>
                        </div>
                        <div>
                            <div class="text-2xl font-bold text-[#333333]">{{CI_P90}} min</div>
                            <div class="text-xs text-[#555555]">P90</div>
                        </div>
                    </div>
                </div>
                <div class="mt-2 text-xs text-[#555555]">
                    Tiempo desde "No realizado" hasta "Realizado"
                </div>
            </div>

            <!-- Laboratorios -->
            <div class="kpi-card rounded-lg shadow-md p-4 semaforo-amarillo">
                <div class="flex justify-between items-start mb-2">
                    <h3 class="text-lg font-semibold text-[#333333]">Laboratorios</h3>
                    <div class="text-center">
                        <i class="fas fa-exclamation-triangle status-icon status-warning"></i>
                    </div>
                </div>
                <div id="metricas-individuales-lab" class="hidden">
                    <div class="grid grid-cols-2 gap-2">
                        <div>
                            <div class="text-xl font-bold text-[#333333] mb-1">15 min</div>
                            <div class="text-xs text-[#555555]">Solicitud a espera</div>
                        </div>
                        <div>
                            <div class="text-xl font-bold text-[#333333] mb-1">-- min</div>
                            <div class="text-xs text-[#555555]">Espera a resultados</div>
                        </div>
                    </div>
                    <div class="mt-2 text-sm">
                        <span class="comparison-positive">5 min menos</span> que el promedio
                    </div>
                </div>
                <div id="metricas-grupales-lab">
                    <div class="grid grid-cols-2 gap-2 mb-2">
                        <div>
                            <div class="text-sm font-medium text-[#333333]">No realizado a espera</div>
                            <div class="grid grid-cols-3 gap-1">
                                <div>
                                    <div class="text-base font-bold text-[#333333]">{{LABS_PROMEDIO_SE}} min</div>
                                    <div class="text-xs text-[#555555]">Prom</div>
                                </div>
                                <div>
                                    <div class="text-base font-bold text-[#333333]">{{LABS_MEDIANA_SE}} min</div>
                                    <div class="text-xs text-[#555555]">Med</div>
                                </div>
                                <div>
                                    <div class="text-base font-bold text-[#333333]">{{LABS_P90_SE}} min</div>
                                    <div class="text-xs text-[#555555]">P90</div>
                                </div>
                            </div>
                        </div>
                        <div>
                            <div class="text-sm font-medium text-[#333333]">Espera a resultados:</div>
                            <div class="grid grid-cols-3 gap-1">
                                <div>
                                    <div class="text-base font-bold text-[#333333]">{{LABS_PROMEDIO_ER}} min</div>
                                    <div class="text-xs text-[#555555]">Prom</div>
                                </div>
                                <div>
                                    <div class="text-base font-bold text-[#333333]">{{LABS_MEDIANA_ER}} min</div>
                                    <div class="text-xs text-[#555555]">Med</div>
                                </div>
                                <div>
                                    <div class="text-base font-bold text-[#333333]">{{LABS_P90_ER}} min</div>
                                    <div class="text-xs text-[#555555]">P90</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Imágenes Diagnósticas -->
            <div class="kpi-card rounded-lg shadow-md p-4 semaforo-verde">
                <div class="flex justify-between items-start mb-2">
                    <h3 class="text-lg font-semibold text-[#333333]">Imágenes Diagnósticas</h3>
                    <div class="text-center">
                        <i class="fas fa-check-circle status-icon status-success"></i>
                    </div>
                </div>
                <div id="metricas-individuales-ix" class="hidden">
                    <div class="grid grid-cols-2 gap-2">
                        <div>
                            <div class="text-xl font-bold text-[#333333] mb-1">{{IX_PROMEDIO_SE}} min</div>
                            <div class="text-xs text-[#555555]">No realizado a espera</div>
                        </div>
                        <div>
                            <div class="text-xl font-bold text-[#333333] mb-1">{{IX_MEDIANA_SE}} min</div>
                            <div class="text-xs text-[#555555]">Espera a resultados</div>
                        </div>
                    </div>
                    <div class="mt-2 text-sm">
                        <span class="comparison-positive">10 min menos</span> que el promedio
                    </div>
                </div>
                <div id="metricas-grupales-ix">
                    <div class="grid grid-cols-2 gap-2 mb-2">
                        <div>
                            <div class="text-sm font-medium text-[#333333]">No realizado a espera</div>
                            <div class="grid grid-cols-3 gap-1">
                                <div>
                                    <div class="text-base font-bold text-[#333333]">{{IX_PROMEDIO_SE}} min</div>
                                    <div class="text-xs text-[#555555]">Prom</div>
                                </div>
                                <div>
                                    <div class="text-base font-bold text-[#333333]">{{IX_MEDIANA_SE}} min</div>
                                    <div class="text-xs text-[#555555]">Med</div>
                                </div>
                                <div>
                                    <div class="text-base font-bold text-[#333333]">{{IX_P90_SE}} min</div>
                                    <div class="text-xs text-[#555555]">P90</div>
                                </div>
                            </div>
                        </div>
                        <div>
                            <div class="text-sm font-medium text-[#333333]">Espera a resultados:</div>
                            <div class="grid grid-cols-3 gap-1">
                                <div>
                                    <div class="text-base font-bold text-[#333333]">{{IX_PROMEDIO_ER}} min</div>
                                    <div class="text-xs text-[#555555]">Prom</div>
                                </div>
                                <div>
                                    <div class="text-base font-bold text-[#333333]">{{IX_MEDIANA_ER}} min</div>
                                    <div class="text-xs text-[#555555]">Med</div>
                                </div>
                                <div>
                                    <div class="text-base font-bold text-[#333333]">{{IX_P90_ER}} min</div>
                                    <div class="text-xs text-[#555555]">P90</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Interconsulta -->
            <div class="kpi-card rounded-lg shadow-md p-4 semaforo-amarillo">
                <div class="flex justify-between items-start mb-2">
                    <h3 class="text-lg font-semibold text-[#333333]">Interconsulta</h3>
                    <div class="text-center">
                        <i class="fas fa-exclamation-triangle status-icon status-warning"></i>
                    </div>
                </div>
                <div id="metricas-individuales-ic" class="hidden">
                    <div class="grid grid-cols-2 gap-2">
                        <div>
                            <div class="text-xl font-bold text-[#333333] mb-1">22 min</div>
                            <div class="text-xs text-[#555555]">No abierta a abierta</div>
                        </div>
                        <div>
                            <div class="text-xl font-bold text-[#333333] mb-1">-- min</div>
                            <div class="text-xs text-[#555555]">Abierta a realizada</div>
                        </div>
                    </div>
                    <div class="mt-2 text-sm">
                        <span class="comparison-negative">7 min más</span> que el promedio
                    </div>
                </div>
                <div id="metricas-grupales-ic">
                    <div class="grid grid-cols-2 gap-2 mb-2">
                        <div>
                            <div class="text-sm font-medium text-[#333333]">No abierta a abierta</div>
                            <div class="grid grid-cols-3 gap-1">
                                <div>
                                    <div class="text-base font-bold text-[#333333]">{{IC_PROMEDIO_NA}} min</div>
                                    <div class="text-xs text-[#555555]">Prom</div>
                                </div>
                                <div>
                                    <div class="text-base font-bold text-[#333333]">{{IC_MEDIANA_NA}} min</div>
                                    <div class="text-xs text-[#555555]">Med</div>
                                </div>
                                <div>
                                    <div class="text-base font-bold text-[#333333]">{{IC_P90_NA}} min</div>
                                    <div class="text-xs text-[#555555]">P90</div>
                                </div>
                            </div>
                        </div>
                        <div>
                            <div class="text-sm font-medium text-[#333333]">Abierta a realizada:</div>
                            <div class="grid grid-cols-3 gap-1">
                                <div>
                                    <div class="text-base font-bold text-[#333333]">{{IC_PROMEDIO_AR}} min</div>
                                    <div class="text-xs text-[#555555]">Prom</div>
                                </div>
                                <div>
                                    <div class="text-base font-bold text-[#333333]">{{IC_MEDIANA_AR}} min</div>
                                    <div class="text-xs text-[#555555]">Med</div>
                                </div>
                                <div>
                                    <div class="text-base font-bold text-[#333333]">{{IC_P90_AR}} min</div>
                                    <div class="text-xs text-[#555555]">P90</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Re-valoración -->
            <div class="kpi-card rounded-lg shadow-md p-4 semaforo-rojo">
                <div class="flex justify-between items-start mb-2">
                    <h3 class="text-lg font-semibold text-[#333333]">Re-valoración</h3>
                    <div class="text-center">
                        <i class="fas fa-times-circle status-icon status-danger"></i>
                    </div>
                </div>
                <div id="metricas-individuales-rv" class="hidden">
                    <div class="text-3xl font-bold text-[#333333] mb-1">-- min</div>
                    <div class="text-sm text-[#555555]">Tiempo pendiente</div>
                    <div class="mt-2 text-sm">
                        <span class="comparison-neutral">Pendiente de realizar</span>
                    </div>
                </div>
                <div id="metricas-grupales-rv">
                    <div class="grid grid-cols-3 gap-2 mb-2">
                        <div>
                            <div class="text-2xl font-bold text-[#333333]">{{RV_PROMEDIO}} min</div>
                            <div class="text-xs text-[#555555]">Promedio</div>
                        </div>
                        <div>
                            <div class="text-2xl font-bold text-[#333333]">{{RV_MEDIANA}} min</div>
                            <div class="text-xs text-[#555555]">Mediana</div>
                        </div>
                        <div>
                            <div class="text-2xl font-bold text-[#333333]">{{RV_P90}} min</div>
                            <div class="text-xs text-[#555555]">P90</div>
                        </div>
                    </div>
                </div>
                <div class="mt-2 text-xs text-[#555555]">
                    Tiempo desde "no realizada" hasta "realizada"
                </div>
            </div>
        </div>

        <!-- Gráficos y Datos Detallados -->
        <div id="graficos-grupales" class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <!-- Gráfico de línea temporal -->
            <div class="card p-4">
                <h2 class="text-xl font-semibold mb-4">Evolución Temporal</h2>
                <div>
                    <canvas id="timelineChart" height="300"></canvas>
                </div>
            </div>
            
            <!-- Gráfico de barras comparativas -->
            <div class="card p-4">
                <h2 class="text-xl font-semibold mb-4">Tiempos promedio por etapa</h2>
                <div>
                    <canvas id="barChart" height="300"></canvas>
                </div>
            </div>
        </div>

        <!-- Métricas de cumplimiento SLA -->
        <div id="cumplimiento-sla">
            <h2 class="text-2xl font-bold mb-4">Cumplimiento de SLA</h2>
            <div class="grid grid-cols-2 md:grid-cols-6 gap-4 mb-6">
                <!-- Triaje -->
                <div class="card p-4 text-center">
                    <h3 class="text-lg font-medium mb-2">Triage</h3>
                    <div class="gauge-container w-24 h-24 mx-auto">
                        <canvas id="gaugeTriaje"></canvas>
                        <div class="gauge-value">{{CUMPLIMIENTO_TRIAGE}}%</div>
                    </div>
                </div>
                <!-- Consulta de Ingreso -->
                <div class="card p-4 text-center">
                    <h3 class="text-lg font-medium mb-2">C. Ingreso</h3>
                    <div class="gauge-container w-24 h-24 mx-auto">
                        <canvas id="gaugeCI"></canvas>
                        <div class="gauge-value">{{CUMPLIMIENTO_CI}}%</div>
                    </div>
                </div>
                <!-- Laboratorios -->
                <div class="card p-4 text-center">
                    <h3 class="text-lg font-medium mb-2">Labs</h3>
                    <div class="gauge-container w-24 h-24 mx-auto">
                        <canvas id="gaugeLab"></canvas>
                        <div class="gauge-value">{{CUMPLIMIENTO_LABS}}%</div>
                    </div>
                </div>
                <!-- Imágenes -->
                <div class="card p-4 text-center">
                    <h3 class="text-lg font-medium mb-2">Imágenes</h3>
                    <div class="gauge-container w-24 h-24 mx-auto">
                        <canvas id="gaugeIX"></canvas>
                        <div class="gauge-value">{{CUMPLIMIENTO_IX}}%</div>
                    </div>
                </div>
                <!-- Interconsulta -->
                <div class="card p-4 text-center">
                    <h3 class="text-lg font-medium mb-2">Interconsulta</h3>
                    <div class="gauge-container w-24 h-24 mx-auto">
                        <canvas id="gaugeIC"></canvas>
                        <div class="gauge-value">{{CUMPLIMIENTO_IC}}%</div>
                    </div>
                </div>
                <!-- Revaloración -->
                <div class="card p-4 text-center">
                    <h3 class="text-lg font-medium mb-2">Revaloración</h3>
                    <div class="gauge-container w-24 h-24 mx-auto">
                        <canvas id="gaugeRV"></canvas>
                        <div class="gauge-value">{{CUMPLIMIENTO_RV}}%</div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Gráficos para reporte individual -->
        <div id="graficos-individuales" class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6 hidden">
            <!-- Comparación con el área -->
            <div class="bg-white rounded-lg shadow-md p-4">
                <h3 class="text-lg font-semibold text-[#333333] mb-4">Comparación con el área</h3>
                <div class="chart-container">
                    <canvas id="comparisonChart"></canvas>
                </div>
            </div>

            <!-- Comparación con todas las áreas -->
            <div class="bg-white rounded-lg shadow-md p-4">
                <h3 class="text-lg font-semibold text-[#333333] mb-4">Comparación con todas las áreas</h3>
                <div class="chart-container">
                    <canvas id="allAreasChart"></canvas>
                </div>
            </div>
        </div>
        
        <!-- Tabla de paciente individual -->
        <div id="tabla-paciente-individual" class="bg-white rounded-lg shadow-md p-4 mb-6 hidden">
            <h3 class="text-lg font-semibold text-[#333333] mb-4">Detalle del paciente</h3>
            <div class="overflow-x-auto">
                <table class="min-w-full divide-y divide-gray-200">
                    <thead>
                        <tr>
                            <th class="px-4 py-3 bg-[#E6E6E6] text-left text-xs font-medium text-[#333333] uppercase tracking-wider">Paciente</th>
                            <th class="px-4 py-3 bg-[#E6E6E6] text-left text-xs font-medium text-[#333333] uppercase tracking-wider">Documento</th>
                            <th class="px-4 py-3 bg-[#E6E6E6] text-left text-xs font-medium text-[#333333] uppercase tracking-wider">Área</th>
                            <th class="px-4 py-3 bg-[#E6E6E6] text-left text-xs font-medium text-[#333333] uppercase tracking-wider">Ingreso</th>
                            <th class="px-4 py-3 bg-[#E6E6E6] text-left text-xs font-medium text-[#333333] uppercase tracking-wider">Tiempo Total</th>
                            <th class="px-4 py-3 bg-[#E6E6E6] text-left text-xs font-medium text-[#333333] uppercase tracking-wider">Estado</th>
                            <th class="px-4 py-3 bg-[#E6E6E6] text-left text-xs font-medium text-[#333333] uppercase tracking-wider"></th>
                        </tr>
                    </thead>
                    <tbody class="bg-white divide-y divide-gray-200">
                        <tr class="expandable-row table-row-odd">
                            <td class="px-4 py-3 whitespace-nowrap">Juan Pérez</td>
                            <td class="px-4 py-3 whitespace-nowrap">CC 12345678</td>
                            <td class="px-4 py-3 whitespace-nowrap">Urgencias</td>
                            <td class="px-4 py-3 whitespace-nowrap">2023-12-15 08:30</td>
                            <td class="px-4 py-3 whitespace-nowrap">3h 45min</td>
                            <td class="px-4 py-3 whitespace-nowrap">
                                <span class="px-2 py-1 text-xs rounded-full bg-green-100 text-green-800">Alta</span>
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
                                        <h4 class="font-medium text-[#333333]">Triaje</h4>
                                        <p class="text-sm">Tiempo: 12 min <span class="comparison-positive">(-5 min)</span></p>
                                        <p class="text-sm">Estado: <i class="fas fa-check-circle text-[#28a745]"></i> Completado</p>
                                    </div>
                                    <div>
                                        <h4 class="font-medium text-[#333333]">Consulta de Ingreso</h4>
                                        <p class="text-sm">Tiempo: 28 min <span class="comparison-negative">(+8 min)</span></p>
                                        <p class="text-sm">Estado: <i class="fas fa-check-circle text-[#28a745]"></i> Completado</p>
                                    </div>
                                    <div>
                                        <h4 class="font-medium text-[#333333]">Laboratorios</h4>
                                        <p class="text-sm">Tiempo total: 55 min <span class="comparison-positive">(-10 min)</span></p>
                                        <p class="text-sm">Estado: <i class="fas fa-check-circle text-[#28a745]"></i> Completado</p>
                                    </div>
                                    <div>
                                        <h4 class="font-medium text-[#333333]">Imágenes</h4>
                                        <p class="text-sm">Tiempo total: 53 min <span class="comparison-positive">(-17 min)</span></p>
                                        <p class="text-sm">Estado: <i class="fas fa-check-circle text-[#28a745]"></i> Completado</p>
                                    </div>
                                    <div>
                                        <h4 class="font-medium text-[#333333]">Interconsulta</h4>
                                        <p class="text-sm">Tiempo: 22 min <span class="comparison-negative">(+7 min)</span></p>
                                        <p class="text-sm">Estado: <i class="fas fa-exclamation-triangle text-[#E6B800]"></i> Abierta</p>
                                    </div>
                                    <div>
                                        <h4 class="font-medium text-[#333333]">Re-valoración</h4>
                                        <p class="text-sm">Tiempo: Pendiente</p>
                                        <p class="text-sm">Estado: <i class="fas fa-times-circle text-[#B75353]"></i> No realizada</p>
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
        // Inicializar el canal web para comunicación con Python
        window.onload = function() {
            new QWebChannel(qt.webChannelTransport, function(channel) {
                window.handler = channel.objects.handler;
                console.log("QWebChannel establecido correctamente");
                
                // Configurar listeners de eventos
                setupEventListeners();
                
                // Inicializar los gráficos
                initializeCharts();
            });
        };

        function setupEventListeners() {
            // Exportar a PDF
            document.getElementById('exportPdf').addEventListener('click', function() {
                window.handler.exportarPdf();
            });
            
            // Generar informe con filtros
            document.getElementById('generarInforme').addEventListener('click', function() {
                // Get date inputs directly - there are only two in the form
                const dateInputs = document.querySelectorAll('input[type="date"]');
                const fechaInicio = dateInputs[0].value;
                const fechaFin = dateInputs[1].value;
                
                // Get area selector safely
                const areaSelect = document.querySelector('#areaSelector select');
                const area = areaSelect ? areaSelect.value : 'todas';
                
                console.log("Generating report with:", fechaInicio, fechaFin, area);
                window.handler.generarInformeConFiltros(fechaInicio, fechaFin, area);
                
                // Reiniciar estado después de generar informe para asegurar visibilidad correcta
                setTimeout(aplicarEstadoActual, 300);
            });
            
            // Funcionalidad de pestañas
            document.getElementById('tabIndividual').addEventListener('click', function() {
                this.classList.add('tab-active');
                this.classList.remove('text-gray-500');
                
                const tabGrupal = document.getElementById('tabGrupal');
                if (tabGrupal) {
                    tabGrupal.classList.remove('tab-active');
                    tabGrupal.classList.add('text-gray-500');
                }
                
                // Aplicar estado actualizado
                aplicarEstadoActual();
            });

            document.getElementById('tabGrupal').addEventListener('click', function() {
                this.classList.add('tab-active');
                this.classList.remove('text-gray-500');
                
                const tabIndividual = document.getElementById('tabIndividual');
                if (tabIndividual) {
                    tabIndividual.classList.remove('tab-active');
                    tabIndividual.classList.add('text-gray-500');
                }
                
                // Aplicar estado actualizado
                aplicarEstadoActual();
            });

            // Funcionalidad de autocompletar
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
            
            // Funcionalidad de filas expandibles
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
            let titleText = 'Evolución Temporal';
            if (grouping === 'hourly') {
                titleText += ' (Por hora)';
            } else if (grouping === 'daily') {
                titleText += ' (Diaria)';
            } else if (grouping === 'weekly') {
                titleText += ' (Semanal)';
            } else if (grouping === 'monthly') {
                titleText += ' (Mensual)';
            } else if (grouping === 'quarterly') {
                titleText += ' (Trimestral)';
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
            'rgba(34, 197, 94, 0.7)',  // Verde para Triage
            'rgba(59, 130, 246, 0.7)',  // Azul para CI
            'rgba(245, 158, 11, 0.7)',  // Naranja para Labs
            'rgba(139, 92, 246, 0.7)',  // Morado para IX
            'rgba(236, 72, 153, 0.7)',  // Rosa para IC
            'rgba(239, 68, 68, 0.7)'    // Rojo para RV
        ];

        function initializeCharts() {
            // Configuración común para los gráficos gauge
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
            
            // Datos de ejemplo para gráficos
            const timelineLabels = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun']; // Reemplazar con datos reales
            const timelineData = [12, 15, 18, 14, 11, 13];                     // Reemplazar con datos reales
            
            const barLabels = ['Triage', 'Consulta de ingreso', 'Laboratorios', 'Imágenes diagnósticas', 'Interconsulta', 'Revaloración'];      // Reemplazar con datos reales
            const barData = [5, 10, 15, 8, 12, 7];                            // Reemplazar con datos reales
            
            // Inicializar gráfico de línea temporal
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
                            display: false  // Esta es la línea clave que oculta la leyenda
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Minutos'
                            }
                        }
                    }
                }
            });
            
            // Inicializar gráfico de barras comparativas
            const barCtx = document.getElementById('barChart').getContext('2d');
            window.barChart = new Chart(barCtx, {
                type: 'bar',
                data: {
                    labels: ['Triage', 'Consulta de ingreso', 'Laboratorios', 'Imágenes diagnósticas', 'Interconsulta', 'Revaloración'],
                    datasets: [{
                        data: [
                            {{TRIAGE_PROMEDIO}}, 
                            {{CI_PROMEDIO}}, 
                            {{LABS_PROMEDIO}}, 
                            {{IX_PROMEDIO}}, 
                            {{IC_PROMEDIO}}, 
                            {{RV_PROMEDIO}}
                        ],
                        backgroundColor: colorPalette, // Usar la paleta de colores común
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
                                text: 'Minutos'
                            }
                        }
                    }
                }
            });
            
            // Gráfico de comparación individual con área
            const comparisonCtx = document.getElementById('comparisonChart').getContext('2d');
            const comparisonChart = new Chart(comparisonCtx, {
                type: 'bar',
                data: {
                    labels: ['Triage', 'Consulta de Ingreso', 'Laboratorios', 'Imágenes', 'Interconsulta', 'Revaloración'],
                    datasets: [
                        {
                            label: 'Paciente',
                            data: [12, 28, 55, 53, 22, 0],
                            backgroundColor: '#5385B7',
                            borderWidth: 1
                        },
                        {
                            label: 'Promedio del área',
                            data: [17, 20, 65, 70, 15, 40],
                            backgroundColor: '#E6B800',
                            borderWidth: 1
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: true,
                            position: 'top'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Minutos'
                            }
                        }
                    }
                }
            });
            
            // Gráfico de comparación con todas las áreas
            const allAreasCtx = document.getElementById('allAreasChart').getContext('2d');
            const allAreasChart = new Chart(allAreasCtx, {
                type: 'radar',
                data: {
                    labels: ['Triaje', 'Consulta de Ingreso', 'Laboratorios', 'Imágenes', 'Interconsulta', 'Re-valoración'],
                    datasets: [
                        {
                            label: 'Paciente',
                            data: [12, 28, 55, 53, 22, 0],
                            backgroundColor: 'rgba(83, 133, 183, 0.2)',
                            borderColor: '#5385B7',
                            borderWidth: 2,
                            pointBackgroundColor: '#5385B7'
                        },
                        {
                            label: 'Promedio general',
                            data: [17, 20, 65, 70, 15, 40],
                            backgroundColor: 'rgba(230, 184, 0, 0.2)',
                            borderColor: '#E6B800',
                            borderWidth: 2,
                            pointBackgroundColor: '#E6B800'
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: true,
                            position: 'top'
                        }
                    },
                    scales: {
                        r: {
                            beginAtZero: true
                        }
                    }
                }
            });
            
            // Inicializar gráficos gauge con sus valores reales y colores correspondientes
            createGauge('gaugeTriaje', {{CUMPLIMIENTO_TRIAGE}}, 0);
            createGauge('gaugeCI', {{CUMPLIMIENTO_CI}}, 1);
            createGauge('gaugeLab', {{CUMPLIMIENTO_LABS}}, 2);
            createGauge('gaugeIX', {{CUMPLIMIENTO_IX}}, 3);
            createGauge('gaugeIC', {{CUMPLIMIENTO_IC}}, 4);
            createGauge('gaugeRV', {{CUMPLIMIENTO_RV}}, 5);
        }

        function createGauge(elementId, value, colorIndex) {
            const ctx = document.getElementById(elementId).getContext('2d');
            const gaugeChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    datasets: [{
                        data: [value, 100 - value],
                        backgroundColor: [
                            colorPalette[colorIndex], // Usar el color correspondiente de la paleta
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
            
        // Establecer estado inicial según la pestaña activa
        document.addEventListener('DOMContentLoaded', function() {
            // Verificar qué pestaña está activa inicialmente
            const tabGrupalActivo = document.getElementById('tabGrupal').classList.contains('tab-active');
            
            // Aplicar visibilidad inicial correcta
            if (tabGrupalActivo) {
                document.getElementById('tabGrupal').click();
            } else {
                document.getElementById('tabIndividual').click();
            }
        });

        // Función dedicada para aplicar el estado correcto en cualquier momento
        function aplicarEstadoActual() {
            const tabGrupalActivo = document.getElementById('tabGrupal').classList.contains('tab-active');
            
            // Manejar visibilidad del filtro individual
            const filtroIndividual = document.getElementById('filtroIndividual');
            if (filtroIndividual) {
                if (tabGrupalActivo) {
                    filtroIndividual.classList.add('hidden');
                } else {
                    filtroIndividual.classList.remove('hidden');
                }
            }
            
            // Manejar visibilidad de métricas
            if (tabGrupalActivo) {
                document.querySelectorAll('[id^="metricas-individuales-"]').forEach(el => el.classList.add('hidden'));
                document.querySelectorAll('[id^="metricas-grupales-"]').forEach(el => el.classList.remove('hidden'));
                
                const graficosGrupales = document.getElementById('graficos-grupales');
                if (graficosGrupales) graficosGrupales.classList.remove('hidden');
                
                const cumplimientoSla = document.getElementById('cumplimiento-sla');
                if (cumplimientoSla) cumplimientoSla.classList.remove('hidden');
                
                const graficosIndividuales = document.getElementById('graficos-individuales');
                if (graficosIndividuales) graficosIndividuales.classList.add('hidden');
                
                const tablaPacienteIndividual = document.getElementById('tabla-paciente-individual');
                if (tablaPacienteIndividual) tablaPacienteIndividual.classList.add('hidden');
            } else {
                document.querySelectorAll('[id^="metricas-individuales-"]').forEach(el => el.classList.remove('hidden'));
                document.querySelectorAll('[id^="metricas-grupales-"]').forEach(el => el.classList.add('hidden'));
                
                const graficosGrupales = document.getElementById('graficos-grupales');
                if (graficosGrupales) graficosGrupales.classList.add('hidden');
                
                const cumplimientoSla = document.getElementById('cumplimiento-sla');
                if (cumplimientoSla) cumplimientoSla.classList.add('hidden');
                
                const graficosIndividuales = document.getElementById('graficos-individuales');
                if (graficosIndividuales) graficosIndividuales.classList.remove('hidden');
                
                const tablaPacienteIndividual = document.getElementById('tabla-paciente-individual');
                if (tablaPacienteIndividual) tablaPacienteIndividual.classList.remove('hidden');
            }
        }

        // Llamar a la función inmediatamente y también en DOMContentLoaded
        aplicarEstadoActual();
        window.addEventListener('load', aplicarEstadoActual);
    </script>
</body>
</html>
        """
        
        # Guardar la plantilla en caché
        self.html_template = html_template
        
        # Cargar los datos y actualizar la plantilla
        self.actualizar_datos_informe()
           
    def actualizar_datos_informe(self):
        """Actualiza los datos del informe con las métricas obtenidas de la base de datos"""
        if not hasattr(self, 'html_template'):
            return
            
        # Obtener datos reales de métricas desde el modelo
        datos = self.obtener_datos_reales()
        if not datos:
            self.mostrar_mensaje_error(
                    self, "Error", "No se pudieron obtener los datos para el informe.")
            return
        
        # Preparamos los datos para reemplazar en el HTML
        html_content = self.html_template
        
        # Reemplazar marcadores con datos reales
        html_content = self.reemplazar_datos_en_html(html_content, datos)
        
        # Cargar el contenido HTML actualizado en la vista web
        self.web_view.setHtml(html_content, baseUrl=QUrl.fromLocalFile(self.ruta_base + "/"))
        
        if self.modo_actual == "individual" and self.paciente_seleccionado:
            js_code = """
            setTimeout(function() {
                // Aseguramos que la vista individual esté activa
                const tabIndividual = document.getElementById('tabIndividual');
                if (tabIndividual && !tabIndividual.classList.contains('tab-active')) {
                    tabIndividual.click();
                }
                
                // Reinicializamos la búsqueda si es necesario
                if (document.getElementById('searchPatient')) {
                    document.getElementById('searchPatient').disabled = false;
                }
            }, 200);
            """
            self.web_view.page().runJavaScript(js_code)
            
            # Volver a configurar la búsqueda
            QTimer.singleShot(300, self.configurar_busqueda_pacientes)
        
    def create_report_template(self, file_path):
        """Crea la plantilla HTML base para el informe si no existe"""
        # Extraer el contenido HTML base del informe de ejemplo
        report_html_path = os.path.join(self.ruta_base, "report.html")
        try:
            with open(report_html_path, 'r', encoding='utf-8') as file:
                html_content = file.read()
            
            # Guardar el contenido como plantilla
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(html_content)
                
        except Exception as e:
            self.mostrar_mensaje_error(
                    self, "Error", f"Error al crear la plantilla de informe: {str(e)}")
    
    def update_report_data(self):
        """Actualiza los datos del informe con las métricas actuales"""
        if not hasattr(self, 'html_template'):
            return
        
        # En una implementación real, aquí obtendríamos los datos reales de ModeloMetricas
        # Por ahora usamos los datos de ejemplo
        html_content = self.html_template
        
        # Aplicar los filtros seleccionados
        html_content = self.apply_filters_to_html(html_content)
        
        # Actualizar los datos en la vista web
        self.web_view.setHtml(html_content, baseUrl=QUrl.fromLocalFile(self.ruta_base + "/"))
    
    def apply_filters_to_html(self, html_content):
        """Aplica los filtros seleccionados al contenido HTML"""
        # Implementar la lógica para modificar el HTML según los filtros seleccionados
        # Por ejemplo, mostrar/ocultar elementos según el modo (individual/grupal)
        
        # Por ahora, simplemente devolvemos el mismo contenido sin modificar
        return html_content

    def generar_informe(self):
        """Método principal para generar el informe basado en los filtros seleccionados"""
        # Esta función será llamada desde la interfaz principal
        # Actualizará los datos y mostrará el informe
        self.update_report_data()

    def cambiarModo(self, modo):
        """Cambia entre modo individual y grupal"""
        if modo != self.modo_actual:
            self.modo_actual = modo
            
            # Resetear el paciente seleccionado si cambiamos a modo grupal
            if modo == "grupal":
                self.paciente_seleccionado = None
                
            # Actualizar interfaz inmediatamente
            self.actualizar_datos_informe()
            
            # Asegurarse que la búsqueda de pacientes se configure correctamente en modo individual
            if modo == "individual":
                QTimer.singleShot(300, self.configurar_busqueda_pacientes)
    
    def generar_js_actualizacion_graficos(self, datos_graficos):
        """Genera el código JavaScript para actualizar los gráficos"""
        # Get grouping from timeline data
        grouping = datos_graficos["timeline"].get("grouping", "daily")
        
        js_code = """
        // Actualizar gráfico de línea de tiempo
        if (Array.isArray(%s) && %s.length > 0) {
            updateTimelineChart(%s, %s, '%s');
        } else {
            // No hay datos, mostrar mensaje en el gráfico
            if (window.timelineChart) {
                window.timelineChart.data.labels = [];
                window.timelineChart.data.datasets[0].data = [];
                window.timelineChart.options.plugins.title = {
                    display: true,
                    text: 'No hay datos disponibles para este filtro',
                    font: {size: 16, weight: 'bold'}
                };
                window.timelineChart.update();
            }
        }
        
        // Actualizar gráfico de barras
        barChart.data.datasets[0].data = %s;
        barChart.update();
        
        // Actualizar gráficos gauge
        gaugeTriaje.data.datasets[0].data = [%d, %d];
        gaugeTriaje.update();
        
        gaugeCI.data.datasets[0].data = [%d, %d];
        gaugeCI.update();
        
        gaugeLab.data.datasets[0].data = [%d, %d];
        gaugeLab.update();
        
        gaugeIX.data.datasets[0].data = [%d, %d];
        gaugeIX.update();
        
        gaugeIC.data.datasets[0].data = [%d, %d];
        gaugeIC.update();
        
        gaugeRV.data.datasets[0].data = [%d, %d];
        gaugeRV.update();
        """ % (
            json.dumps(datos_graficos["timeline"]["etiquetas"]),
            json.dumps(datos_graficos["timeline"]["datos"]),
            grouping,  # Pass grouping info to updateTimelineChart
            json.dumps(datos_graficos["barras"]["data"]),
            datos_graficos["gauge"]["triaje"], 100 - datos_graficos["gauge"]["triaje"],
            datos_graficos["gauge"]["ci"], 100 - datos_graficos["gauge"]["ci"],
            datos_graficos["gauge"]["labs"], 100 - datos_graficos["gauge"]["labs"],
            datos_graficos["gauge"]["ix"], 100 - datos_graficos["gauge"]["ix"],
            datos_graficos["gauge"]["ic"], 100 - datos_graficos["gauge"]["ic"],
            datos_graficos["gauge"]["rv"], 100 - datos_graficos["gauge"]["rv"]
        )
        
        return js_code
        
    # Añadir a ReportGenerator para crear la plantilla HTML si no existe
    def create_report_template(self, file_path):
        """Crea la plantilla HTML base para el informe si no existe"""
        try:
            # Buscar primero el archivo report.html en la ruta base
            report_html_path = os.path.join(self.ruta_base, "report.html")
            
            if os.path.exists(report_html_path):
                # Si existe, usamos ese archivo como plantilla
                with open(report_html_path, 'r', encoding='utf-8') as file:
                    html_content = file.read()
            else:
                # Si no existe, creamos una plantilla básica con la estructura necesaria
                html_content = self.get_basic_template_html()
            
            # Modificar el HTML para hacerlo compatible con QWebEngineView y añadir puentes de comunicación
            modified_html = self.prepare_html_for_webengine(html_content)
            
            # Guardar la plantilla modificada
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(modified_html)
                
            print(f"Plantilla HTML creada en: {file_path}")
            
        except Exception as e:
            print(f"Error al crear la plantilla HTML: {str(e)}")
            self.mostrar_mensaje_informacion("Error", f"Error al crear la plantilla de informe: {str(e)}", QMessageBox.Critical)

    def prepare_html_for_webengine(self, html_content):
        """Prepara el HTML para ser compatible con QWebEngineView"""
        # Insertar el código del canal web justo antes del cierre </head>
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

    def obtener_datos_reales(self):
        """Obtiene los datos reales de métricas desde el modelo"""
        try:
            # Convertir fechas a formato string para la consulta
            fecha_inicio_str = self.fecha_inicio.strftime('%Y-%m-%d')
            fecha_fin_str = self.fecha_fin.strftime('%Y-%m-%d')
            
            # Determinar área para filtrar (None si es "todas")
            area = None if self.area_seleccionada == "todas" else self.area_seleccionada
            
            # Para la vista individual, obtener datos del paciente específico
            if self.modo_actual == "individual" and self.paciente_seleccionado:
                datos_paciente = ModeloMetricas.obtener_metricas_paciente(self.paciente_seleccionado)
                
                if not datos_paciente:
                    return None
                    
                # Obtener métricas generales del área para comparación
                metricas_area = datos_paciente["promedios_area"]
                
                # Datos para gráficos de comparación
                etiquetas = ['Triaje', 'Consulta de Ingreso', 'Laboratorios', 'Imágenes', 'Interconsulta', 'Revaloración']
                datos_paciente_comp = [
                    datos_paciente['metricas']['triage']['tiempo'] or 0,
                    datos_paciente['metricas']['ci']['tiempo'] or 0,
                    datos_paciente['metricas']['labs']['tiempo'] or 0,
                    datos_paciente['metricas']['ix']['tiempo'] or 0,
                    datos_paciente['metricas']['inter']['tiempo'] or 0,
                    datos_paciente['metricas']['rv']['tiempo'] or 0,
                ]
                
                datos_area_comp = [
                    metricas_area['triage']['estadisticas']['promedio'] or 0,
                    metricas_area['consulta_ingreso']['estadisticas']['promedio'] or 0,
                    metricas_area['laboratorios']['estadisticas']['promedio'] or 0,
                    metricas_area['imagenes']['estadisticas']['promedio'] or 0,
                    metricas_area['interconsulta']['estadisticas_total']['promedio'] or 0,
                    metricas_area['revaloracion']['estadisticas']['promedio'] or 0
                ]
                
                # Obtener datos generales para el gráfico de radar
                datos_generales = ModeloMetricas.obtener_todas_metricas(fecha_inicio=fecha_inicio_str, fecha_fin=fecha_fin_str)
                datos_generales_comp = [
                    datos_generales['triage']['estadisticas']['promedio'] or 0,
                    datos_generales['consulta_ingreso']['estadisticas']['promedio'] or 0,
                    datos_generales['laboratorios']['estadisticas']['promedio'] or 0,
                    datos_generales['imagenes']['estadisticas']['promedio'] or 0,
                    datos_generales['interconsulta']['estadisticas_total']['promedio'] or 0,
                    datos_generales['revaloracion']['estadisticas']['promedio'] or 0
                ]
                
                return {
                    "individual": True,
                    "paciente": datos_paciente["paciente"],
                    "metricas": datos_paciente["metricas"],
                    "graficos": {
                        "barras": {
                            "etiquetas": etiquetas,
                            "datos_paciente": datos_paciente_comp,
                            "datos_area": datos_area_comp
                        },
                        "radar": {
                            "etiquetas": etiquetas,
                            "datos_paciente": datos_paciente_comp,
                            "datos_generales": datos_generales_comp
                        }
                    }
                }
            else:
                # Para vista grupal, obtener métricas agregadas
                # Obtener todas las métricas mediante el método general
                metricas = ModeloMetricas.obtener_todas_metricas(
                    area=area,
                    fecha_inicio=fecha_inicio_str,
                    fecha_fin=fecha_fin_str
                )
                
                # Obtener datos para los gráficos
                datos_graficos = {
                    "timeline": ModeloMetricas.generar_datos_linea_tiempo(
                        area=area,
                        fecha_inicio=fecha_inicio_str,
                        fecha_fin=fecha_fin_str
                    ),
                    "barras": ModeloMetricas.generar_datos_barras_comparativas(
                        area=area,
                        fecha_inicio=fecha_inicio_str,
                        fecha_fin=fecha_fin_str
                    )
                }
                
                # Obtener datos de cumplimiento de SLA
                datos_sla = ModeloMetricas.obtener_metricas_cumplimiento_sla(
                    area=area,
                    fecha_inicio=fecha_inicio_str,
                    fecha_fin=fecha_fin_str
                )
                
                # Integrar todos los datos
                return {
                    "individual": False,
                    "metricas": metricas,
                    "graficos": datos_graficos,
                    "sla": datos_sla,
                    "configuracion": {
                        "fecha_inicio": fecha_inicio_str,
                        "fecha_fin": fecha_fin_str,
                        "area": self.area_seleccionada
                    }
                }
            
        except Exception as e:
            print(f"Error al obtener datos reales: {str(e)}")
            self.mostrar_mensaje_advertencia("Advertencia", 
                                        f"Error al obtener datos de métricas: {str(e)}.")
            return None

    def reemplazar_datos_en_html(self, html_content, datos):
        """Reemplaza los marcadores de posición en el HTML con datos reales"""
        try:
            # Datos de configuración generales
            html_content = html_content.replace("{{FECHA_INICIO}}", datos["configuracion"]["fecha_inicio"])
            html_content = html_content.replace("{{FECHA_FIN}}", datos["configuracion"]["fecha_fin"])
            
            area_actual = self.area_seleccionada if hasattr(self, 'area_seleccionada') else "todas"
            areas = ["todas", "Antigua", "Amarilla", "Pediatría", "Pasillos", "Clini", "Salaespera"]
            
            for area in areas:
                key = area.upper()
                if area == "Salaespera":
                    key = "SALA_ESPERA"
                marker = f"{{{{SELECTED_{key}}}}}"
                
                if area == area_actual:
                    html_content = html_content.replace(marker, " selected")
                else:
                    html_content = html_content.replace(marker, "")
            
            if datos.get("individual", False):
                # Código para modo individual
                paciente = datos["paciente"]
                metricas = datos["metricas"]
                # Implementar la lógica para insertar datos individuales
                # ...
            else:
                # Modo grupal - Obtener datos de las métricas
                metricas = datos["metricas"]
                
                # Triage
                triage = metricas.get('triage', {})
                if triage and 'estadisticas' in triage:
                    html_content = html_content.replace("{{TRIAGE_PROMEDIO}}", str(triage['estadisticas'].get('promedio', '-')))
                    html_content = html_content.replace("{{TRIAGE_MEDIANA}}", str(triage['estadisticas'].get('mediana', '-')))
                    html_content = html_content.replace("{{TRIAGE_P90}}", str(triage['estadisticas'].get('p90', '-')))
                
                # Consulta de Ingreso (CI)
                ci = metricas.get('consulta_ingreso', {})
                if ci and 'estadisticas' in ci:
                    html_content = html_content.replace("{{CI_PROMEDIO}}", str(ci['estadisticas'].get('promedio', '-')))
                    html_content = html_content.replace("{{CI_MEDIANA}}", str(ci['estadisticas'].get('mediana', '-')))
                    html_content = html_content.replace("{{CI_P90}}", str(ci['estadisticas'].get('p90', '-')))
                
                # Laboratorios
                labs = metricas.get('laboratorios', {})
                # Usar las claves correctas para labs basadas en la estructura de ModeloMetricas
                if labs:
                    # Solicitud a espera (No realizado a En espera)
                    if 'estadisticas_solicitud' in labs:
                        html_content = html_content.replace("{{LABS_PROMEDIO_SE}}", str(labs['estadisticas_solicitud'].get('promedio', '-')))
                        html_content = html_content.replace("{{LABS_MEDIANA_SE}}", str(labs['estadisticas_solicitud'].get('mediana', '-')))
                        html_content = html_content.replace("{{LABS_P90_SE}}", str(labs['estadisticas_solicitud'].get('p90', '-')))
                    
                    # Espera a resultados (En espera a Resultados)
                    if 'estadisticas_resultados' in labs:
                        html_content = html_content.replace("{{LABS_PROMEDIO_ER}}", str(labs['estadisticas_resultados'].get('promedio', '-')))
                        html_content = html_content.replace("{{LABS_MEDIANA_ER}}", str(labs['estadisticas_resultados'].get('mediana', '-')))
                        html_content = html_content.replace("{{LABS_P90_ER}}", str(labs['estadisticas_resultados'].get('p90', '-')))

                    if 'estadisticas_total' in labs:
                        html_content = html_content.replace("{{LABS_PROMEDIO}}", str(labs['estadisticas_total'].get('promedio', '-')))
                        html_content = html_content.replace("{{LABS_MEDIANA}}", str(labs['estadisticas_total'].get('mediana', '-')))
                        html_content = html_content.replace("{{LABS_P90}}", str(labs['estadisticas_total'].get('p90', '-')))             
                
                # Imágenes (IX)
                ix = metricas.get('imagenes', {})
                if ix:
                    # Solicitud a espera
                    if 'estadisticas_solicitud' in ix:
                        html_content = html_content.replace("{{IX_PROMEDIO_SE}}", str(ix['estadisticas_solicitud'].get('promedio', '-')))
                        html_content = html_content.replace("{{IX_MEDIANA_SE}}", str(ix['estadisticas_solicitud'].get('mediana', '-')))
                        html_content = html_content.replace("{{IX_P90_SE}}", str(ix['estadisticas_solicitud'].get('p90', '-')))
                    
                    # Espera a resultados
                    if 'estadisticas_resultados' in ix:
                        html_content = html_content.replace("{{IX_PROMEDIO_ER}}", str(ix['estadisticas_resultados'].get('promedio', '-')))
                        html_content = html_content.replace("{{IX_MEDIANA_ER}}", str(ix['estadisticas_resultados'].get('mediana', '-')))
                        html_content = html_content.replace("{{IX_P90_ER}}", str(ix['estadisticas_resultados'].get('p90', '-')))
                
                    if 'estadisticas_total' in ix:
                        html_content = html_content.replace("{{IX_PROMEDIO}}", str(ix['estadisticas_total'].get('promedio', '-')))
                        html_content = html_content.replace("{{IX_MEDIANA}}", str(ix['estadisticas_total'].get('mediana', '-')))
                        html_content = html_content.replace("{{IX_P90}}", str(ix['estadisticas_total'].get('p90', '-')))    
                
                # Interconsulta
                ic = metricas.get('interconsulta', {})
                if ic:
                    # No abierta a abierta
                    if 'estadisticas_apertura' in ic:
                        html_content = html_content.replace("{{IC_PROMEDIO_NA}}", str(ic['estadisticas_apertura'].get('promedio', '-')))
                        html_content = html_content.replace("{{IC_MEDIANA_NA}}", str(ic['estadisticas_apertura'].get('mediana', '-')))
                        html_content = html_content.replace("{{IC_P90_NA}}", str(ic['estadisticas_apertura'].get('p90', '-')))
                    
                    # Abierta a realizada
                    if 'estadisticas_realizacion' in ic:
                        html_content = html_content.replace("{{IC_PROMEDIO_AR}}", str(ic['estadisticas_realizacion'].get('promedio', '-')))
                        html_content = html_content.replace("{{IC_MEDIANA_AR}}", str(ic['estadisticas_realizacion'].get('mediana', '-')))
                        html_content = html_content.replace("{{IC_P90_AR}}", str(ic['estadisticas_realizacion'].get('p90', '-')))
                
                    if 'estadisticas_total' in ic:
                        html_content = html_content.replace("{{IC_PROMEDIO}}", str(ic['estadisticas_total'].get('promedio', '-')))
                        html_content = html_content.replace("{{IC_MEDIANA}}", str(ic['estadisticas_total'].get('mediana', '-')))
                        html_content = html_content.replace("{{IC_P90}}", str(ic['estadisticas_total'].get('p90', '-')))    
                
                # Revaloración
                rv = metricas.get('revaloracion', {})
                if rv and 'estadisticas' in rv:
                    html_content = html_content.replace("{{RV_PROMEDIO}}", str(rv['estadisticas'].get('promedio', '-')))
                    html_content = html_content.replace("{{RV_MEDIANA}}", str(rv['estadisticas'].get('mediana', '-')))
                    html_content = html_content.replace("{{RV_P90}}", str(rv['estadisticas'].get('p90', '-')))
                
                # Tiempo total
                tiempo_total = metricas.get('tiempo_total', {})
                if tiempo_total and 'estadisticas' in tiempo_total:
                    html_content = html_content.replace("{{TIEMPO_PROMEDIO_TOTAL}}", str(tiempo_total['estadisticas'].get('promedio', '-')))
                    html_content = html_content.replace("{{TIEMPO_MEDIANA_TOTAL}}", str(tiempo_total['estadisticas'].get('mediana', '-')))
                    html_content = html_content.replace("{{TIEMPO_P90_TOTAL}}", str(tiempo_total['estadisticas'].get('p90', '-')))
                    
                # Datos para gráficos de gauge (cumplimiento de SLA)
                sla = datos["sla"]
                html_content = html_content.replace("{{CUMPLIMIENTO_TRIAGE}}", str(sla["triage"]))
                html_content = html_content.replace("{{CUMPLIMIENTO_CI}}", str(sla["ci"]))
                html_content = html_content.replace("{{CUMPLIMIENTO_LABS}}", str(sla["labs"]))
                html_content = html_content.replace("{{CUMPLIMIENTO_IX}}", str(sla["ix"]))
                html_content = html_content.replace("{{CUMPLIMIENTO_IC}}", str(sla["inter"]))
                html_content = html_content.replace("{{CUMPLIMIENTO_RV}}", str(sla["rv"]))

            # Si hay datos de SLA y métricas, generar JavaScript para actualizar los semáforos
            if "sla" in datos and "metricas" in datos:
                js_semaforos = self.generar_js_actualizacion_semaforos(datos["sla"], datos["metricas"])
                # Inyectar el script justo antes del cierre del body
                html_content = html_content.replace('</body>', f'<script>{js_semaforos}</script></body>')
                
            if not datos.get("individual", False) and "graficos" in datos and "timeline" in datos["graficos"]:
                timeline_data = datos["graficos"]["timeline"]
                barras_data = datos["graficos"]["barras"]
                
                # Verificar que timeline_data no sea None antes de usarlo
                if timeline_data is not None:
                    # Create JavaScript to update the bar chart
                    barras_js = f"""
                    <script>
                    document.addEventListener('DOMContentLoaded', function() {{
                        setTimeout(function() {{
                            if (window.barChart) {{
                                window.barChart.data.datasets[0].data = {json.dumps(barras_data.get("datos", []))};
                                window.barChart.update();
                                console.log("Updated bar chart with:", {json.dumps(barras_data.get("datos", []))});
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
                                const labels = {json.dumps(timeline_data.get("etiquetas", []))};
                                const data = {json.dumps(timeline_data.get("datos", []))};
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
                    html_content = html_content.replace('</body>', f'{barras_js}</body>')
                else:
                    print("Advertencia: timeline_data es None, se omite la generación de JavaScript para gráficos")
            
            return html_content
            
        except Exception as e:
            print(f"Error al reemplazar datos en HTML: {str(e)}")
            traceback.print_exc()
            return html_content

    def exportar_pdf(self):
        pass
    
    def generar_js_actualizacion_semaforos(self, datos_sla, datos_metricas):
        """Genera el código JavaScript para actualizar los semáforos de las tarjetas KPI según comparativa con SLA"""
        
        slas = {
            # Formato: {clase_triage: tiempo_objetivo_en_minutos}
            'triage': {'1': 0, '2': 30, '3': 120, '4': 30, '5': 60},
            'ci': {'1': 210, '2': 210, '3': 360, '4': 420, '5': 420},
            'labs': {'1': 360, '2': 360, '3': 360, '4': 360, '5': 360},
            'ix': {'1': 360, '2': 360, '3': 360, '4': 360, '5': 360},
            'inter': {'1': 30, '2': 45, '3': 60, '4': 120, '5': 180},
            'rv': {'1': 30, '2': 60, '3': 120, '4': 240, '5': 360}
        }
        
        js_code = """
        // Actualizar las clases de las tarjetas según el tiempo vs SLA
        document.addEventListener('DOMContentLoaded', function() {
            const kpiCards = document.querySelectorAll('.kpi-card');
            // Mapeo de título a clave de SLA
            const slaMapping = {
                "Triage": "triage",
                "Consulta de Ingreso": "ci",
                "Laboratorios": "labs",
                "Imágenes Diagnósticas": "ix",
                "Interconsulta": "inter",
                "Re-valoración": "rv"
            };
            
            // SLA definidos por clase de triage
            const slas = %s;
            
            // Tiempos promedio reales
            const tiempoPromedios = %s;
            
            // Porcentajes de cumplimiento
            const porcentajeCumplimiento = %s;
            
            kpiCards.forEach(card => {
                const titleElement = card.querySelector('h3');
                if (!titleElement) return;
                
                const title = titleElement.textContent.trim();
                const slaKey = slaMapping[title];
                
                if (!slaKey) return;
                
                // Obtener el tiempo promedio para este tipo
                const tiempoPromedio = tiempoPromedios[slaKey];
                const cumplimiento = porcentajeCumplimiento[slaKey];
                
                console.log(`KPI ${title}: Tiempo ${tiempoPromedio}, Cumplimiento ${cumplimiento}%%`);
                
                // Determinar clase y color en base al cumplimiento
                const [semaforo, statusClass, iconClass] = determinarClases(cumplimiento);
                
                // Actualizar las clases del card
                card.classList.remove('semaforo-verde', 'semaforo-amarillo', 'semaforo-rojo');
                card.classList.add(semaforo);
                
                // Actualizar las clases del ícono
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

        function determinarClases(porcentaje) {
            if (porcentaje === null || porcentaje === undefined || isNaN(porcentaje)) {
                return ['semaforo-amarillo', 'status-warning', 'fa-exclamation-triangle'];
            }
            
            if (porcentaje >= 90) {
                return ['semaforo-verde', 'status-success', 'fa-check-circle'];
            } else if (porcentaje >= 60) {
                return ['semaforo-amarillo', 'status-warning', 'fa-exclamation-triangle'];
            } else {
                return ['semaforo-rojo', 'status-danger', 'fa-times-circle'];
            }
        }
        """ % (
            json.dumps(slas),
            self._obtener_tiempos_promedio(datos_metricas),
            json.dumps(datos_sla)
        )
        
        return js_code

    def _obtener_tiempos_promedio(self, metricas):
        """Extrae los tiempos promedio de las métricas para cada tipo de proceso"""
        tiempos = {}
        
        # Triage
        if 'triage' in metricas and 'estadisticas' in metricas['triage']:
            tiempos['triage'] = metricas['triage']['estadisticas'].get('promedio', 0)
        
        # Consulta de ingreso
        if 'consulta_ingreso' in metricas and 'estadisticas' in metricas['consulta_ingreso']:
            tiempos['ci'] = metricas['consulta_ingreso']['estadisticas'].get('promedio', 0)
        
        # Laboratorios (tiempo total)
        if 'laboratorios' in metricas and 'estadisticas_total' in metricas['laboratorios']:
            tiempos['labs'] = metricas['laboratorios']['estadisticas_total'].get('promedio', 0)
        
        # Imágenes (tiempo total)
        if 'imagenes' in metricas and 'estadisticas_total' in metricas['imagenes']:
            tiempos['ix'] = metricas['imagenes']['estadisticas_total'].get('promedio', 0)
        
        # Interconsulta (tiempo total)
        if 'interconsulta' in metricas and 'estadisticas_total' in metricas['interconsulta']:
            tiempos['inter'] = metricas['interconsulta']['estadisticas_total'].get('promedio', 0)
        
        # Revaloración
        if 'revaloracion' in metricas and 'estadisticas' in metricas['revaloracion']:
            tiempos['rv'] = metricas['revaloracion']['estadisticas'].get('promedio', 0)
        
        return json.dumps(tiempos)
    
    def generar_informe_con_filtros(self, fecha_inicio_str, fecha_fin_str, area, tipo_reporte=None):
        """Genera un nuevo informe aplicando los filtros seleccionados"""
        try:
            # Validate dates
            if not fecha_inicio_str or not fecha_fin_str:
                self.mostrar_mensaje_advertencia("Advertencia", "Por favor seleccione fechas válidas.")
                return
                    
            # Actualizar las variables de instancia con los nuevos filtros
            self.fecha_inicio = datetime.strptime(fecha_inicio_str, "%Y-%m-%d")
            self.fecha_fin = datetime.strptime(fecha_fin_str, "%Y-%m-%d")
            self.area_seleccionada = area
            
            # Regenerar el informe con los nuevos datos
            self.actualizar_datos_informe()
            
            # MODIFICAR el JavaScript - Hacer más robusto el selector de área
            js_code = f"""
            (function() {{
                // Función para intentar establecer la selección de área
                function setAreaSelection() {{
                    var areaSelector = document.querySelector('#areaSelector select');
                    if (areaSelector) {{
                        console.log("Intentando establecer área seleccionada a: {area}");
                        
                        // Limpiar cualquier selección previa
                        for (var i = 0; i < areaSelector.options.length; i++) {{
                            areaSelector.options[i].selected = false;
                        }}
                        
                        // Verificar si el valor del área es "Sala de espera", convertirlo a "Salaespera" para el selector
                        var valorArea = "{area}";
                        if (valorArea === "Sala de espera") {{
                            valorArea = "Salaespera";
                        }}
                        
                        // Buscar la opción correspondiente
                        var encontrada = false;
                        for (var i = 0; i < areaSelector.options.length; i++) {{
                            if (areaSelector.options[i].value === valorArea) {{
                                areaSelector.options[i].selected = true;
                                areaSelector.selectedIndex = i;
                                encontrada = true;
                                console.log("Área encontrada y seleccionada: " + valorArea);
                                break;
                            }}
                        }}
                        
                        if (!encontrada) {{
                            console.warn("Área no encontrada en el selector: " + valorArea);
                        }}
                        
                        // Guardar la selección para futura referencia
                        areaSelector.setAttribute('data-selected-area', valorArea);
                        
                        // Asegurar que los eventos de cambio respetan esta selección
                        areaSelector.addEventListener('change', function() {{
                            console.log("Cambio en selector: nuevo valor = " + this.value);
                        }});
                        
                        console.log("Estado final del selector:", areaSelector.value);
                        return encontrada;
                    }} 
                    return false;
                }}
                
                // Intentar establecer la selección varias veces para mayor seguridad
                if (!setAreaSelection()) {{
                    setTimeout(setAreaSelection, 100);
                    setTimeout(setAreaSelection, 500);
                    setTimeout(setAreaSelection, 1000);
                }}
            }})();
            """
            
            self.web_view.page().runJavaScript(js_code)
            
            self.mostrar_mensaje_informacion("Informe Generado", 
                                        f"Informe generado con éxito para el período: {fecha_inicio_str} a {fecha_fin_str}")

        except Exception as e:
            print(f"Error generating report: {str(e)}")
            traceback.print_exc()
            self.mostrar_mensaje_informacion("Error", f"Error al generar informe: {str(e)}", QMessageBox.Critical)

    # Crear un alias para mantener la compatibilidad con código existente
    generarInformeConFiltros = generar_informe_con_filtros

    def mostrar_mensaje_error(self, titulo, mensaje):
        """Muestra un mensaje de error estilizado"""
        msg_box = StyledMessageBox(self, titulo, mensaje, QMessageBox.Critical, "error")
        
        # Crear botón OK estilizado
        btn_ok = QPushButton("Aceptar")
        btn_ok.setCursor(Qt.PointingHandCursor)
        
        msg_box.addButton(btn_ok, QMessageBox.AcceptRole)
        msg_box.setDefaultButton(btn_ok)
        
        return msg_box.exec_()
    
    def mostrar_mensaje_confirmacion(self, titulo, mensaje, icon=QMessageBox.Question):
        """Muestra un mensaje de confirmación estilizado"""
        msg_box = StyledMessageBox(self, titulo, mensaje, icon, "confirmation")
        
        # Crear botones estilizados
        btn_si = QPushButton("Sí")
        btn_no = QPushButton("No")
        
        # Estilizar los botones si es necesario
        btn_si.setCursor(Qt.PointingHandCursor)
        btn_no.setCursor(Qt.PointingHandCursor)
        
        msg_box.addButton(btn_si, QMessageBox.YesRole)
        msg_box.addButton(btn_no, QMessageBox.NoRole)
        
        # Establecer botón predeterminado
        msg_box.setDefaultButton(btn_no)
        
        # Ejecutar cuadro de diálogo
        resultado = msg_box.exec_()
        
        # Devolver True si se presionó "Sí", False en caso contrario
        return msg_box.clickedButton() == btn_si

    def mostrar_mensaje_informacion(self, titulo, mensaje, icon=QMessageBox.Information):
        """Muestra un mensaje informativo estilizado"""
        # Determinar el tipo de estilo según el ícono
        style_type = "error" if icon == QMessageBox.Critical else "info"
        
        msg_box = StyledMessageBox(self, titulo, mensaje, icon, style_type)
        
        # Crear botón OK estilizado
        btn_ok = QPushButton("Aceptar")
        btn_ok.setCursor(Qt.PointingHandCursor)
        
        msg_box.addButton(btn_ok, QMessageBox.AcceptRole)
        
        # Establecer botón predeterminado
        msg_box.setDefaultButton(btn_ok)
        
        # Ejecutar cuadro de diálogo
        return msg_box.exec_()

    def mostrar_mensaje_advertencia(self, titulo, mensaje):
        """Muestra un mensaje de advertencia estilizado"""
        msg_box = StyledMessageBox(self, titulo, mensaje, QMessageBox.Warning, "warning")
        
        # Crear botón OK estilizado
        btn_ok = QPushButton("Aceptar")
        btn_ok.setCursor(Qt.PointingHandCursor)
        
        msg_box.addButton(btn_ok, QMessageBox.AcceptRole)
        
        # Establecer botón predeterminado
        msg_box.setDefaultButton(btn_ok)
        
        # Ejecutar cuadro de diálogo
        return msg_box.exec_()

class WebHandler(QObject):
    """Clase puente para comunicación entre JavaScript y Python"""
    
    def __init__(self, report_generator):
        super().__init__()
        self.report_generator = report_generator
    
    @pyqtSlot()
    def exportarPdf(self):
        """Exporta el informe actual a PDF cuando se hace clic en el botón correspondiente"""
        self.report_generator.exportar_pdf() 
    
    @pyqtSlot(str, str, str)
    def generarInformeConFiltros(self, fecha_inicio, fecha_fin, area):
        """Genera un nuevo informe aplicando los filtros seleccionados por el usuario"""
        self.report_generator.generar_informe_con_filtros(fecha_inicio, fecha_fin, area)
    
    @pyqtSlot(str)
    def cambiarModo(self, modo):
        """Cambia entre modos de visualización (individual/grupal)"""
        self.report_generator.cambiarModo(modo)