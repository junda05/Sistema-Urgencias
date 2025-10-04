// Funcionalidad de pestañas
document.getElementById('tabIndividual').addEventListener('click', function() {
    this.classList.add('active');
    document.getElementById('tabGrupal').classList.remove('active');
    document.getElementById('filtroIndividual').classList.remove('hidden');
    document.getElementById('filtroGrupal').classList.add('hidden');
    
    // Mostrar métricas individuales
    document.querySelectorAll('[id^="metricas-individuales-"]').forEach(el => el.classList.remove('hidden'));
    document.querySelectorAll('[id^="metricas-grupales-"]').forEach(el => el.classList.add('hidden'));
    
    // Cambiar gráficos
    document.getElementById('graficos-grupales').classList.add('hidden');
    document.getElementById('graficos-individuales').classList.remove('hidden');
    
    // Cambiar tabla
    document.getElementById('tabla-pacientes-grupal').classList.add('hidden');
    document.getElementById('tabla-paciente-individual').classList.remove('hidden');
});

document.getElementById('tabGrupal').addEventListener('click', function() {
    this.classList.add('active');
    document.getElementById('tabIndividual').classList.remove('active');
    document.getElementById('filtroGrupal').classList.remove('hidden');
    document.getElementById('filtroIndividual').classList.add('hidden');
    
    // Mostrar métricas grupales
    document.querySelectorAll('[id^="metricas-individuales-"]').forEach(el => el.classList.add('hidden'));
    document.querySelectorAll('[id^="metricas-grupales-"]').forEach(el => el.classList.remove('hidden'));
    
    // Cambiar gráficos
    document.getElementById('graficos-grupales').classList.remove('hidden');
    document.getElementById('graficos-individuales').classList.add('hidden');
    
    // Cambiar tabla
    document.getElementById('tabla-pacientes-grupal').classList.remove('hidden');
    document.getElementById('tabla-paciente-individual').classList.add('hidden');
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

// Gráficos
window.onload = function() {
    // Gráfico de línea de tiempo
    const timelineCtx = document.getElementById('timelineChart').getContext('2d');
    const timelineChart = new Chart(timelineCtx, {
        type: 'line',
        data: {
            labels: ['1 Dic', '2 Dic', '3 Dic', '4 Dic', '5 Dic', '6 Dic', '7 Dic', '8 Dic', '9 Dic', '10 Dic', '11 Dic', '12 Dic', '13 Dic', '14 Dic', '15 Dic'],
            datasets: [{
                label: 'Tiempo promedio (minutos)',
                data: [240, 255, 235, 270, 220, 210, 230, 245, 260, 250, 240, 235, 225, 240, 255],
                borderColor: '#5385B7',
                backgroundColor: 'rgba(83, 133, 183, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4
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
                    beginAtZero: false,
                    title: {
                        display: true,
                        text: 'Minutos'
                    }
                }
            }
        }
    });
    
    // Gráfico de barras
    const barCtx = document.getElementById('barChart').getContext('2d');
    const barChart = new Chart(barCtx, {
        type: 'bar',
        data: {
            labels: ['Triaje', 'Consulta de Ingreso', 'Laboratorios', 'Imágenes', 'Interconsulta', 'Re-valoración'],
            datasets: [{
                label: 'Tiempo promedio (minutos)',
                data: [17, 20, 65, 70, 50, 40],
                backgroundColor: [
                    '#28a745',
                    '#5385B7',
                    '#E6B800',
                    '#4A7296',
                    '#659BD1',
                    '#B75353'
                ],
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
            labels: ['Triaje', 'Consulta de Ingreso', 'Laboratorios', 'Imágenes', 'Interconsulta', 'Re-valoración'],
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
    
    // Función para crear gráficos de gauge
    function createGauge(elementId, value, color) {
        const ctx = document.getElementById(elementId).getContext('2d');
        return new Chart(ctx, {
            type: 'doughnut',
            data: {
                datasets: [{
                    data: [value, 100 - value],
                    backgroundColor: [color, '#E8F0F7'],
                    borderWidth: 0,
                    cutout: '80%'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        enabled: false
                    }
                }
            }
        });
    }
    
    // Crear gráficos de gauge
    createGauge('gaugeTriaje', 92, '#28a745');
    createGauge('gaugeCI', 85, '#5385B7');
    createGauge('gaugeLab', 78, '#E6B800');
    createGauge('gaugeIX', 82, '#4A7296');
    createGauge('gaugeIC', 65, '#659BD1');
    createGauge('gaugeRV', 70, '#B75353');
};

// Funcionalidad de exportación
document.getElementById('exportPdf').addEventListener('click', function() {
    alert('Exportando informe en formato PDF...');
});

document.getElementById('exportExcel').addEventListener('click', function() {
    alert('Exportando informe en formato Excel...');
});

// Funcionalidad de generación de informe
document.getElementById('generarInforme').addEventListener('click', function() {
    alert('Generando informe con los filtros seleccionados...');
});

// Cambio de tipo de reporte grupal
document.getElementById('tipoReporteGrupal').addEventListener('change', function() {
    if (this.value === 'areas') {
        document.getElementById('areaSelector').classList.remove('hidden');
    } else {
        document.getElementById('areaSelector').classList.remove('hidden');
    }
});

// Actualizar gráficos con nuevas fechas
document.getElementById('actualizarGraficos').addEventListener('click', function() {
    const fechaInicio = document.getElementById('chartDateStart').value;
    const fechaFin = document.getElementById('chartDateEnd').value;
    alert(`Actualizando gráficos para el período: ${fechaInicio} - ${fechaFin}`);
    // Aquí iría la lógica para actualizar los gráficos con las nuevas fechas
});