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
        self.crear_plantilla_html()
        QTimer.singleShot(2000, self.configurar_busqueda_pacientes)
        
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
        
        .chart-container {
            position: relative;
            height: 350px;  /* Altura fija para los gráficos */
            width: 100%;
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
                        <input type="text" id="searchPatient" class="w-full border border-gray-300 rounded-md px-3 py-2" placeholder="Buscar por nombre o documento...">
                        <div id="patientResults" class="absolute z-10 bg-white w-full mt-1 rounded-md shadow-lg hidden max-h-60 overflow-y-auto">
                            <!-- Los resultados de búsqueda se cargarán dinámicamente aquí -->
                        </div>
                    </div>
                    <p class="text-xs text-gray-500 mt-1">Presione Enter para buscar o escriba al menos 3 caracteres</p>
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
                    <button id="generarInformeGrupal" class="btn-primary w-full">
                        <i class="fas fa-sync-alt mr-2"></i>Generar Informe Grupal
                    </button>
                    <button id="generarInformeIndividual" class="btn-primary w-full hidden">
                        <i class="fas fa-sync-alt mr-2"></i>Generar Informe Individual
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
                <div class="text-3xl font-bold text-[#333333] mb-1">{{TIEMPO_TOTAL}} min</div>
                <div class="text-sm text-[#555555]">Tiempo de clasificación</div>
                <div class="mt-2 text-sm">
                    {{COMPARACION_TOTAL}}
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
                <div id="metricas-individuales-triage" class="hidden">
                    <div class="text-3xl font-bold text-[#333333] mb-1">{{TRIAGE_TIEMPO}} min</div>
                    <div class="text-sm text-[#555555]">Tiempo de clasificación</div>
                    <div class="mt-2 text-sm">
                        {{COMPARACION_TRIAGE}}
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
                    Tiempo desde "No realizado" hasta clasificación
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
                    <div class="text-3xl font-bold text-[#333333] mb-1">{{CI_TIEMPO}} min</div>
                    <div class="text-sm text-[#555555]">Tiempo de atención</div>
                    <div class="mt-2 text-sm">
                        {{COMPARACION_CI}}
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
                            <div class="text-xl font-bold text-[#333333] mb-1">{{LABS_TIEMPO_NR}} min</div>
                            <div class="text-xs text-[#555555]">Solicitud a espera</div>
                        </div>
                        <div>
                            <div class="text-xl font-bold text-[#333333] mb-1">{{LABS_TIEMPO_ER}} min</div>
                            <div class="text-xs text-[#555555]">Espera a resultados</div>
                        </div>
                    </div>
                    <div class="mt-2 text-sm">
                        {{COMPARACION_LABS}}
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
                            <div class="text-xl font-bold text-[#333333] mb-1">{{IX_TIEMPO_NR}} min</div>
                            <div class="text-xs text-[#555555]">No realizado a espera</div>
                        </div>
                        <div>
                            <div class="text-xl font-bold text-[#333333] mb-1">{{IX_TIEMPO_ER}} min</div>
                            <div class="text-xs text-[#555555]">Espera a resultados</div>
                        </div>
                    </div>
                    <div class="mt-2 text-sm">
                        {{COMPARACION_IX}}
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
                            <div class="text-xl font-bold text-[#333333] mb-1">{{INTER_TIEMPO_NA}} min</div>
                            <div class="text-xs text-[#555555]">No abierta a abierta</div>
                        </div>
                        <div>
                            <div class="text-xl font-bold text-[#333333] mb-1">{{INTER_TIEMPO_AR}} min</div>
                            <div class="text-xs text-[#555555]">Abierta a realizada</div>
                        </div>
                    </div>
                    <div class="mt-2 text-sm">
                        {{COMPARACION_INTER}}
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
                    <h3 class="text-lg font-semibold text-[#333333]">Revaloración</h3>
                    <div class="text-center">
                        <i class="fas fa-times-circle status-icon status-danger"></i>
                    </div>
                </div>
                <div id="metricas-individuales-rv" class="hidden">
                    <div class="text-3xl font-bold text-[#333333] mb-1">{{RV_TIEMPO}} min</div>
                    <div class="text-sm text-[#555555]">Tiempo pendiente</div>
                    <div class="mt-2 text-sm">
                        {{COMPARACION_RV}}
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
                            <td class="px-4 py-3 whitespace-nowrap">Jose Mauricio Unda Ortiz</td>
                            <td class="px-4 py-3 whitespace-nowrap">1114565784</td>
                            <td class="px-4 py-3 whitespace-nowrap">Amarilla</td>
                            <td class="px-4 py-3 whitespace-nowrap">2025-05-02 09:39:27</td>
                            <td class="px-4 py-3 whitespace-nowrap">56 min</td>
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
                                        <h4 class="font-medium text-[#333333]">Triage</h4>
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
                                        <h4 class="font-medium text-[#333333]">Revaloración</h4>
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
            
            // Generar informe grupal
            document.getElementById('generarInformeGrupal').addEventListener('click', function() {
                // Get date inputs
                const dateInputs = document.querySelectorAll('input[type="date"]');
                const fechaInicio = dateInputs[0].value;
                const fechaFin = dateInputs[1].value;
                
                // Get area selector safely
                const areaSelect = document.querySelector('#areaSelector select');
                const area = areaSelect ? areaSelect.value : 'todas';
                
                console.log("Generating group report with:", fechaInicio, fechaFin, area);
                window.handler.generarInformeConFiltros(fechaInicio, fechaFin, area);
            });
            
            // Generar informe individual
            document.getElementById('generarInformeIndividual').addEventListener('click', function() {
                const searchInput = document.getElementById('searchPatient');
                if (!searchInput || !searchInput.value.trim()) {
                    alert("Por favor, seleccione un paciente antes de generar el informe individual.");
                    return;
                }
                
                // Forzar el modo individual ANTES de generar el informe
                document.body.setAttribute('data-modo-actual', 'individual');
                
                // Activar pestaña individual de forma explícita
                const tabIndividual = document.getElementById('tabIndividual');
                if (tabIndividual) {
                    tabIndividual.classList.add('tab-active');
                    tabIndividual.classList.remove('text-gray-500');
                    
                    const tabGrupal = document.getElementById('tabGrupal');
                    if (tabGrupal) {
                        tabGrupal.classList.remove('tab-active');
                        tabGrupal.classList.add('text-gray-500');
                    }
                }
                
                // Get date inputs for time range (might be used for historical data)
                const dateInputs = document.querySelectorAll('input[type="date"]');
                const fechaInicio = dateInputs[0].value;
                const fechaFin = dateInputs[1].value;
                
                console.log("Generating individual report for patient:", searchInput.value);
                window.handler.generarInformeIndividual(fechaInicio, fechaFin);
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
                document.getElementById('generarInformeGrupal').classList.remove('hidden');
                document.getElementById('generarInformeIndividual').classList.add('hidden');
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
                document.getElementById('generarInformeGrupal').classList.add('hidden');
                document.getElementById('generarInformeIndividual').classList.remove('hidden');
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
                
        print(f"Actualizando datos del informe. Modo actual: {self.modo_actual}")
        print(f"Paciente seleccionado: {self.paciente_seleccionado}")
        
        # Obtener datos reales de métricas desde el modelo
        datos = self.obtener_datos_reales()
        if self.modo_actual == "individual" and self.paciente_seleccionado:
            if not datos or 'graficos' not in datos or not datos['graficos']:
                print("ADVERTENCIA: No hay datos de gráficos disponibles para el paciente individual")
                # Usar datos de muestra para evitar errores
                if 'graficos' not in datos:
                    datos['graficos'] = {}
                if 'comparacion' not in datos['graficos']:
                    datos['graficos']['comparacion'] = {
                        "etiquetas": ["Triage", "Consulta de Ingreso", "Laboratorios", "Imágenes", "Interconsulta", "Revaloración"],
                        "datos_paciente": [0, 0, 0, 0, 0, 0],
                        "datos_area": [0, 0, 0, 0, 0, 0]
                    }
                if 'todas_areas' not in datos['graficos']:
                    datos['graficos']['todas_areas'] = {
                        "etiquetas": ["Triage", "Consulta de Ingreso", "Laboratorios", "Imágenes", "Interconsulta", "Revaloración"],
                        "datos_paciente": [0, 0, 0, 0, 0, 0],
                        "datos_generales": [0, 0, 0, 0, 0, 0]
                    }
        
        # Preparamos los datos para reemplazar en el HTML
        html_content = self.html_template
        
        # Reemplazar marcadores con datos reales
        html_content = self.reemplazar_datos_en_html(html_content, datos)
        
        # Cargar el contenido HTML actualizado en la vista web
        self.web_view.setHtml(html_content, baseUrl=QUrl.fromLocalFile(self.ruta_base + "/"))
        
        # Asegurarnos que después de la carga se mantenga el modo correcto
        # mediante JavaScript adicional
        if self.modo_actual == "individual" and self.paciente_seleccionado:
            js_code = """
            setTimeout(function() {
                // Aseguramos que la vista individual esté activa
                const tabIndividual = document.getElementById('tabIndividual');
                if (tabIndividual && !tabIndividual.classList.contains('tab-active')) {
                    tabIndividual.click();
                }
            }, 200);
            """
            self.web_view.page().runJavaScript(js_code)
        
    def buscar_paciente(self, termino_busqueda):
        """Busca pacientes por nombre o documento"""
        try:
            from Back_end.Manejo_DB import ModeloPaciente
            modelo = ModeloPaciente()
            
            # Crear una instancia específica para búsqueda, independiente de otros filtros
            # Esto garantiza que la búsqueda de pacientes no se vea afectada por filtros grupales
            print(f"Realizando búsqueda de paciente con término: '{termino_busqueda}'")
            
            # La búsqueda debe ser independiente de cualquier filtro de área o fecha
            resultados = modelo.buscar_pacientes(termino_busqueda)
            print(f"Resultados de búsqueda: {len(resultados)} pacientes encontrados")
            return resultados
        except Exception as e:
            print(f"Error al buscar paciente: {str(e)}")
            traceback.print_exc()
            self.mostrar_mensaje_advertencia("Error", f"Error al buscar paciente: {str(e)}")
            return []

    def mostrar_resultados_busqueda(self, resultados):
        """Actualiza la interfaz con los resultados de búsqueda usando JavaScript"""
        try:
            # Generar HTML para los resultados
            resultados_html = ""
            if resultados:
                for paciente in resultados:
                    if len(paciente) >= 4:  # Asegurarse que tiene todos los campos necesarios
                        nombre = paciente[0] if paciente[0] else ""
                        documento = paciente[1] if paciente[1] else ""
                        ubicacion = paciente[2] if len(paciente) > 2 else ""
                        paciente_id = str(paciente[3]) if len(paciente) > 3 else ""
                        
                        # Escape HTML special characters to prevent XSS
                        nombre = nombre.replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
                        documento = documento.replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
                        ubicacion = ubicacion.replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
                        
                        # Crear elemento HTML para cada paciente
                        resultados_html += f"""
                        <div class="p-2 hover:bg-[#E8F0F7] cursor-pointer" 
                            data-paciente-id="{paciente_id}"
                            data-nombre="{nombre}" 
                            data-documento="{documento}"
                            data-ubicacion="{ubicacion}">
                            {nombre} - {documento} - {ubicacion}
                        </div>
                        """
            else:
                resultados_html = '<div class="p-2 text-gray-500">No se encontraron resultados</div>'
            
            # Ejecutar JavaScript para actualizar la lista de resultados
            js_code = f"""
            (function() {{
                console.log("Actualizando resultados de búsqueda...");
                const resultadosContainer = document.getElementById('patientResults');
                if (resultadosContainer) {{
                    resultadosContainer.innerHTML = `{resultados_html}`;
                    resultadosContainer.classList.remove('hidden');
                    
                    // Agregar eventos click a cada resultado con comportamiento mejorado
                    resultadosContainer.querySelectorAll('div[data-paciente-id]').forEach(item => {{
                        item.addEventListener('click', function() {{
                            const pacienteId = this.dataset.pacienteId;
                            const nombre = this.dataset.nombre;
                            const documento = this.dataset.documento;
                            const ubicacion = this.dataset.ubicacion;
                            
                            // Actualizar el campo de búsqueda con el resultado seleccionado
                            // y mantenerlo visible
                            const searchInput = document.getElementById('searchPatient');
                            if (searchInput) {{
                                searchInput.value = nombre + ' - ' + documento;
                                // Enfocar brevemente y desenfocar para confirmar la selección visualmente
                                searchInput.focus();
                                setTimeout(() => searchInput.blur(), 100);
                            }}
                            
                            console.log("Paciente seleccionado:", pacienteId, nombre, documento, ubicacion);
                            
                            // Llamar a la función Python para seleccionar el paciente
                            // y actualizar la vista
                            if (window.handler) {{
                                // Marcar explícitamente que estamos en modo individual antes de la selección
                                document.body.setAttribute('data-modo-actual', 'individual');
                                window.handler.seleccionarPaciente(pacienteId, nombre, documento, ubicacion);
                                
                                // Ocultar resultados después de un breve retraso
                                setTimeout(function() {{
                                    resultadosContainer.classList.add('hidden');
                                }}, 300);
                            }} else {{
                                console.error("window.handler no está disponible");
                            }}
                        }});
                    }});
                }} else {{
                    console.error("Contenedor de resultados no encontrado");
                }}
            }})();
            """
            
            self.web_view.page().runJavaScript(js_code)
        except Exception as e:
            print(f"Error al mostrar resultados de búsqueda: {str(e)}")
            import traceback
            traceback.print_exc()
            self.mostrar_mensaje_advertencia("Error", f"Error al mostrar resultados: {str(e)}")

    def configurar_busqueda_pacientes(self):
        """Configura los eventos JavaScript para la búsqueda de pacientes con manejo robusto de DOM"""
        try:
            js_code = """
            // Función para inicializar la búsqueda con manejo de errores mejorado
            function initializeSearch(retryCount = 0) {
                console.log("Intentando inicializar búsqueda de pacientes... (intento " + (retryCount + 1) + ")");
                
                // Buscar el campo de búsqueda de múltiples formas
                let searchInput = document.getElementById('searchPatient');
                
                // Si no lo encontramos por ID, intentar con otros selectores
                if (!searchInput) {
                    console.log("Buscando campo de búsqueda con selectores alternativos...");
                    // Intentar con diferentes selectores que podrían coincidir
                    searchInput = document.querySelector('input[type="search"]');
                    
                    if (!searchInput) {
                        searchInput = document.querySelector('input[placeholder*="paciente"]');
                    }
                    
                    if (!searchInput) {
                        searchInput = document.querySelector('input[placeholder*="buscar"]');
                    }
                    
                    if (!searchInput) {
                        // Buscar cualquier input en la sección de búsqueda individual
                        const seccionIndividual = document.querySelector('#seccion-individual');
                        if (seccionIndividual) {
                            searchInput = seccionIndividual.querySelector('input');
                        }
                    }
                    
                    if (searchInput) {
                        console.log("Campo de búsqueda encontrado con selector alternativo");
                        // Asignarle el ID para futuras referencias
                        searchInput.id = 'searchPatient';
                    }
                }
                
                // Si aún no lo encontramos, reintentar después de un retraso
                if (!searchInput) {
                    console.warn("Elemento de búsqueda no encontrado en el DOM");
                    if (retryCount < 10) { // Máximo 10 intentos
                        console.log("Reintentando en " + (500 + retryCount * 100) + "ms...");
                        setTimeout(() => initializeSearch(retryCount + 1), 500 + retryCount * 100);
                    } else {
                        console.error("No se pudo encontrar el campo de búsqueda después de múltiples intentos");
                        // Último recurso: Crear el campo de búsqueda si no existe
                        createSearchFieldIfNeeded();
                    }
                    return;
                }
                
                console.log("Campo de búsqueda encontrado con ID:", searchInput.id);
                
                // Configurar búsqueda por Enter con un retraso menor
                searchInput.addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') {
                        e.preventDefault();
                        const termino = this.value.trim();
                        if (termino) {
                            console.log("Buscando paciente:", termino);
                            document.body.setAttribute('data-modo-actual', 'individual');
                            if (window.handler) {
                                window.handler.buscarPacientes(termino);
                            } else {
                                console.error("window.handler no está disponible");
                            }
                        }
                    }
                });
                
                // También buscar cuando el input cambia, con debounce
                let typingTimer;
                const doneTypingInterval = 500; // ms
                
                searchInput.addEventListener('input', function() {
                    clearTimeout(typingTimer);
                    const termino = this.value.trim();
                    if (termino.length >= 3) {
                        typingTimer = setTimeout(function() {
                            console.log("Búsqueda automática:", termino);
                            document.body.setAttribute('data-modo-actual', 'individual');
                            if (window.handler) {
                                window.handler.buscarPacientes(termino);
                            } else {
                                console.error("window.handler no está disponible");
                            }
                        }, doneTypingInterval);
                    }
                });
                
                // Función para mostrar/ocultar los resultados
                function toggleResultsVisibility(show) {
                    const resultadosContainer = document.getElementById('patientResults');
                    if (resultadosContainer) {
                        if (show) {
                            resultadosContainer.classList.remove('hidden');
                        } else {
                            setTimeout(() => resultadosContainer.classList.add('hidden'), 200);
                        }
                    } else if (show) {
                        // Si el contenedor no existe y necesitamos mostrarlo, crearlo
                        createResultsContainer();
                    }
                }
                
                // Mantener el dropdown abierto durante la interacción
                searchInput.addEventListener('focus', function() {
                    // Asegurarse que estamos en la pestaña individual
                    const tabIndividual = document.getElementById('tabIndividual');
                    if (tabIndividual) {
                        tabIndividual.click();
                    }
                    
                    toggleResultsVisibility(true);
                    
                    // Si ya hay texto, realizar búsqueda inmediata
                    const termino = this.value.trim();
                    if (termino.length >= 3 && window.handler) {
                        window.handler.buscarPacientes(termino);
                    }
                });
                
                // Cerrar el dropdown cuando se pierde el foco, con retraso para permitir clicks
                searchInput.addEventListener('blur', function() {
                    toggleResultsVisibility(false);
                });
                
                console.log("Búsqueda de pacientes inicializada correctamente");
            }
            
            // Función para crear el contenedor de resultados si no existe
            function createResultsContainer() {
                if (!document.getElementById('patientResults')) {
                    console.log("Creando contenedor de resultados...");
                    const searchInput = document.getElementById('searchPatient');
                    if (searchInput) {
                        // Crear el contenedor de resultados
                        const resultsContainer = document.createElement('div');
                        resultsContainer.id = 'patientResults';
                        resultsContainer.className = 'hidden absolute z-50 bg-white shadow-lg rounded mt-1 w-full border';
                        
                        // Insertar después del input
                        if (searchInput.parentNode) {
                            searchInput.parentNode.insertBefore(resultsContainer, searchInput.nextSibling);
                        }
                    }
                }
            }
            
            // Función para crear el campo de búsqueda como último recurso
            function createSearchFieldIfNeeded() {
                console.log("Intentando crear campo de búsqueda como último recurso...");
                
                // Buscar la sección donde debe ir el buscador
                const seccionBusqueda = document.querySelector('#seccion-individual, #individual-search-section');
                
                if (!seccionBusqueda) {
                    console.error("No se pudo encontrar sección para agregar el buscador");
                    return;
                }
                
                // Crear el campo de búsqueda
                const searchContainer = document.createElement('div');
                searchContainer.className = 'relative w-full max-w-md mb-4';
                searchContainer.innerHTML = `
                    <input id="searchPatient" type="text" 
                        placeholder="Buscar paciente por nombre o documento" 
                        class="w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                    <div id="patientResults" class="hidden absolute z-50 bg-white shadow-lg rounded mt-1 w-full border"></div>
                `;
                
                // Insertar al inicio de la sección
                seccionBusqueda.insertBefore(searchContainer, seccionBusqueda.firstChild);
                
                console.log("Campo de búsqueda creado. Intentando inicializar eventos...");
                // Reintentar inicialización después de crear el campo
                setTimeout(() => initializeSearch(0), 200);
            }
            
            // Inicializar cuando el DOM esté completamente cargado
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', () => initializeSearch(0));
            } else {
                // Si el DOM ya está cargado, inicializar inmediatamente
                initializeSearch(0);
            }
            
            // También intentar inicializar cuando la ventana esté completamente cargada
            window.addEventListener('load', () => {
                console.log("Evento load detectado, verificando si la búsqueda está inicializada");
                if (!document.getElementById('searchPatient')) {
                    initializeSearch(0);
                }
            });
            """
            
            self.web_view.page().runJavaScript(js_code)
            print("Script de búsqueda de pacientes configurado")
        except Exception as e:
            print(f"Error al configurar búsqueda de pacientes: {str(e)}")
            import traceback
            traceback.print_exc()

    def seleccionar_paciente(self, paciente_id, nombre, documento, ubicacion):
        """Selecciona un paciente para generar el informe individual"""
        try:
            # Guardar el ID del paciente seleccionado
            self.paciente_seleccionado = paciente_id
            # IMPORTANTE: Establecer el modo actual antes de actualizar datos
            self.modo_actual = "individual"
            print(f"Paciente seleccionado: ID={paciente_id}, Nombre={nombre}, Documento={documento}")
            
            nombre_escapado = nombre.replace("'", "\\'").replace('"', '\\"')
            documento_escapado = documento.replace("'", "\\'").replace('"', '\\"')
            
            # Modificar la secuencia para garantizar que permanezca en modo individual
            js_code = """
            // Primero aseguramos que el valor del campo de búsqueda se mantenga
            const searchInput = document.getElementById('searchPatient');
            if (searchInput && searchInput.value.indexOf('""" + nombre_escapado + """') === -1) {
                searchInput.value = '""" + nombre_escapado + """ - """ + documento_escapado + """';
            }
            
            // Luego activamos la pestaña individual de forma más robusta
            const tabIndividual = document.getElementById('tabIndividual');
            if (tabIndividual) {
                // Marcar esta pestaña como activa
                tabIndividual.classList.add('tab-active');
                tabIndividual.classList.remove('text-gray-500');
                
                // Desmarcar la pestaña grupal
                const tabGrupal = document.getElementById('tabGrupal');
                if (tabGrupal) {
                    tabGrupal.classList.remove('tab-active');
                    tabGrupal.classList.add('text-gray-500');
                }
                
                // Asegurar visibilidad del filtro individual
                const filtroIndividual = document.getElementById('filtroIndividual');
                if (filtroIndividual) {
                    filtroIndividual.classList.remove('hidden');
                }
                
                // Asegurar visibilidad de componentes individuales
                document.querySelectorAll('[id^="metricas-individuales-"]').forEach(el => el.classList.remove('hidden'));
                
                // Mostrar gráficos individuales y tabla de paciente
                const graficosIndividuales = document.getElementById('graficos-individuales');
                if (graficosIndividuales) graficosIndividuales.classList.remove('hidden');
                
                const tablaPacienteIndividual = document.getElementById('tabla-paciente-individual');
                if (tablaPacienteIndividual) tablaPacienteIndividual.classList.remove('hidden');
                
                // Ocultar componentes grupales
                const graficosGrupales = document.getElementById('graficos-grupales');
                if (graficosGrupales) graficosGrupales.classList.add('hidden');
                
                const cumplimientoSla = document.getElementById('cumplimiento-sla');
                if (cumplimientoSla) cumplimientoSla.classList.add('hidden');
                
                // Ocultar contenido grupal
                document.querySelectorAll('[id^="metricas-grupales-"]').forEach(el => el.classList.add('hidden'));
                
                // Mostrar el botón de informe individual y ocultar el grupal
                document.getElementById('generarInformeGrupal').classList.add('hidden');
                document.getElementById('generarInformeIndividual').classList.remove('hidden');
                
                // Almacenar el modo como datos para asegurar que persista
                document.body.setAttribute('data-modo-actual', 'individual');
            }
            """
            
            # Ejecutar el código JavaScript
            self.web_view.page().runJavaScript(js_code)
            
        except Exception as e:
            print(f"Error al seleccionar paciente: {str(e)}")
            traceback.print_exc()
            self.mostrar_mensaje_advertencia("Error", f"Error al seleccionar paciente: {str(e)}")
    
    def calcular_cumplimiento_sla_individual(self, metricas_paciente):
        """Calcula el porcentaje de cumplimiento del SLA para un paciente individual"""
        # Obtener la clase de triage del paciente (valor por defecto: 3)
        clase_triage = metricas_paciente.get("triage", {}).get("valor", "3")
        
        # Definir los SLA según el tipo de triage (mismo que en generar_js_actualizacion_semaforos)
        slas = {
            'triage': {'1': 0, '2': 30, '3': 120, '4': 30, '5': 60},
            'ci': {'1': 210, '2': 210, '3': 360, '4': 420, '5': 420},
            'labs': {'1': 360, '2': 360, '3': 360, '4': 360, '5': 360},
            'ix': {'1': 360, '2': 360, '3': 360, '4': 360, '5': 360},
            'inter': {'1': 30, '2': 45, '3': 60, '4': 120, '5': 180},
            'rv': {'1': 30, '2': 60, '3': 120, '4': 240, '5': 360}
        }
        
        # Preparar diccionario para los porcentajes de cumplimiento
        cumplimiento = {}
        
        # Para cada tipo de proceso, calcular el cumplimiento
        procesos = ['triage', 'ci', 'labs', 'ix', 'inter', 'rv']
        for proceso in procesos:
            tiempo = metricas_paciente.get(proceso, {}).get("tiempo", 0) or 0
            sla_valor = slas[proceso].get(clase_triage, slas[proceso]['3'])
            
            if tiempo > 0 and sla_valor > 0:
                # Si el tiempo es menor o igual al SLA, cumplimiento del 100%
                if tiempo <= sla_valor:
                    cumplimiento[proceso] = 100
                else:
                    # El cumplimiento disminuye proporcionalmente al exceso
                    exceso = (tiempo - sla_valor) / sla_valor
                    cumplimiento[proceso] = max(0, min(100, 100 - exceso * 100))
            else:
                cumplimiento[proceso] = None
        
        return cumplimiento
    
    def generar_js_actualizacion_graficos(self, datos_graficos):
        """Genera el código JavaScript para actualizar los gráficos"""
        try:
            # Iniciar con una base simple
            js_code = "console.log('Actualizando gráficos...');\n"
            
            # Añadir código para actualizar gráfico de línea de tiempo si hay datos timeline
            if "timeline" in datos_graficos and datos_graficos["timeline"]:
                try:
                    # Extraer datos de manera segura y usar json.dumps() para asegurar formato válido
                    grouping = datos_graficos["timeline"].get("grouping", "daily")
                    etiquetas = json.dumps(datos_graficos["timeline"].get("etiquetas", []))
                    datos = json.dumps(datos_graficos["timeline"].get("datos", []))
                    
                    # Usar una forma más segura de template string, evitando caracteres que puedan romper la sintaxis
                    js_code += """
                    // Actualizar gráfico de línea de tiempo
                    if (window.timelineChart) {
                        try {
                            const labels = """ + etiquetas + """;
                            const data = """ + datos + """;
                            if (Array.isArray(labels) && Array.isArray(data) && labels.length > 0) {
                                updateTimelineChart(labels, data, '""" + grouping + """');
                            } else {
                                // No hay datos, mostrar mensaje en el gráfico
                                window.timelineChart.data.labels = [];
                                window.timelineChart.data.datasets[0].data = [];
                                window.timelineChart.options.plugins.title = {
                                    display: true,
                                    text: 'No hay datos disponibles para este filtro',
                                    font: {size: 16, weight: 'bold'}
                                };
                                window.timelineChart.update();
                            }
                        } catch(e) {
                            console.error("Error al actualizar gráfico de línea temporal:", e);
                        }
                    }
                    """

                except Exception as e:
                    print(f"Error processing timeline data: {e}")
                    
            # Si hay datos de comparación, añadir código para actualizar esos gráficos
            if "comparacion" in datos_graficos:
                try:
                    datos_comp = datos_graficos["comparacion"]
                    etiquetas = json.dumps(datos_comp.get("etiquetas", []))
                    datos_paciente = json.dumps(datos_comp.get("datos_paciente", []))
                    datos_area = json.dumps(datos_comp.get("datos_area", []))
                    
                    js_code += f"""
                    // Actualizar el gráfico de comparación
                    (function() {{
                        const comparisonCtx = document.getElementById('comparisonChart');
                        if (!comparisonCtx) {{
                            console.error("No se encontró el canvas para el gráfico de comparación");
                            return;
                        }}
                        
                        try {{
                            // Datos para el gráfico
                            const etiquetas = {etiquetas};
                            const datosPaciente = {datos_paciente};
                            const datosArea = {datos_area};
                            
                            // Si ya existe el gráfico y es válido, actualizarlo
                            if (window.comparisonChart && typeof window.comparisonChart.update === 'function') {{
                                window.comparisonChart.data.labels = etiquetas;
                                window.comparisonChart.data.datasets[0].data = datosPaciente;
                                window.comparisonChart.data.datasets[1].data = datosArea;
                                window.comparisonChart.update();
                                console.log("Gráfico de comparación actualizado correctamente");
                            }} else {{
                                // Si el gráfico anterior existe pero no es válido, intentar limpiarlo
                                if (window.comparisonChart) {{
                                    try {{
                                        if (typeof window.comparisonChart.destroy === 'function') {{
                                            window.comparisonChart.destroy();
                                        }}
                                    }} catch (e) {{
                                        console.warn("No se pudo destruir el gráfico anterior:", e);
                                    }}
                                }}
                                
                                // Crear nuevo gráfico
                                window.comparisonChart = new Chart(comparisonCtx, {{
                                    type: 'bar',
                                    data: {{
                                        labels: etiquetas,
                                        datasets: [
                                            {{
                                                label: 'Paciente',
                                                data: datosPaciente,
                                                backgroundColor: '#5385B7',
                                                borderWidth: 1
                                            }},
                                            {{
                                                label: 'Promedio del área',
                                                data: datosArea,
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
                                                    text: 'Minutos'
                                                }}
                                            }}
                                        }}
                                    }}
                                }});
                                console.log("Nuevo gráfico de comparación creado");
                            }}
                        }} catch(e) {{
                            console.error("Error al crear/actualizar gráfico de comparación:", e);
                        }}
                    }})();
                    """
                except Exception as e:
                    print(f"Error processing comparison chart data: {e}")
            
            # Código para actualizar gráfico radar de todas las áreas
            if "todas_areas" in datos_graficos:
                try:
                    datos_todas = datos_graficos["todas_areas"]
                    etiquetas = json.dumps(datos_todas.get("etiquetas", []))
                    datos_paciente = json.dumps(datos_todas.get("datos_paciente", []))
                    datos_generales = json.dumps(datos_todas.get("datos_generales", []))
                    
                    js_code += f"""
                    // Actualizar el gráfico radar
                    (function() {{
                        const radarCtx = document.getElementById('allAreasChart');
                        if (!radarCtx) {{
                            console.error("No se encontró el canvas para el gráfico radar");
                            return;
                        }}
                        
                        try {{
                            // Datos para el gráfico
                            const etiquetas = {etiquetas};
                            const datosPaciente = {datos_paciente};
                            const datosGenerales = {datos_generales};
                            
                            // Si ya existe el gráfico y es válido, actualizarlo
                            if (window.allAreasChart && typeof window.allAreasChart.update === 'function') {{
                                window.allAreasChart.data.labels = etiquetas;
                                window.allAreasChart.data.datasets[0].data = datosPaciente;
                                window.allAreasChart.data.datasets[1].data = datosGenerales;
                                window.allAreasChart.update();
                                console.log("Gráfico radar actualizado correctamente");
                            }} else {{
                                // Si el gráfico anterior existe pero no es válido, intentar limpiarlo
                                if (window.allAreasChart) {{
                                    try {{
                                        if (typeof window.allAreasChart.destroy === 'function') {{
                                            window.allAreasChart.destroy();
                                        }}
                                    }} catch (e) {{
                                        console.warn("No se pudo destruir el gráfico anterior:", e);
                                    }}
                                }}
                                
                                // Crear nuevo gráfico
                                window.allAreasChart = new Chart(radarCtx, {{
                                    type: 'radar',
                                    data: {{
                                        labels: etiquetas,
                                        datasets: [
                                            {{
                                                label: 'Paciente',
                                                data: datosPaciente,
                                                backgroundColor: 'rgba(83, 133, 183, 0.2)',
                                                borderColor: '#5385B7',
                                                pointBackgroundColor: '#5385B7',
                                                borderWidth: 2,
                                            }},
                                            {{
                                                label: 'Promedio general',
                                                data: datosGenerales,
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
                                console.log("Nuevo gráfico radar creado");
                            }}
                        }} catch(e) {{
                            console.error("Error al crear/actualizar gráfico radar:", e);
                        }}
                    }})();
                    """
                except Exception as e:
                    print(f"Error processing radar chart data: {e}")
            
            # Código para hacer visible el contenedor de gráficos y asegurar que se inicialicen
            js_code += """
            // Hacer visible el contenedor de gráficos
            (function() {
                const graficosIndividuales = document.getElementById('graficos-individuales');
                if (graficosIndividuales) {
                    // Hacer visible el contenedor
                    graficosIndividuales.classList.remove('hidden');
                    graficosIndividuales.style.display = 'grid';
                    console.log("Visibilidad de gráficos individuales activada");
                }
            })();
            """
            # Debug to help diagnose issues
            print("JavaScript generado sin errores de sintaxis")
            return js_code
            
        except Exception as e:
            print(f"Error al generar JavaScript para gráficos: {e}")
            import traceback
            traceback.print_exc()
            return "console.error('Error al generar datos para gráficos: " + str(e).replace("'", "\\'") + "');"

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
        from Back_end.ModeloMetricas import ModeloMetricas
        
        # Calcular fechas dinámicamente para ambos modos
        fecha_inicio_str = self.fecha_inicio.strftime('%Y-%m-%d')
        fecha_fin_str = self.fecha_fin.strftime('%Y-%m-%d')
        
        # Para informe individual (un paciente específico)
        if self.modo_actual == "individual" and self.paciente_seleccionado:
            try:
                # Obtener métricas específicas del paciente
                datos_paciente = ModeloMetricas.obtener_metricas_paciente(self.paciente_seleccionado)
                if not datos_paciente:
                    print(f"No se encontraron métricas para el paciente ID {self.paciente_seleccionado}")
                    return None
                
                # Obtener el área del paciente para las comparativas
                area_paciente = datos_paciente.get('area', "todas")
                
                # Obtener métricas generales de todas las áreas para comparativas
                metricas_area = datos_paciente.get("promedios_area", {})
                datos_generales = ModeloMetricas.obtener_todas_metricas(
                    fecha_inicio=fecha_inicio_str, fecha_fin=fecha_fin_str
                )
                
                # Preparar datos para los gráficos
                etiquetas = ['Triage', 'Consulta de Ingreso', 'Laboratorios', 'Imágenes', 'Interconsulta', 'Revaloración']
                
                # Usar get() seguro para todas las rutas de datos del paciente
                datos_paciente_comp = [
                    datos_paciente.get('metricas', {}).get('triage', {}).get('tiempo', 0) or 0,
                    datos_paciente.get('metricas', {}).get('ci', {}).get('tiempo', 0) or 0,
                    datos_paciente.get('metricas', {}).get('labs', {}).get('tiempo', 0) or 0,
                    datos_paciente.get('metricas', {}).get('ix', {}).get('tiempo', 0) or 0,
                    datos_paciente.get('metricas', {}).get('inter', {}).get('tiempo', 0) or 0,
                    datos_paciente.get('metricas', {}).get('rv', {}).get('tiempo', 0) or 0
                ]
                
                # Acceder a los datos con .get() para prevenir errores cuando una clave no existe
                datos_area_comp = [
                    metricas_area.get('triage', {}).get('estadisticas', {}).get('promedio', 0) or 0,
                    metricas_area.get('consulta_ingreso', {}).get('estadisticas', {}).get('promedio', 0) or 0,
                    # Laboratorios e imágenes pueden tener estadisticas_total en lugar de estadisticas
                    metricas_area.get('laboratorios', {}).get('estadisticas_total', {}).get('promedio', 0) or 0,
                    metricas_area.get('imagenes', {}).get('estadisticas_total', {}).get('promedio', 0) or 0,
                    metricas_area.get('interconsulta', {}).get('estadisticas_total', {}).get('promedio', 0) or 0,
                    metricas_area.get('revaloracion', {}).get('estadisticas', {}).get('promedio', 0) or 0
                ]
                
                # Datos para todas las áreas (gráfico radar)
                datos_generales_comp = [
                    datos_generales.get('triage', {}).get('estadisticas', {}).get('promedio', 0) or 0,
                    datos_generales.get('consulta_ingreso', {}).get('estadisticas', {}).get('promedio', 0) or 0,
                    datos_generales.get('laboratorios', {}).get('estadisticas_total', {}).get('promedio', 0) or 0,
                    datos_generales.get('imagenes', {}).get('estadisticas_total', {}).get('promedio', 0) or 0,
                    datos_generales.get('interconsulta', {}).get('estadisticas_total', {}).get('promedio', 0) or 0,
                    datos_generales.get('revaloracion', {}).get('estadisticas', {}).get('promedio', 0) or 0
                ]
                
                datos_graficos = {
                    "comparacion": {
                        "etiquetas": etiquetas,
                        "datos_paciente": datos_paciente_comp,
                        "datos_area": datos_area_comp,
                    },
                    "todas_areas": {
                        "etiquetas": etiquetas,
                        "datos_paciente": datos_paciente_comp,
                        "datos_generales": datos_generales_comp,
                    }
                }

                return {
                    "individual": True,
                    "paciente": datos_paciente.get("paciente", {}),
                    "metricas": datos_paciente.get("metricas", {}),
                    "graficos": datos_graficos,
                    "promedios_area": metricas_area,
                    "promedios_generales": datos_generales,
                    "tiempo_total": datos_paciente.get("tiempo_total", 0),
                    "configuracion": {
                        "fecha_inicio": fecha_inicio_str,
                        "fecha_fin": fecha_fin_str,
                        "area": area_paciente
                    }
                }
            except Exception as e:
                print(f"Error al obtener datos reales para informe individual: {str(e)}")
                import traceback
                traceback.print_exc()
                return None
        else:
            # Para vista grupal, obtener métricas agregadas
            try:
                # Determinar área para filtrar (None si es "todas")
                area = None if self.area_seleccionada == "todas" else self.area_seleccionada
                
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

    def calcular_comparaciones_area(self, metricas_paciente, promedios_area, tiempo_total=0):
        """Calcula las comparaciones de tiempos del paciente con el promedio del área"""
        comparaciones = {}
        
        # Triage
        tiempo_triage = metricas_paciente.get("triage", {}).get("tiempo", 0) or 0
        promedio_triage = promedios_area.get("triage", {}).get("estadisticas", {}).get("promedio", 0) or 0
        if tiempo_triage > 0 and promedio_triage > 0:
            diferencia = tiempo_triage - promedio_triage
            if diferencia < 0:
                comparaciones["triage"] = f'<span class="comparison-positive">{abs(diferencia):.2f} min menos</span> que el promedio del área'
            elif diferencia > 0:
                comparaciones["triage"] = f'<span class="comparison-negative">{diferencia:.2f} min más</span> que el promedio del área'
            else:
                comparaciones["triage"] = f'<span class="comparison-neutral">Igual</span> al promedio del área'
        else:
            comparaciones["triage"] = '<span class="comparison-neutral">No hay datos comparativos</span>'
        
        # Consulta de Ingreso (CI)
        tiempo_ci = metricas_paciente.get("ci", {}).get("tiempo", 0) or 0
        promedio_ci = promedios_area.get("consulta_ingreso", {}).get("estadisticas", {}).get("promedio", 0) or 0
        if tiempo_ci > 0 and promedio_ci > 0:
            diferencia = tiempo_ci - promedio_ci
            if diferencia < 0:
                comparaciones["ci"] = f'<span class="comparison-positive">{abs(diferencia):.2f} min menos</span> que el promedio del área'
            elif diferencia > 0:
                comparaciones["ci"] = f'<span class="comparison-negative">{diferencia:.2f} min más</span> que el promedio del área'
            else:
                comparaciones["ci"] = f'<span class="comparison-neutral">Igual</span> al promedio del área'
        else:
            comparaciones["ci"] = '<span class="comparison-neutral">No hay datos comparativos</span>'
        
        # Labs
        tiempo_labs = metricas_paciente.get("labs", {}).get("tiempo", 0) or 0
        promedio_labs = promedios_area.get("laboratorios", {}).get("estadisticas_total", {}).get("promedio", 0) or 0
        if tiempo_labs > 0 and promedio_labs > 0:
            diferencia = tiempo_labs - promedio_labs
            if diferencia < 0:
                comparaciones["labs"] = f'<span class="comparison-positive">{abs(diferencia):.2f} min menos</span> que el promedio del área'
            elif diferencia > 0:
                comparaciones["labs"] = f'<span class="comparison-negative">{diferencia:.2f} min más</span> que el promedio del área'
            else:
                comparaciones["labs"] = f'<span class="comparison-neutral">Igual</span> al promedio del área'
        else:
            comparaciones["labs"] = '<span class="comparison-neutral">No hay datos comparativos</span>'
        
        # Imágenes (IX)
        tiempo_ix = metricas_paciente.get("ix", {}).get("tiempo", 0) or 0
        promedio_ix = promedios_area.get("imagenes", {}).get("estadisticas_total", {}).get("promedio", 0) or 0
        if tiempo_ix > 0 and promedio_ix > 0:
            diferencia = tiempo_ix - promedio_ix
            if diferencia < 0:
                comparaciones["ix"] = f'<span class="comparison-positive">{abs(diferencia):.2f} min menos</span> que el promedio del área'
            elif diferencia > 0:
                comparaciones["ix"] = f'<span class="comparison-negative">{diferencia:.2f} min más</span> que el promedio del área'
            else:
                comparaciones["ix"] = f'<span class="comparison-neutral">Igual</span> al promedio del área'
        else:
            comparaciones["ix"] = '<span class="comparison-neutral">No hay datos comparativos</span>'
        
        # Interconsulta (INTER)
        tiempo_inter = metricas_paciente.get("inter", {}).get("tiempo", 0) or 0
        promedio_inter = promedios_area.get("interconsulta", {}).get("estadisticas_total", {}).get("promedio", 0) or 0
        if tiempo_inter > 0 and promedio_inter > 0:
            diferencia = tiempo_inter - promedio_inter
            if diferencia < 0:
                comparaciones["inter"] = f'<span class="comparison-positive">{abs(diferencia):.2f} min menos</span> que el promedio del área'
            elif diferencia > 0:
                comparaciones["inter"] = f'<span class="comparison-negative">{diferencia:.2f} min más</span> que el promedio del área'
            else:
                comparaciones["inter"] = f'<span class="comparison-neutral">Igual</span> al promedio del área'
        else:
            comparaciones["inter"] = '<span class="comparison-neutral">No hay datos comparativos</span>'
        
        # Revaloración (RV)
        tiempo_rv = metricas_paciente.get("rv", {}).get("tiempo", 0) or 0
        promedio_rv = promedios_area.get("revaloracion", {}).get("estadisticas", {}).get("promedio", 0) or 0
        if tiempo_rv > 0 and promedio_rv > 0:
            diferencia = tiempo_rv - promedio_rv
            if diferencia < 0:
                comparaciones["rv"] = f'<span class="comparison-positive">{abs(diferencia):.2f} min menos</span> que el promedio del área'
            elif diferencia > 0:
                comparaciones["rv"] = f'<span class="comparison-negative">{diferencia:.2f} min más</span> que el promedio del área'
            else:
                comparaciones["rv"] = f'<span class="comparison-neutral">Igual</span> al promedio del área'
        else:
            comparaciones["rv"] = '<span class="comparison-neutral">No hay datos comparativos</span>'
        
        # Tiempo total
        promedio_total = promedios_area.get("tiempo_total", {}).get("estadisticas", {}).get("promedio", 0) or 0
        print(f"Tiempo total paciente: {tiempo_total}, Promedio área: {promedio_total}")
        if tiempo_total > 0 and promedio_total > 0:
            diferencia = tiempo_total - promedio_total
            if diferencia < 0:
                comparaciones["tiempo_total"] = f'<span class="comparison-positive">{abs(diferencia):.2f} min menos</span> que el promedio del área'
            elif diferencia > 0:
                comparaciones["tiempo_total"] = f'<span class="comparison-negative">{diferencia:.2f} min más</span> que el promedio del área'
            else:
                comparaciones["tiempo_total"] = f'<span class="comparison-neutral">Igual</span> al promedio del área'
        else:
            comparaciones["tiempo_total"] = '<span class="comparison-neutral">No hay datos comparativos</span>'
        
        return comparaciones

    def _obtener_icono_y_texto_estado(self, estado, tipo):
        """Devuelve el icono HTML y el texto formateado según el estado"""
        # Determinar el icono según el estado
        if tipo == "triage" and estado in ["1", "2", "3", "4", "5"]:
            icono = '<i class="fas fa-check-circle text-[#28a745]"></i>'
            texto = f"Triage {estado}"
        elif estado in ["Realizado", "Realizada", "Resultados completos"]:
            icono = '<i class="fas fa-check-circle text-[#28a745]"></i>'
            if estado == "Resultados completos":
                texto = "Completado"
            else:
                texto = estado
        elif estado in ["En espera de resultados", "Abierta"]:
            icono = '<i class="fas fa-exclamation-triangle text-[#E6B800]"></i>'
            if estado == "En espera de resultados":
                texto = "En espera"
            else:
                texto = estado
        else:
            icono = '<i class="fas fa-times-circle text-[#B75353]"></i>'
            if estado == "No se ha realizado":
                texto = "No realizado"
            elif estado == "No se ha abierto":
                texto = "No abierta" 
            else:
                texto = estado
        
        return icono, texto

    def formatear_tiempo(self, valor):
        """Formatea el tiempo para mostrar -- si es 0, None o cualquier valor que evalúe a False"""
        if valor is None or valor == 0 or not valor:
            return "--"
        return str(valor)

    def reemplazar_datos_en_html(self, html_content, datos):
        """Reemplaza los marcadores de posición en el HTML con datos reales"""
        try:
            # Configurar valores iniciales por defecto
            area_actual = datos.get('configuracion', {}).get('area', 'todas')
            
            # Reemplazar marcadores de fecha
            fecha_inicio = datos.get('configuracion', {}).get('fecha_inicio', '')
            fecha_fin = datos.get('configuracion', {}).get('fecha_fin', '')
            html_content = html_content.replace("{{FECHA_INICIO}}", fecha_inicio)
            html_content = html_content.replace("{{FECHA_FIN}}", fecha_fin)
            
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
                paciente = datos["paciente"]
                metricas = datos["metricas"]
                promedios_area = datos.get("promedios_area", {})
                print("DEBUG: datos['graficos'] structure:", json.dumps(datos.get("graficos", {}), default=str))

                # Marcar explícitamente que estamos en modo individual
                html_content = html_content.replace('<body', '<body data-modo-actual="individual"')
                
                # Datos del paciente para la tabla individual
                html_content = html_content.replace("{{PACIENTE_NOMBRE}}", paciente.get("nombre", "-"))
                html_content = html_content.replace("{{PACIENTE_DOCUMENTO}}", paciente.get("documento", "-"))
                html_content = html_content.replace("{{PACIENTE_AREA}}", paciente.get("area", "-"))
                
                if metricas:
                                # Calcular cumplimiento SLA para el paciente individual
                                datos_sla = self.calcular_cumplimiento_sla_individual(metricas)
                                
                                # Generar el JavaScript para actualizar los semáforos
                                js_semaforos = self.generar_js_actualizacion_semaforos(datos_sla, metricas)
                                
                                # Insertar el script para actualizar semáforos antes del cierre del body
                                html_content = html_content.replace('</body>', f'<script>{js_semaforos}</script></body>')
                
                # Actualizar la tabla de detalles del paciente con datos reales
                # Generar HTML para la fila principal
                nombre = paciente.get("nombre", "-")
                documento = paciente.get("documento", "-")
                area = paciente.get("area", "-")
                ingreso = paciente.get("ingreso", "-")
                tiempo_total = datos.get("tiempo_total", 0) or "-"
                conducta = paciente.get("estado_actual", {}).get("conducta", "-")
                
                # Determinar estilo para el estado de conducta
                conducta_estilo = "bg-green-100 text-green-800"  # Por defecto (alta)
                if conducta == "Hospitalización":
                    conducta_estilo = "bg-blue-100 text-blue-800"
                elif conducta == "Observación":
                    conducta_estilo = "bg-yellow-100 text-yellow-800"
                elif conducta != "De Alta":
                    conducta_estilo = "bg-gray-100 text-gray-800"
                    if not conducta:
                        conducta = "En proceso"
                
                # HTML para la fila principal
                fila_html = f"""
                <tr class="expandable-row table-row-odd">
                    <td class="px-4 py-3 whitespace-nowrap">{nombre}</td>
                    <td class="px-4 py-3 whitespace-nowrap">{documento}</td>
                    <td class="px-4 py-3 whitespace-nowrap">{area}</td>
                    <td class="px-4 py-3 whitespace-nowrap">{ingreso}</td>
                    <td class="px-4 py-3 whitespace-nowrap">{tiempo_total} min</td>
                    <td class="px-4 py-3 whitespace-nowrap">
                        <span class="px-2 py-1 text-xs rounded-full {conducta_estilo}">{conducta}</span>
                    </td>
                    <td class="px-4 py-3 whitespace-nowrap text-right">
                        <button class="text-[#0066cc] hover:text-[#004c99]">
                            <i class="fas fa-chevron-down"></i>
                        </button>
                    </td>
                </tr>
                """
                
                # Obtener las comparaciones calculadas para cada etapa
                comparaciones = self.calcular_comparaciones_area(metricas, promedios_area, tiempo_total)
                
                # HTML para la fila de detalles
                detalles_html = """
                <tr class="detail-row" style="display: table-row;">
                    <td colspan="7" class="px-4 py-3">
                        <div class="grid grid-cols-3 gap-4">
                """
                
                # Triage
                triage_tiempo = self.formatear_tiempo(metricas.get("triage", {}).get("tiempo", "-"))
                triage_estado = paciente.get("estado_actual", {}).get("triage", "No realizado")
                triage_icon, triage_texto = self._obtener_icono_y_texto_estado(triage_estado, "triage")
                detalles_html += f"""
                <div>
                    <h4 class="font-medium text-[#333333]">Triage</h4>
                    <p class="text-sm">Tiempo: {triage_tiempo} min</p>
                    <p class="text-sm">{comparaciones.get("triage", "")}</p>
                    <p class="text-sm">Estado: {triage_icon} {triage_texto}</p>
                </div>
                """

                # Consulta de Ingreso
                ci_tiempo = self.formatear_tiempo(metricas.get("ci", {}).get("tiempo", "-"))
                ci_estado = paciente.get("estado_actual", {}).get("ci", "No realizado")
                ci_icon, ci_texto = self._obtener_icono_y_texto_estado(ci_estado, "ci")
                detalles_html += f"""
                <div>
                    <h4 class="font-medium text-[#333333]">Consulta de Ingreso</h4>
                    <p class="text-sm">Tiempo: {ci_tiempo} min</p>
                    <p class="text-sm">{comparaciones.get("ci", "")}</p>
                    <p class="text-sm">Estado: {ci_icon} {ci_texto}</p>
                </div>
                """

                # Labs
                labs_tiempo = self.formatear_tiempo(metricas.get("labs", {}).get("tiempo", "-"))
                labs_estado = paciente.get("estado_actual", {}).get("labs", "No se ha realizado")
                labs_icon, labs_texto = self._obtener_icono_y_texto_estado(labs_estado, "labs")
                detalles_html += f"""
                <div>
                    <h4 class="font-medium text-[#333333]">Laboratorios</h4>
                    <p class="text-sm">Tiempo total: {labs_tiempo} min</p>
                    <p class="text-sm">{comparaciones.get("labs", "")}</p>
                    <p class="text-sm">Estado: {labs_icon} {labs_texto}</p>
                </div>
                """

                # Imágenes
                ix_tiempo = self.formatear_tiempo(metricas.get("ix", {}).get("tiempo", "-"))
                ix_estado = paciente.get("estado_actual", {}).get("ix", "No se ha realizado")
                ix_icon, ix_texto = self._obtener_icono_y_texto_estado(ix_estado, "ix")
                detalles_html += f"""
                <div>
                    <h4 class="font-medium text-[#333333]">Imágenes</h4>
                    <p class="text-sm">Tiempo total: {ix_tiempo} min</p>
                    <p class="text-sm">{comparaciones.get("ix", "")}</p>
                    <p class="text-sm">Estado: {ix_icon} {ix_texto}</p>
                </div>
                """

                # Interconsulta
                inter_tiempo = self.formatear_tiempo(metricas.get("inter", {}).get("tiempo", "-"))
                inter_estado = paciente.get("estado_actual", {}).get("inter", "No se ha abierto")
                inter_icon, inter_texto = self._obtener_icono_y_texto_estado(inter_estado, "inter")
                detalles_html += f"""
                <div>
                    <h4 class="font-medium text-[#333333]">Interconsulta</h4>
                    <p class="text-sm">Tiempo: {inter_tiempo} min</p>
                    <p class="text-sm">{comparaciones.get("inter", "")}</p>
                    <p class="text-sm">Estado: {inter_icon} {inter_texto}</p>
                </div>
                """

                # Revaloración
                rv_tiempo = self.formatear_tiempo(metricas.get("rv", {}).get("tiempo", "-"))
                rv_estado = paciente.get("estado_actual", {}).get("rv", "No realizado")
                rv_icon, rv_texto = self._obtener_icono_y_texto_estado(rv_estado, "rv")
                detalles_html += f"""
                <div>
                    <h4 class="font-medium text-[#333333]">Revaloración</h4>
                    <p class="text-sm">Tiempo: {rv_tiempo} min</p>
                    <p class="text-sm">{comparaciones.get("rv", "")}</p>
                    <p class="text-sm">Estado: {rv_icon} {rv_texto}</p>
                </div>
                """
                
                detalles_html += """
                        </div>
                    </td>
                </tr>
                """
                
                # Reemplazar la tabla de ejemplo con los datos reales
                import re
                patron_tabla = re.compile(
                    r'<tr class="expandable-row.*?</tr>\s*<tr class="detail-row".*?</tr>', 
                    re.DOTALL
                )
                html_content = re.sub(patron_tabla, fila_html + detalles_html, html_content)
                
                # Reemplazar tiempos principales de cada etapa
                html_content = html_content.replace("{{TRIAGE_TIEMPO}}", self.formatear_tiempo(metricas.get("triage", {}).get("tiempo", "-")))
                html_content = html_content.replace("{{CI_TIEMPO}}", self.formatear_tiempo(metricas.get("ci", {}).get("tiempo", "-")))
                html_content = html_content.replace("{{LABS_TIEMPO}}", self.formatear_tiempo(metricas.get("labs", {}).get("tiempo", "-")))
                html_content = html_content.replace("{{IX_TIEMPO}}", self.formatear_tiempo(metricas.get("ix", {}).get("tiempo", "-")))
                html_content = html_content.replace("{{INTER_TIEMPO}}", self.formatear_tiempo(metricas.get("inter", {}).get("tiempo", "-")))
                html_content = html_content.replace("{{RV_TIEMPO}}", self.formatear_tiempo(metricas.get("rv", {}).get("tiempo", "-")))
                
                # Reemplazar tiempos específicos para Labs
                html_content = html_content.replace("{{LABS_TIEMPO_NR}}", self.formatear_tiempo(metricas.get("labs", {}).get("tiempo_solicitud", "-")))
                html_content = html_content.replace("{{LABS_TIEMPO_ER}}", self.formatear_tiempo(metricas.get("labs", {}).get("tiempo_resultados", "-")))
                
                # Reemplazar tiempos específicos para IX
                html_content = html_content.replace("{{IX_TIEMPO_NR}}", self.formatear_tiempo(metricas.get("ix", {}).get("tiempo_solicitud", "-")))
                html_content = html_content.replace("{{IX_TIEMPO_ER}}", self.formatear_tiempo(metricas.get("ix", {}).get("tiempo_resultados", "-")))
                
                # Reemplazar tiempos específicos para Interconsulta
                html_content = html_content.replace("{{INTER_TIEMPO_NA}}", self.formatear_tiempo(metricas.get("inter", {}).get("tiempo_apertura", "-")))
                html_content = html_content.replace("{{INTER_TIEMPO_AR}}", self.formatear_tiempo(metricas.get("inter", {}).get("tiempo_realizacion", "-")))
                
                # Tiempo total
                tiempo_total = datos["tiempo_total"]
                html_content = html_content.replace("{{TIEMPO_TOTAL}}", self.formatear_tiempo(tiempo_total))
                
                # Calcular comparaciones con promedio del área
                comparaciones = self.calcular_comparaciones_area(metricas, promedios_area, datos["tiempo_total"])
                            
                html_content = html_content.replace("{{COMPARACION_TRIAGE}}", comparaciones.get("triage", "-"))
                html_content = html_content.replace("{{COMPARACION_CI}}", comparaciones.get("ci", "-"))
                html_content = html_content.replace("{{COMPARACION_LABS}}", comparaciones.get("labs", "-"))
                html_content = html_content.replace("{{COMPARACION_IX}}", comparaciones.get("ix", "-"))
                html_content = html_content.replace("{{COMPARACION_INTER}}", comparaciones.get("inter", "-"))
                html_content = html_content.replace("{{COMPARACION_RV}}", comparaciones.get("rv", "-"))
                html_content = html_content.replace("{{COMPARACION_TOTAL}}", comparaciones.get("tiempo_total", "-"))
                
                # Datos para gráficos de comparación
                graficos_data = datos.get("graficos", {})
                if "comparacion" in graficos_data:
                    js_charts = self.generar_js_actualizacion_graficos(graficos_data)
                    if js_charts:
                        # Insert before closing body tag
                        html_content = html_content.replace('</body>', f'<script>{js_charts}</script></body>')
                    else:
                        html_content = html_content.replace('</body>', '<script>// No hay datos para gráficos</script></body>')
                
                # Asegurarse que los div de metricas individuales sean visibles
                js_mostrar_individual = """
                <script>
                document.addEventListener('DOMContentLoaded', function() {
                    // Establecer modo individual 
                    document.body.setAttribute('data-modo-actual', 'individual');
                    
                    // Activar pestaña individual
                    const tabIndividual = document.getElementById('tabIndividual');
                    if (tabIndividual) {
                        tabIndividual.classList.add('tab-active');
                        tabIndividual.classList.remove('text-gray-500');
                        
                        const tabGrupal = document.getElementById('tabGrupal');
                        if (tabGrupal) {
                            tabGrupal.classList.remove('tab-active');
                            tabGrupal.classList.add('text-gray-500');
                        }
                    }
                    
                    // Mostrar componentes individuales
                    document.querySelectorAll('[id^="metricas-individuales-"]').forEach(el => {
                        el.classList.remove('hidden');
                    });
                    
                    // Mostrar gráficos individuales
                    const graficosIndividuales = document.getElementById('graficos-individuales');
                    if (graficosIndividuales) {
                        graficosIndividuales.classList.remove('hidden');
                    }
                    
                    // Mostrar tabla de paciente
                    const tablaPacienteIndividual = document.getElementById('tabla-paciente-individual');
                    if (tablaPacienteIndividual) {
                        tablaPacienteIndividual.classList.remove('hidden');
                    }
                    
                    // Ocultar componentes grupales
                    document.querySelectorAll('[id^="metricas-grupales-"]').forEach(el => {
                        el.classList.add('hidden');
                    });
                    
                    // Ocultar gráficos y SLA grupales
                    const graficosGrupales = document.getElementById('graficos-grupales');
                    if (graficosGrupales) {
                        graficosGrupales.classList.add('hidden');
                    }
                    
                    const cumplimientoSla = document.getElementById('cumplimiento-sla');
                    if (cumplimientoSla) {
                        cumplimientoSla.classList.add('hidden');
                    }
                    
                    // Mostrar botón correcto
                    const btnIndividual = document.getElementById('generarInformeIndividual');
                    const btnGrupal = document.getElementById('generarInformeGrupal');
                    if (btnIndividual) btnIndividual.classList.remove('hidden');
                    if (btnGrupal) btnGrupal.classList.add('hidden');
                    
                    console.log("Modo individual establecido correctamente por script de inicialización.");
                });
                </script>
                """
                
                # Insertar el script antes del cierre de body
                html_content = html_content.replace('</body>', f'{js_mostrar_individual}</body>')
                
                js_show_charts = """
                <script>
                document.addEventListener('DOMContentLoaded', function() {
                    setTimeout(function() {
                        // Asegurar que los elementos estén visibles
                        const graficosIndividuales = document.getElementById('graficos-individuales');
                        if (graficosIndividuales) {
                            graficosIndividuales.style.display = 'grid';
                            graficosIndividuales.classList.remove('hidden');
                            
                            // Regenerar los gráficos individuales si hay funciones disponibles para ello
                            setTimeout(function() {
                                if (typeof updateComparisonChart === 'function') {
                                    console.log("Regenerando gráfico de comparación...");
                                    updateComparisonChart();
                                }
                                
                                if (typeof updateRadarChart === 'function') {
                                    console.log("Regenerando gráfico de radar...");
                                    updateRadarChart();
                                }
                                
                                console.log("Visibilidad y regeneración de gráficos individuales completada");
                            }, 200);
                        }
                    }, 800);
                });
                </script>
                """
                
                html_content = html_content.replace('</body>', f'{js_show_charts}</body>')
                
            else:
                # Modo grupal - Obtener datos de las métricas
                metricas = datos["metricas"]
                
                # Triage
                triage = metricas.get('triage', {})
                if triage and 'estadisticas' in triage:
                    html_content = html_content.replace("{{TRIAGE_PROMEDIO}}", self.formatear_tiempo(triage['estadisticas'].get('promedio', '-')))
                    html_content = html_content.replace("{{TRIAGE_MEDIANA}}", self.formatear_tiempo(triage['estadisticas'].get('mediana', '-')))
                    html_content = html_content.replace("{{TRIAGE_P90}}", self.formatear_tiempo(triage['estadisticas'].get('p90', '-')))
                
                # Consulta de Ingreso (CI)
                ci = metricas.get('consulta_ingreso', {})
                if ci and 'estadisticas' in ci:
                    html_content = html_content.replace("{{CI_PROMEDIO}}", self.formatear_tiempo(ci['estadisticas'].get('promedio', '-')))
                    html_content = html_content.replace("{{CI_MEDIANA}}", self.formatear_tiempo(ci['estadisticas'].get('mediana', '-')))
                    html_content = html_content.replace("{{CI_P90}}", self.formatear_tiempo(ci['estadisticas'].get('p90', '-')))
                
                # Laboratorios
                labs = metricas.get('laboratorios', {})
                if labs:
                    # Solicitud a espera (No realizado a En espera)
                    if 'estadisticas_solicitud' in labs:
                        html_content = html_content.replace("{{LABS_PROMEDIO_SE}}", self.formatear_tiempo(labs['estadisticas_solicitud'].get('promedio', '-')))
                        html_content = html_content.replace("{{LABS_MEDIANA_SE}}", self.formatear_tiempo(labs['estadisticas_solicitud'].get('mediana', '-')))
                        html_content = html_content.replace("{{LABS_P90_SE}}", self.formatear_tiempo(labs['estadisticas_solicitud'].get('p90', '-')))
                    
                    # Espera a resultados (En espera a Resultados)
                    if 'estadisticas_resultados' in labs:
                        html_content = html_content.replace("{{LABS_PROMEDIO_ER}}", self.formatear_tiempo(labs['estadisticas_resultados'].get('promedio', '-')))
                        html_content = html_content.replace("{{LABS_MEDIANA_ER}}", self.formatear_tiempo(labs['estadisticas_resultados'].get('mediana', '-')))
                        html_content = html_content.replace("{{LABS_P90_ER}}", self.formatear_tiempo(labs['estadisticas_resultados'].get('p90', '-')))

                    if 'estadisticas_total' in labs:
                        html_content = html_content.replace("{{LABS_PROMEDIO}}", self.formatear_tiempo(labs['estadisticas_total'].get('promedio', '-')))
                        html_content = html_content.replace("{{LABS_MEDIANA}}", self.formatear_tiempo(labs['estadisticas_total'].get('mediana', '-')))
                        html_content = html_content.replace("{{LABS_P90}}", self.formatear_tiempo(labs['estadisticas_total'].get('p90', '-')))             
                
                # Imágenes (IX)
                ix = metricas.get('imagenes', {})
                if ix:
                    # Solicitud a espera
                    if 'estadisticas_solicitud' in ix:
                        html_content = html_content.replace("{{IX_PROMEDIO_SE}}", self.formatear_tiempo(ix['estadisticas_solicitud'].get('promedio', '-')))
                        html_content = html_content.replace("{{IX_MEDIANA_SE}}", self.formatear_tiempo(ix['estadisticas_solicitud'].get('mediana', '-')))
                        html_content = html_content.replace("{{IX_P90_SE}}", self.formatear_tiempo(ix['estadisticas_solicitud'].get('p90', '-')))
                    
                    # Espera a resultados
                    if 'estadisticas_resultados' in ix:
                        html_content = html_content.replace("{{IX_PROMEDIO_ER}}", self.formatear_tiempo(ix['estadisticas_resultados'].get('promedio', '-')))
                        html_content = html_content.replace("{{IX_MEDIANA_ER}}", self.formatear_tiempo(ix['estadisticas_resultados'].get('mediana', '-')))
                        html_content = html_content.replace("{{IX_P90_ER}}", self.formatear_tiempo(ix['estadisticas_resultados'].get('p90', '-')))
                
                    if 'estadisticas_total' in ix:
                        html_content = html_content.replace("{{IX_PROMEDIO}}", self.formatear_tiempo(ix['estadisticas_total'].get('promedio', '-')))
                        html_content = html_content.replace("{{IX_MEDIANA}}", self.formatear_tiempo(ix['estadisticas_total'].get('mediana', '-')))
                        html_content = html_content.replace("{{IX_P90}}", self.formatear_tiempo(ix['estadisticas_total'].get('p90', '-')))    
                
                # Interconsulta
                ic = metricas.get('interconsulta', {})
                if ic:
                    # No abierta a abierta
                    if 'estadisticas_apertura' in ic:
                        html_content = html_content.replace("{{IC_PROMEDIO_NA}}", self.formatear_tiempo(ic['estadisticas_apertura'].get('promedio', '-')))
                        html_content = html_content.replace("{{IC_MEDIANA_NA}}", self.formatear_tiempo(ic['estadisticas_apertura'].get('mediana', '-')))
                        html_content = html_content.replace("{{IC_P90_NA}}", self.formatear_tiempo(ic['estadisticas_apertura'].get('p90', '-')))
                    
                    # Abierta a realizada
                    if 'estadisticas_realizacion' in ic:
                        html_content = html_content.replace("{{IC_PROMEDIO_AR}}", self.formatear_tiempo(ic['estadisticas_realizacion'].get('promedio', '-')))
                        html_content = html_content.replace("{{IC_MEDIANA_AR}}", self.formatear_tiempo(ic['estadisticas_realizacion'].get('mediana', '-')))
                        html_content = html_content.replace("{{IC_P90_AR}}", self.formatear_tiempo(ic['estadisticas_realizacion'].get('p90', '-')))
                
                    if 'estadisticas_total' in ic:
                        html_content = html_content.replace("{{IC_PROMEDIO}}", self.formatear_tiempo(ic['estadisticas_total'].get('promedio', '-')))
                        html_content = html_content.replace("{{IC_MEDIANA}}", self.formatear_tiempo(ic['estadisticas_total'].get('mediana', '-')))
                        html_content = html_content.replace("{{IC_P90}}", self.formatear_tiempo(ic['estadisticas_total'].get('p90', '-')))    
                
                # Revaloración
                rv = metricas.get('revaloracion', {})
                if rv and 'estadisticas' in rv:
                    html_content = html_content.replace("{{RV_PROMEDIO}}", self.formatear_tiempo(rv['estadisticas'].get('promedio', '-')))
                    html_content = html_content.replace("{{RV_MEDIANA}}", self.formatear_tiempo(rv['estadisticas'].get('mediana', '-')))
                    html_content = html_content.replace("{{RV_P90}}", self.formatear_tiempo(rv['estadisticas'].get('p90', '-')))
                
                # Tiempo total
                tiempo_total = metricas.get('tiempo_total', {})
                if tiempo_total and 'estadisticas' in tiempo_total:
                    html_content = html_content.replace("{{TIEMPO_PROMEDIO_TOTAL}}", self.formatear_tiempo(tiempo_total['estadisticas'].get('promedio', '-')))
                    html_content = html_content.replace("{{TIEMPO_MEDIANA_TOTAL}}", self.formatear_tiempo(tiempo_total['estadisticas'].get('mediana', '-')))
                    html_content = html_content.replace("{{TIEMPO_P90_TOTAL}}", self.formatear_tiempo(tiempo_total['estadisticas'].get('p90', '-')))
                    
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
                
            # Si hay datos de gráficos y no estamos en modo individual, generar JavaScript para actualizar los gráficos grupales
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
            
            js_tab_switch = """
            <script>
            document.addEventListener('DOMContentLoaded', function() {
                console.log("DOM cargado, configurando manejo de modo");
                
                // Verificar el modo actual en el body
                const modoActual = document.body.getAttribute('data-modo-actual') || 'grupal';
                console.log("Modo actual detectado:", modoActual);
                
                // Aplicar visibilidad basada en el modo
                if (modoActual === 'individual') {
                    console.log("Aplicando modo individual");
                    // Activar pestaña individual
                    const tabIndividual = document.getElementById('tabIndividual');
                    if (tabIndividual) {
                        tabIndividual.classList.add('tab-active');
                        tabIndividual.classList.remove('text-gray-500');
                        
                        const tabGrupal = document.getElementById('tabGrupal');
                        if (tabGrupal) {
                            tabGrupal.classList.remove('tab-active');
                            tabGrupal.classList.add('text-gray-500');
                        }
                    }
                    
                    // Mostrar componentes individuales
                    document.querySelectorAll('[id^="metricas-individuales-"]').forEach(el => {
                        el.classList.remove('hidden');
                        console.log("Mostrando elemento individual:", el.id);
                    });
                    
                    const graficosIndividuales = document.getElementById('graficos-individuales');
                    if (graficosIndividuales) {
                        graficosIndividuales.classList.remove('hidden');
                        console.log("Mostrando gráficos individuales");
                    }
                    
                    const tablaPacienteIndividual = document.getElementById('tabla-paciente-individual');
                    if (tablaPacienteIndividual) {
                        tablaPacienteIndividual.classList.remove('hidden');
                        console.log("Mostrando tabla paciente individual");
                    }
                    
                    // Ocultar contenido grupal
                    document.querySelectorAll('[id^="metricas-grupales-"]').forEach(el => {
                        el.classList.add('hidden');
                        console.log("Ocultando elemento grupal:", el.id);
                    });
                    
                    const graficosGrupales = document.getElementById('graficos-grupales');
                    if (graficosGrupales) {
                        graficosGrupales.classList.add('hidden');
                        console.log("Ocultando gráficos grupales");
                    }
                    
                    const cumplimientoSla = document.getElementById('cumplimiento-sla');
                    if (cumplimientoSla) {
                        cumplimientoSla.classList.add('hidden');
                        console.log("Ocultando cumplimiento SLA");
                    }
                    
                    // Mostrar botón correspondiente
                    const btnIndividual = document.getElementById('generarInformeIndividual');
                    const btnGrupal = document.getElementById('generarInformeGrupal');
                    if (btnIndividual) btnIndividual.classList.remove('hidden');
                    if (btnGrupal) btnGrupal.classList.add('hidden');
                }
            });
            </script>
            """

            html_content = html_content.replace('</body>', f'{js_tab_switch}</body>')
            
            return html_content
            
        except Exception as e:
            print(f"Error al reemplazar datos en HTML: {str(e)}")
            traceback.print_exc()
            return html_content

    def exportar_pdf(self):
        """Exporta el informe actual a PDF"""
        try:
            from Front_end.styles.exportar_pdf import export_report_to_pdf
            
            # Mostrar un mensaje de inicio de exportación
            self.mostrar_mensaje_informacion("Iniciando exportación", 
                                        "Se iniciará el proceso de exportación a PDF.\n"
                                        "Esto puede tardar unos momentos, por favor espere...")
            
            # Dar un breve tiempo para que el mensaje informativo se muestre
            QTimer.singleShot(500, lambda: self._iniciar_exportacion_pdf())
            
        except Exception as e:
            print(f"Error al exportar PDF: {str(e)}")
            import traceback
            traceback.print_exc()
            self.mostrar_mensaje_error("Error al exportar", 
                                    f"No se pudo exportar el informe a PDF: {str(e)}")
                                    
    def _iniciar_exportacion_pdf(self):
        """Inicia el proceso de exportación a PDF después de mostrar el mensaje inicial"""
        try:
            from Front_end.styles.exportar_pdf import export_report_to_pdf
            
            # Llamar a la función de exportación con nuestra vista web
            export_report_to_pdf(self.web_view)
            
        except Exception as e:
            print(f"Error al iniciar exportación PDF: {str(e)}")
            import traceback
            traceback.print_exc()
            self.mostrar_mensaje_error("Error al exportar", 
                                    f"No se pudo iniciar la exportación del informe a PDF: {str(e)}")
    
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
                "Revaloración": "rv"
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
            json.dumps(self._obtener_tiempos_promedio(datos_metricas)),
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
                self.mostrar_mensaje_advertencia("Error", "Por favor seleccione fechas válidas")
                return
                    
            # Actualizar las variables de instancia con los nuevos filtros
            self.fecha_inicio = datetime.strptime(fecha_inicio_str, "%Y-%m-%d")
            self.fecha_fin = datetime.strptime(fecha_fin_str, "%Y-%m-%d")
            self.area_seleccionada = area
            
            # Regenerar el informe con los nuevos datos
            self.actualizar_datos_informe()
            
            if self.modo_actual == "individual" and self.paciente_seleccionado:
                js_code_adicional = """
                setTimeout(function() {
                    // Forzar modo individual después de actualizar datos
                    document.body.setAttribute('data-modo-actual', 'individual');
                    
                    // Simular clic en la pestaña individual para asegurar que esté activa
                    const tabIndividual = document.getElementById('tabIndividual');
                    if (tabIndividual) {
                        tabIndividual.click();
                        
                        // También asegurarnos que el contenido individual esté visible
                        document.querySelectorAll('[id^="metricas-individuales-"]').forEach(el => {
                            el.classList.remove('hidden');
                        });
                        
                        // Y ocultar el contenido grupal
                        document.querySelectorAll('[id^="metricas-grupales-"]').forEach(el => {
                            el.classList.add('hidden');
                        });
                        
                        // Asegurar visibilidad de gráficos individuales
                        const graficosIndividuales = document.getElementById('graficos-individuales');
                        if (graficosIndividuales) graficosIndividuales.classList.remove('hidden');
                        
                        const graficosGrupales = document.getElementById('graficos-grupales');
                        if (graficosGrupales) graficosGrupales.classList.add('hidden');
                    }
                }, 500);
                """
                self.web_view.page().runJavaScript(js_code_adicional)
            
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
                
                // Código para asegurar que la búsqueda siga funcionando después de generar informe
                function reiniciarBusquedaPacientes() {{
                    const searchInput = document.getElementById('searchPatient');
                    if (searchInput) {{
                        // No limpiar el campo si estamos en modo individual
                        if (document.body.getAttribute('data-modo-actual') !== 'individual') {{
                            searchInput.value = '';
                        }}
                        
                        // Asegurar que el input está habilitado
                        searchInput.disabled = false;
                        
                        // Reconectar eventos si es necesario
                        if (!searchInput._hasSearchEvents) {{
                            searchInput.addEventListener('keypress', function(e) {{
                                if (e.key === 'Enter') {{
                                    e.preventDefault();
                                    const termino = this.value.trim();
                                    if (termino && window.handler) {{
                                        window.handler.buscarPacientes(termino);
                                    }}
                                }}
                            }});
                            searchInput._hasSearchEvents = true;
                        }}
                    }}
                }}
                
                // Ejecutar ambas funciones con retrasos para asegurar que el DOM esté listo
                setTimeout(setAreaSelection, 100);
                setTimeout(reiniciarBusquedaPacientes, 500);
            }})();
            """
            
            self.web_view.page().runJavaScript(js_code)
            
            self.mostrar_mensaje_informacion("Informe Generado", 
                                        f"Informe generado con éxito para el período: {fecha_inicio_str} a {fecha_fin_str}")
            QTimer.singleShot(700, self.configurar_busqueda_pacientes)

        except Exception as e:
            print(f"Error generating report: {str(e)}")
            import traceback
            traceback.print_exc()
            self.mostrar_mensaje_informacion("Error", f"Error al generar informe: {str(e)}", QMessageBox.Critical)

    # Crear un alias para mantener la compatibilidad con código existente
    generarInformeConFiltros = generar_informe_con_filtros

    def cambiar_modo(self, modo):
        """Cambia entre modo individual y grupal"""
        if modo != self.modo_actual:
            self.modo_actual = modo
            
            # Resetear el paciente seleccionado si cambiamos a modo grupal
            if modo == "grupal":
                self.paciente_seleccionado = None
                
            # Actualizar interfaz inmediatamente
            self.actualizar_datos_informe()
            
            # Mostrar/ocultar botones según el modo
            js_code = """
            if ("%s" === "individual") {
                document.getElementById('generarInformeGrupal').classList.add('hidden');
                document.getElementById('generarInformeIndividual').classList.remove('hidden');
            } else {
                document.getElementById('generarInformeGrupal').classList.remove('hidden');
                document.getElementById('generarInformeIndividual').classList.add('hidden');
            }
            """ % modo
            
            self.web_view.page().runJavaScript(js_code)
            
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
        self.report_generator.cambiar_modo(modo)
        
    @pyqtSlot(str)
    def buscarPacientes(self, termino):
        """Busca pacientes cuando se presiona Enter en el campo de búsqueda"""
        print(f"Buscando paciente con término: {termino}")
        
        # Evitar búsqueda adicional si el término parece ser un resultado ya seleccionado
        if " - " in termino and len(termino.split(" - ")) >= 2:
            print(f"Ignorando búsqueda para término que parece resultado ya seleccionado: {termino}")
            return
            
        if termino and len(termino.strip()) >= 1:  # Permitir búsquedas con al menos 1 carácter
            # Forzar modo individual al buscar pacientes
            self.report_generator.modo_actual = "individual"
            
            # Realizar la búsqueda
            resultados = self.report_generator.buscar_paciente(termino)
            
            # Mostrar los resultados
            self.report_generator.mostrar_resultados_busqueda(resultados)

    @pyqtSlot(str, str, str, str)
    def seleccionarPaciente(self, paciente_id, nombre, documento, ubicacion):
        """Selecciona un paciente para el informe individual"""
        print(f"WebHandler: Seleccionando paciente ID={paciente_id}, Nombre={nombre}")
        # Forzar el modo individual antes de llamar a seleccionar_paciente
        self.report_generator.modo_actual = "individual"
        self.report_generator.seleccionar_paciente(paciente_id, nombre, documento, ubicacion)
        
    @pyqtSlot(str, str)
    def generarInformeIndividual(self, fecha_inicio, fecha_fin):
        """Genera un informe individual para el paciente seleccionado"""
        if not self.report_generator.paciente_seleccionado:
            self.report_generator.mostrar_mensaje_advertencia(
                "Error", "No se ha seleccionado ningún paciente"
            )
            return
        
        # Asegurar que estamos en modo individual
        self.report_generator.modo_actual = "individual"
        
        # Actualizar las fechas
        try:
            self.report_generator.fecha_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d")
            self.report_generator.fecha_fin = datetime.strptime(fecha_fin, "%Y-%m-%d")
        except ValueError:
            # Si hay error en el formato de fecha, usar el rango por defecto
            self.report_generator.fecha_inicio = datetime.now() - timedelta(days=30)
            self.report_generator.fecha_fin = datetime.now()
        
        # Generar el informe
        self.report_generator.actualizar_datos_informe()