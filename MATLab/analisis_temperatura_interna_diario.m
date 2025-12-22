% =========================================================================
% SCRIPT DE ANÁLISIS DE TEMPERATURA INTERNA (CÁMARA EVAPORACIÓN)
% =========================================================================
clc; clear; close all;

% --- CONFIGURACIÓN DE USUARIO ---
% Define la fecha que quieres analizar (Formato: YYYY_MM_DD)
target_date = '2025_12_20';

% -------------------------------------------------------------------------

% 1. Construcción de la ruta del archivo dinámicamente
if isempty(mfilename)
    script_path = pwd;
else
    script_path = fileparts(mfilename('fullpath'));
end

filename = [target_date, '_temperature.csv'];
full_path = fullfile(script_path, filename);

fprintf('Buscando archivo en: %s\n', full_path);

% 2. Verificación de existencia
if ~isfile(full_path)
    error('El archivo no se encuentra en la misma carpeta que el script.\nBusqué en: %s', full_path);
end

% 3. Lectura de los datos
opts = detectImportOptions(full_path);
opts.VariableNamingRule = 'preserve';
data = readtable(full_path, opts);

% Verificar si la tabla está vacía
if isempty(data)
    warning('El archivo CSV está vacío.');
    return;
end

% 4. Procesamiento de datos
% Asumimos que la columna 1 es 'Time' y la columna 2 es 'Internal_Temp'
raw_time = data{:, 1}; 
temp_vals = data{:, 2}; 

% Convertir la hora (string) a datetime
time_str = string(raw_time);
full_datetime_str = target_date + " " + time_str;

% Formato de entrada: YYYY_MM_DD HH:mm:ss
t = datetime(full_datetime_str, 'InputFormat', 'yyyy_MM_dd HH:mm:ss');

% Límites del día completo (00:00:00 a 23:59:59)
t_start = datetime(target_date + " 00:00:00", 'InputFormat', 'yyyy_MM_dd HH:mm:ss');
t_end   = datetime(target_date + " 23:59:59", 'InputFormat', 'yyyy_MM_dd HH:mm:ss');

% 5. Graficación
fig = figure('Name', 'Análisis de Temperatura Cámara', 'Color', 'w');

% Usamos rojo (#c0392b) para temperatura
plot(t, temp_vals, 'LineWidth', 1.5, 'Color', '#c0392b'); 

% Formato de Ejes
title(['Perfil de Temperatura Interna - ', strrep(target_date, '_', '-')]);
xlabel('Hora del día');
ylabel('Temperatura (°C)');
grid on;
grid minor;

% Formatear el eje X para mostrar las 24 horas completas
xtickformat('HH:mm');
xlim([t_start, t_end]); 

% 6. Estadísticas Básicas
max_val = max(temp_vals);
mean_val = mean(temp_vals);
min_val = min(temp_vals);

% Añadir anotación (Caja de texto)
dim = [0.15 0.8 0.3 0.1]; 
str = {['Máxima: ', num2str(max_val, '%.2f'), ' °C'], ...
       ['Promedio: ', num2str(mean_val, '%.2f'), ' °C'], ...
       ['Mínima: ', num2str(min_val, '%.2f'), ' °C']};

annotation('textbox', dim, 'String', str, 'FitBoxToText', 'on', ...
           'BackgroundColor', 'white', 'FaceAlpha', 0.8);

fprintf('--- Estadísticas ---\n');
fprintf('Temperatura Máxima: %.2f °C\n', max_val);
fprintf('Temperatura Promedio: %.2f °C\n', mean_val);

% -------------------------------------------------------------------------
% 7. GUARDAR IMAGEN AUTOMÁTICAMENTE
% -------------------------------------------------------------------------
img_name = [target_date, '_analisis_temperatura.png'];
full_save_path = fullfile(script_path, img_name);

try
    saveas(fig, full_save_path);
    fprintf('Imagen guardada automáticamente en: %s\n', full_save_path);
catch err
    warning('No se pudo guardar la imagen: %s', err.message);
end