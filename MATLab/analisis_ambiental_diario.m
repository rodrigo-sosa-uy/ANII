% =========================================================================
% SCRIPT DE ANÁLISIS AMBIENTAL DIARIO (BME280)
% =========================================================================
clc; clear; close all;

% --- CONFIGURACIÓN DE USUARIO ---
% Define la fecha a analizar
target_date = '2025_12_20'; 

% -------------------------------------------------------------------------
% 1. Configuración de Rutas
if isempty(mfilename)
    script_path = pwd;
else
    script_path = fileparts(mfilename('fullpath'));
end

filename = [target_date, '_environment.csv'];
full_path = fullfile(script_path, filename);

fprintf('Analizando datos ambientales: %s\n', full_path);

% 2. Verificación y Carga
if ~isfile(full_path)
    error('El archivo no existe en la carpeta actual: %s', filename);
end

opts = detectImportOptions(full_path);
opts.VariableNamingRule = 'preserve';
data = readtable(full_path, opts);

if isempty(data)
    warning('El archivo CSV está vacío.');
    return;
end

% 3. Procesamiento de Datos
% Estructura esperada: Time, Amb_Temp(°C), Humidity(%), Pressure(hPa)
% Usamos índices numéricos para robustez
raw_time = data{:, 1};
val_temp = data{:, 2};
val_hum  = data{:, 3};
val_pres = data{:, 4};

% Crear vector de tiempo datetime
time_str = string(raw_time);
t = datetime(target_date + " " + time_str, 'InputFormat', 'yyyy_MM_dd HH:mm:ss');

% Límites del día (00:00 - 23:59)
t_start = datetime(target_date + " 00:00:00", 'InputFormat', 'yyyy_MM_dd HH:mm:ss');
t_end   = datetime(target_date + " 23:59:59", 'InputFormat', 'yyyy_MM_dd HH:mm:ss');

% Fecha formateada para títulos (sin guiones bajos para evitar subíndices)
date_display = strrep(target_date, '_', '-');

% -------------------------------------------------------------------------
% 4. GRAFICACIÓN (TRIPLE SUBPLOT)
% -------------------------------------------------------------------------
fig = figure('Name', ['Ambiente - ', target_date], 'Color', 'w', 'Position', [100, 50, 1000, 900]);

% --- 1. TEMPERATURA ---
subplot(3, 1, 1);
plot(t, val_temp, 'LineWidth', 1.5, 'Color', '#D95319'); % Naranja rojizo
title(['Temperatura Ambiente - ', date_display]); % Fecha corregida
ylabel('Temp (°C)');
grid on; grid minor;
xtickformat('HH:mm');
xlim([t_start, t_end]);

% Ajuste dinámico de límites Y (Margen del 10% para que entren etiquetas)
range_t = max(val_temp) - min(val_temp);
if range_t == 0, range_t = 1; end
ylim([min(val_temp) - range_t*0.15, max(val_temp) + range_t*0.15]);

% Marcadores de Min/Max con fondo blanco para legibilidad
[max_t, idx_max_t] = max(val_temp);
[min_t, idx_min_t] = min(val_temp);

text(t(idx_max_t), max_t, sprintf(' Max: %.1f', max_t), ...
    'VerticalAlignment', 'bottom', 'HorizontalAlignment', 'left', ...
    'BackgroundColor', 'w', 'EdgeColor', 'none', 'Margin', 1);

text(t(idx_min_t), min_t, sprintf(' Min: %.1f', min_t), ...
    'VerticalAlignment', 'top', 'HorizontalAlignment', 'left', ...
    'BackgroundColor', 'w', 'EdgeColor', 'none', 'Margin', 1);


% --- 2. HUMEDAD ---
subplot(3, 1, 2);
plot(t, val_hum, 'LineWidth', 1.5, 'Color', '#0072BD'); % Azul
title(['Humedad Relativa - ', date_display]); % Fecha corregida
ylabel('Humedad (%)');
grid on; grid minor;
xtickformat('HH:mm');
xlim([t_start, t_end]);
ylim([-5 105]); % Margen extra para etiquetas cerca de 0 o 100

% Línea promedio
yline(mean(val_hum), '--', sprintf('Prom: %.1f%%', mean(val_hum)), ...
    'Color', '#0072BD', 'LabelHorizontalAlignment', 'right');


% --- 3. PRESIÓN ---
subplot(3, 1, 3);
plot(t, val_pres, 'LineWidth', 1.5, 'Color', '#77AC30'); % Verde
title(['Presión Atmosférica - ', date_display]); % Fecha corregida
ylabel('Presión (hPa)');
xlabel('Hora del día');
grid on; grid minor;
xtickformat('HH:mm');
xlim([t_start, t_end]);

% Ajuste dinámico de límites Y para presión (suele variar muy poco)
range_p = max(val_pres) - min(val_pres);
if range_p == 0, range_p = 1; end
ylim([min(val_pres) - range_p*0.2, max(val_pres) + range_p*0.2]);

% Marcador de Promedio (Mejor que Min/Max para presión que es ruidosa)
yline(mean(val_pres), '--', sprintf('Prom: %.1f hPa', mean(val_pres)), ...
    'Color', '#77AC30', 'LabelHorizontalAlignment', 'right', 'LabelVerticalAlignment', 'bottom');


% -------------------------------------------------------------------------
% 5. ANÁLISIS ESTADÍSTICO EN CONSOLA
% -------------------------------------------------------------------------
fprintf('\n========================================\n');
fprintf(' RESUMEN AMBIENTAL: %s\n', target_date);
fprintf('========================================\n');

fprintf('🌡️ TEMPERATURA (°C):\n');
fprintf('   Máxima: %.2f  |  Mínima: %.2f  |  Promedio: %.2f\n', max(val_temp), min(val_temp), mean(val_temp));
fprintf('   Desviación Estándar: %.3f\n\n', std(val_temp));

fprintf('💧 HUMEDAD (%%):\n');
fprintf('   Máxima: %.2f  |  Mínima: %.2f  |  Promedio: %.2f\n\n', max(val_hum), min(val_hum), mean(val_hum));

fprintf('⏲️ PRESIÓN (hPa):\n');
fprintf('   Máxima: %.2f  |  Mínima: %.2f  |  Promedio: %.2f\n', max(val_pres), min(val_pres), mean(val_pres));
fprintf('========================================\n');


% -------------------------------------------------------------------------
% 6. GUARDADO AUTOMÁTICO
% -------------------------------------------------------------------------
img_name = [target_date, '_analisis_ambiental.png'];
full_save_path = fullfile(script_path, img_name);

try
    saveas(fig, full_save_path);
    fprintf('Imagen guardada automáticamente en: %s\n', full_save_path);
catch err
    warning('No se pudo guardar la imagen: %s', err.message);
end