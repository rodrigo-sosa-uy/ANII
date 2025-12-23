% =========================================================================
% SCRIPT ESTANDARIZADO: RADIACIÓN SOLAR DIARIA
% =========================================================================
clc; clear; close all;

% --- CONFIGURACIÓN ---
target_date = '2025_12_22'; 

% 1. Rutas
if isempty(mfilename)
    script_path = pwd;
else
    script_path = fileparts(mfilename('fullpath'));
end

filename = [target_date, '_radiation.csv'];
full_path = fullfile(script_path, filename);
fprintf('Procesando: %s\n', filename);

if ~isfile(full_path), error('Archivo no encontrado.'); end

% 2. Carga
opts = detectImportOptions(full_path);
opts.VariableNamingRule = 'preserve';
data = readtable(full_path, opts);

if isempty(data), warning('CSV vacío.'); return; end

raw_time = data{:, 1}; 
val_rad = data{:, 2}; 

% Tiempo
t = datetime(target_date + " " + string(raw_time), 'InputFormat', 'yyyy_MM_dd HH:mm:ss');
t_start = datetime(target_date + " 00:00:00", 'InputFormat', 'yyyy_MM_dd HH:mm:ss');
t_end   = datetime(target_date + " 23:59:59", 'InputFormat', 'yyyy_MM_dd HH:mm:ss');

% Limpieza (Negativos a 0)
val_rad(val_rad < 0) = 0;

% 3. Gráfico
fig = figure('Name', 'Radiación', 'Color', 'w', 'Position', [100, 100, 1000, 600]);
plot(t, val_rad, 'LineWidth', 1.5, 'Color', '#e67e22'); % Naranja
title(['Radiación Solar - ', strrep(target_date, '_', '-')]);
ylabel('Irradiancia (W/m^2)');
xlabel('Hora');
grid on; grid minor;
xtickformat('HH:mm');
xlim([t_start, t_end]);

% Estadísticas visuales
[max_val, idx] = max(val_rad);
text(t(idx), max_val, sprintf(' Pico: %.0f W/m^2', max_val), 'VerticalAlignment', 'bottom');

% 4. Guardar Imagen
img_name = [target_date, '_analisis_radiacion.png'];
saveas(fig, fullfile(script_path, img_name));
fprintf('Imagen guardada: %s\n', img_name);

% 5. Generar Reporte de Texto
% Calculamos energía (Wh/m2) integrando la curva
hours_vec = hour(t) + minute(t)/60 + second(t)/3600;
energy_wh = trapz(hours_vec, val_rad);

txt_name = [target_date, '_resumen_radiacion.txt'];
fid = fopen(fullfile(script_path, txt_name), 'w');

if fid ~= -1
    fprintf(fid, '========================================\r\n');
    fprintf(fid, ' RESUMEN RADIACIÓN: %s\r\n', target_date);
    fprintf(fid, '========================================\r\n\r\n');
    fprintf(fid, '🌞 IRRADIANCIA (W/m^2):\r\n');
    fprintf(fid, '   Pico Máximo:   %.2f\r\n', max_val);
    fprintf(fid, '   Promedio Día:  %.2f\r\n', mean(val_rad));
    fprintf(fid, '   Mínimo:        %.2f\r\n\r\n', min(val_rad));
    fprintf(fid, '⚡ ENERGÍA ACUMULADA:\r\n');
    fprintf(fid, '   Total Diaria:  %.2f Wh/m^2\r\n', energy_wh);
    fprintf(fid, '   Horas de Luz:  %.1f h (aprox > 10 W/m^2)\r\n', sum(val_rad > 10) * (mean(diff(hours_vec))));
    fclose(fid);
    fprintf('Reporte guardado: %s\n', txt_name);
end