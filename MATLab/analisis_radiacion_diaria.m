% =========================================================================
% SCRIPT PARA GRAFICAR DATOS DE RADIACIÓN DESDE CSV
% =========================================================================
clc; clear; close all;

% --- CONFIGURACIÓN DE USUARIO ---
% Define la fecha que quieres analizar (Formato: YYYY_MM_DD)
% El archivo CSV debe llamarse: '2025_11_25_radiation.csv'
% y debe estar EN LA MISMA CARPETA que este script.
target_date = '2025_11_25';

% -------------------------------------------------------------------------

% 1. Construcción de la ruta del archivo dinámicamente
% Obtenemos la ruta de la carpeta donde está guardado este script
if isempty(mfilename)
    % Si el código se ejecuta bloque a bloque sin guardar el archivo, usa pwd
    script_path = pwd;
else
    script_path = fileparts(mfilename('fullpath'));
end

filename = [target_date, '_radiation.csv'];
full_path = fullfile(script_path, filename);

fprintf('Buscando archivo en: %s\n', full_path);

% 2. Verificación de existencia
if ~isfile(full_path)
    error('El archivo no se encuentra en la misma carpeta que el script.\nBusqué en: %s', full_path);
end

% 3. Lectura de los datos
opts = detectImportOptions(full_path);
opts.VariableNamingRule = 'preserve'; % Para mantener caracteres especiales en headers
data = readtable(full_path, opts);

% Verificar si la tabla está vacía
if isempty(data)
    warning('El archivo CSV está vacío.');
    return;
end

% 4. Procesamiento de datos
% Asumimos que la columna 1 es 'Time' y la columna 2 es 'Radiation'
% Extraemos los datos crudos
raw_time = data{:, 1}; % Columna de tiempo (HH:MM:SS)
radiation_vals = data{:, 2}; % Columna de radiación

% Convertir la hora (string) a datetime de MATLAB
% Concatenamos la fecha del nombre del archivo con la hora del CSV para tener un eje X real
time_str = string(raw_time);
full_datetime_str = target_date + " " + time_str;

% Formato de entrada: YYYY_MM_DD HH:mm:ss
t = datetime(full_datetime_str, 'InputFormat', 'yyyy_MM_dd HH:mm:ss');

% 5. Graficación
figure('Name', 'Análisis de Radiación Solar', 'Color', 'w');
plot(t, radiation_vals, 'LineWidth', 1.5, 'Color', '#D95319'); % Color naranja quemado

% Formato de Ejes
title(['Perfil de Radiación Solar - ', strrep(target_date, '_', '-')]);
xlabel('Hora del día');
ylabel('Radiación (W/m^2)');
grid on;
grid minor;

% Formatear el eje X para mostrar solo horas y minutos
xtickformat('HH:mm');
xlim([min(t), max(t)]); % Ajustar límites al rango de datos

% 6. Estadísticas Básicas
max_rad = max(radiation_vals);
mean_rad = mean(radiation_vals);

% Añadir anotación en el gráfico con los valores máximos
dim = [0.15 0.8 0.3 0.1]; % Posición x, y, ancho, alto
str = {['Máximo: ', num2str(max_rad, '%.2f'), ' W/m^2'], ...
       ['Promedio: ', num2str(mean_rad, '%.2f'), ' W/m^2']};
annotation('textbox', dim, 'String', str, 'FitBoxToText', 'on', ...
           'BackgroundColor', 'white', 'FaceAlpha', 0.8);

fprintf('--- Estadísticas ---\n');
fprintf('Radiación Máxima: %.2f W/m^2\n', max_rad);
fprintf('Radiación Promedio: %.2f W/m^2\n', mean_rad);
